#pragma once

#include <string>
#include <vector>

#include <nlohmann/json.hpp>

struct BacktestResult;
struct TradingSignal;
struct PriceData;

namespace JsonHelpers {
    
    // Convert BacktestResult to JSON with standardized format
    nlohmann::json backTestResultToJson(const BacktestResult& result);
    
    // Convert TradingSignal to JSON
    nlohmann::json tradingSignalToJson(const TradingSignal& signal);
    
    // Convert vector of TradingSignals to JSON array
    nlohmann::json tradingSignalsToJsonArray(const std::vector<TradingSignal>& signals);
    
    // Create equity curve JSON with dates
    nlohmann::json createEquityCurveJson(const std::vector<double>& equity_curve,
                                        const std::vector<PriceData>& price_data,
                                        const std::string& start_date);
    
    // Create performance metrics JSON object
    nlohmann::json createPerformanceMetricsJson(const BacktestResult& result);
    
    // Create progress JSON for real-time updates
    nlohmann::json createProgressJson(double progress_pct, 
                                     const std::string& current_date,
                                     double current_value,
                                     double current_price,
                                     int day,
                                     int total_days);
    
    // Safe JSON value extraction with defaults
    template<typename T>
    T getJsonValue(const nlohmann::json& json, const std::string& key, const T& default_value);
    
    // Validate required JSON fields
    bool validateJsonFields(const nlohmann::json& json, const std::vector<std::string>& required_fields);
}