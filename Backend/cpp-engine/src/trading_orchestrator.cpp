#include "trading_orchestrator.h"
#include "trading_engine.h"
#include "data_conversion.h"
#include "json_helpers.h"
#include "logger.h"
#include "trading_exceptions.h"
#include "error_utils.h"
#include <sstream>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <chrono>
#include <thread>
#include <set>

// Main orchestration methods
Result<std::string> TradingOrchestrator::runSimulation(const TradingConfig& config,
                                                      Portfolio& portfolio,
                                                      MarketData* market_data,
                                                      DataProcessor* data_processor,
                                                      StrategyManager* strategy_manager,
                                                      ResultCalculator* result_calculator) {
    Logger::debug("TradingOrchestrator::runSimulation called with: symbols=[", config.symbols.size(), " symbols], "
                 "start_date='", config.start_date, "', end_date='", config.end_date, "', capital=", config.starting_capital);
    
    logOrchestrationStart(config);
    
    // Use common validation
    auto validation_result = validateSimulationParameters(config, market_data);
    if (validation_result.isError()) {
        return Result<std::string>(validation_result.getError());
    }
    
    // Reset portfolio with new capital
    portfolio = Portfolio(config.starting_capital);
    Logger::debug("Portfolio initialized with capital: ", config.starting_capital, ", initial capital: ", portfolio.getInitialCapital());
    
    // Create a dummy execution service for this simulation
    auto execution_service = std::make_unique<ExecutionService>();
    auto progress_service = std::make_unique<ProgressService>();
    auto portfolio_allocator = std::make_unique<PortfolioAllocator>();
    
    // Run backtest and convert to JSON
    auto backtest_result = runBacktest(config, portfolio, market_data, execution_service.get(), 
                                      progress_service.get(), portfolio_allocator.get(), 
                                      data_processor, strategy_manager, result_calculator);
    if (backtest_result.isError()) {
        return Result<std::string>(backtest_result.getError());
    }
    
    const auto& result = backtest_result.getValue();
    Logger::debug("Backtest completed. Result: starting_capital=", result.starting_capital, 
                 ", ending_value=", result.ending_value, ", total_return_pct=", result.total_return_pct,
                 ", total_trades=", result.total_trades);
    
    logOrchestrationEnd(result);
    
    // Convert to JSON for API response
    auto json_result = getBacktestResultsAsJson(result, market_data, data_processor);
    if (json_result.isError()) {
        return Result<std::string>(json_result.getError());
    }
    
    return Result<std::string>(json_result.getValue().dump(2));
}

Result<BacktestResult> TradingOrchestrator::runBacktest(const TradingConfig& config,
                                                       Portfolio& portfolio,
                                                       MarketData* market_data,
                                                       ExecutionService* execution_service,
                                                       ProgressService* progress_service,
                                                       PortfolioAllocator* portfolio_allocator,
                                                       DataProcessor* data_processor,
                                                       StrategyManager* strategy_manager,
                                                       ResultCalculator* result_calculator) {
    Logger::debug("TradingOrchestrator::runBacktest called with: symbol='", config.symbols[0],
                 "', start_date='", config.start_date, "', end_date='", config.end_date,
                 "', starting_capital=", config.starting_capital);
    
    BacktestResult result;
    
    // Sequential error handling
    auto validation_result = validateTradingConfig(config, strategy_manager);
    if (validation_result.isError()) {
        return Result<BacktestResult>(validation_result.getError());
    }
    
    auto init_result = initializeBacktest(config, result, portfolio, execution_service);
    if (init_result.isError()) {
        return Result<BacktestResult>(init_result.getError());
    }
    
    auto market_data_result = data_processor->loadMultiSymbolData(config.symbols, config.start_date, config.end_date, market_data);
    if (market_data_result.isError()) {
        return Result<BacktestResult>(market_data_result.getError());
    }
    
    auto simulation_result = runSimulationLoop(market_data_result.getValue(), config, result, portfolio,
                                              execution_service, progress_service, portfolio_allocator,
                                              data_processor, strategy_manager, market_data);
    if (simulation_result.isError()) {
        return Result<BacktestResult>(simulation_result.getError());
    }
    
    auto finalize_result = finalizeBacktestResults(result, portfolio, result_calculator);
    if (finalize_result.isError()) {
        return Result<BacktestResult>(finalize_result.getError());
    }
    
    return Result<BacktestResult>(result);
}

