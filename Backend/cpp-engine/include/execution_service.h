#pragma once

#include <string>
#include <vector>

#include "memory_optimizable.h"
#include "portfolio.h"
#include "result.h"
#include "trading_exceptions.h"
#include "trading_strategy.h"

class ExecutionService : public IMemoryOptimizable {
public:
    ExecutionService() = default;
    ~ExecutionService() = default;
    
    // Non-copyable but movable
    ExecutionService(const ExecutionService&) = delete;
    ExecutionService& operator=(const ExecutionService&) = delete;
    ExecutionService(ExecutionService&&) = default;
    ExecutionService& operator=(ExecutionService&&) = default;
    
    // Signal execution
    Result<void> executeSignal(const TradingSignal& signal, 
                               const std::string& symbol, 
                               Portfolio& portfolio,
                               TradingStrategy* strategy);
    
    // Executed signals management
    std::vector<TradingSignal> getExecutedSignals() const;
    void clearExecutedSignals();
    void addExecutedSignal(const TradingSignal& signal);
    
    // Execution statistics
    int getTotalExecutions() const;
    int getSuccessfulExecutions() const;
    int getFailedExecutions() const;
    
    // Memory optimization interface
    void optimizeMemory() override;
    size_t getMemoryUsage() const override;
    std::string getMemoryReport() const override;

private:
    std::vector<TradingSignal> executed_signals_;
    int failed_executions_counter_ = 0;
    
    // Internal execution logic
    Result<void> executeBuySignal(const TradingSignal& signal, 
                                  const std::string& symbol, 
                                  Portfolio& portfolio,
                                  TradingStrategy* strategy);
    
    Result<void> executeSellSignal(const TradingSignal& signal, 
                                   const std::string& symbol, 
                                   Portfolio& portfolio);
    
    // Execution validation
    Result<void> validateSignal(const TradingSignal& signal, const std::string& symbol) const;
};