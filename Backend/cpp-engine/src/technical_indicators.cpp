#include "technical_indicators.h"
#include "error_utils.h"
#include <algorithm>
#include <numeric>
#include <cmath>
#include <future>
#include <thread>

TechnicalIndicators::TechnicalIndicators(const std::vector<PriceData>& data) 
    : price_data_(data) {}

TechnicalIndicators::TechnicalIndicators(TechnicalIndicators&& other) noexcept
    : price_data_(std::move(other.price_data_)), 
      indicator_cache_(std::move(other.indicator_cache_)) {}

TechnicalIndicators& TechnicalIndicators::operator=(TechnicalIndicators&& other) noexcept {
    if (this != &other) {
        price_data_ = std::move(other.price_data_);
        indicator_cache_ = std::move(other.indicator_cache_);
    }
    return *this;
}

void TechnicalIndicators::setPriceData(const std::vector<PriceData>& data) {
    price_data_ = data;
    clearCache();
}

void TechnicalIndicators::addPriceData(const PriceData& data) {
    price_data_.push_back(data);
    clearCache();
}

Result<void> TechnicalIndicators::validatePeriod(int period) const {
    if (period <= 0) {
        return Result<void>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PERIOD, 
                           "Period must be positive, got: " + std::to_string(period));
    }
    return Result<void>();
}

Result<std::vector<double>> TechnicalIndicators::calculateSMA(int period) const {
    // Validate period parameter
    auto validation_result = validatePeriod(period);
    if (validation_result.isError()) {
        return Result<std::vector<double>>(validation_result.getError());
    }
    
    std::string cache_key = getCacheKey("SMA", period);
    if (isCached(cache_key)) {
        return Result<std::vector<double>>(getCachedIndicator(cache_key));
    }
    
    std::vector<double> sma_values;
    
    // Check if we have enough data points for the calculation
    if (static_cast<int>(price_data_.size()) < period) {
        return Result<std::vector<double>>(ErrorCode::TECHNICAL_ANALYSIS_INSUFFICIENT_DATA,
                                          "Insufficient data for SMA calculation. Required: " + 
                                          std::to_string(period) + ", Available: " + 
                                          std::to_string(price_data_.size()));
    }
    
    // Vectorized SMA calculation
    sma_values.reserve(price_data_.size() - period + 1);
    
    // Calculate initial sum
    double sum = 0.0;
    for (int j = 0; j < period; ++j) {
        sum += price_data_[j].close;
    }
    sma_values.push_back(sum / period);
    
    // Rolling calculation for efficiency
    for (size_t i = period; i < price_data_.size(); ++i) {
        sum = sum - price_data_[i - period].close + price_data_[i].close;
        sma_values.push_back(sum / period);
    }
    
    cacheIndicator(cache_key, sma_values);
    return Result<std::vector<double>>(sma_values);
}

Result<std::vector<double>> TechnicalIndicators::calculateEMA(int period) const {
    // Validate period parameter
    auto validation_result = validatePeriod(period);
    if (validation_result.isError()) {
        return Result<std::vector<double>>(validation_result.getError());
    }
    
    std::string cache_key = getCacheKey("EMA", period);
    if (isCached(cache_key)) {
        return Result<std::vector<double>>(getCachedIndicator(cache_key));
    }
    
    std::vector<double> ema_values;
    
    // Check if we have any data
    if (price_data_.empty()) {
        return Result<std::vector<double>>(ErrorCode::TECHNICAL_ANALYSIS_INSUFFICIENT_DATA,
                                          "No price data available for EMA calculation");
    }
    
    double multiplier = 2.0 / (period + 1);
    
    double ema = price_data_[0].close;
    ema_values.push_back(ema);
    
    for (size_t i = 1; i < price_data_.size(); ++i) {
        ema = (price_data_[i].close * multiplier) + (ema * (1 - multiplier));
        ema_values.push_back(ema);
    }
    
    cacheIndicator(cache_key, ema_values);
    return Result<std::vector<double>>(ema_values);
}

