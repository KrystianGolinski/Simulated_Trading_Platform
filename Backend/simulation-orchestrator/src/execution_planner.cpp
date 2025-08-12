#include "execution_planner.h"
#include <algorithm>
#include <cmath>
#include <iostream>

namespace TradingOrchestrator {

ExecutionPlanner::ExecutionPlanner() {
}

TradingCommon::ExecutionPlan ExecutionPlanner::createExecutionPlan(const TradingCommon::SimulationConfig& config) {
    TradingCommon::ExecutionPlan plan;
    
    // Analyze complexity
    plan.complexity = config.analyzeComplexity();
    
    std::cout << "Complexity Analysis:" << std::endl;
    std::cout << "  Category: " << plan.complexity.complexity_category << std::endl;
    std::cout << "  Total Complexity: " << plan.complexity.total_complexity << std::endl;
    std::cout << "  Should Use Parallel: " << (plan.complexity.should_use_parallel ? "Yes" : "No") << std::endl;
    
    // Determine execution mode
    bool should_parallelize = strategy_analyzer_.shouldUseParallelExecution(plan.complexity);
    
    if (should_parallelize) {
        plan.execution_mode = "parallel";
        plan.max_workers = strategy_analyzer_.getRecommendedWorkerCount(plan.complexity);
        
        // Group symbols for parallel execution
        plan.symbol_groups = groupSymbols(config.symbols, plan.max_workers);
        
        // Create worker configurations
        plan.worker_configs = createWorkerConfigs(config, plan.symbol_groups);
        
        std::cout << "Execution Plan: Parallel with " << plan.max_workers << " workers" << std::endl;
        std::cout << "Symbol groups created: " << plan.symbol_groups.size() << std::endl;
        for (size_t i = 0; i < plan.symbol_groups.size(); i++) {
            std::cout << "  Group " << i << ": ";
            for (const auto& symbol : plan.symbol_groups[i]) {
                std::cout << symbol << " ";
            }
            std::cout << std::endl;
        }
        
    } else {
        plan.execution_mode = "sequential";
        plan.max_workers = 1;
        
        // Single group with all symbols
        plan.symbol_groups = {config.symbols};
        plan.worker_configs = {config};
        
        std::cout << "Execution Plan: Sequential (single worker)" << std::endl;
    }
    
    return plan;
}

std::vector<std::vector<std::string>> ExecutionPlanner::groupSymbols(
    const std::vector<std::string>& symbols, 
    int target_groups) const {
    
    if (target_groups <= 1 || symbols.size() <= 1) {
        return {symbols};
    }
    
    // Use balanced grouping algorithm
    return groupSymbolsBalanced(symbols, target_groups);
}

std::vector<std::vector<std::string>> ExecutionPlanner::groupSymbolsBalanced(
    const std::vector<std::string>& symbols, 
    int target_groups) const {
    
    std::vector<std::vector<std::string>> groups(target_groups);
    
    // Distribute symbols as evenly as possible
    for (size_t i = 0; i < symbols.size(); i++) {
        int group_index = i % target_groups;
        groups[group_index].push_back(symbols[i]);
    }
    
    // Remove empty groups
    groups.erase(
        std::remove_if(groups.begin(), groups.end(),
            [](const std::vector<std::string>& group) { return group.empty(); }),
        groups.end()
    );
    
    return groups;
}

std::vector<std::vector<std::string>> ExecutionPlanner::groupSymbolsRoundRobin(
    const std::vector<std::string>& symbols, 
    int target_groups) const {
    
    // Same as balanced for now - could implement more sophisticated algorithms later
    return groupSymbolsBalanced(symbols, target_groups);
}

std::vector<TradingCommon::SimulationConfig> ExecutionPlanner::createWorkerConfigs(
    const TradingCommon::SimulationConfig& base_config,
    const std::vector<std::vector<std::string>>& symbol_groups) const {
    
    std::vector<TradingCommon::SimulationConfig> worker_configs;
    worker_configs.reserve(symbol_groups.size());
    
    for (const auto& group : symbol_groups) {
        TradingCommon::SimulationConfig worker_config = base_config;
        worker_config.symbols = group;
        worker_configs.push_back(worker_config);
    }
    
    return worker_configs;
}

double ExecutionPlanner::estimateExecutionTime(const TradingCommon::ExecutionPlan& plan) const {
    // Simple estimation based on complexity and parallelization
    double base_time = plan.complexity.total_complexity / 1000.0; // Convert to seconds
    
    if (plan.execution_mode == "parallel") {
        // Apply Amdahl's Law approximation
        double parallel_fraction = 0.8; // Assume 80% can be parallelized
        double serial_fraction = 1.0 - parallel_fraction;
        
        double speedup = 1.0 / (serial_fraction + parallel_fraction / plan.max_workers);
        return base_time / speedup;
    } else {
        return base_time;
    }
}

} // namespace TradingOrchestrator