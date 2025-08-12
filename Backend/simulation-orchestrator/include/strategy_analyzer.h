#pragma once

#include "simulation_config.h"
#include <string>
#include <map>

namespace TradingOrchestrator {
    
    class StrategyAnalyzer {
    public:
        StrategyAnalyzer();
        
        // Analyze strategy complexity and requirements
        double getStrategyComplexityMultiplier(const std::string& strategy) const;
        
        // Determine optimal execution parameters for a strategy
        int getRecommendedWorkerCount(const TradingCommon::ComplexityAnalysis& analysis) const;
        
        // Check if strategy benefits from parallelization
        bool shouldUseParallelExecution(const TradingCommon::ComplexityAnalysis& analysis) const;
        
        // Get strategy-specific optimization hints
        std::map<std::string, std::string> getOptimizationHints(const std::string& strategy) const;
        
    private:
        std::map<std::string, double> strategy_multipliers_;
        std::map<std::string, std::map<std::string, std::string>> strategy_hints_;
        
        void initializeStrategyData();
    };
    
} // namespace TradingOrchestrator