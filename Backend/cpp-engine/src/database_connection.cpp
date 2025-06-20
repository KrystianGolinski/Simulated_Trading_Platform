#include "database_connection.h"
#include <iostream>
#include <sstream>
#include <cstdlib>
#include <stdexcept>

// Constructors and destructor
DatabaseConnection::DatabaseConnection() 
    : connection_(nullptr), connected_(false),
      host_("postgres"), port_("5432"), database_("simulated_trading_platform"),
      username_("trading_user"), password_("trading_password") {
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

void DatabaseConnection::handleError(const std::string& operation) {
    if (connection_) {
        std::cerr << "Database error during " << operation << ": " 
                  << PQerrorMessage(connection_) << std::endl;
    } else {
        std::cerr << "Database error during " << operation << ": No connection" << std::endl;
    }
}

// Connection management
bool DatabaseConnection::connect() {
    if (connected_) {
        return true;
    }
    
    connection_ = PQconnectdb(connection_string_.c_str());
    
    if (PQstatus(connection_) != CONNECTION_OK) {
        handleError("connection");
        disconnect();
        return false;
    }
    
    connected_ = true;
    return true;
}

bool DatabaseConnection::disconnect() {
    if (connection_) {
        PQfinish(connection_);
        connection_ = nullptr;
    }
    connected_ = false;
    return true;
}

bool DatabaseConnection::isConnected() const {
    return connected_ && connection_ && PQstatus(connection_) == CONNECTION_OK;
}

bool DatabaseConnection::testConnection() {
    if (!connect()) {
        return false;
    }
    
    // Execute a simple test query
    PGresult* result = PQexec(connection_, "SELECT version();");
    
    if (PQresultStatus(result) != PGRES_TUPLES_OK) {
        handleError("test query");
        PQclear(result);
        return false;
    }
    
    PQclear(result);
    return true;
}

// Configuration
void DatabaseConnection::setConnectionParams(const std::string& host, const std::string& port,
                                            const std::string& database, const std::string& username,
                                            const std::string& password) {
    if (connected_) {
        disconnect();
    }
    
    host_ = host;
    port_ = port;
    database_ = database;
    username_ = username;
    password_ = password;
    
    buildConnectionString();
}

// Query execution
bool DatabaseConnection::executeQuery(const std::string& query, PGresult*& result) {
    if (!isConnected() && !connect()) {
        return false;
    }
    
    result = PQexec(connection_, query.c_str());
    
    if (!result) {
        handleError("query execution");
        return false;
    }
    
    ExecStatusType status = PQresultStatus(result);
    if (status != PGRES_COMMAND_OK && status != PGRES_TUPLES_OK) {
        handleError("query execution");
        PQclear(result);
        result = nullptr;
        return false;
    }
    
    return true;
}

bool DatabaseConnection::executeQuery(const std::string& query) {
    PGresult* result;
    bool success = executeQuery(query, result);
    if (result) {
        PQclear(result);
    }
    return success;
}

std::vector<std::map<std::string, std::string>> DatabaseConnection::selectQuery(const std::string& query) {
    std::vector<std::map<std::string, std::string>> results;
    
    PGresult* result;
    if (!executeQuery(query, result)) {
        return results;
    }
    
    PGResultWrapper wrapper(result);
    
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
    
    return results;
}

// Stock data specific queries
std::vector<std::map<std::string, std::string>> DatabaseConnection::getStockPrices(
    const std::string& symbol, 
    const std::string& start_date, 
    const std::string& end_date) {
    
    std::stringstream query;
    query << "SELECT to_char(time, 'YYYY-MM-DD\"T\"HH24:MI:SS\"+00:00\"') as time, symbol, open, high, low, close, volume "
          << "FROM stock_prices_daily "
          << "WHERE symbol = '" << symbol << "' "
          << "AND time >= '" << start_date << "' "
          << "AND time <= '" << end_date << "' "
          << "ORDER BY time ASC;";
    
    return selectQuery(query.str());
}

std::vector<std::string> DatabaseConnection::getAvailableSymbols() {
    std::vector<std::string> symbols;
    
    std::string query = "SELECT DISTINCT symbol FROM stock_prices_daily ORDER BY symbol;";
    auto results = selectQuery(query);
    
    for (const auto& row : results) {
        auto it = row.find("symbol");
        if (it != row.end()) {
            symbols.push_back(it->second);
        }
    }
    
    return symbols;
}

bool DatabaseConnection::checkSymbolExists(const std::string& symbol) {
    std::stringstream query;
    query << "SELECT COUNT(*) as count FROM stock_prices_daily WHERE symbol = '" << symbol << "';";
    
    auto results = selectQuery(query.str());
    
    if (!results.empty()) {
        auto it = results[0].find("count");
        if (it != results[0].end()) {
            return std::stoi(it->second) > 0;
        }
    }
    
    return false;
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
DatabaseConnection DatabaseConnection::createFromEnvironment() {
    // Always assume Docker environment with known container names and credentials
    const char* host = std::getenv("DB_HOST");
    const char* port = std::getenv("DB_PORT");
    const char* database = std::getenv("DB_NAME");
    const char* username = std::getenv("DB_USER");
    const char* password = std::getenv("DB_PASSWORD");
    
    return DatabaseConnection(
        host ? host : "postgres",           // Docker service name
        port ? port : "5432",              // Standard PostgreSQL port inside container
        database ? database : "simulated_trading_platform",
        username ? username : "trading_user",
        password ? password : "trading_password"
    );
}

DatabaseConnection DatabaseConnection::createDefault() {
    // Always use Docker environment defaults
    return createFromEnvironment();
}