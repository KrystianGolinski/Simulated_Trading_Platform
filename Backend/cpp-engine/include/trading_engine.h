#ifndef TRADING_ENGINE_H
#define TRADING_ENGINE_H

#include "portfolio.h"
#include "market_data.h"
#include "trading_strategy.h"
#include "technical_indicators.h"
#include <string>
#include <memory>
#include <vector>
#include <map>

struct BacktestConfig {
    std::string symbol;
    std::string start_date;
    std::string end_date;
    double starting_capital;
    std::string strategy_name;
    StrategyConfig strategy_config;
    
    BacktestConfig() : starting_capital(0.0), strategy_name("ma_crossover") {}
};

class TradingEngine {
private:
    Portfolio portfolio_;
    MarketData market_data_;
    std::unique_ptr<TradingStrategy> strategy_;
    std::vector<TradingSignal> executed_signals_;
    
    // Performance optimization members
    std::map<std::string, std::vector<PriceData>> price_data_cache_;
    bool cache_enabled_;
    
public:
    TradingEngine();
    explicit TradingEngine(double initial_capital);
    
    TradingEngine(const TradingEngine&) = delete;
    TradingEngine& operator=(const TradingEngine&) = delete;
    
    TradingEngine(TradingEngine&& other) noexcept;
    TradingEngine& operator=(TradingEngine&& other) noexcept;
    
    // Strategy management
    void setStrategy(std::unique_ptr<TradingStrategy> strategy);
    void setMovingAverageStrategy(int short_period = 20, int long_period = 50);
    void setRSIStrategy(int period = 14, double oversold = 30.0, double overbought = 70.0);
    
    // Simulation methods
    std::string runSimulationWithParams(const std::string& symbol, const std::string& start_date, const std::string& end_date, double capital);
    BacktestResult runBacktest(const BacktestConfig& config);
    BacktestResult runBacktestMultiSymbol(const std::vector<std::string>& symbols,
                                         const std::string& start_date,
                                         const std::string& end_date,
                                         double starting_capital);
    
    // Enhanced multi-symbol processing with performance optimizations
    std::string runSimulationMultiSymbol(const std::vector<std::string>& symbols, 
                                       const std::string& start_date, 
                                       const std::string& end_date, 
                                       double capital,
                                       bool enable_progress = false);
    
    // Memory optimization methods
    void optimizeMemoryUsage();
    void clearCache();
    
    // Portfolio access
    std::string getPortfolioStatus();
    Portfolio& getPortfolio();
    const Portfolio& getPortfolio() const;
    
    // Results and analytics
    std::vector<TradingSignal> getExecutedSignals() const;
    nlohmann::json getBacktestResultsAsJson(const BacktestResult& result) const;
    
private:
    bool executeSignal(const TradingSignal& signal, const std::string& symbol);
    std::vector<PriceData> convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data) const;
    double calculateSharpeRatio(const std::vector<double>& returns, double risk_free_rate = 0.02) const;
    double calculateMaxDrawdown(const std::vector<double>& equity_curve) const;
    std::vector<double> calculateDailyReturns(const std::vector<double>& equity_curve) const;
};

#endif // TRADING_ENGINE_H