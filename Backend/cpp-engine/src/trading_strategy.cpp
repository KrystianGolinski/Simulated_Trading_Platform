#include "trading_strategy.h"
#include <algorithm>
#include <cmath>

// Base TradingStrategy implementation
double TradingStrategy::calculatePositionSize(double available_capital, double stock_price) const {
    if (stock_price <= 0 || available_capital <= 0) {
        return 0.0;
    }
    
    double max_investment = available_capital * config_.max_position_size;
    double max_shares = std::floor(max_investment / stock_price);
    
    // Don't apply risk management when no portfolio is provided (standalone calculation)
    return max_shares;
}

double TradingStrategy::calculatePositionSize(const Portfolio& portfolio, const std::string& symbol, double stock_price, double portfolio_value) const {
    if (stock_price <= 0 || portfolio_value <= 0) {
        return 0.0;
    }
    
    // Check if position increases are enabled
    if (!config_.allow_position_increases) {
        // If position increases are disabled, only allow new positions
        if (portfolio.hasPosition(symbol) && portfolio.getPosition(symbol).getShares() > 0) {
            return 0.0;
        }
        return calculatePositionSize(portfolio.getCashBalance(), stock_price);
    }
    
    // Calculate current position value as percentage of portfolio
    double current_position_value = 0.0;
    bool has_existing_position = portfolio.hasPosition(symbol) && portfolio.getPosition(symbol).getShares() > 0;
    
    if (has_existing_position) {
        const Position& position = portfolio.getPosition(symbol);
        current_position_value = position.getShares() * stock_price;
    }
    
    double current_position_pct = current_position_value / portfolio_value;
    
    // Check if we've reached maximum position percentage
    if (current_position_pct >= config_.max_position_percentage) {
        return 0.0; // Cannot increase position further
    }
    
    // For new positions, use the standard max_position_size
    // For existing positions, use the smaller position_increase_size
    double investment_pct = has_existing_position ? config_.position_increase_size : config_.max_position_size;
    double target_investment = portfolio_value * investment_pct;
    
    // Ensure we don't exceed maximum position percentage
    double max_additional_investment = (portfolio_value * config_.max_position_percentage) - current_position_value;
    target_investment = std::min(target_investment, max_additional_investment);
    
    // Ensure we don't exceed available cash
    target_investment = std::min(target_investment, portfolio.getCashBalance());
    
    if (target_investment <= 0) {
        return 0.0;
    }
    
    return std::floor(target_investment / stock_price);
}

bool TradingStrategy::shouldApplyRiskManagement(const Portfolio& portfolio, const std::string& symbol) const {
    if (!config_.enable_risk_management) {
        return false;
    }
    
    return portfolio.hasPosition(symbol);
}

double TradingStrategy::applyRiskManagement(double position_size, const Portfolio& portfolio) const {
    if (!config_.enable_risk_management) {
        return position_size;
    }
    
    // Use cash balance as proxy for portfolio value when no prices provided
    double portfolio_value = portfolio.getCashBalance() * 2; // Rough estimate
    double max_risk = portfolio_value * 0.02;
    
    if (position_size * 100 > max_risk) {
        return std::floor(max_risk / 100);
    }
    
    return position_size;
}

// MovingAverageCrossoverStrategy implementation
MovingAverageCrossoverStrategy::MovingAverageCrossoverStrategy() 
    : TradingStrategy("Moving Average Crossover"),
      short_period_(20), long_period_(50),
      indicators_(std::make_unique<TechnicalIndicators>()) {
    config_.max_position_size = 0.1; // Default 10% position size
}

MovingAverageCrossoverStrategy::MovingAverageCrossoverStrategy(int short_period, int long_period)
    : TradingStrategy("Moving Average Crossover"),
      short_period_(short_period), long_period_(long_period),
      indicators_(std::make_unique<TechnicalIndicators>()) {
    
    if (short_period >= long_period) {
        throw std::invalid_argument("Short period must be less than long period");
    }
    config_.max_position_size = 0.1; // Default 10% position size
}

TradingSignal MovingAverageCrossoverStrategy::evaluateSignal(const std::vector<PriceData>& price_data, 
                                                           const Portfolio& portfolio,
                                                           const std::string& symbol) {
    if (price_data.empty()) {
        return TradingSignal();
    }
    
    updateIndicators(price_data);
    
    if (!indicators_->hasEnoughData(long_period_)) {
        return TradingSignal();
    }
    
    // Calculate moving averages for the last few data points
    auto short_ma = indicators_->calculateSMA(short_period_);
    auto long_ma = indicators_->calculateSMA(long_period_);
    
    if (short_ma.size() < 2 || long_ma.size() < 2) {
        return TradingSignal();
    }
    
    // Get the last two values to detect crossover
    size_t short_idx = short_ma.size() - 1;
    size_t long_idx = long_ma.size() - 1;
    
    double prev_short = short_ma[short_idx - 1];
    double prev_long = long_ma[long_idx - 1];
    double curr_short = short_ma[short_idx];
    double curr_long = long_ma[long_idx];
    
    // Get current price and date
    double current_price = price_data.back().close;
    std::string current_date = price_data.back().date;
    
    // Check for bullish crossover (buy signal) - allow position increases
    if (prev_short <= prev_long && curr_short > curr_long) {
        return TradingSignal(Signal::BUY, current_price, current_date, 
                           "MA Crossover: Short MA crossed above Long MA");
    }
    
    // Check for bearish crossover (sell signal) - only if we have a position
    if (prev_short >= prev_long && curr_short < curr_long) {
        // Only generate sell signal if we have a position for this symbol
        if (!symbol.empty() && portfolio.hasPosition(symbol) && portfolio.getPosition(symbol).getShares() > 0) {
            return TradingSignal(Signal::SELL, current_price, current_date, 
                               "MA Crossover: Short MA crossed below Long MA");
        }
    }
    
    return TradingSignal(); // No signal
}