Result<std::vector<double>> TechnicalIndicators::calculateRSI(int period) const {
    // Validate period parameter
    auto validation_result = validatePeriod(period);
    if (validation_result.isError()) {
        return Result<std::vector<double>>(validation_result.getError());
    }
    
    std::string cache_key = getCacheKey("RSI", period);
    if (isCached(cache_key)) {
        return Result<std::vector<double>>(getCachedIndicator(cache_key));
    }
    
    std::vector<double> rsi_values;
    
    // Check if we have enough data for RSI calculation (need at least period + 1 for changes)
    if (static_cast<int>(price_data_.size()) <= period) {
        return Result<std::vector<double>>(ErrorCode::TECHNICAL_ANALYSIS_INSUFFICIENT_DATA,
                                          "Insufficient data for RSI calculation. Required: " + 
                                          std::to_string(period + 1) + ", Available: " + 
                                          std::to_string(price_data_.size()));
    }
    
    std::vector<double> gains, losses;
    
    for (size_t i = 1; i < price_data_.size(); ++i) {
        double change = price_data_[i].close - price_data_[i-1].close;
        gains.push_back(change > 0 ? change : 0);
        losses.push_back(change < 0 ? -change : 0);
    }
    
    double avg_gain = 0.0, avg_loss = 0.0;
    for (int i = 0; i < period; ++i) {
        avg_gain += gains[i];
        avg_loss += losses[i];
    }
    avg_gain /= period;
    avg_loss /= period;
    
    if (avg_loss == 0) {
        rsi_values.push_back(100.0);
    } else {
        double rs = avg_gain / avg_loss;
        rsi_values.push_back(100.0 - (100.0 / (1.0 + rs)));
    }
    
    for (size_t i = period; i < gains.size(); ++i) {
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period;
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period;
        
        if (avg_loss == 0) {
            rsi_values.push_back(100.0);
        } else {
            double rs = avg_gain / avg_loss;
            rsi_values.push_back(100.0 - (100.0 / (1.0 + rs)));
        }
    }
    
    cacheIndicator(cache_key, rsi_values);
    return Result<std::vector<double>>(rsi_values);
}

Result<std::vector<double>> TechnicalIndicators::calculateBollingerBands(int period, double std_dev) const {
    // Validate period parameter
    auto validation_result = validatePeriod(period);
    if (validation_result.isError()) {
        return Result<std::vector<double>>(validation_result.getError());
    }
    
    // Validate standard deviation parameter
    if (std_dev <= 0) {
        return Result<std::vector<double>>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER,
                                          "Standard deviation must be positive, got: " + std::to_string(std_dev));
    }
    
    auto sma_result = calculateSMA(period);
    if (sma_result.isError()) {
        return Result<std::vector<double>>(sma_result.getError());
    }
    
    const auto& sma = sma_result.getValue();
    std::vector<double> bb_values;
    
    if (sma.empty()) {
        return Result<std::vector<double>>(ErrorCode::TECHNICAL_ANALYSIS_INSUFFICIENT_DATA,
                                          "SMA calculation returned no data for Bollinger Bands");
    }
    
    for (size_t i = 0; i < sma.size(); ++i) {
        size_t start_idx = i + period - 1;
        double sum_sq_diff = 0.0;
        
        for (int j = 0; j < period; ++j) {
            double diff = price_data_[start_idx - j].close - sma[i];
            sum_sq_diff += diff * diff;
        }
        
        double variance = sum_sq_diff / period;
        double standard_deviation = std::sqrt(variance);
        
        // Upper band, middle band (SMA), lower band
        bb_values.push_back(sma[i] + (std_dev * standard_deviation));
        bb_values.push_back(sma[i]);
        bb_values.push_back(sma[i] - (std_dev * standard_deviation));
    }
    
    return Result<std::vector<double>>(bb_values);
}

