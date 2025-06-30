#include "database_connection.h"
#include "error_utils.h"
#include <iostream>
#include <sstream>
#include <cstdlib>
#include <stdexcept>

// Constructors and destructor
DatabaseConnection::DatabaseConnection() 
    : connection_(nullptr), connected_(false),
      host_(getenv("DB_HOST") ? getenv("DB_HOST") : "localhost"),
      port_(getenv("DB_PORT") ? getenv("DB_PORT") : "5433"),
      database_(getenv("DB_NAME") ? getenv("DB_NAME") : "simulated_trading_platform"),
      username_(getenv("DB_USER") ? getenv("DB_USER") : "trading_user"),
      password_(getenv("DB_PASSWORD") ? getenv("DB_PASSWORD") : "trading_password") {
    
    // Log connection configuration (without password for security)
    std::cerr << "[CONFIG] Database connection: " << username_ << "@" << host_ << ":" << port_ << "/" << database_ << std::endl;
    if (getenv("DB_HOST")) {
        std::cerr << "[CONFIG] Using environment variables for database configuration" << std::endl;
    } else {
        std::cerr << "[CONFIG] Using default database configuration" << std::endl;
    }
    
    buildConnectionString();
}

DatabaseConnection::DatabaseConnection(const std::string& host, const std::string& port,
                                     const std::string& database, const std::string& username,
                                     const std::string& password)
    : connection_(nullptr), connected_(false),
      host_(host), port_(port), database_(database),
      username_(username), password_(password) {
    buildConnectionString();
}

DatabaseConnection::~DatabaseConnection() {
    disconnect();
}

// Move constructor
DatabaseConnection::DatabaseConnection(DatabaseConnection&& other) noexcept
    : connection_(other.connection_), connection_string_(std::move(other.connection_string_)),
      connected_(other.connected_), host_(std::move(other.host_)),
      port_(std::move(other.port_)), database_(std::move(other.database_)),
      username_(std::move(other.username_)), password_(std::move(other.password_)) {
    other.connection_ = nullptr;
    other.connected_ = false;
}

// Move assignment
DatabaseConnection& DatabaseConnection::operator=(DatabaseConnection&& other) noexcept {
    if (this != &other) {
        disconnect();
        
        connection_ = other.connection_;
        connection_string_ = std::move(other.connection_string_);
        connected_ = other.connected_;
        host_ = std::move(other.host_);
        port_ = std::move(other.port_);
        database_ = std::move(other.database_);
        username_ = std::move(other.username_);
        password_ = std::move(other.password_);
        
        other.connection_ = nullptr;
        other.connected_ = false;
    }
    return *this;
}

// Helper methods
void DatabaseConnection::buildConnectionString() {
    std::stringstream ss;
    ss << "host=" << host_ 
       << " port=" << port_ 
       << " dbname=" << database_ 
       << " user=" << username_;
    
    if (!password_.empty()) {
        ss << " password=" << password_;
    }
    
    connection_string_ = ss.str();
}


// Connection management
Result<void> DatabaseConnection::connect() {
    if (connected_) {
        return Result<void>();
    }
    
    connection_ = PQconnectdb(connection_string_.c_str());
    
    if (PQstatus(connection_) != CONNECTION_OK) {
        std::string error_msg = "Database connection failed: " + std::string(PQerrorMessage(connection_));
        disconnect();
        return Result<void>(ErrorCode::DATABASE_CONNECTION_FAILED, error_msg);
    }
    
    connected_ = true;
    return Result<void>();
}

Result<void> DatabaseConnection::disconnect() {
    if (connection_) {
        PQfinish(connection_);
        connection_ = nullptr;
    }
    connected_ = false;
    return Result<void>();
}

bool DatabaseConnection::isConnected() const {
    return connected_ && connection_ && PQstatus(connection_) == CONNECTION_OK;
}

Result<void> DatabaseConnection::testConnection() {
    auto conn_result = connect();
    if (conn_result.isError()) {
        return conn_result;
    }
    
    // Execute a simple test query
    auto query_result = executeQueryInternal("SELECT version();");
    if (query_result.isError()) {
        return Result<void>(query_result.getError());
    }
    
    PQclear(query_result.getValue());
    return Result<void>();
}

