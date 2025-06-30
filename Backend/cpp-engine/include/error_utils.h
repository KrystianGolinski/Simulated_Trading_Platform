#pragma once

#include <functional>
#include <exception>
#include <string>
#include "result.h"
#include "trading_exceptions.h"

// Namespace for error handling utilities
namespace ErrorUtils {

    // Convert exception to Result<T>
    template<typename T>
    Result<T> fromException(const std::exception& e) {
        // Try to cast to TradingException first for structured error info
        if (const auto* trading_ex = dynamic_cast<const TradingException*>(&e)) {
            return Result<T>(trading_ex->toErrorInfo());
        }
        
        // Handle standard exceptions
        if (const auto* invalid_arg = dynamic_cast<const std::invalid_argument*>(&e)) {
            return Result<T>(ErrorCode::VALIDATION_INVALID_INPUT, invalid_arg->what());
        }
        
        if (const auto* out_of_range = dynamic_cast<const std::out_of_range*>(&e)) {
            return Result<T>(ErrorCode::VALIDATION_OUT_OF_RANGE, out_of_range->what());
        }
        
        if (const auto* runtime_error = dynamic_cast<const std::runtime_error*>(&e)) {
            return Result<T>(ErrorCode::SYSTEM_UNEXPECTED_ERROR, runtime_error->what());
        }
        
        if (const auto* bad_alloc = dynamic_cast<const std::bad_alloc*>(&e)) {
            return Result<T>(ErrorCode::SYSTEM_MEMORY_ALLOCATION_FAILED, "Memory allocation failed");
        }
        
        // Generic exception fallback
        return Result<T>(ErrorCode::SYSTEM_UNEXPECTED_ERROR, e.what());
    }
    
    // Convert exception to Result<void>
    inline Result<void> fromExceptionVoid(const std::exception& e) {
        // Try to cast to TradingException first for structured error info
        if (const auto* trading_ex = dynamic_cast<const TradingException*>(&e)) {
            return Result<void>(trading_ex->toErrorInfo());
        }
        
        // Handle standard exceptions
        if (const auto* invalid_arg = dynamic_cast<const std::invalid_argument*>(&e)) {
            return Result<void>(ErrorCode::VALIDATION_INVALID_INPUT, invalid_arg->what());
        }
        
        if (const auto* out_of_range = dynamic_cast<const std::out_of_range*>(&e)) {
            return Result<void>(ErrorCode::VALIDATION_OUT_OF_RANGE, out_of_range->what());
        }
        
        if (const auto* runtime_error = dynamic_cast<const std::runtime_error*>(&e)) {
            return Result<void>(ErrorCode::SYSTEM_UNEXPECTED_ERROR, runtime_error->what());
        }
        
        if (const auto* bad_alloc = dynamic_cast<const std::bad_alloc*>(&e)) {
            return Result<void>(ErrorCode::SYSTEM_MEMORY_ALLOCATION_FAILED, "Memory allocation failed");
        }
        
        // Generic exception fallback
        return Result<void>(ErrorCode::SYSTEM_UNEXPECTED_ERROR, e.what());
    }
    
    // Execute function and convert any exceptions to Result<T>
    template<typename F>
    auto safeExecute(F&& func) -> Result<decltype(func())> {
        using ReturnType = decltype(func());
        
        try {
            if constexpr (std::is_void_v<ReturnType>) {
                func();
                return Result<void>();
            } else {
                return Result<ReturnType>(func());
            }
        } catch (const std::exception& e) {
            if constexpr (std::is_void_v<ReturnType>) {
                return fromExceptionVoid(e);
            } else {
                return fromException<ReturnType>(e);
            }
        }
    }
    
