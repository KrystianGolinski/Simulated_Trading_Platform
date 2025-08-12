#pragma once

#include <string>
#include <vector>
#include <map>

namespace TradingCommon {
    
    // Forward declarations
    struct ComplexityAnalysis;
    struct ExecutionPlan;
    
    struct SimulationConfig {
        std::vector<std::string> symbols;
        std::string start_date;
        std::string end_date;
        double starting_capital;
        std::string strategy;
        std::map<std::string, std::string> strategy_parameters;
        
        // Serialization methods
        std::string toJson() const;
        static SimulationConfig fromJson(const std::string& json);
        
        // Validation methods
        bool isValid() const;
        std::string getValidationError() const;
        
        // Complexity analysis
        ComplexityAnalysis analyzeComplexity() const;
    };
    
    struct ComplexityAnalysis {
        int symbols_count;
        int date_range_days;
        int base_complexity;
        double strategy_multiplier;
        double market_complexity_multiplier;
        int total_complexity;
        std::string complexity_category;
        bool should_use_parallel;
        int recommended_workers;
        
        std::string toJson() const;
        static ComplexityAnalysis fromJson(const std::string& json);
    };
    
    struct ExecutionPlan {
        std::string execution_mode; // "sequential" or "parallel"
        int max_workers;
        std::vector<std::vector<std::string>> symbol_groups;
        std::vector<SimulationConfig> worker_configs;
        ComplexityAnalysis complexity;
        
        std::string toJson() const;
        static ExecutionPlan fromJson(const std::string& json);
    };
    
} // namespace TradingCommon