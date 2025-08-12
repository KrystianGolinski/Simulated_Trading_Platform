#pragma once

#include "simulation_config.h"
#include "strategy_analyzer.h"
#include <vector>
#include <string>

namespace TradingOrchestrator {
    
    class ExecutionPlanner {
    public:
        ExecutionPlanner();
        
        // Create execution plan based on configuration and complexity analysis
        TradingCommon::ExecutionPlan createExecutionPlan(const TradingCommon::SimulationConfig& config);
        
        // Group symbols optimally for parallel execution
        std::vector<std::vector<std::string>> groupSymbols(
            const std::vector<std::string>& symbols, 
            int target_groups) const;
        
        // Create worker configurations from symbol groups
        std::vector<TradingCommon::SimulationConfig> createWorkerConfigs(
            const TradingCommon::SimulationConfig& base_config,
            const std::vector<std::vector<std::string>>& symbol_groups) const;
        
        // Estimate execution time for a plan
        double estimateExecutionTime(const TradingCommon::ExecutionPlan& plan) const;
        
    private:
        StrategyAnalyzer strategy_analyzer_;
        
        // Symbol grouping algorithms
        std::vector<std::vector<std::string>> groupSymbolsBalanced(
            const std::vector<std::string>& symbols, 
            int target_groups) const;
        
        std::vector<std::vector<std::string>> groupSymbolsRoundRobin(
            const std::vector<std::string>& symbols, 
            int target_groups) const;
    };
    
} // namespace TradingOrchestrator