#pragma once

#include <optional>
#include <stdexcept>
#include <string>
#include <variant>

// Error code categories for structured error handling
enum class ErrorCode {
    // Database related errors
    DATABASE_CONNECTION_FAILED,
    DATABASE_QUERY_FAILED,
    DATABASE_TRANSACTION_FAILED,
    DATABASE_CONSTRAINT_VIOLATION,
    
    // Data validation errors
    VALIDATION_INVALID_INPUT,
    VALIDATION_MISSING_REQUIRED_FIELD,
    VALIDATION_OUT_OF_RANGE,
    VALIDATION_INVALID_FORMAT,
    
    // Market data errors
    DATA_SYMBOL_NOT_FOUND,
    DATA_INSUFFICIENT_HISTORY,
    DATA_INVALID_DATE_RANGE,
    DATA_PARSING_FAILED,
    
    // Network/Connection errors
    NETWORK_CONNECTION_TIMEOUT,
    NETWORK_REQUEST_FAILED,
    NETWORK_AUTHENTICATION_FAILED,
    
    // Trading/Execution errors
    EXECUTION_INSUFFICIENT_FUNDS,
    EXECUTION_INVALID_SIGNAL,
    EXECUTION_INVALID_SIGNAL_TYPE,
    EXECUTION_INVALID_SYMBOL,
    EXECUTION_INVALID_PRICE,
    EXECUTION_INVALID_DATE,
    EXECUTION_HOLD_SIGNAL,
    EXECUTION_NO_POSITION,
    EXECUTION_ORDER_FAILED,
    EXECUTION_POSITION_LIMIT_EXCEEDED,
    EXECUTION_MARKET_CLOSED,
    
    // Technical Analysis errors
    TECHNICAL_ANALYSIS_INVALID_PERIOD,
    TECHNICAL_ANALYSIS_INVALID_PARAMETER,
    TECHNICAL_ANALYSIS_INSUFFICIENT_DATA,
    
    // Progress reporting errors
    PROGRESS_INVALID_SYMBOL,
    PROGRESS_INVALID_DATE,
    PROGRESS_INVALID_TOTAL_STEPS,
    PROGRESS_INVALID_CURRENT_STEP,
    PROGRESS_INVALID_CAPITAL,
    PROGRESS_INVALID_VALUE,
    PROGRESS_INVALID_TRADES,
    PROGRESS_INVALID_INTERVAL,
    
    // Trading Engine errors
    ENGINE_NO_STRATEGY_CONFIGURED,
    ENGINE_INVALID_SYMBOL,
    ENGINE_INVALID_CAPITAL,
    ENGINE_INVALID_DATE_RANGE,
    ENGINE_NO_DATA_AVAILABLE,
    ENGINE_SIMULATION_FAILED,
    ENGINE_BACKTEST_FAILED,
    ENGINE_MULTI_SYMBOL_FAILED,
    ENGINE_PORTFOLIO_ACCESS_FAILED,
    ENGINE_RESULTS_GENERATION_FAILED,
    
    // System/General errors
    SYSTEM_MEMORY_ALLOCATION_FAILED,
    SYSTEM_FILE_ACCESS_DENIED,
    SYSTEM_CONFIGURATION_ERROR,
    SYSTEM_UNEXPECTED_ERROR,
    
    // Success indicator
    SUCCESS
};

// Error information structure
struct ErrorInfo {
    ErrorCode code;
    std::string message;
    std::string details;
    
    ErrorInfo(ErrorCode error_code, const std::string& error_message, const std::string& error_details = "")
        : code(error_code), message(error_message), details(error_details) {}
};

// Result<T> template class for unified error handling
template<typename T>
class Result {
private:
    std::variant<T, ErrorInfo> data_;
    
public:
    // Success constructor
    explicit Result(T&& value) : data_(std::move(value)) {}
    explicit Result(const T& value) : data_(value) {}
    
    // Error constructor
    explicit Result(ErrorInfo&& error) : data_(std::move(error)) {}
    explicit Result(const ErrorInfo& error) : data_(error) {}
    
    // Convenience error constructor
    Result(ErrorCode code, const std::string& message, const std::string& details = "")
        : data_(ErrorInfo(code, message, details)) {}
    
    // Check if result contains success value
    bool isSuccess() const {
        return std::holds_alternative<T>(data_);
    }
    
    // Check if result contains error
    bool isError() const {
        return std::holds_alternative<ErrorInfo>(data_);
    }
    
    // Get success value (throws if error)
    const T& getValue() const {
        if (isError()) {
            throw std::runtime_error("Attempted to get value from error result: " + getError().message);
        }
        return std::get<T>(data_);
    }
    
