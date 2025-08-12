#include "worker_result.h"
#include <sstream>

namespace TradingCommon {

std::string WorkerResult::toJson() const {
    std::stringstream ss;
    ss << "{";
    ss << "\"symbols\":[";
    for (size_t i = 0; i < symbols.size(); i++) {
        ss << "\"" << symbols[i] << "\"";
        if (i < symbols.size() - 1) ss << ",";
    }
    ss << "],";
    ss << "\"return_code\":" << return_code << ",";
    ss << "\"stdout_data\":\"" << stdout_data << "\",";
    ss << "\"stderr_data\":\"" << stderr_data << "\",";
    ss << "\"execution_time_ms\":" << execution_time_ms;
    ss << "}";
    return ss.str();
}

WorkerResult WorkerResult::fromJson(const std::string& json) {
    // Placeholder implementation
    // In a real implementation, you'd parse the JSON properly
    WorkerResult result;
    result.return_code = 0;
    result.execution_time_ms = 0.0;
    return result;
}

bool WorkerResult::isSuccess() const {
    return return_code == 0;
}

bool WorkerResult::hasErrors() const {
    return return_code != 0 || !stderr_data.empty();
}

std::string WorkerResult::getErrorMessage() const {
    if (return_code != 0) {
        return "Process failed with exit code " + std::to_string(return_code) + 
               (stderr_data.empty() ? "" : ": " + stderr_data);
    }
    if (!stderr_data.empty()) {
        return stderr_data;
    }
    return "No errors";
}

} // namespace TradingCommon