// Configuration validation
Result<void> TradingOrchestrator::validateTradingConfig(const TradingConfig& config,
                                                       StrategyManager* strategy_manager) const {
    if (!strategy_manager->hasStrategy()) {
        Logger::error("No strategy configured for backtesting");
        return Result<void>(ErrorCode::ENGINE_NO_STRATEGY_CONFIGURED, "No strategy configured for backtesting");
    }
    
    if (config.symbols.empty()) {
        Logger::error("Symbols list cannot be empty");
        return Result<void>(ErrorCode::ENGINE_INVALID_SYMBOL, "Symbols list cannot be empty");
    }
    
    // Validate each symbol in the list
    for (const auto& symbol : config.symbols) {
        if (symbol.empty()) {
            Logger::error("Symbol cannot be empty");
            return Result<void>(ErrorCode::ENGINE_INVALID_SYMBOL, "Symbol cannot be empty");
        }
    }
    
    if (config.starting_capital <= 0) {
        Logger::error("Starting capital must be positive");
        return Result<void>(ErrorCode::ENGINE_INVALID_CAPITAL, "Starting capital must be positive", 
                           "Provided capital: " + std::to_string(config.starting_capital));
    }
    
    return Result<void>(); // Success
}

Result<void> TradingOrchestrator::validateSimulationParameters(const TradingConfig& config,
                                                              MarketData* market_data) const {
    // Basic parameter validation
    if (config.symbols.empty()) {
        return Result<void>(ErrorCode::ENGINE_INVALID_SYMBOL, "Symbols list cannot be empty");
    }
    
    // Check for empty symbols in the list
    for (const auto& symbol : config.symbols) {
        if (symbol.empty()) {
            return Result<void>(ErrorCode::ENGINE_INVALID_SYMBOL, "Symbol cannot be empty");
        }
    }
    
    if (config.starting_capital <= 0) {
        return Result<void>(ErrorCode::ENGINE_INVALID_CAPITAL, "Starting capital must be positive");
    }
    
    if (config.start_date.empty() || config.end_date.empty()) {
        return Result<void>(ErrorCode::ENGINE_INVALID_DATE_RANGE, "Start date and end date cannot be empty");
    }
    
    // Temporal validation
    if (market_data) {
        Logger::info("Performing temporal validation");
        
        // Get database connection from market data service
        auto db_connection = market_data->getDatabaseConnection();
        if (!db_connection) {
            Logger::warning("No database connection available for temporal validation");
            return Result<void>(); // Continue without temporal validation
        }
        
        // Dynamic temporal validation - allow all symbols but track their availability
        // This enables backtesting where stocks are traded only when actually available to trade
        // Check which symbols exist in the database
        std::vector<std::string> missing_symbols;
        for (const auto& symbol : config.symbols) {
            auto exists_result = db_connection->checkSymbolExists(symbol);
            if (exists_result.isError() || !exists_result.getValue()) {
                missing_symbols.push_back(symbol);
            }
        }
        
        if (!missing_symbols.empty()) {
            std::string error_msg = "Symbols not found in database: ";
            for (size_t i = 0; i < missing_symbols.size(); ++i) {
                error_msg += missing_symbols[i];
                if (i < missing_symbols.size() - 1) {
                    error_msg += ", ";
                }
            }
            Logger::error("Database validation failed: " + error_msg);
            return Result<void>(ErrorCode::DATA_SYMBOL_NOT_FOUND, error_msg);
        }
        
        // Log temporal validation approach
        Logger::info("Using dynamic temporal validation - symbols will be traded only when available during " + 
                    config.start_date + " to " + config.end_date);
        
        // Get temporal info for each symbol for informational logging
        for (const auto& symbol : config.symbols) {
            auto temporal_info = db_connection->getStockTemporalInfo(symbol);
            if (temporal_info.isSuccess()) {
                const auto& info = temporal_info.getValue();
                auto ipo_it = info.find("ipo_date");
                auto delisting_it = info.find("delisting_date");
                
                if (ipo_it != info.end() && !ipo_it->second.empty()) {
                    Logger::debug("Symbol " + symbol + " temporal info: IPO " + ipo_it->second + 
                                 (delisting_it != info.end() && !delisting_it->second.empty() ? 
                                  ", Delisted " + delisting_it->second : ", Currently active"));
                }
            }
        }
    } else {
        Logger::warning("No market data service available for temporal validation");
    }
    
    return Result<void>(); // Success
}

