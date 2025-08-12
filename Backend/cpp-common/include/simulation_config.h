#pragma once

#include <string>
#include <vector>
#include <nlohmann/json.hpp>

namespace TradingCommon {
    
    struct SimulationConfig {
        std::vector<std::string> symbols;
        std::string start_date;
        std::string end_date;
        double starting_capital;
        std::string strategy;
        nlohmann::json strategy_parameters;
        
        // Serialization methods
        std::string toJson() const;
        static SimulationConfig fromJson(const std::string& json);
        
        // Validation methods
        bool isValid() const;
        std::string getValidationError() const;
    };
    
} // namespace TradingCommon