#pragma once

#include <stdexcept>
#include <string>

#include "result.h"

// Base exception class for all trading system exceptions
class TradingException : public std::exception {
protected:
    ErrorCode error_code_;
    std::string message_;
    std::string details_;

public:
    TradingException(ErrorCode code, const std::string& message, const std::string& details = "")
        : error_code_(code), message_(message), details_(details) {}

    const char* what() const noexcept override {
        return message_.c_str();
    }

    ErrorCode getErrorCode() const noexcept {
        return error_code_;
    }

    const std::string& getMessage() const noexcept {
        return message_;
    }

    const std::string& getDetails() const noexcept {
        return details_;
    }

    // Convert to ErrorInfo for Result<T> compatibility
    ErrorInfo toErrorInfo() const {
        return ErrorInfo(error_code_, message_, details_);
    }
};

// Database-related exceptions
class DatabaseException : public TradingException {
public:
    DatabaseException(ErrorCode code, const std::string& message, const std::string& details = "")
        : TradingException(code, message, details) {}
};

class DatabaseConnectionException : public DatabaseException {
public:
    DatabaseConnectionException(const std::string& message, const std::string& details = "")
        : DatabaseException(ErrorCode::DATABASE_CONNECTION_FAILED, message, details) {}
};

class DatabaseQueryException : public DatabaseException {
public:
    DatabaseQueryException(const std::string& message, const std::string& details = "")
        : DatabaseException(ErrorCode::DATABASE_QUERY_FAILED, message, details) {}
};

class DatabaseTransactionException : public DatabaseException {
public:
    DatabaseTransactionException(const std::string& message, const std::string& details = "")
        : DatabaseException(ErrorCode::DATABASE_TRANSACTION_FAILED, message, details) {}
};

class DatabaseConstraintException : public DatabaseException {
public:
    DatabaseConstraintException(const std::string& message, const std::string& details = "")
        : DatabaseException(ErrorCode::DATABASE_CONSTRAINT_VIOLATION, message, details) {}
};

// Validation-related exceptions
class ValidationException : public TradingException {
public:
    ValidationException(ErrorCode code, const std::string& message, const std::string& details = "")
        : TradingException(code, message, details) {}
};

class InvalidInputException : public ValidationException {
public:
    InvalidInputException(const std::string& message, const std::string& details = "")
        : ValidationException(ErrorCode::VALIDATION_INVALID_INPUT, message, details) {}
};

class MissingRequiredFieldException : public ValidationException {
public:
    MissingRequiredFieldException(const std::string& field_name, const std::string& details = "")
        : ValidationException(ErrorCode::VALIDATION_MISSING_REQUIRED_FIELD, 
                            "Missing required field: " + field_name, details) {}
};

class OutOfRangeException : public ValidationException {
public:
    OutOfRangeException(const std::string& message, const std::string& details = "")
        : ValidationException(ErrorCode::VALIDATION_OUT_OF_RANGE, message, details) {}
};

class InvalidFormatException : public ValidationException {
public:
    InvalidFormatException(const std::string& message, const std::string& details = "")
        : ValidationException(ErrorCode::VALIDATION_INVALID_FORMAT, message, details) {}
};

// Data-related exceptions
class DataException : public TradingException {
public:
    DataException(ErrorCode code, const std::string& message, const std::string& details = "")
        : TradingException(code, message, details) {}
};

class SymbolNotFoundException : public DataException {
public:
    // Constructor for use with symbol only (prepends "Symbol not found: ")
    SymbolNotFoundException(const std::string& symbol, const std::string& details = "")
        : DataException(ErrorCode::DATA_SYMBOL_NOT_FOUND, 
                       "Symbol not found: " + symbol, details) {}
    
    // Constructor for use with full message (for throwIfError compatibility)
    static SymbolNotFoundException fromMessage(const std::string& message, const std::string& details = "") {
        return SymbolNotFoundException("", details, message);
    }

private:
    // Private constructor for fromMessage
    SymbolNotFoundException(const std::string&, const std::string& details, const std::string& full_message)
        : DataException(ErrorCode::DATA_SYMBOL_NOT_FOUND, full_message, details) {}
};

