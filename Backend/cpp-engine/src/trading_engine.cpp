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

// Constructors
TradingEngine::TradingEngine() : portfolio_(10000.0), cache_enabled_(false) {
    initializeServices();
    setMovingAverageStrategy();
}

TradingEngine::TradingEngine(double initial_capital) : portfolio_(initial_capital), cache_enabled_(false) {
    initializeServices();
    setMovingAverageStrategy();
}

TradingEngine::TradingEngine(double initial_capital,
                           std::unique_ptr<MarketData> market_data,
                           std::unique_ptr<ExecutionService> exec_service,
                           std::unique_ptr<ProgressService> progress_service)
    : portfolio_(initial_capital), cache_enabled_(false),
      market_data_(std::move(market_data)),
      execution_service_(std::move(exec_service)),
      progress_service_(std::move(progress_service)) {
    setMovingAverageStrategy();
}

// Move constructor
TradingEngine::TradingEngine(TradingEngine&& other) noexcept
    : portfolio_(std::move(other.portfolio_)),
      strategy_(std::move(other.strategy_)),
      market_data_(std::move(other.market_data_)),
      execution_service_(std::move(other.execution_service_)),
      progress_service_(std::move(other.progress_service_)),
      portfolio_allocator_(std::move(other.portfolio_allocator_)),
      price_data_cache_(std::move(other.price_data_cache_)),
      cache_enabled_(other.cache_enabled_) {}

// Move assignment
TradingEngine& TradingEngine::operator=(TradingEngine&& other) noexcept {
    if (this != &other) {
        portfolio_ = std::move(other.portfolio_);
        strategy_ = std::move(other.strategy_);
        market_data_ = std::move(other.market_data_);
        execution_service_ = std::move(other.execution_service_);
        progress_service_ = std::move(other.progress_service_);
        portfolio_allocator_ = std::move(other.portfolio_allocator_);
        price_data_cache_ = std::move(other.price_data_cache_);
        cache_enabled_ = other.cache_enabled_;
    }
    return *this;
}

// Strategy management
void TradingEngine::setStrategy(std::unique_ptr<TradingStrategy> strategy) {
    strategy_ = std::move(strategy);
}

void TradingEngine::setMovingAverageStrategy(int short_period, int long_period) {
    strategy_ = std::make_unique<MovingAverageCrossoverStrategy>(short_period, long_period);
}

void TradingEngine::setRSIStrategy(int period, double oversold, double overbought) {
    strategy_ = std::make_unique<RSIStrategy>(period, oversold, overbought);
}