// Configuration
void DatabaseConnection::setConnectionParams(const std::string& host, const std::string& port,
                                            const std::string& database, const std::string& username,
                                            const std::string& password) {
    if (connected_) {
        auto disc_result = disconnect();
        // Log disconnect error but don't fail the assignment
        if (disc_result.isError()) {
            std::cerr << "Database disconnect error during move assignment: " << disc_result.getError().message << std::endl;
        }
    }
    
    host_ = host;
    port_ = port;
    database_ = database;
    username_ = username;
    password_ = password;
    
    buildConnectionString();
}

// Query execution helper - returns PGresult* wrapped in Result<T>
Result<PGresult*> DatabaseConnection::executeQueryInternal(const std::string& query) {
    // Ensure connection
    if (!isConnected()) {
        auto conn_result = connect();
        if (conn_result.isError()) {
            return Result<PGresult*>(conn_result.getError());
        }
    }
    
    PGresult* result = PQexec(connection_, query.c_str());
    
    if (!result) {
        return Result<PGresult*>(ErrorCode::DATABASE_QUERY_FAILED, 
                                "Query execution failed: no result returned");
    }
    
    ExecStatusType status = PQresultStatus(result);
    if (status != PGRES_COMMAND_OK && status != PGRES_TUPLES_OK) {
        std::string error_msg = "Query execution failed: " + std::string(PQerrorMessage(connection_));
        PQclear(result);
        return Result<PGresult*>(ErrorCode::DATABASE_QUERY_FAILED, error_msg);
    }
    
    return Result<PGresult*>(result);
}

Result<void> DatabaseConnection::executeQuery(const std::string& query) {
    auto result = executeQueryInternal(query);
    if (result.isError()) {
        return Result<void>(result.getError());
    }
    
    PQclear(result.getValue());
    return Result<void>();
}

Result<std::vector<std::map<std::string, std::string>>> DatabaseConnection::selectQuery(const std::string& query) {
    auto result = executeQueryInternal(query);
    if (result.isError()) {
        return Result<std::vector<std::map<std::string, std::string>>>(result.getError());
    }
    
    PGResultWrapper wrapper(result.getValue());
    PGresult* pg_result = result.getValue();
    
    std::vector<std::map<std::string, std::string>> results;
    int num_rows = PQntuples(pg_result);
    int num_cols = PQnfields(pg_result);
    
    for (int row = 0; row < num_rows; ++row) {
        std::map<std::string, std::string> row_data;
        
        for (int col = 0; col < num_cols; ++col) {
            std::string field_name = PQfname(pg_result, col);
            std::string field_value = PQgetisnull(pg_result, row, col) ? 
                                    "" : PQgetvalue(pg_result, row, col);
            row_data[field_name] = field_value;
        }
        
        results.push_back(std::move(row_data));
    }
    
    return Result<std::vector<std::map<std::string, std::string>>>(std::move(results));
}

Result<std::vector<std::map<std::string, std::string>>> DatabaseConnection::executePreparedQuery(
    const std::string& query, 
    const std::vector<std::string>& params) {
    
    // Ensure connection
    if (!isConnected()) {
        auto conn_result = connect();
        if (conn_result.isError()) {
            return Result<std::vector<std::map<std::string, std::string>>>(conn_result.getError());
        }
    }
    
    // Convert parameters to C-style arrays for PostgreSQL
    std::vector<const char*> param_values;
    param_values.reserve(params.size());
    
    for (const auto& param : params) {
        param_values.push_back(param.c_str());
    }
    
    // Execute parameterized query
    PGresult* result = PQexecParams(
        connection_,
        query.c_str(),
        static_cast<int>(params.size()),
        nullptr,  // param types (NULL = infer)
        param_values.data(),
        nullptr,  // param lengths (NULL = text format)
        nullptr,  // param formats (NULL = text format)
        0         // result format (0 = text)
    );
    
    if (!result) {
        return Result<std::vector<std::map<std::string, std::string>>>(
            ErrorCode::DATABASE_QUERY_FAILED, "Prepared query execution failed: no result returned");
    }
    
    PGResultWrapper wrapper(result);
    
    ExecStatusType status = PQresultStatus(result);
    if (status != PGRES_TUPLES_OK) {
        std::string error_msg = "Prepared query execution failed: " + std::string(PQerrorMessage(connection_));
        return Result<std::vector<std::map<std::string, std::string>>>(ErrorCode::DATABASE_QUERY_FAILED, error_msg);
    }
    
    // Process results same as selectQuery
    std::vector<std::map<std::string, std::string>> results;
    int num_rows = PQntuples(result);
    int num_cols = PQnfields(result);
    
    for (int row = 0; row < num_rows; ++row) {
        std::map<std::string, std::string> row_data;
        
        for (int col = 0; col < num_cols; ++col) {
            std::string field_name = PQfname(result, col);
            std::string field_value = PQgetisnull(result, row, col) ? 
                                    "" : PQgetvalue(result, row, col);
            row_data[field_name] = field_value;
        }
        
        results.push_back(std::move(row_data));
    }
    
    return Result<std::vector<std::map<std::string, std::string>>>(std::move(results));
}