    // Get success value (throws if error)
    T& getValue() {
        if (isError()) {
            throw std::runtime_error("Attempted to get value from error result: " + getError().message);
        }
        return std::get<T>(data_);
    }
    
    // Get error information (throws if success)
    const ErrorInfo& getError() const {
        if (isSuccess()) {
            throw std::runtime_error("Attempted to get error from success result");
        }
        return std::get<ErrorInfo>(data_);
    }
    
    // Get error code (returns SUCCESS if no error)
    ErrorCode getErrorCode() const {
        return isError() ? getError().code : ErrorCode::SUCCESS;
    }
    
    // Get error message (returns empty string if no error)
    std::string getErrorMessage() const {
        return isError() ? getError().message : "";
    }
    
    // Get error details (returns empty string if no error)
    std::string getErrorDetails() const {
        return isError() ? getError().details : "";
    }
    
    // Safe value access with default
    template<typename U = T>
    T getValueOr(U&& default_value) const {
        return isSuccess() ? getValue() : T(std::forward<U>(default_value));
    }
    
    // Transform success value (returns error if current result is error)
    template<typename F>
    auto map(F&& func) -> Result<decltype(func(std::declval<T>()))> {
        using ReturnType = decltype(func(std::declval<T>()));
        
        if (isError()) {
            return Result<ReturnType>(getError());
        }
        
        try {
            return Result<ReturnType>(func(getValue()));
        } catch (const std::exception& e) {
            return Result<ReturnType>(ErrorCode::SYSTEM_UNEXPECTED_ERROR, 
                                    "Exception in map transformation", e.what());
        }
    }
    
    // Chain operations (monadic bind)
    template<typename F>
    auto flatMap(F&& func) -> decltype(func(std::declval<T>())) {
        using ReturnType = decltype(func(std::declval<T>()));
        
        if (isError()) {
            return ReturnType(getError());
        }
        
        try {
            return func(getValue());
        } catch (const std::exception& e) {
            return ReturnType(ErrorCode::SYSTEM_UNEXPECTED_ERROR, 
                            "Exception in flatMap operation", e.what());
        }
    }
};

// Specialization for void results
template<>
class Result<void> {
private:
    std::optional<ErrorInfo> error_;
    
public:
    // Success constructor
    Result() : error_(std::nullopt) {}
    
    // Error constructor
    explicit Result(ErrorInfo&& error) : error_(std::move(error)) {}
    explicit Result(const ErrorInfo& error) : error_(error) {}
    
    // Convenience error constructor
    Result(ErrorCode code, const std::string& message, const std::string& details = "")
        : error_(ErrorInfo(code, message, details)) {}
    
    // Check if result is success
    bool isSuccess() const {
        return !error_.has_value();
    }
    
    // Check if result contains error
    bool isError() const {
        return error_.has_value();
    }
    
    // Get error information (throws if success)
    const ErrorInfo& getError() const {
        if (isSuccess()) {
            throw std::runtime_error("Attempted to get error from success result");
        }
        return error_.value();
    }
    
    // Get error code (returns SUCCESS if no error)
    ErrorCode getErrorCode() const {
        return isError() ? getError().code : ErrorCode::SUCCESS;
    }
    
    // Get error message (returns empty string if no error)
    std::string getErrorMessage() const {
        return isError() ? getError().message : "";
    }
    
    // Get error details (returns empty string if no error)
    std::string getErrorDetails() const {
        return isError() ? getError().details : "";
    }
    
    // Chain operations for void results
    template<typename F>
    auto flatMap(F&& func) -> decltype(func()) {
        using ReturnType = decltype(func());
        
        if (isError()) {
            return ReturnType(getError());
        }
        
        try {
            return func();
        } catch (const std::exception& e) {
            return ReturnType(ErrorCode::SYSTEM_UNEXPECTED_ERROR, 
                            "Exception in flatMap operation", e.what());
        }
    }
};

// Helper functions for creating results
template<typename T>
Result<T> makeSuccess(T&& value) {
    return Result<T>(std::forward<T>(value));
}

template<typename T>
Result<T> makeSuccess(const T& value) {
    return Result<T>(value);
}

inline Result<void> makeSuccess() {
    return Result<void>();
}

template<typename T>
Result<T> makeError(ErrorCode code, const std::string& message, const std::string& details = "") {
    return Result<T>(code, message, details);
}

template<typename T>
Result<T> makeError(const ErrorInfo& error) {
    return Result<T>(error);
}

inline Result<void> makeErrorVoid(ErrorCode code, const std::string& message, const std::string& details = "") {
    return Result<void>(code, message, details);
}

// Utility function to convert ErrorCode to string
std::string errorCodeToString(ErrorCode code);

