#include "technical_indicators.h"
#include <algorithm>
#include <numeric>
#include <cmath>
#include <stdexcept>

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

std::vector<double> TechnicalIndicators::calculateSMA(int period) const {
    if (period <= 0) {
        throw std::invalid_argument("Period must be positive");
    }
    
    std::string cache_key = getCacheKey("SMA", period);
    if (isCached(cache_key)) {
        return getCachedIndicator(cache_key);
    }
    
    std::vector<double> sma_values;
    
    if (static_cast<int>(price_data_.size()) < period) {
        return sma_values;
    }
    
    for (size_t i = period - 1; i < price_data_.size(); ++i) {
        double sum = 0.0;
        for (int j = 0; j < period; ++j) {
            sum += price_data_[i - j].close;
        }
        sma_values.push_back(sum / period);
    }
    
    const_cast<TechnicalIndicators*>(this)->cacheIndicator(cache_key, sma_values);
    return sma_values;
}

std::vector<double> TechnicalIndicators::calculateEMA(int period) const {
    if (period <= 0) {
        throw std::invalid_argument("Period must be positive");
    }
    
    std::string cache_key = getCacheKey("EMA", period);
    if (isCached(cache_key)) {
        return getCachedIndicator(cache_key);
    }
    
    std::vector<double> ema_values;
    
    if (price_data_.empty()) {
        return ema_values;
    }
    
    double multiplier = 2.0 / (period + 1);
    
    double ema = price_data_[0].close;
    ema_values.push_back(ema);
    
    for (size_t i = 1; i < price_data_.size(); ++i) {
        ema = (price_data_[i].close * multiplier) + (ema * (1 - multiplier));
        ema_values.push_back(ema);
    }
    
    const_cast<TechnicalIndicators*>(this)->cacheIndicator(cache_key, ema_values);
    return ema_values;
}

std::vector<double> TechnicalIndicators::calculateRSI(int period) const {
    if (period <= 0) {
        throw std::invalid_argument("Period must be positive");
    }
    
    std::string cache_key = getCacheKey("RSI", period);
    if (isCached(cache_key)) {
        return getCachedIndicator(cache_key);
    }
    
    std::vector<double> rsi_values;
    
    if (static_cast<int>(price_data_.size()) <= period) {
        return rsi_values;
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
    
    const_cast<TechnicalIndicators*>(this)->cacheIndicator(cache_key, rsi_values);
    return rsi_values;
}

std::vector<double> TechnicalIndicators::calculateBollingerBands(int period, double std_dev) const {
    if (period <= 0) {
        throw std::invalid_argument("Period must be positive");
    }
    
    std::vector<double> sma = calculateSMA(period);
    std::vector<double> bb_values;
    
    if (sma.empty()) {
        return bb_values;
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
        
        bb_values.push_back(sma[i] + (std_dev * standard_deviation));
        bb_values.push_back(sma[i]);
        bb_values.push_back(sma[i] - (std_dev * standard_deviation));
    }
    
    return bb_values;
}

std::vector<TradingSignal> TechnicalIndicators::detectMACrossover(int short_period, int long_period) const {
    std::vector<TradingSignal> signals;
    
    if (short_period >= long_period) {
        throw std::invalid_argument("Short period must be less than long period");
    }
    
    std::vector<double> short_ma = calculateSMA(short_period);
    std::vector<double> long_ma = calculateSMA(long_period);
    
    if (short_ma.size() < 2 || long_ma.size() < 2) {
        return signals;
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
    
    return signals;
}

std::vector<TradingSignal> TechnicalIndicators::detectRSISignals(double oversold, double overbought) const {
    std::vector<TradingSignal> signals;
    std::vector<double> rsi = calculateRSI();
    
    if (rsi.size() < 2) {
        return signals;
    }
    
    for (size_t i = 1; i < rsi.size(); ++i) {
        size_t price_idx = i + 14;
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
    
    return signals;
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
    indicator_cache_.clear();
}

std::string TechnicalIndicators::getCacheKey(const std::string& indicator, int period) const {
    return indicator + "_" + std::to_string(period);
}

bool TechnicalIndicators::isCached(const std::string& key) const {
    return indicator_cache_.find(key) != indicator_cache_.end();
}

void TechnicalIndicators::cacheIndicator(const std::string& key, const std::vector<double>& values) {
    indicator_cache_[key] = values;
}

const std::vector<double>& TechnicalIndicators::getCachedIndicator(const std::string& key) const {
    return indicator_cache_.at(key);
}