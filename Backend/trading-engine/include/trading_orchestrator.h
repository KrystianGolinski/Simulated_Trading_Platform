#pragma once

#include <map>
#include <memory>
#include <string>
#include <vector>

#include "data_processor.h"
#include "execution_service.h"
#include "market_data.h"
#include "portfolio.h"
#include "portfolio_allocator.h"
#include "progress_service.h"
#include "result.h"
#include "result_calculator.h"
#include "strategy_manager.h"
#include "trading_strategy.h"

// Forward declarations
struct TradingConfig;
struct BacktestResult;
struct PriceData;

// High-level orchestration of trading simulations and backtests
class TradingOrchestrator {
public:
    TradingOrchestrator() = default;
    ~TradingOrchestrator() = default;
    
    // Delete copy constructor and assignment operator to prevent copying
    TradingOrchestrator(const TradingOrchestrator&) = delete;
    TradingOrchestrator& operator=(const TradingOrchestrator&) = delete;
    
    // Allow move constructor and assignment
    TradingOrchestrator(TradingOrchestrator&&) = default;
    TradingOrchestrator& operator=(TradingOrchestrator&&) = default;
    
    // Main orchestration methods
    Result<std::string> runSimulation(const TradingConfig& config,
                                     Portfolio& portfolio,
                                     MarketData* market_data,
                                     DataProcessor* data_processor,
                                     StrategyManager* strategy_manager,
                                     ResultCalculator* result_calculator);
    
    Result<BacktestResult> runBacktest(const TradingConfig& config,
                                      Portfolio& portfolio,
                                      MarketData* market_data,
                                      ExecutionService* execution_service,
                                      ProgressService* progress_service,
                                      PortfolioAllocator* portfolio_allocator,
                                      DataProcessor* data_processor,
                                      StrategyManager* strategy_manager,
                                      ResultCalculator* result_calculator);
    
    // Configuration validation
    Result<void> validateTradingConfig(const TradingConfig& config,
                                      StrategyManager* strategy_manager) const;
    
    Result<void> validateSimulationParameters(const TradingConfig& config,
                                             MarketData* market_data) const;
    
    // Backtest lifecycle management
    Result<void> initializeBacktest(const TradingConfig& config,
                                   BacktestResult& result,
                                   Portfolio& portfolio,
                                   ExecutionService* execution_service) const;
    
    Result<void> runSimulationLoop(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data,
                                  const TradingConfig& config,
                                  BacktestResult& result,
                                  Portfolio& portfolio,
                                  ExecutionService* execution_service,
                                  ProgressService* progress_service,
                                  PortfolioAllocator* portfolio_allocator,
                                  DataProcessor* data_processor,
                                  StrategyManager* strategy_manager,
                                  MarketData* market_data) const;
    
    Result<void> finalizeBacktestResults(BacktestResult& result,
                                        Portfolio& portfolio,
                                        ResultCalculator* result_calculator) const;
    
    // Results processing
    Result<nlohmann::json> getBacktestResultsAsJson(const BacktestResult& result,
                                                   MarketData* market_data,
                                                   DataProcessor* data_processor) const;
    
    // Memory optimization support
    void optimizeMemoryUsage();
    void clearInternalCaches();
    
private:
    // Internal state for optimization
    std::map<std::string, std::vector<PriceData>> orchestrator_cache_;
    bool cache_enabled_ = false;
    
    // Helper methods for orchestration flow
    Result<void> validateOrchestrationParameters(const TradingConfig& config) const;
    Result<void> prepareSimulationEnvironment(const TradingConfig& config,
                                             Portfolio& portfolio,
                                             ExecutionService* execution_service) const;
    
    // Orchestration utilities
    std::string createSimulationSummary(const TradingConfig& config,
                                       const BacktestResult& result) const;
    
    void logOrchestrationStart(const TradingConfig& config) const;
    void logOrchestrationEnd(const BacktestResult& result) const;
    
    // Error handling helpers
    std::string formatOrchestrationError(const std::string& operation,
                                        const std::string& error_message) const;
};