// Backtest lifecycle management
Result<void> TradingOrchestrator::initializeBacktest(const TradingConfig& config,
                                                    BacktestResult& result,
                                                    Portfolio& portfolio,
                                                    ExecutionService* execution_service) const {
    try {
        // Initialize multi-symbol backtest result
        result.symbols = config.symbols;
        result.starting_capital = config.starting_capital;
        result.start_date = config.start_date;
        result.end_date = config.end_date;
        result.strategy_name = config.strategy_name;
        
        // Initialize per-symbol performance tracking
        for (const auto& symbol : config.symbols) {
            result.addSymbol(symbol);
        }
        
        portfolio = Portfolio(config.starting_capital);
        execution_service->clearExecutedSignals();
        
        Logger::debug("Multi-symbol backtest initialized with ", config.symbols.size(), " symbols and capital: ", config.starting_capital);
        return Result<void>(); // Success
    } catch (const std::exception& e) {
        Logger::error("Error initializing backtest: ", e.what());
        return Result<void>(ErrorCode::ENGINE_BACKTEST_FAILED, "Failed to initialize backtest", e.what());
    }
}

Result<void> TradingOrchestrator::finalizeBacktestResults(BacktestResult& result,
                                                         Portfolio& portfolio,
                                                         ResultCalculator* result_calculator) const {
    // Use ResultCalculator to handle all performance calculations
    result_calculator->finalizeResults(result, portfolio);
    
    return Result<void>(); // Success
}

// Results processing
Result<nlohmann::json> TradingOrchestrator::getBacktestResultsAsJson(const BacktestResult& result,
                                                                    MarketData* market_data,
                                                                    DataProcessor* data_processor) const {
    try {
        nlohmann::json json_result = JsonHelpers::backTestResultToJson(result);
        
        // For multi-symbol backtests, use the first symbol as reference for equity curve dates
        const std::string& reference_symbol = result.symbols.empty() ? "AAPL" : result.symbols[0];
        
        // Add equity curve with actual dates from market data
        return ErrorUtils::chain(market_data->getHistoricalPrices(reference_symbol, result.start_date, result.end_date), 
            [data_processor, &json_result, &result](const std::vector<std::map<std::string, std::string>>& price_data_raw) {
                auto price_data = data_processor->convertToTechnicalData(price_data_raw);
                json_result["equity_curve"] = JsonHelpers::createEquityCurveJson(result.equity_curve, price_data, result.start_date);
                return Result<nlohmann::json>(json_result);
            });
    } catch (const std::exception& e) {
        Logger::error("Error generating backtest results JSON: ", e.what());
        return Result<nlohmann::json>(ErrorCode::ENGINE_RESULTS_GENERATION_FAILED, 
                                     "Failed to generate backtest results JSON", e.what());
    }
}