void MovingAverageCrossoverStrategy::configure(const StrategyConfig& config) {
    TradingStrategy::configure(config);
    
    short_period_ = static_cast<int>(config.getParameter("short_period", 20));
    long_period_ = static_cast<int>(config.getParameter("long_period", 50));
    
    if (short_period_ >= long_period_) {
        short_period_ = 20;
        long_period_ = 50;
    }
}

bool MovingAverageCrossoverStrategy::validateConfig() const {
    return short_period_ > 0 && long_period_ > 0 && short_period_ < long_period_;
}

std::string MovingAverageCrossoverStrategy::getDescription() const {
    return "Moving Average Crossover strategy using " + 
           std::to_string(short_period_) + "/" + 
           std::to_string(long_period_) + " day periods";
}

void MovingAverageCrossoverStrategy::setMovingAveragePeriods(int short_period, int long_period) {
    if (short_period >= long_period || short_period <= 0 || long_period <= 0) {
        throw std::invalid_argument("Invalid moving average periods");
    }
    
    short_period_ = short_period;
    long_period_ = long_period;
}

std::pair<int, int> MovingAverageCrossoverStrategy::getMovingAveragePeriods() const {
    return {short_period_, long_period_};
}

void MovingAverageCrossoverStrategy::updateIndicators(const std::vector<PriceData>& price_data) {
    indicators_->setPriceData(price_data);
}

bool MovingAverageCrossoverStrategy::hasValidCrossover(const std::vector<double>& short_ma, 
                                                     const std::vector<double>& long_ma) const {
    if (short_ma.size() < 2 || long_ma.size() < 2) {
        return false;
    }
    
    size_t short_idx = short_ma.size() - 1;
    size_t long_idx = long_ma.size() - 1;
    
    double prev_short = short_ma[short_idx - 1];
    double prev_long = long_ma[long_idx - 1];
    double curr_short = short_ma[short_idx];
    double curr_long = long_ma[long_idx];
    
    return (prev_short <= prev_long && curr_short > curr_long) ||
           (prev_short >= prev_long && curr_short < curr_long);
}

// RSIStrategy implementation
RSIStrategy::RSIStrategy() 
    : TradingStrategy("RSI Strategy"),
      rsi_period_(14), oversold_threshold_(30.0), overbought_threshold_(70.0),
      indicators_(std::make_unique<TechnicalIndicators>()) {
    config_.max_position_size = 0.1; // Default 10% position size
}

RSIStrategy::RSIStrategy(int period, double oversold, double overbought)
    : TradingStrategy("RSI Strategy"),
      rsi_period_(period), oversold_threshold_(oversold), overbought_threshold_(overbought),
      indicators_(std::make_unique<TechnicalIndicators>()) {
    config_.max_position_size = 0.1; // Default 10% position size
}

TradingSignal RSIStrategy::evaluateSignal(const std::vector<PriceData>& price_data, 
                                         const Portfolio& portfolio,
                                         const std::string& symbol) {
    if (price_data.empty()) {
        return TradingSignal();
    }
    
    updateIndicators(price_data);
    
    if (!indicators_->hasEnoughData(rsi_period_ + 1)) {
        return TradingSignal();
    }
    
    auto signals = indicators_->detectRSISignals(oversold_threshold_, overbought_threshold_);
    
    if (signals.empty()) {
        return TradingSignal();
    }
    
    return signals.back();
}

void RSIStrategy::configure(const StrategyConfig& config) {
    TradingStrategy::configure(config);
    
    rsi_period_ = static_cast<int>(config.getParameter("rsi_period", 14));
    oversold_threshold_ = config.getParameter("oversold_threshold", 30.0);
    overbought_threshold_ = config.getParameter("overbought_threshold", 70.0);
}

bool RSIStrategy::validateConfig() const {
    return rsi_period_ > 0 && 
           oversold_threshold_ < overbought_threshold_ &&
           oversold_threshold_ >= 0 && 
           overbought_threshold_ <= 100;
}

std::string RSIStrategy::getDescription() const {
    return "RSI Strategy with " + std::to_string(rsi_period_) + 
           " period, oversold=" + std::to_string(oversold_threshold_) +
           ", overbought=" + std::to_string(overbought_threshold_);
}

void RSIStrategy::setRSIParameters(int period, double oversold, double overbought) {
    if (period <= 0 || oversold >= overbought || oversold < 0 || overbought > 100) {
        throw std::invalid_argument("Invalid RSI parameters");
    }
    
    rsi_period_ = period;
    oversold_threshold_ = oversold;
    overbought_threshold_ = overbought;
}

void RSIStrategy::updateIndicators(const std::vector<PriceData>& price_data) {
    indicators_->setPriceData(price_data);
}