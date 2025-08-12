#include <iostream>
#include <sstream>

#include "error_utils.h"
#include "logger.h"

namespace ErrorUtils {
    
    // Log error information
    void logError(const ErrorInfo& error, const std::string& context) {
        std::string log_message = "Error";
        if (!context.empty()) {
            log_message += " in " + context;
        }
        log_message += ": [" + errorCodeToString(error.code) + "] " + error.message;
        
        if (!error.details.empty()) {
            log_message += " | Details: " + error.details;
        }
        
        // Use existing logger if available, otherwise fallback to cout
        try {
            Logger::log(LogLevel::ERROR, log_message);
        } catch (...) {
            std::cout << log_message << std::endl;
        }
    }
    
    void logError(const Result<void>& result, const std::string& context) {
        if (result.isError()) {
            logError(result.getError(), context);
        }
    }
    
    // Format error for display
    std::string formatError(const ErrorInfo& error) {
        std::ostringstream oss;
        oss << "[" << errorCodeToString(error.code) << "] " << error.message;
        
        if (!error.details.empty()) {
            oss << " (Details: " << error.details << ")";
        }
        
        return oss.str();
    }
    
    std::string formatError(const Result<void>& result) {
        if (result.isError()) {
            return formatError(result.getError());
        }
        return "No error";
    }
    
}