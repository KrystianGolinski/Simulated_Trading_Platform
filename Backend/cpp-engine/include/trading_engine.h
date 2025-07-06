#pragma once

#include "portfolio.h"
#include "market_data.h"
#include "execution_service.h"
#include "progress_service.h"
#include "trading_strategy.h"
#include "technical_indicators.h"
#include "portfolio_allocator.h"
#include "result_calculator.h"
#include "data_processor.h"
#include "strategy_manager.h"
#include "trading_orchestrator.h"
#include "result.h"
#include "error_utils.h"
#include <string>
#include <memory>
#include <vector>
#include <map>

// Unified configuration struct
// Supports both single and multi-symbol operations with flexible parameter management
struct TradingConfig {
    std::vector<std::string> symbols;              // Support for multiple symbols (single symbol = symbols[0])
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
};

class TradingEngine {
private:
    Portfolio portfolio_;
    
    // Service components (dependency injection)
    std::unique_ptr<MarketData> market_data_;
    std::unique_ptr<ExecutionService> execution_service_;
    std::unique_ptr<ProgressService> progress_service_;
    std::unique_ptr<PortfolioAllocator> portfolio_allocator_;
    std::unique_ptr<ResultCalculator> result_calculator_;
    std::unique_ptr<DataProcessor> data_processor_;
    std::unique_ptr<StrategyManager> strategy_manager_;
    std::unique_ptr<TradingOrchestrator> trading_orchestrator_;
    
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
    
    // Strategy manager access
    StrategyManager* getStrategyManager() const;
    
    // Trading orchestrator access
    TradingOrchestrator* getTradingOrchestrator() const;
    
    // Memory optimization methods
    void optimizeMemoryUsage();
    void clearCache();
    
    // Portfolio access
    Portfolio& getPortfolio();
    const Portfolio& getPortfolio() const;
    
    // Service access for testing and configuration
    MarketData* getMarketData() const;
    ExecutionService* getExecutionService() const;
    ProgressService* getProgressService() const;
    DataProcessor* getDataProcessor() const;
    ResultCalculator* getResultCalculator() const;
    PortfolioAllocator* getPortfolioAllocator() const;
private:
    // Service initialization
    void initializeServices();
};