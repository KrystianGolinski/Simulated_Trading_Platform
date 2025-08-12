#pragma once

#include <string>
#include <vector>
#include <nlohmann/json.hpp>

namespace TradingCommon {
    
    struct WorkerResult {
        std::vector<std::string> symbols;
        int return_code;
        std::string stdout_data;
        std::string stderr_data;
        nlohmann::json result_data;
        double execution_time_ms;
        
        // Serialization methods
        std::string toJson() const;
        static WorkerResult fromJson(const std::string& json);
        
        // Status checks
        bool isSuccess() const;
        bool hasErrors() const;
        std::string getErrorMessage() const;
    };
    
} // namespace TradingCommon