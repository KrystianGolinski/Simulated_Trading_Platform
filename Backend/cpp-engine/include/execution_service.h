#pragma once

#include "result.h"
#include "trading_exceptions.h"
#include "portfolio.h"
#include "trading_strategy.h"
#include <string>
#include <vector>

class ExecutionService {
private:
    std::vector<TradingSignal> executed_signals_;
    // TODO: Add failed_executions_counter_ to track execution failures
    
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
    
private:
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