// Memory optimization support
void TradingOrchestrator::optimizeMemoryUsage() {
    orchestrator_cache_.clear();
    cache_enabled_ = false;
    Logger::debug("TradingOrchestrator memory optimized - cache cleared");
}

void TradingOrchestrator::clearInternalCaches() {
    orchestrator_cache_.clear();
    Logger::debug("TradingOrchestrator internal caches cleared");
}

// Helper methods
Result<void> TradingOrchestrator::validateOrchestrationParameters(const TradingConfig& config) const {
    if (config.symbols.empty()) {
        return Result<void>(ErrorCode::ENGINE_INVALID_SYMBOL, "Orchestration requires at least one symbol");
    }
    
    if (config.starting_capital <= 0) {
        return Result<void>(ErrorCode::ENGINE_INVALID_CAPITAL, "Orchestration requires positive starting capital");
    }
    
    return Result<void>(); // Success
}

Result<void> TradingOrchestrator::prepareSimulationEnvironment(const TradingConfig& config,
                                                              Portfolio& portfolio,
                                                              ExecutionService* execution_service) const {
    try {
        // Reset portfolio to starting capital
        portfolio = Portfolio(config.starting_capital);
        
        // Clear any previous execution history
        if (execution_service) {
            execution_service->clearExecutedSignals();
        }
        
        Logger::debug("Simulation environment prepared for ", config.symbols.size(), " symbols");
        return Result<void>(); // Success
    } catch (const std::exception& e) {
        return Result<void>(ErrorCode::SYSTEM_UNEXPECTED_ERROR, 
                           "Failed to prepare simulation environment", e.what());
    }
}

// Orchestration utilities
std::string TradingOrchestrator::createSimulationSummary(const TradingConfig& config,
                                                        const BacktestResult& result) const {
    std::stringstream summary;
    summary << "Simulation Summary:\n";
    summary << "  Symbols: " << config.symbols.size() << " (";
    for (size_t i = 0; i < config.symbols.size(); ++i) {
        summary << config.symbols[i];
        if (i < config.symbols.size() - 1) summary << ", ";
    }
    summary << ")\n";
    summary << "  Period: " << config.start_date << " to " << config.end_date << "\n";
    summary << "  Strategy: " << config.strategy_name << "\n";
    summary << "  Starting Capital: $" << config.starting_capital << "\n";
    summary << "  Ending Value: $" << result.ending_value << "\n";
    summary << "  Total Return: " << result.total_return_pct << "%\n";
    summary << "  Total Trades: " << result.total_trades << "\n";
    return summary.str();
}

void TradingOrchestrator::logOrchestrationStart(const TradingConfig& config) const {
    Logger::info("=== Trading Orchestration Started ===");
    Logger::info("Configuration:");
    Logger::info("  Symbols: ", config.symbols.size(), " symbols");
    Logger::info("  Date Range: ", config.start_date, " to ", config.end_date);
    Logger::info("  Starting Capital: $", config.starting_capital);
    Logger::info("  Strategy: ", config.strategy_name);
}

void TradingOrchestrator::logOrchestrationEnd(const BacktestResult& result) const {
    Logger::info("=== Trading Orchestration Completed ===");
    Logger::info("Results Summary:");
    Logger::info("  Ending Value: $", result.ending_value);
    Logger::info("  Total Return: ", result.total_return_pct, "%");
    Logger::info("  Total Trades: ", result.total_trades);
    Logger::info("  Win Rate: ", result.win_rate, "%");
}

// Error handling helpers
std::string TradingOrchestrator::formatOrchestrationError(const std::string& operation,
                                                         const std::string& error_message) const {
    return "Orchestration failed during " + operation + ": " + error_message;
}

