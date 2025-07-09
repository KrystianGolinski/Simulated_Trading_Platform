#pragma once

#include <map>
#include <memory>
#include <string>
#include <vector>

#include <libpq-fe.h>
#include <nlohmann/json.hpp>

#include "result.h"
#include "trading_exceptions.h"

/**
 * Database connection class for PostgreSQL/TimescaleDB integration.
 * Handles connection management, query execution, and result processing.
 */
class DatabaseConnection {
public:
    // Constructors and destructor
    DatabaseConnection();
    DatabaseConnection(const std::string& host, const std::string& port, 
                      const std::string& database, const std::string& username, 
                      const std::string& password);
    ~DatabaseConnection();
    
    // Move constructor and assignment (no copying for safety)
    DatabaseConnection(DatabaseConnection&& other) noexcept;
    DatabaseConnection& operator=(DatabaseConnection&& other) noexcept;
    
    // Disable copy constructor and assignment
    DatabaseConnection(const DatabaseConnection&) = delete;
    DatabaseConnection& operator=(const DatabaseConnection&) = delete;
    
    // Connection management
    Result<void> connect();
    Result<void> disconnect();
    bool isConnected() const;
    Result<void> testConnection();
    
    // Configuration
    void setConnectionParams(const std::string& host, const std::string& port,
                           const std::string& database, const std::string& username,
                           const std::string& password);
    
    // Query execution
    Result<void> executeQuery(const std::string& query);
    Result<std::vector<std::map<std::string, std::string>>> selectQuery(const std::string& query);
    
    // Prepared statement methods for secure queries
    Result<std::vector<std::map<std::string, std::string>>> executePreparedQuery(
        const std::string& query, 
        const std::vector<std::string>& params
    );
    
    // Stock data specific queries
    Result<std::vector<std::map<std::string, std::string>>> getStockPrices(
        const std::string& symbol, 
        const std::string& start_date, 
        const std::string& end_date
    );
    
    Result<std::vector<std::string>> getAvailableSymbols();
    
    Result<bool> checkSymbolExists(const std::string& symbol);
    
    // Temporal validation methods
    Result<bool> checkStockTradeable(const std::string& symbol, const std::string& check_date);
    
    Result<std::vector<std::string>> getEligibleStocksForPeriod(
        const std::string& start_date, 
        const std::string& end_date
    );
    
    Result<std::map<std::string, std::string>> getStockTemporalInfo(const std::string& symbol);
    
    Result<std::vector<std::string>> validateSymbolsForPeriod(
        const std::vector<std::string>& symbols,
        const std::string& start_date,
        const std::string& end_date
    );
    
    // Utility methods
    std::string getLastError() const;
    nlohmann::json getConnectionInfo() const;
    
    // Static methods for environment-based connection
    static Result<DatabaseConnection> createFromEnvironment();

private:
    PGconn* connection_;
    std::string connection_string_;
    bool connected_;
    
    // Connection parameters
    std::string host_;
    std::string port_;
    std::string database_;
    std::string username_;
    std::string password_;
    
    // Helper methods
    void buildConnectionString();
    Result<PGresult*> executeQueryInternal(const std::string& query);
    void handleError(const std::string& operation);
};

// RAII wrapper for PGresult to ensure proper cleanup
class PGResultWrapper {
public:
    explicit PGResultWrapper(PGresult* result) : result_(result) {}
    ~PGResultWrapper() { if (result_) PQclear(result_); }
    
    // Move constructor and assignment
    PGResultWrapper(PGResultWrapper&& other) noexcept : result_(other.result_) {
        other.result_ = nullptr;
    }
    
    PGResultWrapper& operator=(PGResultWrapper&& other) noexcept {
        if (this != &other) {
            if (result_) PQclear(result_);
            result_ = other.result_;
            other.result_ = nullptr;
        }
        return *this;
    }
    
    // Disable copy
    PGResultWrapper(const PGResultWrapper&) = delete;
    PGResultWrapper& operator=(const PGResultWrapper&) = delete;
    
    PGresult* get() const { return result_; }
    PGresult* release() { 
        PGresult* temp = result_; 
        result_ = nullptr; 
        return temp; 
    }

private:
    PGresult* result_;
};

