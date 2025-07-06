#include "date_time_utils.h"
#include <sstream>
#include <iomanip>
#include <chrono>
#include <ctime>
#include <stdexcept>

namespace DateTimeUtils {

std::string getCurrentDate() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d");
    return ss.str();
}

bool isValidDateFormat(const std::string& date) {
    if (date.length() != 10) return false;
    if (date[4] != '-' || date[7] != '-') return false;
    
    try {
        int year = std::stoi(date.substr(0, 4));
        int month = std::stoi(date.substr(5, 2));
        int day = std::stoi(date.substr(8, 2));
        
        return (year >= 1900 && year <= 2100 && 
                month >= 1 && month <= 12 && 
                day >= 1 && day <= 31);
    } catch (const std::exception&) {
        return false;
    }
}

std::string formatDate(const std::string& date) {
    if (isValidDateFormat(date)) {
        return date;
    }
    return getCurrentDate();
}

std::chrono::system_clock::time_point stringToTimePoint(const std::string& date) {
    std::tm tm = {};
    std::stringstream ss(date);
    ss >> std::get_time(&tm, "%Y-%m-%d");
    
    if (ss.fail()) {
        throw std::invalid_argument("Invalid date format: " + date);
    }
    
    auto time_t = std::mktime(&tm);
    return std::chrono::system_clock::from_time_t(time_t);
}

std::string timePointToString(const std::chrono::system_clock::time_point& time_point) {
    auto time_t = std::chrono::system_clock::to_time_t(time_point);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d");
    return ss.str();
}

} // namespace DateTimeUtils