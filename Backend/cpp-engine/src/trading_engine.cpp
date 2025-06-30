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
                           std::unique_ptr<DatabaseService> db_service,
                           std::unique_ptr<ExecutionService> exec_service,
                           std::unique_ptr<ProgressService> progress_service)
    : portfolio_(initial_capital), cache_enabled_(false),
      database_service_(std::move(db_service)),
      execution_service_(std::move(exec_service)),
      progress_service_(std::move(progress_service)) {
    setMovingAverageStrategy();
}

// Move constructor
TradingEngine::TradingEngine(TradingEngine&& other) noexcept
    : portfolio_(std::move(other.portfolio_)),
      strategy_(std::move(other.strategy_)),
      database_service_(std::move(other.database_service_)),
      execution_service_(std::move(other.execution_service_)),
      progress_service_(std::move(other.progress_service_)),
      price_data_cache_(std::move(other.price_data_cache_)),
      cache_enabled_(other.cache_enabled_) {}

// Move assignment
TradingEngine& TradingEngine::operator=(TradingEngine&& other) noexcept {
    if (this != &other) {
        portfolio_ = std::move(other.portfolio_);
        strategy_ = std::move(other.strategy_);
        database_service_ = std::move(other.database_service_);
        execution_service_ = std::move(other.execution_service_);
        progress_service_ = std::move(other.progress_service_);
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

// Simulation method with parameters - now using Result<T> patterns
Result<std::string> TradingEngine::runSimulationWithParams(const std::string& symbol, const std::string& start_date, const std::string& end_date, double capital) {
    Logger::debug("TradingEngine::runSimulationWithParams called with: symbol='", symbol, 
                 "', start_date='", start_date, "', end_date='", end_date, "', capital=", capital);
    
    // Validate input parameters first
    if (symbol.empty()) {
        return Result<std::string>(ErrorCode::ENGINE_INVALID_SYMBOL, "Symbol cannot be empty");
    }
    if (capital <= 0) {
        return Result<std::string>(ErrorCode::ENGINE_INVALID_CAPITAL, "Starting capital must be positive");
    }
    if (start_date.empty() || end_date.empty()) {
        return Result<std::string>(ErrorCode::ENGINE_INVALID_DATE_RANGE, "Start date and end date cannot be empty");
    }
    
    BacktestConfig config;
    config.symbol = symbol;
    config.start_date = start_date;
    config.end_date = end_date;
    config.starting_capital = capital;
    
    Logger::debug("BacktestConfig created: symbol='", config.symbol, "', start_date='", 
                 config.start_date, "', end_date='", config.end_date, "', capital=", config.starting_capital);
    
    // Reset portfolio with new capital
    portfolio_ = Portfolio(capital);
    Logger::debug("Portfolio initialized with capital: ", capital, ", initial capital: ", portfolio_.getInitialCapital());
    
    // Use ErrorUtils::chain for error handling pipeline
    auto backtest_result = runBacktest(config);
    if (backtest_result.isError()) {
        return Result<std::string>(backtest_result.getError());
    }
    
    const auto& result = backtest_result.getValue();
    Logger::debug("Backtest completed. Result: starting_capital=", result.starting_capital, 
                 ", ending_value=", result.ending_value, ", total_return_pct=", result.total_return_pct,
                 ", total_trades=", result.total_trades);
    
    auto json_result = getBacktestResultsAsJson(result);
    if (json_result.isError()) {
        return Result<std::string>(json_result.getError());
    }
    
    return Result<std::string>(json_result.getValue().dump(2));
}

// Main backtesting implementation - now using Result<T> patterns
Result<BacktestResult> TradingEngine::runBacktest(const BacktestConfig& config) {
    Logger::debug("TradingEngine::runBacktest called with: symbol='", config.symbol,
                 "', start_date='", config.start_date, "', end_date='", config.end_date,
                 "', starting_capital=", config.starting_capital);
    
    BacktestResult result;
    
    // Sequential error handling with proper Result<T> patterns
    auto validation_result = validateBacktestConfig(config);
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

Result<BacktestResult> TradingEngine::runBacktestMultiSymbol(const std::vector<std::string>& symbols,
                                                                const std::string& start_date,
                                                                const std::string& end_date,
                                                                double starting_capital) {
    // Validate input parameters
    if (symbols.empty()) {
        return Result<BacktestResult>(ErrorCode::ENGINE_INVALID_SYMBOL, "Symbol list cannot be empty");
    }
    if (starting_capital <= 0) {
        return Result<BacktestResult>(ErrorCode::ENGINE_INVALID_CAPITAL, "Starting capital must be positive");
    }
    if (start_date.empty() || end_date.empty()) {
        return Result<BacktestResult>(ErrorCode::ENGINE_INVALID_DATE_RANGE, "Start date and end date cannot be empty");
    }
    
    BacktestResult combined_result;
    combined_result.starting_capital = starting_capital;
    combined_result.start_date = start_date;
    combined_result.end_date = end_date;
    
    try {
        // Reset portfolio and set up multi-symbol allocation
        portfolio_ = Portfolio(starting_capital);
        double capital_per_symbol = starting_capital / symbols.size();
    
    // Get historical data for all symbols and convert to PriceData format
    std::map<std::string, std::vector<PriceData>> symbol_price_data;
    for (const auto& symbol : symbols) {
        auto raw_data_result = database_service_->getHistoricalPrices(symbol, start_date, end_date);
        
        if (raw_data_result.isError()) {
            Logger::error("Error getting historical data for ", symbol, ": ", raw_data_result.getErrorMessage());
            continue;
        }
        
        const auto& raw_data = raw_data_result.getValue();
        std::vector<PriceData> price_data;
        
        for (const auto& row : raw_data) {
            try {
                PriceData pd = DataConversion::convertRowToPriceData(row);
                price_data.push_back(pd);
            } catch (const std::exception& e) {
                Logger::error("Error parsing data for ", symbol, ": ", e.what());
                continue;
            }
        }
        
        if (!price_data.empty()) {
            symbol_price_data[symbol] = price_data;
        } else {
            Logger::warning("No valid data found for symbol ", symbol);
        }
    }
    
    // Find the maximum number of trading days across all symbols
    size_t max_days = 0;
    for (const auto& [symbol, data] : symbol_price_data) {
        max_days = std::max(max_days, data.size());
    }
    
    // Process each symbol individually with allocated capital
    for (const auto& symbol : symbols) {
        if (symbol_price_data.find(symbol) == symbol_price_data.end()) {
            continue; // Skip symbols with no data
        }
        
        const auto& price_data = symbol_price_data[symbol];
        
        // Create a temporary portfolio for this symbol
        Portfolio temp_portfolio(capital_per_symbol);
        
        // Generate signals using the strategy
        if (strategy_) {
            auto signals = strategy_->evaluateSignal(price_data, temp_portfolio, symbol);
            
            // For now, use simple buy-and-hold for each symbol as a placeholder
            // This ensures the multi-symbol framework works before implementing complex signal coordination
            if (!price_data.empty()) {
                // Buy shares at the beginning
                double first_price = price_data[0].close;
                int shares = static_cast<int>(capital_per_symbol / first_price);
                
                if (shares > 0 && portfolio_.buyStock(symbol, shares, first_price)) {
                    TradingSignal buy_signal(Signal::BUY, first_price, price_data[0].date, "Multi-symbol allocation");
                    combined_result.signals_generated.push_back(buy_signal);
                    combined_result.total_trades++;
                }
            }
        }
    }
    
    // Calculate final portfolio value
    std::map<std::string, double> final_prices;
    for (const auto& symbol : symbols) {
        if (symbol_price_data.find(symbol) != symbol_price_data.end() && !symbol_price_data[symbol].empty()) {
            final_prices[symbol] = symbol_price_data[symbol].back().close;
        }
    }
    
        combined_result.ending_value = portfolio_.getTotalValue(final_prices);
        combined_result.total_return_pct = ((combined_result.ending_value - combined_result.starting_capital) / combined_result.starting_capital) * 100.0;
        combined_result.win_rate = combined_result.total_trades > 0 ? 
            (static_cast<double>(combined_result.winning_trades) / combined_result.total_trades) * 100.0 : 0.0;
        
        return Result<BacktestResult>(combined_result);
        
    } catch (const std::exception& e) {
        Logger::error("Error in multi-symbol backtest: ", e.what());
        return Result<BacktestResult>(ErrorCode::ENGINE_MULTI_SYMBOL_FAILED, 
                                     "Multi-symbol backtest failed", e.what());
    }
}

Result<std::string> TradingEngine::getPortfolioStatus() {
    return ErrorUtils::chain(database_service_->getCurrentPrices(), [this](const std::map<std::string, double>& current_prices) {
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
        
        // Add equity curve with actual dates from market data using Result<T> patterns
        return ErrorUtils::chain(database_service_->getHistoricalPrices(result.symbol, result.start_date, result.end_date), 
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
    database_service_ = std::make_unique<DatabaseService>();
    execution_service_ = std::make_unique<ExecutionService>();
    progress_service_ = std::make_unique<ProgressService>();
}

// Service accessors
DatabaseService* TradingEngine::getDatabaseService() const {
    return database_service_.get();
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
    
    double annualized_return = mean_return * 252; // 252 trading days
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

// Decomposed backtest methods - now using Result<T> patterns
Result<void> TradingEngine::validateBacktestConfig(const BacktestConfig& config) const {
    if (!strategy_) {
        Logger::error("No strategy configured for backtesting");
        return Result<void>(ErrorCode::ENGINE_NO_STRATEGY_CONFIGURED, "No strategy configured for backtesting");
    }
    
    if (config.symbol.empty()) {
        Logger::error("Symbol cannot be empty");
        return Result<void>(ErrorCode::ENGINE_INVALID_SYMBOL, "Symbol cannot be empty");
    }
    
    if (config.starting_capital <= 0) {
        Logger::error("Starting capital must be positive");
        return Result<void>(ErrorCode::ENGINE_INVALID_CAPITAL, "Starting capital must be positive", 
                           "Provided capital: " + std::to_string(config.starting_capital));
    }
    
    return Result<void>(); // Success
}

Result<void> TradingEngine::initializeBacktest(const BacktestConfig& config, BacktestResult& result) {
    try {
        result.symbol = config.symbol;
        result.starting_capital = config.starting_capital;
        result.start_date = config.start_date;
        result.end_date = config.end_date;
        
        portfolio_ = Portfolio(config.starting_capital);
        execution_service_->clearExecutedSignals();
        
        Logger::debug("Backtest initialized with capital: ", config.starting_capital);
        return Result<void>(); // Success
    } catch (const std::exception& e) {
        Logger::error("Error initializing backtest: ", e.what());
        return Result<void>(ErrorCode::ENGINE_BACKTEST_FAILED, "Failed to initialize backtest", e.what());
    }
}

Result<std::vector<PriceData>> TradingEngine::prepareMarketData(const BacktestConfig& config) {
    Logger::debug("Getting historical price data...");
    
    return ErrorUtils::chain(database_service_->getHistoricalPrices(config.symbol, config.start_date, config.end_date),
        [this, &config](const std::vector<std::map<std::string, std::string>>& price_data_raw) {
            Logger::debug("Retrieved ", price_data_raw.size(), " price records");
            
            if (price_data_raw.empty()) {
                return Result<std::vector<PriceData>>(ErrorCode::ENGINE_NO_DATA_AVAILABLE, 
                    "No historical price data available for symbol " + config.symbol + 
                    " in date range " + config.start_date + " to " + config.end_date);
            }
            
            try {
                auto price_data = convertToTechnicalData(price_data_raw);
                Logger::debug("Converted to ", price_data.size(), " technical data points");
                
                if (price_data.empty()) {
                    return Result<std::vector<PriceData>>(ErrorCode::ENGINE_NO_DATA_AVAILABLE, 
                        "Failed to convert price data for symbol " + config.symbol);
                }
                
                return Result<std::vector<PriceData>>(price_data);
            } catch (const std::exception& e) {
                Logger::error("Error converting price data: ", e.what());
                return Result<std::vector<PriceData>>(ErrorCode::DATA_PARSING_FAILED, 
                    "Failed to convert price data", e.what());
            }
        });
}

Result<void> TradingEngine::runSimulationLoop(const std::vector<PriceData>& price_data, const BacktestConfig& config, BacktestResult& result) {
    result.equity_curve.reserve(price_data.size());
    result.equity_curve.push_back(config.starting_capital);
    
    // Pre-allocate containers to avoid repeated allocations
    std::vector<PriceData> historical_window;
    historical_window.reserve(price_data.size());
    // Initialize with first data point
    historical_window.push_back(price_data[0]);
    
    std::map<std::string, double> current_prices;
    current_prices[config.symbol] = 0.0; // Pre-initialize map entry
    
    Logger::info("Starting backtest loop with ", price_data.size(), " data points");
    Logger::debug("Initial portfolio value: ", portfolio_.getTotalValue({}));
    
    for (size_t i = 1; i < price_data.size(); ++i) {
        const auto& data_point = price_data[i];
        
        auto progress_result = progress_service_->reportProgress(i, price_data.size(), data_point, config.symbol, portfolio_);
        if (progress_result.isError()) {
            Logger::warning("Progress reporting failed: ", progress_result.getErrorMessage());
        }
        
        if (i % 50 == 0) {
            Logger::debug("Day ", i, ": Price = ", data_point.close, 
                         ", Portfolio = ", portfolio_.getTotalValue({{config.symbol, data_point.close}}));
        }
        
        // Efficiently build historical window by appending only new data point
        historical_window.push_back(data_point);
        
        TradingSignal signal = strategy_->evaluateSignal(historical_window, portfolio_, config.symbol);
        
        if (signal.signal != Signal::HOLD) {
            Logger::debug("Generated signal: ", (signal.signal == Signal::BUY ? "BUY" : "SELL"), 
                         " confidence=", signal.confidence, " at price=", signal.price);
            
            auto execution_result = execution_service_->executeSignal(signal, config.symbol, portfolio_, strategy_.get());
            if (execution_result.isSuccess()) {
                result.signals_generated.push_back(signal);
                result.total_trades++;
                Logger::debug("Signal EXECUTED");
            } else {
                Logger::debug("Signal REJECTED: ", execution_result.getErrorMessage());
            }
        }
        
        // Reuse existing map entry instead of clearing
        current_prices[config.symbol] = data_point.close;
        double portfolio_value = portfolio_.getTotalValue(current_prices);
        result.equity_curve.push_back(portfolio_value);
    }
    
    Logger::info("Backtest loop completed");
    Logger::info("Total signals generated: ", execution_service_->getTotalExecutions());
    Logger::info("Total trades executed: ", result.total_trades);
    
    return Result<void>(); // Success
}

Result<void> TradingEngine::finalizeBacktestResults(BacktestResult& result) {
    if (!result.equity_curve.empty()) {
        result.ending_value = result.equity_curve.back();
        result.total_return_pct = ((result.ending_value - result.starting_capital) / result.starting_capital) * 100.0;
        
        Logger::debug("Final calculations: Portfolio cash=", portfolio_.getCashBalance(),
                     ", ending value=", result.ending_value, ", return=", result.total_return_pct, "%");
    } else {
        result.ending_value = result.starting_capital;
        result.total_return_pct = 0.0;
        Logger::warning("Empty equity curve, using starting capital as ending value");
    }
    
    auto daily_returns = calculateDailyReturns(result.equity_curve);
    result.sharpe_ratio = calculateSharpeRatio(daily_returns);
    result.max_drawdown = calculateMaxDrawdown(result.equity_curve);
    
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
    
    result.win_rate = result.total_trades > 0 ? 
        (static_cast<double>(result.winning_trades) / result.total_trades) * 100.0 : 0.0;
    
    return Result<void>(); // Success
}

