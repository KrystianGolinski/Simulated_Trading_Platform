#pragma once

#include "portfolio.h"
#include "database_service.h"
#include "execution_service.h"
#include "progress_service.h"
#include "trading_strategy.h"
#include "technical_indicators.h"
#include "result.h"
#include "error_utils.h"
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
    std::unique_ptr<TradingStrategy> strategy_;
    
    // Service components (dependency injection)
    std::unique_ptr<DatabaseService> database_service_;
    std::unique_ptr<ExecutionService> execution_service_;
    std::unique_ptr<ProgressService> progress_service_;
    
    // Performance optimization members
    std::map<std::string, std::vector<PriceData>> price_data_cache_;
    bool cache_enabled_;
    
public:
    TradingEngine();
    explicit TradingEngine(double initial_capital);
    
    // Constructor with custom services (dependency injection)
    TradingEngine(double initial_capital,
                 std::unique_ptr<DatabaseService> db_service,
                 std::unique_ptr<ExecutionService> exec_service,
                 std::unique_ptr<ProgressService> progress_service);
    
    TradingEngine(const TradingEngine&) = delete;
    TradingEngine& operator=(const TradingEngine&) = delete;
    
    TradingEngine(TradingEngine&& other) noexcept;
    TradingEngine& operator=(TradingEngine&& other) noexcept;
    
    // Strategy management
    void setStrategy(std::unique_ptr<TradingStrategy> strategy);
    void setMovingAverageStrategy(int short_period = 20, int long_period = 50);
    void setRSIStrategy(int period = 14, double oversold = 30.0, double overbought = 70.0);
    
    // Simulation methods - now using Result<T> patterns
    Result<std::string> runSimulationWithParams(const std::string& symbol, const std::string& start_date, const std::string& end_date, double capital);
    Result<BacktestResult> runBacktest(const BacktestConfig& config);
    Result<BacktestResult> runBacktestMultiSymbol(const std::vector<std::string>& symbols,
                                                  const std::string& start_date,
                                                  const std::string& end_date,
                                                  double starting_capital);
    
    // Enhanced multi-symbol processing with performance optimizations
    Result<std::string> runSimulationMultiSymbol(const std::vector<std::string>& symbols, 
                                                const std::string& start_date, 
                                                const std::string& end_date, 
                                                double capital,
                                                bool enable_progress = false);
    
    // Memory optimization methods
    void optimizeMemoryUsage();
    void clearCache();
    
    // Portfolio access
    Result<std::string> getPortfolioStatus();
    Portfolio& getPortfolio();
    const Portfolio& getPortfolio() const;
    
    // Results and analytics
    std::vector<TradingSignal> getExecutedSignals() const;
    Result<nlohmann::json> getBacktestResultsAsJson(const BacktestResult& result) const;
    
    // Service access for testing and configuration
    DatabaseService* getDatabaseService() const;
    ExecutionService* getExecutionService() const;
    ProgressService* getProgressService() const;
    
private:
    // Decomposed backtest methods - now using Result<T> patterns
    Result<void> validateBacktestConfig(const BacktestConfig& config) const;
    Result<void> initializeBacktest(const BacktestConfig& config, BacktestResult& result);
    Result<std::vector<PriceData>> prepareMarketData(const BacktestConfig& config);
    Result<void> runSimulationLoop(const std::vector<PriceData>& price_data, const BacktestConfig& config, BacktestResult& result);
    Result<void> finalizeBacktestResults(BacktestResult& result);
    
    // Service initialization
    void initializeServices();
    std::vector<PriceData> convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data) const;
    double calculateSharpeRatio(const std::vector<double>& returns, double risk_free_rate = 0.02) const;
    double calculateMaxDrawdown(const std::vector<double>& equity_curve) const;
    std::vector<double> calculateDailyReturns(const std::vector<double>& equity_curve) const;
};