Result<std::vector<TradingSignal>> TechnicalIndicators::detectMACrossover(int short_period, int long_period) const {
    std::vector<TradingSignal> signals;
    
    // Validate that short period is less than long period
    if (short_period >= long_period) {
        return Result<std::vector<TradingSignal>>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER,
                                                  "Short period must be less than long period. Short: " + 
                                                  std::to_string(short_period) + ", Long: " + std::to_string(long_period));
    }
    
    // Calculate moving averages using Result<T> patterns
    auto short_ma_result = calculateSMA(short_period);
    if (short_ma_result.isError()) {
        return Result<std::vector<TradingSignal>>(short_ma_result.getError());
    }
    
    auto long_ma_result = calculateSMA(long_period);
    if (long_ma_result.isError()) {
        return Result<std::vector<TradingSignal>>(long_ma_result.getError());
    }
    
    const auto& short_ma = short_ma_result.getValue();
    const auto& long_ma = long_ma_result.getValue();
    
    // Check if we have enough data points for crossover detection
    if (short_ma.size() < 2 || long_ma.size() < 2) {
        return Result<std::vector<TradingSignal>>(ErrorCode::TECHNICAL_ANALYSIS_INSUFFICIENT_DATA,
                                                  "Insufficient moving average data for crossover detection. Short MA: " + 
                                                  std::to_string(short_ma.size()) + ", Long MA: " + std::to_string(long_ma.size()));
    }
    
    size_t long_ma_start = long_period - short_period;
    
    for (size_t i = 1; i < long_ma.size(); ++i) {
        size_t short_idx = i + long_ma_start;
        size_t price_idx = i + long_period - 1;
        
        if (short_idx >= short_ma.size() || price_idx >= price_data_.size()) {
            continue;
        }
        
        double prev_short = short_ma[short_idx - 1];
        double prev_long = long_ma[i - 1];
        double curr_short = short_ma[short_idx];
        double curr_long = long_ma[i];
        
        if (prev_short <= prev_long && curr_short > curr_long) {
            signals.emplace_back(Signal::BUY, price_data_[price_idx].close, 
                               price_data_[price_idx].date, 
                               "MA Crossover: Short MA crossed above Long MA");
        } else if (prev_short >= prev_long && curr_short < curr_long) {
            signals.emplace_back(Signal::SELL, price_data_[price_idx].close, 
                               price_data_[price_idx].date, 
                               "MA Crossover: Short MA crossed below Long MA");
        }
    }
    
    return Result<std::vector<TradingSignal>>(signals);
}

Result<std::vector<TradingSignal>> TechnicalIndicators::detectRSISignals(double oversold, double overbought) const {
    std::vector<TradingSignal> signals;
    
    // Validate RSI thresholds
    if (oversold >= overbought) {
        return Result<std::vector<TradingSignal>>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER,
                                                  "Oversold threshold must be less than overbought. Oversold: " + 
                                                  std::to_string(oversold) + ", Overbought: " + std::to_string(overbought));
    }
    
    if (oversold < 0 || oversold > 100 || overbought < 0 || overbought > 100) {
        return Result<std::vector<TradingSignal>>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER,
                                                  "RSI thresholds must be between 0 and 100. Oversold: " + 
                                                  std::to_string(oversold) + ", Overbought: " + std::to_string(overbought));
    }
    
    // Calculate RSI using Result<T> patterns
    auto rsi_result = calculateRSI();
    if (rsi_result.isError()) {
        return Result<std::vector<TradingSignal>>(rsi_result.getError());
    }
    
    const auto& rsi = rsi_result.getValue();
    
    // Check if we have enough RSI data for signal detection
    if (rsi.size() < 2) {
        return Result<std::vector<TradingSignal>>(ErrorCode::TECHNICAL_ANALYSIS_INSUFFICIENT_DATA,
                                                  "Insufficient RSI data for signal detection. Available: " + 
                                                  std::to_string(rsi.size()));
    }
    
    for (size_t i = 1; i < rsi.size(); ++i) {
        size_t price_idx = i + 14; // Default RSI period
        if (price_idx >= price_data_.size()) {
            continue;
        }
        
        if (rsi[i-1] <= oversold && rsi[i] > oversold) {
            signals.emplace_back(Signal::BUY, price_data_[price_idx].close, 
                               price_data_[price_idx].date, 
                               "RSI Oversold Recovery");
        } else if (rsi[i-1] >= overbought && rsi[i] < overbought) {
            signals.emplace_back(Signal::SELL, price_data_[price_idx].close, 
                               price_data_[price_idx].date, 
                               "RSI Overbought Reversal");
        }
    }
    
    return Result<std::vector<TradingSignal>>(signals);
}

