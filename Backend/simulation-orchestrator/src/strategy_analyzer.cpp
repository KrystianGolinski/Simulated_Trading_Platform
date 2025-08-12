#include "strategy_analyzer.h"
#include <algorithm>

namespace TradingOrchestrator {

StrategyAnalyzer::StrategyAnalyzer() {
    initializeStrategyData();
}

void StrategyAnalyzer::initializeStrategyData() {
    // Strategy complexity multipliers based on computational intensity
    strategy_multipliers_["ma_crossover"] = 1.0;    // Base complexity
    strategy_multipliers_["rsi"] = 1.2;             // Slightly more complex
    strategy_multipliers_["bollinger_bands"] = 1.5; // More complex calculations
    strategy_multipliers_["macd"] = 1.3;            // Moderate complexity
    strategy_multipliers_["stochastic"] = 1.4;      // Higher complexity
    
    // Strategy-specific optimization hints
    strategy_hints_["ma_crossover"] = {
        {"memory_usage", "low"},
        {"cpu_intensive", "false"},
        {"io_bound", "true"}
    };
    
    strategy_hints_["rsi"] = {
        {"memory_usage", "medium"},
        {"cpu_intensive", "true"},
        {"io_bound", "false"}
    };
    
    strategy_hints_["bollinger_bands"] = {
        {"memory_usage", "high"},
        {"cpu_intensive", "true"},
        {"io_bound", "false"}
    };
}

double StrategyAnalyzer::getStrategyComplexityMultiplier(const std::string& strategy) const {
    auto it = strategy_multipliers_.find(strategy);
    if (it != strategy_multipliers_.end()) {
        return it->second;
    }
    
    // Default multiplier for unknown strategies
    return 1.0;
}

int StrategyAnalyzer::getRecommendedWorkerCount(const TradingCommon::ComplexityAnalysis& analysis) const {
    if (!analysis.should_use_parallel) {
        return 1;
    }
    
    // Base recommendation from complexity analysis
    int base_workers = analysis.recommended_workers;
    
    // Adjust based on complexity category
    if (analysis.complexity_category == "low") {
        return 1;
    } else if (analysis.complexity_category == "medium") {
        return std::min(2, base_workers);
    } else if (analysis.complexity_category == "high") {
        return std::min(4, base_workers);
    } else { // extreme
        return std::min(8, base_workers);
    }
}

bool StrategyAnalyzer::shouldUseParallelExecution(const TradingCommon::ComplexityAnalysis& analysis) const {
    // Don't parallelize if complexity is too low
    if (analysis.complexity_category == "low") {
        return false;
    }
    
    // Don't parallelize if we have very few symbols
    if (analysis.symbols_count < 2) {
        return false;
    }
    
    // Use parallelization for medium+ complexity with multiple symbols
    return analysis.should_use_parallel && analysis.symbols_count >= 2;
}

std::map<std::string, std::string> StrategyAnalyzer::getOptimizationHints(const std::string& strategy) const {
    auto it = strategy_hints_.find(strategy);
    if (it != strategy_hints_.end()) {
        return it->second;
    }
    
    // Default hints for unknown strategies
    return {
        {"memory_usage", "medium"},
        {"cpu_intensive", "unknown"},
        {"io_bound", "unknown"}
    };
}

} // namespace TradingOrchestrator