// Stock data specific queries
Result<std::vector<std::map<std::string, std::string>>> DatabaseConnection::getStockPrices(
    const std::string& symbol, 
    const std::string& start_date, 
    const std::string& end_date) {
    
    std::string query = "SELECT to_char(time, 'YYYY-MM-DD\"T\"HH24:MI:SS\"+00:00\"') as time, symbol, open, high, low, close, volume "
                       "FROM stock_prices_daily "
                       "WHERE symbol = $1 "
                       "AND time >= $2 "
                       "AND time <= $3 "
                       "ORDER BY time ASC;";
    
    std::vector<std::string> params = {symbol, start_date, end_date};
    return executePreparedQuery(query, params);
}

Result<std::vector<std::string>> DatabaseConnection::getAvailableSymbols() {
    std::string query = "SELECT DISTINCT symbol FROM stock_prices_daily ORDER BY symbol;";
    auto results = selectQuery(query);
    
    if (results.isError()) {
        return Result<std::vector<std::string>>(results.getError());
    }
    
    std::vector<std::string> symbols;
    for (const auto& row : results.getValue()) {
        auto it = row.find("symbol");
        if (it != row.end()) {
            symbols.push_back(it->second);
        }
    }
    
    return Result<std::vector<std::string>>(std::move(symbols));
}

Result<bool> DatabaseConnection::checkSymbolExists(const std::string& symbol) {
    std::string query = "SELECT COUNT(*) as count FROM stock_prices_daily WHERE symbol = $1;";
    
    std::vector<std::string> params = {symbol};
    auto results = executePreparedQuery(query, params);
    
    if (results.isError()) {
        return Result<bool>(results.getError());
    }
    
    const auto& result_data = results.getValue();
    if (!result_data.empty()) {
        auto it = result_data[0].find("count");
        if (it != result_data[0].end()) {
            try {
                bool exists = std::stoi(it->second) > 0;
                return Result<bool>(exists);
            } catch (const std::exception& e) {
                return Result<bool>(ErrorCode::DATA_PARSING_FAILED, 
                                  "Failed to parse count result: " + std::string(e.what()));
            }
        }
    }
    
    return Result<bool>(ErrorCode::DATA_SYMBOL_NOT_FOUND, "No count result returned for symbol: " + symbol);
}

// Utility methods
std::string DatabaseConnection::getLastError() const {
    if (connection_) {
        return PQerrorMessage(connection_);
    }
    return "No connection established";
}

nlohmann::json DatabaseConnection::getConnectionInfo() const {
    nlohmann::json info;
    info["host"] = host_;
    info["port"] = port_;
    info["database"] = database_;
    info["username"] = username_;
    info["connected"] = connected_;
    
    if (connection_) {
        info["db_version"] = PQparameterStatus(connection_, "server_version");
        info["client_encoding"] = PQparameterStatus(connection_, "client_encoding");
    }
    
    return info;
}

// Static methods - Simplified for Docker environment
Result<DatabaseConnection> DatabaseConnection::createFromEnvironment() {
    try {
        // Always assume Docker environment with known container names and credentials
        const char* host = std::getenv("DB_HOST");
        const char* port = std::getenv("DB_PORT");
        const char* database = std::getenv("DB_NAME");
        const char* username = std::getenv("DB_USER");
        const char* password = std::getenv("DB_PASSWORD");
        
        DatabaseConnection conn(
            host ? host : "postgres",           // Docker service name
            port ? port : "5432",              // Standard PostgreSQL port inside container
            database ? database : "simulated_trading_platform",
            username ? username : "trading_user",
            password ? password : "trading_password"
        );
        
        return Result<DatabaseConnection>(std::move(conn));
    } catch (const std::exception& e) {
        return Result<DatabaseConnection>(ErrorCode::SYSTEM_CONFIGURATION_ERROR, 
                                        "Failed to create database connection from environment: " + std::string(e.what()));
    }
}