// Helper function to validate simulation parameters with temporal validation
Result<void> TradingEngine::validateSimulationParameters(const TradingConfig& config) {
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
    if (market_data_) {
        Logger::info("Performing temporal validation");
        
        // Get database connection from market data service
        auto db_connection = market_data_->getDatabaseConnection();
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

// Simulation method that returns JSON string
Result<std::string> TradingEngine::runSimulation(const TradingConfig& config) {
    Logger::debug("TradingEngine::runSimulation called with: symbols=[", config.symbols.size(), " symbols], "
                 "start_date='", config.start_date, "', end_date='", config.end_date, "', capital=", config.starting_capital);
    
    // Use common validation
    auto validation_result = validateSimulationParameters(config);
    if (validation_result.isError()) {
        return Result<std::string>(validation_result.getError());
    }
    
    // Reset portfolio with new capital
    portfolio_ = Portfolio(config.starting_capital);
    Logger::debug("Portfolio initialized with capital: ", config.starting_capital, ", initial capital: ", portfolio_.getInitialCapital());
    
    // Run backtest and convert to JSON
    auto backtest_result = runBacktest(config);
    if (backtest_result.isError()) {
        return Result<std::string>(backtest_result.getError());
    }
    
    const auto& result = backtest_result.getValue();
    Logger::debug("Backtest completed. Result: starting_capital=", result.starting_capital, 
                 ", ending_value=", result.ending_value, ", total_return_pct=", result.total_return_pct,
                 ", total_trades=", result.total_trades);
    
    // Convert to JSON for API response
    auto json_result = getBacktestResultsAsJson(result);
    if (json_result.isError()) {
        return Result<std::string>(json_result.getError());
    }
    
    return Result<std::string>(json_result.getValue().dump(2));
}

// Main backtesting implementation - using Result<T> patterns
Result<BacktestResult> TradingEngine::runBacktest(const TradingConfig& config) {
    Logger::debug("TradingEngine::runBacktest called with: symbol='", config.getPrimarySymbol(),
                 "', start_date='", config.start_date, "', end_date='", config.end_date,
                 "', starting_capital=", config.starting_capital);
    
    BacktestResult result;
    
    // Sequential error handling
    auto validation_result = validateTradingConfig(config);
    if (validation_result.isError()) {
        return Result<BacktestResult>(validation_result.getError());
    }
    
    auto init_result = initializeBacktest(config, result);
    if (init_result.isError()) {
        return Result<BacktestResult>(init_result.getError());
    }
    
    auto market_data_result = prepareMarketData(config);
    if (market_data_result.isError()) {
        return Result<BacktestResult>(market_data_result.getError());
    }
    
    auto simulation_result = runSimulationLoop(market_data_result.getValue(), config, result);
    if (simulation_result.isError()) {
        return Result<BacktestResult>(simulation_result.getError());
    }
    
    auto finalize_result = finalizeBacktestResults(result);
    if (finalize_result.isError()) {
        return Result<BacktestResult>(finalize_result.getError());
    }
    
    return Result<BacktestResult>(result);
}

Result<std::string> TradingEngine::getPortfolioStatus() {
    return ErrorUtils::chain(market_data_->getCurrentPrices(), [this](const std::map<std::string, double>& current_prices) {
        try {
            std::string status = portfolio_.toDetailedString(current_prices);
            return Result<std::string>(status);
        } catch (const std::exception& e) {
            Logger::error("Error generating portfolio status: ", e.what());
            return Result<std::string>(ErrorCode::ENGINE_PORTFOLIO_ACCESS_FAILED, 
                                      "Failed to generate portfolio status", e.what());
        }
    });
}

Portfolio& TradingEngine::getPortfolio() {
    return portfolio_;
}

const Portfolio& TradingEngine::getPortfolio() const {
    return portfolio_;
}

// Results and analytics
std::vector<TradingSignal> TradingEngine::getExecutedSignals() const {
    return execution_service_->getExecutedSignals();
}

Result<nlohmann::json> TradingEngine::getBacktestResultsAsJson(const BacktestResult& result) const {
    try {
        nlohmann::json json_result = JsonHelpers::backTestResultToJson(result);
        
        // For multi-symbol backtests, use the first symbol as reference for equity curve dates
        const std::string& reference_symbol = result.symbols.empty() ? "AAPL" : result.symbols[0];
        
        // Add equity curve with actual dates from market data
        return ErrorUtils::chain(market_data_->getHistoricalPrices(reference_symbol, result.start_date, result.end_date), 
            [this, &json_result, &result](const std::vector<std::map<std::string, std::string>>& price_data_raw) {
                auto price_data = convertToTechnicalData(price_data_raw);
                json_result["equity_curve"] = JsonHelpers::createEquityCurveJson(result.equity_curve, price_data, result.start_date);
                return Result<nlohmann::json>(json_result);
            });
    } catch (const std::exception& e) {
        Logger::error("Error generating backtest results JSON: ", e.what());
        return Result<nlohmann::json>(ErrorCode::ENGINE_RESULTS_GENERATION_FAILED, 
                                     "Failed to generate backtest results JSON", e.what());
    }
}

// Service initialization
void TradingEngine::initializeServices() {
    market_data_ = std::make_unique<MarketData>();
    execution_service_ = std::make_unique<ExecutionService>();
    progress_service_ = std::make_unique<ProgressService>();
    
    // Initialize portfolio allocator with default equal weight strategy
    AllocationConfig default_config;
    default_config.strategy = AllocationStrategy::EQUAL_WEIGHT;
    default_config.max_position_weight = 0.08; // Max 8% per position for better diversification
    default_config.min_position_weight = 0.02; // Min 2% per position
    default_config.enable_rebalancing = true;
    default_config.cash_reserve_pct = 0.05; // Keep 5% cash
    portfolio_allocator_ = std::make_unique<PortfolioAllocator>(default_config);
}

// Service accessors
MarketData* TradingEngine::getMarketData() const {
    return market_data_.get();
}

ExecutionService* TradingEngine::getExecutionService() const {
    return execution_service_.get();
}

ProgressService* TradingEngine::getProgressService() const {
    return progress_service_.get();
}

std::vector<PriceData> TradingEngine::convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data) const {
    return DataConversion::convertToTechnicalData(db_data);
}

double TradingEngine::calculateSharpeRatio(const std::vector<double>& returns, double risk_free_rate) const {
    if (returns.empty()) return 0.0;
    
    double mean_return = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    
    double variance = 0.0;
    for (double ret : returns) {
        variance += (ret - mean_return) * (ret - mean_return);
    }
    variance /= returns.size();
    
    double std_dev = std::sqrt(variance);
    if (std_dev == 0.0) return 0.0;
    
    double annualized_return = mean_return * 252; // 252 trading days per year
    double annualized_std = std_dev * std::sqrt(252);
    
    return (annualized_return - risk_free_rate) / annualized_std;
}

double TradingEngine::calculateMaxDrawdown(const std::vector<double>& equity_curve) const {
    if (equity_curve.empty()) return 0.0;
    
    double max_drawdown = 0.0;
    double peak = equity_curve[0];
    
    for (double value : equity_curve) {
        if (value > peak) {
            peak = value;
        }
        double drawdown = (peak - value) / peak;
        max_drawdown = std::max(max_drawdown, drawdown);
    }
    
    return max_drawdown * 100.0; // Return as percentage
}

std::vector<double> TradingEngine::calculateDailyReturns(const std::vector<double>& equity_curve) const {
    std::vector<double> returns;
    
    for (size_t i = 1; i < equity_curve.size(); ++i) {
        if (equity_curve[i-1] > 0) {
            double ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1];
            returns.push_back(ret);
        }
    }
    
    return returns;
}

