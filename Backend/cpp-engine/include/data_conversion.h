#pragma once

#include "technical_indicators.h"
#include <vector>
#include <map>
#include <string>
#include <stdexcept>

namespace DataConversion {
    
    // Standard price data conversion from database format
    std::vector<PriceData> convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data);
    
    // Convert single database row to PriceData
    PriceData convertRowToPriceData(const std::map<std::string, std::string>& row);
    
    // Safe string to double conversion with error handling
    double safeStringToDouble(const std::string& str, const std::string& field_name = "");
    
    // Safe string to long conversion with error handling
    long safeStringToLong(const std::string& str, const std::string& field_name = "");
    
    // Validate required fields exist in database row
    bool validateDatabaseRow(const std::map<std::string, std::string>& row);
    
    // Get field value with fallback
    std::string getFieldValue(const std::map<std::string, std::string>& row, 
                             const std::string& field, 
                             const std::string& fallback = "");
}