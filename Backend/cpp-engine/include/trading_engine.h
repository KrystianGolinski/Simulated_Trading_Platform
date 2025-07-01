#pragma once

#include "portfolio.h"
#include "market_data.h"
#include "execution_service.h"
#include "progress_service.h"
#include "trading_strategy.h"
#include "technical_indicators.h"
#include "portfolio_allocator.h"
#include "result.h"
#include "error_utils.h"
#include <string>
#include <memory>
#include <vector>
#include <map>

// Unified configuration struct that replaces both BacktestConfig and SimulationConfig
// Supports both single and multi-symbol operations with flexible parameter management
struct TradingConfig {
    std::vector<std::string> symbols;              // Support for multiple symbols (single symbol = size 1)
    std::string start_date;
    std::string end_date;
    double starting_capital;
    std::string strategy_name;
    std::map<std::string, double> strategy_parameters;  // Flexible parameter storage
    
    // Default constructor with sensible defaults
    TradingConfig() : starting_capital(10000.0), strategy_name("ma_crossover") {
        symbols.push_back("AAPL");  // Default single symbol
        // Set default parameters for ma_crossover strategy
        strategy_parameters["short_ma"] = 20.0;
        strategy_parameters["long_ma"] = 50.0;
        // Set default parameters for rsi strategy
        strategy_parameters["rsi_period"] = 14.0;
        strategy_parameters["rsi_oversold"] = 30.0;
        strategy_parameters["rsi_overbought"] = 70.0;
    }
    
    // Constructor for single symbol (backward compatibility)
    TradingConfig(const std::string& symbol, const std::string& start, const std::string& end, double capital, const std::string& strategy = "ma_crossover")
        : start_date(start), end_date(end), starting_capital(capital), strategy_name(strategy) {
        symbols.push_back(symbol);
        // Set default strategy parameters
        strategy_parameters["short_ma"] = 20.0;
        strategy_parameters["long_ma"] = 50.0;
        strategy_parameters["rsi_period"] = 14.0;
        strategy_parameters["rsi_oversold"] = 30.0;
        strategy_parameters["rsi_overbought"] = 70.0;
    }
    
    // Helper methods for type-safe parameter access
    int getIntParameter(const std::string& key, int default_value = 0) const {
        auto it = strategy_parameters.find(key);
        return (it != strategy_parameters.end()) ? static_cast<int>(it->second) : default_value;
    }
    
    double getDoubleParameter(const std::string& key, double default_value = 0.0) const {
        auto it = strategy_parameters.find(key);
        return (it != strategy_parameters.end()) ? it->second : default_value;
    }
    
    void setParameter(const std::string& key, double value) {
        strategy_parameters[key] = value;
    }
    
    // Convenience methods
    bool isMultiSymbol() const { return symbols.size() > 1; }
    bool isSingleSymbol() const { return symbols.size() == 1; }
    std::string getPrimarySymbol() const { return symbols.empty() ? "AAPL" : symbols[0]; }
    
    // Convert to StrategyConfig for backward compatibility
    StrategyConfig toStrategyConfig() const {
        StrategyConfig config;
        for (const auto& param : strategy_parameters) {
            config.setParameter(param.first, param.second);
        }
        return config;
    }
};


class TradingEngine {
private:
    Portfolio portfolio_;
    std::unique_ptr<TradingStrategy> strategy_;
    
    // Service components (dependency injection)
    std::unique_ptr<MarketData> market_data_;
    std::unique_ptr<ExecutionService> execution_service_;
    std::unique_ptr<ProgressService> progress_service_;
    std::unique_ptr<PortfolioAllocator> portfolio_allocator_;
    
    // Performance optimization members
    std::map<std::string, std::vector<PriceData>> price_data_cache_;
    bool cache_enabled_;
    
public:
    TradingEngine();
    explicit TradingEngine(double initial_capital);
    
    // Constructor with custom services (dependency injection)
    TradingEngine(double initial_capital,
                 std::unique_ptr<MarketData> market_data,
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
    
    // Unified simulation methods using TradingConfig
    Result<std::string> runSimulation(const TradingConfig& config);
    Result<BacktestResult> runBacktest(const TradingConfig& config);
    
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
    MarketData* getMarketData() const;
    ExecutionService* getExecutionService() const;
    ProgressService* getProgressService() const;
    
private:
    // Unified internal methods using TradingConfig
    Result<void> validateTradingConfig(const TradingConfig& config) const;
    Result<void> initializeBacktest(const TradingConfig& config, BacktestResult& result);
    Result<std::map<std::string, std::vector<PriceData>>> prepareMarketData(const TradingConfig& config);
    Result<void> runSimulationLoop(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data, const TradingConfig& config, BacktestResult& result);
    Result<void> finalizeBacktestResults(BacktestResult& result);
    
    // Helper functions using unified configuration
    Result<void> validateSimulationParameters(const TradingConfig& config);
    std::string createDataErrorMessage(const std::string& symbol, const std::string& start_date, const std::string& end_date, const std::string& error_type);
    void calculateTradeMetrics(BacktestResult& result);
    void calculatePortfolioMetrics(BacktestResult& result);
    void calculatePerSymbolMetrics(BacktestResult& result);
    void calculateComprehensiveMetrics(BacktestResult& result);
    void calculateDiversificationMetrics(BacktestResult& result);
    
    // Service initialization
    void initializeServices();
    std::vector<PriceData> convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data) const;
    double calculateSharpeRatio(const std::vector<double>& returns, double risk_free_rate = 0.02) const;
    double calculateMaxDrawdown(const std::vector<double>& equity_curve) const;
    std::vector<double> calculateDailyReturns(const std::vector<double>& equity_curve) const;
};