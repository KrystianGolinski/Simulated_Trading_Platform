#include "trading_engine.h"
#include <sstream>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <chrono>
#include <thread>

// Constructors
TradingEngine::TradingEngine() : portfolio_(10000.0) {
    setMovingAverageStrategy();
}

TradingEngine::TradingEngine(double initial_capital) : portfolio_(initial_capital) {
    setMovingAverageStrategy();
}

// Move constructor
TradingEngine::TradingEngine(TradingEngine&& other) noexcept
    : portfolio_(std::move(other.portfolio_)),
      market_data_(std::move(other.market_data_)),
      strategy_(std::move(other.strategy_)),
      executed_signals_(std::move(other.executed_signals_)) {}

// Move assignment
TradingEngine& TradingEngine::operator=(TradingEngine&& other) noexcept {
    if (this != &other) {
        portfolio_ = std::move(other.portfolio_);
        market_data_ = std::move(other.market_data_);
        strategy_ = std::move(other.strategy_);
        executed_signals_ = std::move(other.executed_signals_);
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

// New simulation method with parameters
std::string TradingEngine::runSimulationWithParams(const std::string& symbol, const std::string& start_date, const std::string& end_date, double capital) {
    std::cerr << "[DEBUG] TradingEngine::runSimulationWithParams called with:" << std::endl;
    std::cerr << "[DEBUG]   symbol = '" << symbol << "'" << std::endl;
    std::cerr << "[DEBUG]   start_date = '" << start_date << "'" << std::endl;
    std::cerr << "[DEBUG]   end_date = '" << end_date << "'" << std::endl;
    std::cerr << "[DEBUG]   capital = " << capital << std::endl;
    
    BacktestConfig config;
    config.symbol = symbol;
    config.start_date = start_date;
    config.end_date = end_date;
    config.starting_capital = capital;
    
    std::cerr << "[DEBUG] BacktestConfig created:" << std::endl;
    std::cerr << "[DEBUG]   config.symbol = '" << config.symbol << "'" << std::endl;
    std::cerr << "[DEBUG]   config.start_date = '" << config.start_date << "'" << std::endl;
    std::cerr << "[DEBUG]   config.end_date = '" << config.end_date << "'" << std::endl;
    std::cerr << "[DEBUG]   config.starting_capital = " << config.starting_capital << std::endl;
    
    // Reset portfolio with new capital
    portfolio_ = Portfolio(capital);
    std::cerr << "[DEBUG] Portfolio initialized with capital: " << capital << std::endl;
    std::cerr << "[DEBUG] Portfolio initial capital: " << portfolio_.getInitialCapital() << std::endl;
    
    BacktestResult result = runBacktest(config);
    
    std::cerr << "[DEBUG] Backtest completed. Result:" << std::endl;
    std::cerr << "[DEBUG]   starting_capital = " << result.starting_capital << std::endl;
    std::cerr << "[DEBUG]   ending_value = " << result.ending_value << std::endl;
    std::cerr << "[DEBUG]   total_return_pct = " << result.total_return_pct << std::endl;
    std::cerr << "[DEBUG]   total_trades = " << result.total_trades << std::endl;
    
    return getBacktestResultsAsJson(result).dump(2);
}

// Main backtesting implementation
BacktestResult TradingEngine::runBacktest(const BacktestConfig& config) {
    std::cerr << "[DEBUG] TradingEngine::runBacktest called with:" << std::endl;
    std::cerr << "[DEBUG]   config.symbol = '" << config.symbol << "'" << std::endl;
    std::cerr << "[DEBUG]   config.start_date = '" << config.start_date << "'" << std::endl;
    std::cerr << "[DEBUG]   config.end_date = '" << config.end_date << "'" << std::endl;
    std::cerr << "[DEBUG]   config.starting_capital = " << config.starting_capital << std::endl;
    
    BacktestResult result;
    result.symbol = config.symbol;
    result.starting_capital = config.starting_capital;
    result.start_date = config.start_date;
    result.end_date = config.end_date;
    
    if (!strategy_) {
        std::cerr << "[ERROR] No strategy configured for backtesting" << std::endl;
        return result;
    }
    
    // Reset portfolio
    portfolio_ = Portfolio(config.starting_capital);
    executed_signals_.clear();
    
    std::cerr << "[DEBUG] Getting historical price data..." << std::endl;
    // Get historical price data
    auto price_data_raw = market_data_.getHistoricalPrices(config.symbol, config.start_date, config.end_date);
    std::cerr << "[DEBUG] Retrieved " << price_data_raw.size() << " price records" << std::endl;
    
    if (price_data_raw.empty()) {
        std::cerr << "[ERROR] No price data available for " << config.symbol << std::endl;
        return result;
    }
    
    auto price_data = convertToTechnicalData(price_data_raw);
    std::cerr << "[DEBUG] Converted to " << price_data.size() << " technical data points" << std::endl;
    
    if (price_data.empty()) {
        std::cerr << "[ERROR] Failed to convert price data" << std::endl;
        return result;
    }
    
    // Initialize equity curve with pre-allocated capacity
    result.equity_curve.reserve(price_data.size());
    result.equity_curve.push_back(config.starting_capital);
    
    // Pre-allocate containers to avoid repeated allocations
    std::vector<PriceData> historical_window;
    historical_window.reserve(price_data.size());
    std::map<std::string, double> current_prices;
    
    std::cerr << "[DEBUG] Starting backtest loop with " << price_data.size() << " data points" << std::endl;
    std::cerr << "[DEBUG] Initial portfolio value: " << portfolio_.getTotalValue({}) << std::endl;
    
    // Process each day
    for (size_t i = 1; i < price_data.size(); ++i) {
        const auto& data_point = price_data[i];
        
        // Progress reporting every 5% of completion
        if (i % (price_data.size() / 20) == 0 || i == price_data.size() - 1 || price_data.size() <= 20) {
            double progress_pct = (static_cast<double>(i) / (price_data.size() - 1)) * 100.0;
            current_prices.clear();
            current_prices[config.symbol] = data_point.close;
            double current_value = portfolio_.getTotalValue(current_prices);
            
            // Output progress to stderr as JSON
            nlohmann::json progress;
            progress["type"] = "progress";
            progress["progress_pct"] = progress_pct;
            progress["current_date"] = data_point.date;
            progress["current_value"] = current_value;
            progress["current_price"] = data_point.close;
            progress["day"] = static_cast<int>(i);
            progress["total_days"] = static_cast<int>(price_data.size());
            
            std::cerr << progress.dump() << std::endl;
        }
        
        if (i % 50 == 0) { // Log every 50 days
            std::cerr << "[DEBUG] Day " << i << ": Price = " << data_point.close 
                      << ", Portfolio = " << portfolio_.getTotalValue({{config.symbol, data_point.close}}) << std::endl;
        }
        
        // Use sliding window approach - reuse pre-allocated vector
        historical_window.clear();
        historical_window.assign(price_data.begin(), price_data.begin() + i + 1);
        
        // Create a copy of portfolio for strategy evaluation (to avoid modifying original)
        Portfolio portfolio_copy = portfolio_;
        TradingSignal signal = strategy_->evaluateSignal(historical_window, portfolio_copy, config.symbol);
        
        if (signal.signal != Signal::HOLD) {
            std::cerr << "[DEBUG] Generated signal: " << (signal.signal == Signal::BUY ? "BUY" : "SELL") 
                      << " confidence=" << signal.confidence << " at price=" << signal.price << std::endl;
        }
        
        if (signal.signal != Signal::HOLD) {
            if (executeSignal(signal, config.symbol)) {
                executed_signals_.push_back(signal);
                result.signals_generated.push_back(signal);
                result.total_trades++;
                std::cerr << "[DEBUG] Signal EXECUTED" << std::endl;
            } else {
                std::cerr << "[DEBUG] Signal REJECTED" << std::endl;
            }
        }
        
        // Update equity curve - reuse pre-allocated map
        current_prices.clear();
        current_prices[config.symbol] = data_point.close;
        double portfolio_value = portfolio_.getTotalValue(current_prices);
        result.equity_curve.push_back(portfolio_value);
    }
    
    std::cerr << "[DEBUG] Backtest loop completed" << std::endl;
    std::cerr << "[DEBUG] Total signals generated: " << executed_signals_.size() << std::endl;
    std::cerr << "[DEBUG] Total trades executed: " << result.total_trades << std::endl;
    
    // Calculate final results
    if (!result.equity_curve.empty()) {
        result.ending_value = result.equity_curve.back();
        result.total_return_pct = ((result.ending_value - result.starting_capital) / result.starting_capital) * 100.0;
        
        std::cerr << "[DEBUG] Final calculations:" << std::endl;
        if (!price_data.empty()) {
            std::cerr << "[DEBUG]   Final price: " << price_data.back().close << std::endl;
        }
        std::cerr << "[DEBUG]   Portfolio cash: " << portfolio_.getCashBalance() << std::endl;
        std::cerr << "[DEBUG]   Calculated ending value: " << result.ending_value << std::endl;
        std::cerr << "[DEBUG]   Calculated return: " << result.total_return_pct << "%" << std::endl;
    } else {
        result.ending_value = result.starting_capital;
        result.total_return_pct = 0.0;
        std::cerr << "[DEBUG] Empty equity curve, using starting capital as ending value" << std::endl;
    }
    
    // Calculate performance metrics
    auto daily_returns = calculateDailyReturns(result.equity_curve);
    result.sharpe_ratio = calculateSharpeRatio(daily_returns);
    result.max_drawdown = calculateMaxDrawdown(result.equity_curve);
    
    // Count winning/losing trades by analyzing buy-sell pairs
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
    
    return result;
}

BacktestResult TradingEngine::runBacktestMultiSymbol(const std::vector<std::string>& symbols,
                                                   const std::string& start_date,
                                                   const std::string& end_date,
                                                   double starting_capital) {
    BacktestResult combined_result;
    combined_result.starting_capital = starting_capital;
    combined_result.start_date = start_date;
    combined_result.end_date = end_date;
    
    // For multi-symbol, run individual backtests and combine results
    for (const auto& symbol : symbols) {
        BacktestConfig config;
        config.symbol = symbol;
        config.start_date = start_date;
        config.end_date = end_date;
        config.starting_capital = starting_capital / symbols.size();
        
        BacktestResult symbol_result = runBacktest(config);
        
        // Combine results
        combined_result.total_trades += symbol_result.total_trades;
        combined_result.winning_trades += symbol_result.winning_trades;
        combined_result.losing_trades += symbol_result.losing_trades;
        combined_result.signals_generated.insert(combined_result.signals_generated.end(),
                                                symbol_result.signals_generated.begin(),
                                                symbol_result.signals_generated.end());
    }
    
    // Calculate combined metrics
    std::map<std::string, double> final_prices;
    for (const auto& symbol : symbols) {
        final_prices[symbol] = market_data_.getPrice(symbol);
    }
    
    combined_result.ending_value = portfolio_.getTotalValue(final_prices);
    combined_result.total_return_pct = ((combined_result.ending_value - combined_result.starting_capital) / combined_result.starting_capital) * 100.0;
    combined_result.win_rate = combined_result.total_trades > 0 ? 
        (static_cast<double>(combined_result.winning_trades) / combined_result.total_trades) * 100.0 : 0.0;
    
    return combined_result;
}

std::string TradingEngine::getPortfolioStatus() {
    auto current_prices = market_data_.getCurrentPrices();
    return portfolio_.toDetailedString(current_prices);
}

Portfolio& TradingEngine::getPortfolio() {
    return portfolio_;
}

const Portfolio& TradingEngine::getPortfolio() const {
    return portfolio_;
}

// Results and analytics
std::vector<TradingSignal> TradingEngine::getExecutedSignals() const {
    return executed_signals_;
}

nlohmann::json TradingEngine::getBacktestResultsAsJson(const BacktestResult& result) const {
    nlohmann::json json_result;
    
    json_result["starting_capital"] = result.starting_capital;
    json_result["ending_value"] = result.ending_value;
    json_result["total_return_pct"] = result.total_return_pct;
    json_result["trades"] = result.total_trades;
    json_result["winning_trades"] = result.winning_trades;
    json_result["losing_trades"] = result.losing_trades;
    json_result["win_rate"] = result.win_rate;
    json_result["max_drawdown"] = result.max_drawdown;
    json_result["sharpe_ratio"] = result.sharpe_ratio;
    json_result["signals_generated"] = result.signals_generated.size();
    json_result["start_date"] = result.start_date;
    json_result["end_date"] = result.end_date;
    
    // Add performance metrics object
    nlohmann::json performance_metrics;
    performance_metrics["total_return_pct"] = result.total_return_pct;
    performance_metrics["sharpe_ratio"] = result.sharpe_ratio;
    performance_metrics["max_drawdown_pct"] = result.max_drawdown;
    performance_metrics["win_rate"] = result.win_rate;
    performance_metrics["total_trades"] = result.total_trades;
    performance_metrics["winning_trades"] = result.winning_trades;
    performance_metrics["losing_trades"] = result.losing_trades;
    json_result["performance_metrics"] = performance_metrics;
    
    // Add equity curve with actual dates
    nlohmann::json equity_array = nlohmann::json::array();
    
    // Get price data to extract actual dates
    auto price_data_raw = market_data_.getHistoricalPrices(result.symbol, result.start_date, result.end_date);
    auto price_data = convertToTechnicalData(price_data_raw);
    
    for (size_t i = 0; i < result.equity_curve.size() && i < price_data.size(); ++i) {
        nlohmann::json point;
        point["date"] = (i < price_data.size()) ? price_data[i].date : result.start_date;
        point["value"] = result.equity_curve[i];
        equity_array.push_back(point);
    }
    json_result["equity_curve"] = equity_array;
    
    // Add signals
    nlohmann::json signals_array = nlohmann::json::array();
    for (const auto& signal : result.signals_generated) {
        nlohmann::json sig;
        sig["signal"] = (signal.signal == Signal::BUY) ? "BUY" : "SELL";
        sig["price"] = signal.price;
        sig["date"] = signal.date;
        sig["reason"] = signal.reason;
        sig["confidence"] = signal.confidence;
        signals_array.push_back(sig);
    }
    json_result["signals"] = signals_array;
    
    return json_result;
}

// Private helper methods
bool TradingEngine::executeSignal(const TradingSignal& signal, const std::string& symbol) {
    std::cerr << "[DEBUG] executeSignal called: " << (signal.signal == Signal::BUY ? "BUY" : "SELL") 
              << " symbol=" << symbol << " confidence=" << signal.confidence << std::endl;
    
    try {
        if (signal.signal == Signal::BUY) {
            // Only buy if we don't already have a position
            bool has_position = portfolio_.hasPosition(symbol);
            int current_shares = has_position ? portfolio_.getPosition(symbol).getShares() : 0;
            
            std::cerr << "[DEBUG] BUY signal - has_position=" << has_position 
                      << " current_shares=" << current_shares << std::endl;
            
            if (!has_position || current_shares == 0) {
                double cash_available = portfolio_.getCashBalance();
                double position_size = strategy_->calculatePositionSize(cash_available, signal.price);
                
                std::cerr << "[DEBUG] BUY order: cash=" << cash_available 
                          << " position_size=" << position_size 
                          << " price=" << signal.price << std::endl;
                
                if (position_size > 0) {
                    bool success = portfolio_.buyStock(symbol, static_cast<int>(position_size), signal.price);
                    std::cerr << "[DEBUG] Buy order " << (success ? "SUCCESS" : "FAILED") << std::endl;
                    return success;
                }
            }
        } else if (signal.signal == Signal::SELL) {
            // Only sell if we have a position
            bool has_position = portfolio_.hasPosition(symbol);
            int shares_owned = has_position ? portfolio_.getPosition(symbol).getShares() : 0;
            
            std::cerr << "[DEBUG] SELL signal - has_position=" << has_position 
                      << " shares_owned=" << shares_owned << std::endl;
            
            if (has_position && shares_owned > 0) {
                std::cerr << "[DEBUG] SELL order: shares_owned=" << shares_owned 
                          << " price=" << signal.price << std::endl;
                
                bool success = portfolio_.sellStock(symbol, shares_owned, signal.price);
                std::cerr << "[DEBUG] Sell order " << (success ? "SUCCESS" : "FAILED") << std::endl;
                return success;
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] executeSignal exception: " << e.what() << std::endl;
    }
    
    std::cerr << "[DEBUG] executeSignal returning false (no action taken)" << std::endl;
    return false;
}

std::vector<PriceData> TradingEngine::convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data) const {
    std::vector<PriceData> tech_data;
    
    for (const auto& row : db_data) {
        try {
            PriceData data;
            data.date = row.at("time");
            data.open = std::stod(row.at("open"));
            data.high = std::stod(row.at("high"));
            data.low = std::stod(row.at("low"));
            data.close = std::stod(row.at("close"));
            data.volume = std::stol(row.at("volume"));
            tech_data.push_back(data);
        } catch (const std::exception& e) {
            std::cerr << "Error converting price data: " << e.what() << std::endl;
            continue;
        }
    }
    
    return tech_data;
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