#ifndef DATABASE_CONNECTION_H
#define DATABASE_CONNECTION_H

#include <string>
#include <vector>
#include <memory>
#include <map>
#include <libpq-fe.h>
#include <nlohmann/json.hpp>

/**
 * Database connection class for PostgreSQL/TimescaleDB integration.
 * Handles connection management, query execution, and result processing.
 */
class DatabaseConnection {
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
    bool executeQuery(const std::string& query, PGresult*& result);
    void handleError(const std::string& operation);
    
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
    bool connect();
    bool disconnect();
    bool isConnected() const;
    bool testConnection();
    
    // Configuration
    void setConnectionParams(const std::string& host, const std::string& port,
                           const std::string& database, const std::string& username,
                           const std::string& password);
    
    // Query execution
    bool executeQuery(const std::string& query);
    std::vector<std::map<std::string, std::string>> selectQuery(const std::string& query);
    
    // Stock data specific queries
    std::vector<std::map<std::string, std::string>> getStockPrices(
        const std::string& symbol, 
        const std::string& start_date, 
        const std::string& end_date
    );
    
    std::vector<std::string> getAvailableSymbols();
    
    bool checkSymbolExists(const std::string& symbol);
    
    // Utility methods
    std::string getLastError() const;
    nlohmann::json getConnectionInfo() const;
    
    // Static methods for environment-based connection
    static DatabaseConnection createFromEnvironment();
    static DatabaseConnection createDefault();
};

/*
RAII wrapper for PGresult to ensure proper cleanup
*/
class PGResultWrapper {
private:
    PGresult* result_;
    
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
};

#endif // DATABASE_CONNECTION_H