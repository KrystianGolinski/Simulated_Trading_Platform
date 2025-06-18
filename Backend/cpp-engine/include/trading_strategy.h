#pragma once

#include "technical_indicators.h"
#include "portfolio.h"
#include "market_data.h"
#include <memory>
#include <string>
#include <vector>
#include <map>

struct StrategyConfig {
    std::map<std::string, double> parameters;
    double max_position_size = 0.1;
    double stop_loss_pct = -0.05;
    double take_profit_pct = 0.15;
    bool enable_risk_management = true;
    
    void setParameter(const std::string& key, double value) {
        parameters[key] = value;
    }
    
    double getParameter(const std::string& key, double default_value = 0.0) const {
        auto it = parameters.find(key);
        return it != parameters.end() ? it->second : default_value;
    }
};

struct BacktestResult {
    std::string symbol;
    double starting_capital;
    double ending_value;
    double total_return_pct;
    int total_trades;
    int winning_trades;
    int losing_trades;
    double win_rate;
    double max_drawdown;
    double sharpe_ratio;
    std::vector<TradingSignal> signals_generated;
    std::vector<double> equity_curve;
    std::string start_date;
    std::string end_date;
    
    BacktestResult() : starting_capital(0), ending_value(0), total_return_pct(0),
                      total_trades(0), winning_trades(0), losing_trades(0),
                      win_rate(0), max_drawdown(0), sharpe_ratio(0) {}
};

class TradingStrategy {
protected:
    StrategyConfig config_;
    std::string strategy_name_;
    
public:
    explicit TradingStrategy(const std::string& name) : strategy_name_(name) {}
    virtual ~TradingStrategy() = default;
    
    TradingStrategy(const TradingStrategy&) = delete;
    TradingStrategy& operator=(const TradingStrategy&) = delete;
    
    TradingStrategy(TradingStrategy&&) = default;
    TradingStrategy& operator=(TradingStrategy&&) = default;
    
    virtual TradingSignal evaluateSignal(const std::vector<PriceData>& price_data, 
                                       const Portfolio& portfolio,
                                       const std::string& symbol = "") = 0;
    
    virtual void configure(const StrategyConfig& config) { config_ = config; }
    
    virtual std::string getName() const { return strategy_name_; }
    virtual StrategyConfig getConfig() const { return config_; }
    
    virtual bool validateConfig() const = 0;
    virtual std::string getDescription() const = 0;
    
    double calculatePositionSize(double available_capital, double stock_price) const;
    bool shouldApplyRiskManagement(const Portfolio& portfolio, const std::string& symbol) const;
    
protected:
    double applyRiskManagement(double position_size, const Portfolio& portfolio) const;
};

class MovingAverageCrossoverStrategy : public TradingStrategy {
private:
    int short_period_;
    int long_period_;
    std::unique_ptr<TechnicalIndicators> indicators_;
    
public:
    MovingAverageCrossoverStrategy();
    explicit MovingAverageCrossoverStrategy(int short_period, int long_period);
    
    TradingSignal evaluateSignal(const std::vector<PriceData>& price_data, 
                               const Portfolio& portfolio,
                               const std::string& symbol = "") override;
    
    void configure(const StrategyConfig& config) override;
    bool validateConfig() const override;
    std::string getDescription() const override;
    
    void setMovingAveragePeriods(int short_period, int long_period);
    std::pair<int, int> getMovingAveragePeriods() const;
    
private:
    void updateIndicators(const std::vector<PriceData>& price_data);
    bool hasValidCrossover(const std::vector<double>& short_ma, 
                          const std::vector<double>& long_ma) const;
};

class RSIStrategy : public TradingStrategy {
private:
    int rsi_period_;
    double oversold_threshold_;
    double overbought_threshold_;
    std::unique_ptr<TechnicalIndicators> indicators_;
    
public:
    RSIStrategy();
    explicit RSIStrategy(int period, double oversold = 30.0, double overbought = 70.0);
    
    TradingSignal evaluateSignal(const std::vector<PriceData>& price_data, 
                               const Portfolio& portfolio,
                               const std::string& symbol = "") override;
    
    void configure(const StrategyConfig& config) override;
    bool validateConfig() const override;
    std::string getDescription() const override;
    
    void setRSIParameters(int period, double oversold, double overbought);
    
private:
    void updateIndicators(const std::vector<PriceData>& price_data);
};