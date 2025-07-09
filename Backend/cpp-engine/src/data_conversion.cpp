#include <iostream>
#include <sstream>

#include "data_conversion.h"

namespace DataConversion {

std::vector<PriceData> convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data) {
    std::vector<PriceData> tech_data;
    tech_data.reserve(db_data.size());
    
    for (const auto& row : db_data) {
        try {
            if (!validateDatabaseRow(row)) {
                continue;
            }
            
            PriceData data = convertRowToPriceData(row);
            tech_data.push_back(data);
            
        } catch (const std::exception& e) {
            std::cerr << "Error converting price data: " << e.what() << std::endl;
            continue;
        }
    }
    
    return tech_data;
}

PriceData convertRowToPriceData(const std::map<std::string, std::string>& row) {
    PriceData data;
    
    // Try different common field name variations
    data.date = getFieldValue(row, "time", getFieldValue(row, "date", ""));
    
    data.open = safeStringToDouble(getFieldValue(row, "open", getFieldValue(row, "open_price", "0")), "open");
    data.high = safeStringToDouble(getFieldValue(row, "high", getFieldValue(row, "high_price", "0")), "high");
    data.low = safeStringToDouble(getFieldValue(row, "low", getFieldValue(row, "low_price", "0")), "low");
    data.close = safeStringToDouble(getFieldValue(row, "close", getFieldValue(row, "close_price", "0")), "close");
    data.volume = safeStringToLong(getFieldValue(row, "volume", "0"), "volume");
    
    return data;
}

double safeStringToDouble(const std::string& str, const std::string& field_name) {
    if (str.empty()) {
        throw std::invalid_argument("Empty string for field: " + field_name);
    }
    
    try {
        size_t pos;
        double value = std::stod(str, &pos);
        
        // Check if entire string was consumed
        if (pos != str.length()) {
            throw std::invalid_argument("Invalid numeric format in field: " + field_name + ", value: " + str);
        }
        
        return value;
    } catch (const std::invalid_argument& e) {
        throw std::invalid_argument("Invalid double conversion for field: " + field_name + ", value: " + str);
    } catch (const std::out_of_range& e) {
        throw std::out_of_range("Out of range double conversion for field: " + field_name + ", value: " + str);
    }
}

long safeStringToLong(const std::string& str, const std::string& field_name) {
    if (str.empty()) {
        throw std::invalid_argument("Empty string for field: " + field_name);
    }
    
    try {
        size_t pos;
        long value = std::stol(str, &pos);
        
        // Check if entire string was consumed
        if (pos != str.length()) {
            throw std::invalid_argument("Invalid numeric format in field: " + field_name + ", value: " + str);
        }
        
        return value;
    } catch (const std::invalid_argument& e) {
        throw std::invalid_argument("Invalid long conversion for field: " + field_name + ", value: " + str);
    } catch (const std::out_of_range& e) {
        throw std::out_of_range("Out of range long conversion for field: " + field_name + ", value: " + str);
    }
}

bool validateDatabaseRow(const std::map<std::string, std::string>& row) {
    // Check for required fields with common variations
    bool has_date = row.find("time") != row.end() || row.find("date") != row.end();
    bool has_open = row.find("open") != row.end() || row.find("open_price") != row.end();
    bool has_high = row.find("high") != row.end() || row.find("high_price") != row.end();
    bool has_low = row.find("low") != row.end() || row.find("low_price") != row.end();
    bool has_close = row.find("close") != row.end() || row.find("close_price") != row.end();
    bool has_volume = row.find("volume") != row.end();
    
    return has_date && has_open && has_high && has_low && has_close && has_volume;
}

std::string getFieldValue(const std::map<std::string, std::string>& row, 
                         const std::string& field, 
                         const std::string& fallback) {
    auto it = row.find(field);
    return (it != row.end()) ? it->second : fallback;
}

} // namespace DataConversion