// Decomposed backtest methods
Result<void> TradingEngine::validateTradingConfig(const TradingConfig& config) const {
    if (!strategy_) {
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

Result<void> TradingEngine::initializeBacktest(const TradingConfig& config, BacktestResult& result) {
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
        
        portfolio_ = Portfolio(config.starting_capital);
        execution_service_->clearExecutedSignals();
        
        Logger::debug("Multi-symbol backtest initialized with ", config.symbols.size(), " symbols and capital: ", config.starting_capital);
        return Result<void>(); // Success
    } catch (const std::exception& e) {
        Logger::error("Error initializing backtest: ", e.what());
        return Result<void>(ErrorCode::ENGINE_BACKTEST_FAILED, "Failed to initialize backtest", e.what());
    }
}

// Helper function to create standardised error messages for market data
std::string TradingEngine::createDataErrorMessage(const std::string& symbol, const std::string& start_date, const std::string& end_date, const std::string& error_type) {
    if (error_type == "no_data") {
        return "No historical price data available for symbol " + symbol + " in date range " + start_date + " to " + end_date;
    } else if (error_type == "conversion_failed") {
        return "Failed to convert price data for symbol " + symbol;
    }
    return "Data error for symbol " + symbol;
}

Result<std::map<std::string, std::vector<PriceData>>> TradingEngine::prepareMarketData(const TradingConfig& config) {
    Logger::debug("Getting historical price data for ", config.symbols.size(), " symbols:");
    
    std::map<std::string, std::vector<PriceData>> multi_symbol_data;
    std::vector<std::string> failed_symbols;
    
    // Fetch data for each symbol
    for (const auto& symbol : config.symbols) {
        Logger::debug("Fetching data for symbol: ", symbol);
        
        auto symbol_result = market_data_->getHistoricalPrices(symbol, config.start_date, config.end_date);
        
        if (symbol_result.isError()) {
            Logger::debug("Failed to fetch data for symbol ", symbol, ": ", symbol_result.getErrorMessage());
            failed_symbols.push_back(symbol);
            continue;
        }
        
        const auto& price_data_raw = symbol_result.getValue();
        if (price_data_raw.empty()) {
            Logger::debug("No data available for symbol ", symbol, " in date range ", config.start_date, " to ", config.end_date);
            failed_symbols.push_back(symbol);
            continue;
        }
        
        try {
            auto price_data = convertToTechnicalData(price_data_raw);
            if (price_data.empty()) {
                Logger::debug("Failed to convert data for symbol ", symbol);
                failed_symbols.push_back(symbol);
                continue;
            }
            
            multi_symbol_data[symbol] = std::move(price_data);
            Logger::debug("Successfully loaded ", multi_symbol_data[symbol].size(), " data points for ", symbol);
            
        } catch (const std::exception& e) {
            Logger::error("Error converting price data for ", symbol, ": ", e.what());
            failed_symbols.push_back(symbol);
            continue;
        }
    }
    
    // Check if we have data for at least one symbol
    if (multi_symbol_data.empty()) {
        std::string error_msg = "No data available for any of the requested symbols: ";
        for (size_t i = 0; i < config.symbols.size(); ++i) {
            error_msg += config.symbols[i];
            if (i < config.symbols.size() - 1) error_msg += ", ";
        }
        
        return Result<std::map<std::string, std::vector<PriceData>>>(
            ErrorCode::ENGINE_NO_DATA_AVAILABLE, error_msg);
    }
    
    // Log summary of data retrieval
    Logger::debug("Successfully loaded data for ", multi_symbol_data.size(), " out of ", config.symbols.size(), " symbols");
    if (!failed_symbols.empty()) {
        Logger::debug("Failed to load data for symbols: ");
        for (size_t i = 0; i < failed_symbols.size(); ++i) {
            Logger::debug("  - ", failed_symbols[i]);
        }
    }
    
    // Validate that all symbols have data for the same date range
    std::string earliest_date, latest_date;
    size_t min_data_points = SIZE_MAX;
    size_t max_data_points = 0;
    
    for (const auto& [symbol, data] : multi_symbol_data) {
        if (!data.empty()) {
            if (earliest_date.empty() || data.front().date < earliest_date) {
                earliest_date = data.front().date;
            }
            if (latest_date.empty() || data.back().date > latest_date) {
                latest_date = data.back().date;
            }
            min_data_points = std::min(min_data_points, data.size());
            max_data_points = std::max(max_data_points, data.size());
        }
    }
    
    Logger::debug("Data range validation:");
    Logger::debug("  Earliest date: ", earliest_date);
    Logger::debug("  Latest date: ", latest_date);
    Logger::debug("  Min data points: ", min_data_points);
    Logger::debug("  Max data points: ", max_data_points);
    
    // Warn if there are significant differences in data availability between symbols
    if (max_data_points > min_data_points * 1.1) {
        Logger::debug("Significant variation in data availability between symbols");
        Logger::debug("This may cause issues during multi-symbol simulation");
    }
    
    return Result<std::map<std::string, std::vector<PriceData>>>(std::move(multi_symbol_data));
}

Result<void> TradingEngine::runSimulationLoop(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data, const TradingConfig& config, BacktestResult& result) {
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
    
    // Create unified timeline by merging all symbol dates
    std::set<std::string> all_dates;
    for (const auto& [symbol, data] : multi_symbol_data) {
        for (const auto& price_point : data) {
            all_dates.insert(price_point.date);
        }
    }
    
    if (all_dates.empty()) {
        return Result<void>(ErrorCode::ENGINE_NO_DATA_AVAILABLE, "No price data available for any symbol");
    }
    
    // Convert to sorted vector for chronological processing
    std::vector<std::string> timeline(all_dates.begin(), all_dates.end());
    Logger::debug("Created unified timeline with ", timeline.size(), " trading days");
    Logger::debug("Date range: ", timeline.front(), " to ", timeline.back());
    
    // Create symbol-to-data-index mappings for efficient lookups
    std::map<std::string, std::map<std::string, size_t>> symbol_date_indices;
    for (const auto& [symbol, data] : multi_symbol_data) {
        for (size_t i = 0; i < data.size(); ++i) {
            symbol_date_indices[symbol][data[i].date] = i;
        }
        Logger::debug("Indexed ", data.size(), " data points for ", symbol);
    }
    
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
    auto allocation_result = portfolio_allocator_->calculateAllocation(
        available_symbols, config.starting_capital, portfolio_, initial_prices, config.start_date);
    
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
        portfolio_allocator_->setTargetAllocation(fallback_weights, config.starting_capital);
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
        portfolio_allocator_->setTargetAllocation(allocation.target_weights, config.starting_capital);
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
    auto simulation_start_result = progress_service_->reportSimulationStart(
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
            auto progress_result = progress_service_->reportProgress(day_idx, timeline.size(), reference_data, first_symbol, portfolio_);
            if (progress_result.isError()) {
                Logger::debug("Progress reporting failed: ", progress_result.getErrorMessage());
            }
        }
        
        // Update current prices and historical data for each symbol
        bool has_data_today = false;
        for (const auto& [symbol, data] : multi_symbol_data) {
            auto date_it = symbol_date_indices[symbol].find(current_date);
            if (date_it != symbol_date_indices[symbol].end()) {
                // This symbol has data for current date
                const auto& price_point = data[date_it->second];
                current_prices[symbol] = price_point.close;
                historical_windows[symbol].push_back(price_point);
                has_data_today = true;
            }
            // If symbol doesn't have data for this date, keep previous price
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
            if (market_data_) {
                auto db_connection = market_data_->getDatabaseConnection();
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
                if (portfolio_.hasPosition(symbol)) {
                    Logger::info("Force selling position in ", symbol, " on ", current_date, " - stock no longer tradeable (delisting)");
                    // Use current market price if available, otherwise use a reasonable default
                    double sell_price = current_prices.count(symbol) ? current_prices[symbol] : 0.01;
                    portfolio_.sellAllStock(symbol, sell_price);
                }
                // Skip strategy evaluation for non-tradeable stocks
                Logger::debug("Skipping ", symbol, " on ", current_date, " - not tradeable (before IPO or after delisting)");
                continue;
            }
            
            // Evaluate strategy for this specific symbol
            TradingSignal signal = strategy_->evaluateSignal(historical_windows[symbol], portfolio_, symbol);
            
            if (signal.signal != Signal::HOLD) {
                daily_signals[symbol] = signal;
                Logger::debug("Day ", day_idx, " (", current_date, "): ", symbol, " signal: ", 
                            (signal.signal == Signal::BUY ? "BUY" : "SELL"), 
                            " at $", signal.price, " (confidence: ", signal.confidence, ")");
            }
        }
        
        // Execute signals with portfolio allocation and risk management
        double current_portfolio_value = portfolio_.getTotalValue(current_prices);
        
        for (const auto& [symbol, signal] : daily_signals) {
            // Use portfolio allocator for position sizing
            auto position_size_result = portfolio_allocator_->calculatePositionSize(
                symbol, portfolio_, signal.price, current_portfolio_value, signal.signal);
            
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
                execution_success = portfolio_.buyStock(symbol, static_cast<int>(suggested_shares), signal.price);
                if (execution_success) {
                    Logger::debug("BUY executed for ", symbol, ": ", suggested_shares, " shares at $", signal.price);
                }
            } else if (signal.signal == Signal::SELL) {
                execution_success = portfolio_.sellStock(symbol, static_cast<int>(suggested_shares), signal.price);
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
        if (day_idx % 50 == 0 && portfolio_allocator_->shouldRebalance(portfolio_, current_prices, current_date)) {
            Logger::debug("Portfolio rebalancing triggered on day ", day_idx);
            
            auto rebalance_result = portfolio_allocator_->calculateRebalancing(
                portfolio_, current_prices, current_portfolio_value);
            
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
        double portfolio_value = portfolio_.getTotalValue(current_prices);
        result.equity_curve.push_back(portfolio_value);
        
        // Log progress periodically (every 50 days)
        if (day_idx % 50 == 0) {
            Logger::debug("Day ", day_idx, " (", current_date, "): Portfolio value = $", portfolio_value);
            Logger::debug("  Active positions: ", portfolio_.getPositionCount());
            Logger::debug("  Cash balance: $", portfolio_.getCashBalance());
        }
    }
    
    Logger::info("Multi-symbol backtest loop completed");
    Logger::info("Total trading days processed: ", timeline.size());
    Logger::info("Total signals generated: ", result.signals_generated.size());
    Logger::info("Total trades executed: ", result.total_trades);
    Logger::info("Final portfolio positions: ", portfolio_.getPositionCount());
    Logger::info("Final cash balance: $", portfolio_.getCashBalance());
    
    // Report simulation end
    if (!result.equity_curve.empty()) {
        double final_value = result.equity_curve.back();
        double return_pct = ((final_value - config.starting_capital) / config.starting_capital) * 100.0;
        auto simulation_end_result = progress_service_->reportSimulationEnd(
            first_symbol, final_value, return_pct, result.total_trades);
        if (simulation_end_result.isError()) {
            Logger::debug("Failed to report simulation end: ", simulation_end_result.getErrorMessage());
        }
    }
    
    return Result<void>(); // Success
}

// Helper function to calculate trade performance metrics
void TradingEngine::calculateTradeMetrics(BacktestResult& result) {
    std::vector<double> buy_prices;
    
    for (const auto& signal : result.signals_generated) {
        if (signal.signal == Signal::BUY) {
            buy_prices.push_back(signal.price);
        } else if (signal.signal == Signal::SELL && !buy_prices.empty()) {
            double buy_price = buy_prices.back();
            buy_prices.pop_back();
            
            if (signal.price > buy_price) {
                result.winning_trades++;
            } else {
                result.losing_trades++;
            }
        }
    }
}

// Helper function to calculate portfolio performance metrics
void TradingEngine::calculatePortfolioMetrics(BacktestResult& result) {
    if (!result.equity_curve.empty()) {
        result.ending_value = result.equity_curve.back();
        result.cash_remaining = portfolio_.getCashBalance();
        result.total_return_pct = ((result.ending_value - result.starting_capital) / result.starting_capital) * 100.0;
        
        Logger::debug("Final calculations: Portfolio cash=", result.cash_remaining,
                     ", ending value=", result.ending_value, ", return=", result.total_return_pct, "%");
    } else {
        result.ending_value = result.starting_capital;
        result.cash_remaining = result.starting_capital;
        result.total_return_pct = 0.0;
        Logger::debug("Empty equity curve, using starting capital as ending value");
    }
    
    auto daily_returns = calculateDailyReturns(result.equity_curve);
    result.sharpe_ratio = calculateSharpeRatio(daily_returns);
    result.max_drawdown = calculateMaxDrawdown(result.equity_curve);
}

// Helper function to calculate per-symbol performance metrics
void TradingEngine::calculatePerSymbolMetrics(BacktestResult& result) {
    Logger::debug("Calculating per-symbol performance metrics for ", result.symbols.size(), " symbols");
    
    // Map to track trades per symbol
    std::map<std::string, std::vector<double>> symbol_trade_returns;
    std::map<std::string, double> symbol_buy_values;
    std::map<std::string, double> symbol_sell_values;
    
    // Process all signals to calculate per-symbol metrics
    for (const auto& signal : result.signals_generated) {
        const std::string& symbol = signal.date; // TODO: Need to add symbol field to TradingSignal
        auto& symbol_perf = result.symbol_performance[symbol];
        
        // Add signal to symbol-specific list
        symbol_perf.symbol_signals.push_back(signal);
        
        if (signal.signal == Signal::BUY) {
            symbol_buy_values[symbol] += signal.price;
        } else if (signal.signal == Signal::SELL) {
            symbol_sell_values[symbol] += signal.price;
            
            // Calculate trade return if we have a previous buy
            if (symbol_buy_values[symbol] > 0) {
                double trade_return = (signal.price - symbol_buy_values[symbol]) / symbol_buy_values[symbol];
                symbol_trade_returns[symbol].push_back(trade_return);
                
                if (trade_return > 0) {
                    symbol_perf.winning_trades++;
                } else {
                    symbol_perf.losing_trades++;
                }
                symbol_perf.trades_count++;
            }
        }
    }
    
    // Calculate final metrics for each symbol
    for (auto& [symbol, symbol_perf] : result.symbol_performance) {
        // Calculate win rate for this symbol
        if (symbol_perf.trades_count > 0) {
            symbol_perf.win_rate = (static_cast<double>(symbol_perf.winning_trades) / symbol_perf.trades_count) * 100.0;
        }
        
        // Calculate allocation percentage
        if (portfolio_.hasPosition(symbol)) {
            auto position = portfolio_.getPosition(symbol);
            symbol_perf.final_position_value = position.getShares() * position.getAveragePrice();
            symbol_perf.symbol_allocation_pct = (symbol_perf.final_position_value / result.ending_value) * 100.0;
        }
        
        // Calculate symbol return if we have trade data
        if (!symbol_trade_returns[symbol].empty()) {
            double total_return = 0.0;
            for (double ret : symbol_trade_returns[symbol]) {
                total_return += ret;
            }
            symbol_perf.total_return_pct = (total_return / symbol_trade_returns[symbol].size()) * 100.0;
        }
        
        Logger::debug("Symbol ", symbol, " metrics: trades=", symbol_perf.trades_count, 
                     ", win_rate=", symbol_perf.win_rate, "%, allocation=", symbol_perf.symbol_allocation_pct, "%");
    }
}

// Helper function to calculate performance metrics
void TradingEngine::calculateComprehensiveMetrics(BacktestResult& result) {
    // Calculate signals generated count
    result.signals_generated_count = result.signals_generated.size();
    
    // Calculate annualized return
    if (!result.start_date.empty() && !result.end_date.empty()) {
        // Simple approximation: assume 252 trading days per year
        int trading_days = result.equity_curve.size();
        double years = trading_days / 252.0;
        
        if (years > 0) {
            result.annualized_return = (std::pow((result.ending_value / result.starting_capital), (1.0 / years)) - 1.0) * 100.0;
        }
    }
    
    // Calculate profit factor and average win/loss
    double total_wins = 0.0;
    double total_losses = 0.0;
    int win_count = 0;
    int loss_count = 0;
    
    // Simple calculation based on equity curve changes
    auto daily_returns = calculateDailyReturns(result.equity_curve);
    for (double daily_return : daily_returns) {
        if (daily_return > 0) {
            total_wins += daily_return;
            win_count++;
        } else if (daily_return < 0) {
            total_losses += std::abs(daily_return);
            loss_count++;
        }
    }
    
    result.average_win = win_count > 0 ? (total_wins / win_count) * result.starting_capital : 0.0;
    result.average_loss = loss_count > 0 ? (total_losses / loss_count) * result.starting_capital : 0.0;
    result.profit_factor = total_losses > 0 ? total_wins / total_losses : 0.0;
    
    // Calculate volatility (standard deviation of returns)
    if (!daily_returns.empty()) {
        double mean_return = std::accumulate(daily_returns.begin(), daily_returns.end(), 0.0) / daily_returns.size();
        double variance = 0.0;
        
        for (double ret : daily_returns) {
            variance += (ret - mean_return) * (ret - mean_return);
        }
        variance /= daily_returns.size();
        result.volatility = std::sqrt(variance) * std::sqrt(252) * 100.0; // Annualized volatility as percentage
    }
    
    Logger::debug("Metrics calculated: annualized_return=", result.annualized_return, 
                 "%, volatility=", result.volatility, "%, profit_factor=", result.profit_factor);
}

// Helper function to calculate diversification metrics
void TradingEngine::calculateDiversificationMetrics(BacktestResult& result) {
    // Calculate portfolio diversification ratio
    // Simple diversification measure: how evenly capital is distributed across symbols
    
    if (result.symbols.size() <= 1) {
        result.portfolio_diversification_ratio = 0.0; // No diversification with single symbol
        return;
    }
    
    std::vector<double> allocations;
    double total_allocation = 0.0;
    
    for (const auto& [symbol, symbol_perf] : result.symbol_performance) {
        double allocation = symbol_perf.symbol_allocation_pct / 100.0;
        allocations.push_back(allocation);
        total_allocation += allocation;
    }
    
    // Calculate Herfindahl-Hirschman Index (HHI) for diversification
    // Lower HHI indicates better diversification
    double hhi = 0.0;
    for (double allocation : allocations) {
        hhi += allocation * allocation;
    }
    
    // Convert to diversification ratio (1 = perfectly diversified, 0 = concentrated)
    double max_diversification = 1.0 / result.symbols.size(); // Equal allocation across all symbols
    result.portfolio_diversification_ratio = (max_diversification - hhi) / max_diversification;
    
    Logger::debug("Diversification metrics: HHI=", hhi, ", diversification_ratio=", result.portfolio_diversification_ratio);
}

Result<void> TradingEngine::finalizeBacktestResults(BacktestResult& result) {
    // Calculate portfolio performance metrics
    calculatePortfolioMetrics(result);
    
    // Calculate trade performance metrics
    calculateTradeMetrics(result);
    
    // Calculate per-symbol performance metrics
    calculatePerSymbolMetrics(result);
    
    // Calculate overall win rate
    result.win_rate = result.total_trades > 0 ? 
        (static_cast<double>(result.winning_trades) / result.total_trades) * 100.0 : 0.0;
    
    // Calculate additional metrics
    calculateComprehensiveMetrics(result);
    
    // Calculate portfolio diversification ratio
    calculateDiversificationMetrics(result);
    
    Logger::debug("Finalized backtest results for ", result.symbols.size(), " symbols");
    Logger::debug("Total trades: ", result.total_trades, ", Win rate: ", result.win_rate, "%");
    Logger::debug("Total return: ", result.total_return_pct, "%, Sharpe ratio: ", result.sharpe_ratio);
    
    return Result<void>(); // Success
}