    // Convert Result<T> to exception (throws if error)
    template<typename T>
    void throwIfError(const Result<T>& result) {
        if (result.isError()) {
            const auto& error = result.getError();
            
            // Create appropriate exception based on error code
            switch (error.code) {
                case ErrorCode::DATABASE_CONNECTION_FAILED:
                    throw DatabaseConnectionException(error.message, error.details);
                case ErrorCode::DATABASE_QUERY_FAILED:
                    throw DatabaseQueryException(error.message, error.details);
                case ErrorCode::DATABASE_TRANSACTION_FAILED:
                    throw DatabaseTransactionException(error.message, error.details);
                case ErrorCode::DATABASE_CONSTRAINT_VIOLATION:
                    throw DatabaseConstraintException(error.message, error.details);
                    
                case ErrorCode::VALIDATION_INVALID_INPUT:
                    throw InvalidInputException(error.message, error.details);
                case ErrorCode::VALIDATION_MISSING_REQUIRED_FIELD:
                    throw MissingRequiredFieldException(error.message, error.details);
                case ErrorCode::VALIDATION_OUT_OF_RANGE:
                    throw OutOfRangeException(error.message, error.details);
                case ErrorCode::VALIDATION_INVALID_FORMAT:
                    throw InvalidFormatException(error.message, error.details);
                    
                case ErrorCode::DATA_SYMBOL_NOT_FOUND:
                    throw SymbolNotFoundException::fromMessage(error.message, error.details);
                case ErrorCode::DATA_INSUFFICIENT_HISTORY:
                    throw InsufficientHistoryException(error.message, error.details);
                case ErrorCode::DATA_INVALID_DATE_RANGE:
                    throw InvalidDateRangeException(error.message, error.details);
                case ErrorCode::DATA_PARSING_FAILED:
                    throw DataParsingException(error.message, error.details);
                    
                case ErrorCode::NETWORK_CONNECTION_TIMEOUT:
                    throw ConnectionTimeoutException(error.message, error.details);
                case ErrorCode::NETWORK_REQUEST_FAILED:
                    throw RequestFailedException(error.message, error.details);
                case ErrorCode::NETWORK_AUTHENTICATION_FAILED:
                    throw AuthenticationFailedException(error.message, error.details);
                    
                case ErrorCode::EXECUTION_INSUFFICIENT_FUNDS:
                    throw InsufficientFundsException(error.message, error.details);
                case ErrorCode::EXECUTION_INVALID_SIGNAL:
                    throw InvalidSignalException(error.message, error.details);
                case ErrorCode::EXECUTION_POSITION_LIMIT_EXCEEDED:
                    throw PositionLimitExceededException(error.message, error.details);
                case ErrorCode::EXECUTION_MARKET_CLOSED:
                    throw MarketClosedException(error.message, error.details);
                    
                case ErrorCode::SYSTEM_MEMORY_ALLOCATION_FAILED:
                    throw MemoryAllocationException(error.message, error.details);
                case ErrorCode::SYSTEM_FILE_ACCESS_DENIED:
                    throw FileAccessException(error.message, error.details);
                case ErrorCode::SYSTEM_CONFIGURATION_ERROR:
                    throw ConfigurationException(error.message, error.details);
                case ErrorCode::SYSTEM_UNEXPECTED_ERROR:
                    throw UnexpectedException(error.message, error.details);
                    
                default:
                    throw UnexpectedException(error.message, error.details);
            }
        }
    }
    
    // Log error information (basic implementation)
    void logError(const ErrorInfo& error, const std::string& context = "");
    void logError(const Result<void>& result, const std::string& context = "");
    
    template<typename T>
    void logError(const Result<T>& result, const std::string& context = "") {
        if (result.isError()) {
            logError(result.getError(), context);
        }
    }
    
    // Format error for display
    std::string formatError(const ErrorInfo& error);
    std::string formatError(const Result<void>& result);
    
    template<typename T>
    std::string formatError(const Result<T>& result) {
        return result.isError() ? formatError(result.getError()) : "No error";
    }
    
    // Create error from legacy error patterns
    template<typename T>
    Result<T> fromLegacyBool(bool success, const std::string& error_message = "Operation failed", 
                            ErrorCode error_code = ErrorCode::SYSTEM_UNEXPECTED_ERROR) {
        if (success) {
            // Note: This requires a default-constructible T
            return Result<T>(T{});
        } else {
            return Result<T>(error_code, error_message);
        }
    }
    
    inline Result<void> fromLegacyBoolVoid(bool success, const std::string& error_message = "Operation failed", 
                                          ErrorCode error_code = ErrorCode::SYSTEM_UNEXPECTED_ERROR) {
        if (success) {
            return Result<void>();
        } else {
            return Result<void>(error_code, error_message);
        }
    }
    
    // Chain multiple Result operations
    template<typename T, typename F>
    auto chain(const Result<T>& result, F&& func) -> decltype(func(result.getValue())) {
        if (result.isError()) {
            using ReturnType = decltype(func(result.getValue()));
            return ReturnType(result.getError());
        }
        
        return func(result.getValue());
    }
    
    // Specialization for Result<void> chaining
    template<typename F>
    auto chain(const Result<void>& result, F&& func) -> decltype(func()) {
        if (result.isError()) {
            using ReturnType = decltype(func());
            return ReturnType(result.getError());
        }
        
        return func();
    }
    
    // Combine multiple Results (all must succeed)
    template<typename T>
    Result<std::vector<T>> combineResults(const std::vector<Result<T>>& results) {
        std::vector<T> values;
        values.reserve(results.size());
        
        for (const auto& result : results) {
            if (result.isError()) {
                return Result<std::vector<T>>(result.getError());
            }
            values.push_back(result.getValue());
        }
        
        return Result<std::vector<T>>(std::move(values));
    }
}

// Convenience macros for error handling
#define TRY_RESULT(expr) \
    do { \
        auto result = (expr); \
        if (result.isError()) { \
            return decltype(result)(result.getError()); \
        } \
    } while(0)

#define TRY_RESULT_VALUE(var, expr) \
    auto var##_result = (expr); \
    if (var##_result.isError()) { \
        return decltype(var##_result)(var##_result.getError()); \
    } \
    auto var = var##_result.getValue()

#define SAFE_EXECUTE(expr) ErrorUtils::safeExecute([&]() { return (expr); })