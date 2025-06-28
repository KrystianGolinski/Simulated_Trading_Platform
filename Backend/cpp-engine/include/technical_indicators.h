#pragma once

#include <vector>
#include <string>
#include <map>

struct PriceData {
    double open;
    double high;
    double low;
    double close;
    long volume;
    std::string date;
    
    PriceData() : open(0.0), high(0.0), low(0.0), close(0.0), volume(0), date("") {}
    PriceData(double o, double h, double l, double c, long v, const std::string& d)
        : open(o), high(h), low(l), close(c), volume(v), date(d) {}
};

enum class Signal {
    BUY,
    SELL,
    HOLD
};

struct TradingSignal {
    Signal signal;
    double price;
    std::string date;
    std::string reason;
    double confidence;
    
    TradingSignal() : signal(Signal::HOLD), price(0.0), date(""), reason(""), confidence(0.0) {}
    TradingSignal(Signal s, double p, const std::string& d, const std::string& r, double conf = 1.0)
        : signal(s), price(p), date(d), reason(r), confidence(conf) {}
};

class TechnicalIndicators {
private:
    std::vector<PriceData> price_data_;
    std::map<std::string, std::vector<double>> indicator_cache_;
    
public:
    TechnicalIndicators() = default;
    explicit TechnicalIndicators(const std::vector<PriceData>& data);
    
    TechnicalIndicators(const TechnicalIndicators&) = delete;
    TechnicalIndicators& operator=(const TechnicalIndicators&) = delete;
    
    TechnicalIndicators(TechnicalIndicators&& other) noexcept;
    TechnicalIndicators& operator=(TechnicalIndicators&& other) noexcept;
    
    void setPriceData(const std::vector<PriceData>& data);
    void addPriceData(const PriceData& data);
    
    std::vector<double> calculateSMA(int period) const;
    std::vector<double> calculateEMA(int period) const;
    std::vector<double> calculateRSI(int period = 14) const;
    std::vector<double> calculateBollingerBands(int period = 20, double std_dev = 2.0) const;
    
    // Parallel calculation methods for multiple indicators
    struct IndicatorSet {
        std::vector<double> sma_short;
        std::vector<double> sma_long;
        std::vector<double> rsi;
        std::vector<double> ema;
    };
    
    IndicatorSet calculateIndicatorSetParallel(int sma_short_period = 20, 
                                              int sma_long_period = 50, 
                                              int rsi_period = 14, 
                                              int ema_period = 20) const;
    
    std::vector<TradingSignal> detectMACrossover(int short_period, int long_period) const;
    std::vector<TradingSignal> detectRSISignals(double oversold = 30.0, double overbought = 70.0) const;
    
    bool hasEnoughData(int required_period) const;
    int getDataSize() const;
    const std::vector<PriceData>& getPriceData() const;
    
    void clearCache();
    
private:
    void validatePeriod(int period) const;
    std::string getCacheKey(const std::string& indicator, int period) const;
    bool isCached(const std::string& key) const;
    void cacheIndicator(const std::string& key, const std::vector<double>& values);
    const std::vector<double>& getCachedIndicator(const std::string& key) const;
};