Result<void> TradingOrchestrator::runSimulationLoop(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data,
                                                   const TradingConfig& config,
                                                   BacktestResult& result,
                                                   Portfolio& portfolio,
                                                   ExecutionService* execution_service,
                                                   ProgressService* progress_service,
                                                   PortfolioAllocator* portfolio_allocator,
                                                   DataProcessor* data_processor,
                                                   StrategyManager* strategy_manager,
                                                   MarketData* market_data) const {
    Logger::debug("Starting multi-symbol simulation loop with ", multi_symbol_data.size(), " symbols");
    
    // Multi-Symbol Simulation Architecture:
    // 1. Create unified timeline across all symbols (handles different trading calendars)
    // 2. Build efficient date-to-index mappings for fast data lookups
    // 3. Process each trading day chronologically across all symbols
    // 4. Evaluate strategy for each symbol individually
    // 5. Execute signals with portfolio-wide risk management
    // 6. Track portfolio value using current prices from all symbols
    
    if (multi_symbol_data.empty()) {
        return Result<void>(ErrorCode::ENGINE_NO_DATA_AVAILABLE, "No market data available");
    }
    
    // Use DataProcessor to create unified timeline and index mappings
    auto timeline = data_processor->createUnifiedTimeline(multi_symbol_data);
    if (timeline.empty()) {
        return Result<void>(ErrorCode::ENGINE_NO_DATA_AVAILABLE, "No price data available for any symbol");
    }
    
    auto symbol_date_indices = data_processor->createDateIndices(multi_symbol_data);
    
    // Initialize portfolio allocation
    std::vector<std::string> available_symbols;
    std::map<std::string, double> initial_prices;
    
    for (const auto& [symbol, data] : multi_symbol_data) {
        if (!data.empty()) {
            available_symbols.push_back(symbol);
            initial_prices[symbol] = data[0].close; // Use first available price
        }
    }
    
    // Calculate initial portfolio allocation
    auto allocation_result = portfolio_allocator->calculateAllocation(
        available_symbols, config.starting_capital, portfolio, initial_prices, config.start_date);
    
    if (allocation_result.isError()) {
        Logger::error("Failed to calculate portfolio allocation: ", allocation_result.getErrorMessage());
        // Fallback to equal allocation
        double capital_per_symbol = config.starting_capital / multi_symbol_data.size();
        double weight_per_symbol = 1.0 / multi_symbol_data.size();
        Logger::debug("Falling back to equal allocation: $", capital_per_symbol, " per symbol");
        
        // Create fallback allocation and set it in the portfolio allocator
        std::map<std::string, double> fallback_weights;
        for (const auto& symbol : available_symbols) {
            fallback_weights[symbol] = weight_per_symbol;
        }
        portfolio_allocator->setTargetAllocation(fallback_weights, config.starting_capital);
    } else {
        const auto& allocation = allocation_result.getValue();
        Logger::debug("Allocation calculated:");
        Logger::debug("Total allocated: $", allocation.total_allocated_capital);
        Logger::debug("Cash reserved: $", allocation.cash_reserved);
        Logger::debug("Strategy: ", allocation.allocation_reason);
        
        for (const auto& [symbol, weight] : allocation.target_weights) {
            Logger::debug("  ", symbol, ": ", weight * 100, "% ($", allocation.target_values.at(symbol), ")");
        }
        
        // Set target allocation in portfolio allocator for proper position sizing
        portfolio_allocator->setTargetAllocation(allocation.target_weights, config.starting_capital);
    }
    
    // Initialize tracking structures
    result.equity_curve.reserve(timeline.size());
    result.equity_curve.push_back(config.starting_capital);
    
    std::map<std::string, std::vector<PriceData>> historical_windows;
    std::map<std::string, double> current_prices;
    
    // Initialize historical windows for each symbol
    for (const auto& [symbol, data] : multi_symbol_data) {
        historical_windows[symbol].reserve(timeline.size());
        current_prices[symbol] = 0.0;
    }
    
    Logger::info("Starting multi-symbol backtest loop with ", timeline.size(), " trading days");
    Logger::debug("Initial portfolio value: $", config.starting_capital);
    
    // Report simulation start using first symbol for reference
    const auto& first_symbol = config.symbols[0];
    auto simulation_start_result = progress_service->reportSimulationStart(
        first_symbol, config.start_date, config.end_date, config.starting_capital);
    if (simulation_start_result.isError()) {
        Logger::debug("Failed to report simulation start: ", simulation_start_result.getErrorMessage());
    }
    
    // Main simulation loop - process each trading day chronologically
    for (size_t day_idx = 0; day_idx < timeline.size(); ++day_idx) {
        const std::string& current_date = timeline[day_idx];
        
        // Progress reporting using ProgressService's internal logic (use first symbol for reference)
        const auto& first_symbol = multi_symbol_data.begin()->first;
        auto first_symbol_it = symbol_date_indices[first_symbol].find(current_date);
        if (first_symbol_it != symbol_date_indices[first_symbol].end()) {
            const auto& reference_data = multi_symbol_data.at(first_symbol)[first_symbol_it->second];
            auto progress_result = progress_service->reportProgress(day_idx, timeline.size(), reference_data, first_symbol, portfolio);
            if (progress_result.isError()) {
                Logger::debug("Progress reporting failed: ", progress_result.getErrorMessage());
            }
        }
        
        // Update current prices and historical data for each symbol using DataProcessor
        data_processor->updateHistoricalWindows(multi_symbol_data, current_date, symbol_date_indices, 
                                               historical_windows, current_prices);
        
        // Check if we have data today
        bool has_data_today = false;
        for (const auto& [symbol, price] : current_prices) {
            if (price > 0) {
                has_data_today = true;
                break;
            }
        }
        
        // Skip days with no data (holidays, weekends)
        if (!has_data_today) {
            continue;
        }
        
        // Evaluate trading strategy for each symbol
        std::map<std::string, TradingSignal> daily_signals;
        
        for (const auto& [symbol, data] : multi_symbol_data) {
            if (historical_windows[symbol].empty()) {
                continue; // No data yet for this symbol
            }
            
            // Dynamic temporal validation - check if stock is tradeable on current date
            bool is_tradeable_today = true;
            if (market_data) {
                auto db_connection = market_data->getDatabaseConnection();
                if (db_connection) {
                    auto tradeable_result = db_connection->checkStockTradeable(symbol, current_date);
                    if (tradeable_result.isSuccess()) {
                        is_tradeable_today = tradeable_result.getValue();
                    }
                }
            }
            
            // Handle stocks that are not tradeable today
            if (!is_tradeable_today) {
                // If we have a position in a delisted stock, force sell it
                if (portfolio.hasPosition(symbol)) {
                    Logger::info("Force selling position in ", symbol, " on ", current_date, " - stock no longer tradeable (delisting)");
                    // Use current market price if available, otherwise use a reasonable default
                    double sell_price = current_prices.count(symbol) ? current_prices[symbol] : 0.01;
                    portfolio.sellAllStock(symbol, sell_price);
                }
                // Skip strategy evaluation for non-tradeable stocks
                Logger::debug("Skipping ", symbol, " on ", current_date, " - not tradeable (before IPO or after delisting)");
                continue;
            }
            
            // Evaluate strategy for this specific symbol
            TradingSignal signal = strategy_manager->getCurrentStrategy()->evaluateSignal(historical_windows[symbol], portfolio, symbol);
            
            if (signal.signal != Signal::HOLD) {
                daily_signals[symbol] = signal;
                Logger::debug("Day ", day_idx, " (", current_date, "): ", symbol, " signal: ", 
                            (signal.signal == Signal::BUY ? "BUY" : "SELL"), 
                            " at $", signal.price, " (confidence: ", signal.confidence, ")");
            }
        }
        
        // Execute signals with portfolio allocation and risk management
        double current_portfolio_value = portfolio.getTotalValue(current_prices);
        
        for (const auto& [symbol, signal] : daily_signals) {
            // Use portfolio allocator for position sizing
            auto position_size_result = portfolio_allocator->calculatePositionSize(
                symbol, portfolio, signal.price, current_portfolio_value, signal.signal);
            
            if (position_size_result.isError()) {
                Logger::debug("Position sizing failed for ", symbol, ": ", position_size_result.getErrorMessage());
                continue;
            }
            
            double suggested_shares = position_size_result.getValue();
            
            if (suggested_shares <= 0) {
                Logger::debug("Position sizing suggests no action for ", symbol, " (shares: ", suggested_shares, ")");
                continue;
            }
            
            // Execute the signal with portfolio allocator guidance
            bool execution_success = false;
            
            if (signal.signal == Signal::BUY) {
                execution_success = portfolio.buyStock(symbol, static_cast<int>(suggested_shares), signal.price);
                if (execution_success) {
                    Logger::debug("BUY executed for ", symbol, ": ", suggested_shares, " shares at $", signal.price);
                }
            } else if (signal.signal == Signal::SELL) {
                execution_success = portfolio.sellStock(symbol, static_cast<int>(suggested_shares), signal.price);
                if (execution_success) {
                    Logger::debug("SELL executed for ", symbol, ": ", suggested_shares, " shares at $", signal.price);
                }
            }
            
            if (execution_success) {
                result.signals_generated.push_back(signal);
                result.total_trades++;
                
                // Update per-symbol metrics
                auto& symbol_perf = result.symbol_performance[symbol];
                symbol_perf.trades_count++;
                symbol_perf.symbol_signals.push_back(signal);
                
                Logger::debug("Signal EXECUTED for ", symbol, " with allocation-aware position sizing");
            } else {
                Logger::debug("Signal REJECTED for ", symbol, " during execution");
            }
        }
        
        // Check for rebalancing opportunities
        if (day_idx % 50 == 0 && portfolio_allocator->shouldRebalance(portfolio, current_prices, current_date)) {
            Logger::debug("Portfolio rebalancing triggered on day ", day_idx);
            
            auto rebalance_result = portfolio_allocator->calculateRebalancing(
                portfolio, current_prices, current_portfolio_value);
            
            if (rebalance_result.isSuccess()) {
                const auto& rebalance_allocation = rebalance_result.getValue();
                Logger::debug("Rebalancing recommendation generated:");
                for (const auto& [symbol, target_weight] : rebalance_allocation.target_weights) {
                    Logger::debug("  ", symbol, " target weight: ", target_weight * 100, "%");
                }
                // TODO: Actual rebalancing execution would go here
            }
        }
        
        // Calculate and record portfolio value
        double portfolio_value = portfolio.getTotalValue(current_prices);
        result.equity_curve.push_back(portfolio_value);
        
        // Log progress periodically (every 50 days)
        if (day_idx % 50 == 0) {
            Logger::debug("Day ", day_idx, " (", current_date, "): Portfolio value = $", portfolio_value);
            Logger::debug("  Active positions: ", portfolio.getPositionCount());
            Logger::debug("  Cash balance: $", portfolio.getCashBalance());
        }
    }
    
    Logger::info("Multi-symbol backtest loop completed");
    Logger::info("Total trading days processed: ", timeline.size());
    Logger::info("Total signals generated: ", result.signals_generated.size());
    Logger::info("Total trades executed: ", result.total_trades);
    Logger::info("Final portfolio positions: ", portfolio.getPositionCount());
    Logger::info("Final cash balance: $", portfolio.getCashBalance());
    
    // Report simulation end
    if (!result.equity_curve.empty()) {
        double final_value = result.equity_curve.back();
        double return_pct = ((final_value - config.starting_capital) / config.starting_capital) * 100.0;
        auto simulation_end_result = progress_service->reportSimulationEnd(
            first_symbol, final_value, return_pct, result.total_trades);
        if (simulation_end_result.isError()) {
            Logger::debug("Failed to report simulation end: ", simulation_end_result.getErrorMessage());
        }
    }
    
    return Result<void>(); // Success
}