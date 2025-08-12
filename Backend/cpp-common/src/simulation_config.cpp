#include "simulation_config.h"
#include <sstream>
#include <iostream>
#include <ctime>
#include <chrono>

namespace TradingCommon {

// Helper function to parse date string (YYYY-MM-DD format)
int dateToDays(const std::string& date_str, const std::string& reference_date = "1970-01-01") {
    // Simple date difference calculation (placeholder implementation)
    // In a real implementation, you'd use proper date parsing library
    
    // Extract year, month, day from YYYY-MM-DD format
    int year = std::stoi(date_str.substr(0, 4));
    int month = std::stoi(date_str.substr(5, 2));
    int day = std::stoi(date_str.substr(8, 2));
    
    // Simple approximation: days since year 2000
    return (year - 2000) * 365 + month * 30 + day;
}

std::string SimulationConfig::toJson() const {
    std::stringstream ss;
    ss << "{";
    ss << "\"symbols\":[";
    for (size_t i = 0; i < symbols.size(); i++) {
        ss << "\"" << symbols[i] << "\"";
        if (i < symbols.size() - 1) ss << ",";
    }
    ss << "],";
    ss << "\"start_date\":\"" << start_date << "\",";
    ss << "\"end_date\":\"" << end_date << "\",";
    ss << "\"starting_capital\":" << starting_capital << ",";
    ss << "\"strategy\":\"" << strategy << "\",";
    ss << "\"strategy_parameters\":{";
    bool first = true;
    for (const auto& param : strategy_parameters) {
        if (!first) ss << ",";
        ss << "\"" << param.first << "\":\"" << param.second << "\"";
        first = false;
    }
    ss << "}";
    ss << "}";
    return ss.str();
}

SimulationConfig SimulationConfig::fromJson(const std::string& json) {
    // Simple JSON parsing (placeholder implementation)
    // In a real implementation, you'd use a proper JSON library
    SimulationConfig config;
    
    // For now, create a basic config with default values
    // TODO: Implement proper JSON parsing
    config.symbols = {"AAPL"};
    config.start_date = "2023-01-01";
    config.end_date = "2023-12-31";
    config.starting_capital = 10000.0;
    config.strategy = "ma_crossover";
    
    return config;
}

bool SimulationConfig::isValid() const {
    if (symbols.empty()) return false;
    if (starting_capital <= 0) return false;
    if (strategy.empty()) return false;
    if (start_date.empty() || end_date.empty()) return false;
    return true;
}

std::string SimulationConfig::getValidationError() const {
    if (symbols.empty()) return "No symbols specified";
    if (starting_capital <= 0) return "Invalid starting capital";
    if (strategy.empty()) return "No strategy specified";
    if (start_date.empty() || end_date.empty()) return "Invalid date range";
    return "Valid";
}

ComplexityAnalysis SimulationConfig::analyzeComplexity() const {
    ComplexityAnalysis analysis;
    
    analysis.symbols_count = symbols.size();
    
    // Calculate date range (simplified)
    int start_days = dateToDays(start_date);
    int end_days = dateToDays(end_date);
    analysis.date_range_days = end_days - start_days;
    
    // Base complexity calculation
    analysis.base_complexity = analysis.symbols_count * analysis.date_range_days;
    
    // Strategy complexity multiplier
    analysis.strategy_multiplier = 1.0;
    if (strategy == "rsi") {
        analysis.strategy_multiplier = 1.2;
    } else if (strategy == "bollinger_bands") {
        analysis.strategy_multiplier = 1.5;
    }
    
    // Market complexity multiplier
    analysis.market_complexity_multiplier = 1.0;
    if (analysis.date_range_days > 365) {
        analysis.market_complexity_multiplier = 1.2;
    }
    
    // Total complexity
    analysis.total_complexity = static_cast<int>(
        analysis.base_complexity * analysis.strategy_multiplier * analysis.market_complexity_multiplier
    );
    
    // Determine complexity category and parallelization strategy
    if (analysis.total_complexity < 5000) {
        analysis.complexity_category = "low";
        analysis.should_use_parallel = false;
        analysis.recommended_workers = 1;
    } else if (analysis.total_complexity < 25000) {
        analysis.complexity_category = "medium";
        analysis.should_use_parallel = true;
        analysis.recommended_workers = 2;
    } else if (analysis.total_complexity < 100000) {
        analysis.complexity_category = "high";
        analysis.should_use_parallel = true;
        analysis.recommended_workers = 4;
    } else {
        analysis.complexity_category = "extreme";
        analysis.should_use_parallel = true;
        analysis.recommended_workers = 8;
    }
    
    return analysis;
}

std::string ComplexityAnalysis::toJson() const {
    std::stringstream ss;
    ss << "{";
    ss << "\"symbols_count\":" << symbols_count << ",";
    ss << "\"date_range_days\":" << date_range_days << ",";
    ss << "\"base_complexity\":" << base_complexity << ",";
    ss << "\"strategy_multiplier\":" << strategy_multiplier << ",";
    ss << "\"market_complexity_multiplier\":" << market_complexity_multiplier << ",";
    ss << "\"total_complexity\":" << total_complexity << ",";
    ss << "\"complexity_category\":\"" << complexity_category << "\",";
    ss << "\"should_use_parallel\":" << (should_use_parallel ? "true" : "false") << ",";
    ss << "\"recommended_workers\":" << recommended_workers;
    ss << "}";
    return ss.str();
}

ComplexityAnalysis ComplexityAnalysis::fromJson(const std::string& json) {
    // Placeholder implementation
    ComplexityAnalysis analysis;
    analysis.complexity_category = "medium";
    analysis.should_use_parallel = true;
    analysis.recommended_workers = 2;
    return analysis;
}

std::string ExecutionPlan::toJson() const {
    std::stringstream ss;
    ss << "{";
    ss << "\"execution_mode\":\"" << execution_mode << "\",";
    ss << "\"max_workers\":" << max_workers << ",";
    ss << "\"symbol_groups\":[";
    for (size_t i = 0; i < symbol_groups.size(); i++) {
        ss << "[";
        for (size_t j = 0; j < symbol_groups[i].size(); j++) {
            ss << "\"" << symbol_groups[i][j] << "\"";
            if (j < symbol_groups[i].size() - 1) ss << ",";
        }
        ss << "]";
        if (i < symbol_groups.size() - 1) ss << ",";
    }
    ss << "],";
    ss << "\"complexity\":" << complexity.toJson();
    ss << "}";
    return ss.str();
}

ExecutionPlan ExecutionPlan::fromJson(const std::string& json) {
    // Placeholder implementation
    ExecutionPlan plan;
    plan.execution_mode = "parallel";
    plan.max_workers = 2;
    return plan;
}

} // namespace TradingCommon