class InsufficientHistoryException : public DataException {
public:
    InsufficientHistoryException(const std::string& message, const std::string& details = "")
        : DataException(ErrorCode::DATA_INSUFFICIENT_HISTORY, message, details) {}
};

class InvalidDateRangeException : public DataException {
public:
    InvalidDateRangeException(const std::string& message, const std::string& details = "")
        : DataException(ErrorCode::DATA_INVALID_DATE_RANGE, message, details) {}
};

class DataParsingException : public DataException {
public:
    DataParsingException(const std::string& message, const std::string& details = "")
        : DataException(ErrorCode::DATA_PARSING_FAILED, message, details) {}
};

// Network-related exceptions
class NetworkException : public TradingException {
public:
    NetworkException(ErrorCode code, const std::string& message, const std::string& details = "")
        : TradingException(code, message, details) {}
};

class ConnectionTimeoutException : public NetworkException {
public:
    ConnectionTimeoutException(const std::string& message, const std::string& details = "")
        : NetworkException(ErrorCode::NETWORK_CONNECTION_TIMEOUT, message, details) {}
};

class RequestFailedException : public NetworkException {
public:
    RequestFailedException(const std::string& message, const std::string& details = "")
        : NetworkException(ErrorCode::NETWORK_REQUEST_FAILED, message, details) {}
};

class AuthenticationFailedException : public NetworkException {
public:
    AuthenticationFailedException(const std::string& message, const std::string& details = "")
        : NetworkException(ErrorCode::NETWORK_AUTHENTICATION_FAILED, message, details) {}
};

// Execution-related exceptions
class ExecutionException : public TradingException {
public:
    ExecutionException(ErrorCode code, const std::string& message, const std::string& details = "")
        : TradingException(code, message, details) {}
};

class InsufficientFundsException : public ExecutionException {
public:
    InsufficientFundsException(const std::string& message, const std::string& details = "")
        : ExecutionException(ErrorCode::EXECUTION_INSUFFICIENT_FUNDS, message, details) {}
};

class InvalidSignalException : public ExecutionException {
public:
    InvalidSignalException(const std::string& message, const std::string& details = "")
        : ExecutionException(ErrorCode::EXECUTION_INVALID_SIGNAL, message, details) {}
};

class PositionLimitExceededException : public ExecutionException {
public:
    PositionLimitExceededException(const std::string& message, const std::string& details = "")
        : ExecutionException(ErrorCode::EXECUTION_POSITION_LIMIT_EXCEEDED, message, details) {}
};

class MarketClosedException : public ExecutionException {
public:
    MarketClosedException(const std::string& message, const std::string& details = "")
        : ExecutionException(ErrorCode::EXECUTION_MARKET_CLOSED, message, details) {}
};

// System-related exceptions
class SystemException : public TradingException {
public:
    SystemException(ErrorCode code, const std::string& message, const std::string& details = "")
        : TradingException(code, message, details) {}
};

class MemoryAllocationException : public SystemException {
public:
    MemoryAllocationException(const std::string& message, const std::string& details = "")
        : SystemException(ErrorCode::SYSTEM_MEMORY_ALLOCATION_FAILED, message, details) {}
};

class FileAccessException : public SystemException {
public:
    FileAccessException(const std::string& message, const std::string& details = "")
        : SystemException(ErrorCode::SYSTEM_FILE_ACCESS_DENIED, message, details) {}
};

class ConfigurationException : public SystemException {
public:
    ConfigurationException(const std::string& message, const std::string& details = "")
        : SystemException(ErrorCode::SYSTEM_CONFIGURATION_ERROR, message, details) {}
};

class UnexpectedException : public SystemException {
public:
    UnexpectedException(const std::string& message, const std::string& details = "")
        : SystemException(ErrorCode::SYSTEM_UNEXPECTED_ERROR, message, details) {}
};