bool TechnicalIndicators::hasEnoughData(int required_period) const {
    return static_cast<int>(price_data_.size()) >= required_period;
}

int TechnicalIndicators::getDataSize() const {
    return static_cast<int>(price_data_.size());
}

const std::vector<PriceData>& TechnicalIndicators::getPriceData() const {
    return price_data_;
}

void TechnicalIndicators::clearCache() {
    std::lock_guard<std::mutex> lock(cache_mutex_);
    indicator_cache_.clear();
}

std::string TechnicalIndicators::getCacheKey(const std::string& indicator, int period) const {
    return indicator + "_" + std::to_string(period);
}

bool TechnicalIndicators::isCached(const std::string& key) const {
    std::lock_guard<std::mutex> lock(cache_mutex_);
    return indicator_cache_.find(key) != indicator_cache_.end();
}

void TechnicalIndicators::cacheIndicator(const std::string& key, const std::vector<double>& values) const {
    std::lock_guard<std::mutex> lock(cache_mutex_);
    indicator_cache_[key] = values;
}

const std::vector<double>& TechnicalIndicators::getCachedIndicator(const std::string& key) const {
    std::lock_guard<std::mutex> lock(cache_mutex_);
    return indicator_cache_.at(key);
}

Result<TechnicalIndicators::IndicatorSet> TechnicalIndicators::calculateIndicatorSetParallel(int sma_short_period, 
                                                                                                        int sma_long_period, 
                                                                                                        int rsi_period, 
                                                                                                        int ema_period) const {
    IndicatorSet result;
    
    // Use std::async for parallel computation of independent indicators
    auto sma_short_future = std::async(std::launch::async, [this, sma_short_period]() {
        return calculateSMA(sma_short_period);
    });
    
    auto sma_long_future = std::async(std::launch::async, [this, sma_long_period]() {
        return calculateSMA(sma_long_period);
    });
    
    auto rsi_future = std::async(std::launch::async, [this, rsi_period]() {
        return calculateRSI(rsi_period);
    });
    
    auto ema_future = std::async(std::launch::async, [this, ema_period]() {
        return calculateEMA(ema_period);
    });
    
    // Collect results and check for errors
    auto sma_short_result = sma_short_future.get();
    if (sma_short_result.isError()) {
        return Result<IndicatorSet>(sma_short_result.getError());
    }
    
    auto sma_long_result = sma_long_future.get();
    if (sma_long_result.isError()) {
        return Result<IndicatorSet>(sma_long_result.getError());
    }
    
    auto rsi_result = rsi_future.get();
    if (rsi_result.isError()) {
        return Result<IndicatorSet>(rsi_result.getError());
    }
    
    auto ema_result = ema_future.get();
    if (ema_result.isError()) {
        return Result<IndicatorSet>(ema_result.getError());
    }
    
    // All calculations succeeded, populate result
    result.sma_short = sma_short_result.getValue();
    result.sma_long = sma_long_result.getValue();
    result.rsi = rsi_result.getValue();
    result.ema = ema_result.getValue();
    
    return Result<IndicatorSet>(result);
}