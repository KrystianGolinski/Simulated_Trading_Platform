#include "market_data.h"
#include "error_utils.h"
#include "logger.h"
#include "date_time_utils.h"
#include <iostream>
#include <algorithm>
#include <stdexcept>

// MarketData implementation
MarketData::MarketData() 
    : cache_enabled_(true) {
    // Create database connection using Result pattern
    auto conn_result = DatabaseConnection::createFromEnvironment();
    if (conn_result.isSuccess()) {
        db_connection_ = std::make_unique<DatabaseConnection>(std::move(conn_result.getValue()));
    } else {
        // Log error but allow construction - connection will be attempted later
        std::cerr << "Warning: Failed to create database connection during MarketData construction: " 
                  << conn_result.getErrorMessage() << std::endl;
        db_connection_ = nullptr;
    }
}

MarketData::MarketData(std::unique_ptr<DatabaseConnection> db_conn) 
    : db_connection_(std::move(db_conn)), cache_enabled_(true) {
}

// Move constructor
MarketData::MarketData(MarketData&& other) noexcept 
    : db_connection_(std::move(other.db_connection_)),
      price_cache_(std::move(other.price_cache_)),
      cache_enabled_(other.cache_enabled_) {
}

// Move assignment
MarketData& MarketData::operator=(MarketData&& other) noexcept {
    if (this != &other) {
        db_connection_ = std::move(other.db_connection_);
        price_cache_ = std::move(other.price_cache_);
        cache_enabled_ = other.cache_enabled_;
    }
    return *this;
}

// Helper methods
Result<void> MarketData::ensureConnection() const {
    if (!db_connection_) {
        return Result<void>(ErrorCode::DATABASE_CONNECTION_FAILED, "No database connection available");
    }
    
    if (db_connection_->isConnected()) {
        return Result<void>();
    }
    
    return db_connection_->connect();
}

void MarketData::cachePrice(const std::string& symbol, double price) const {
    if (cache_enabled_) {
        std::lock_guard<std::mutex> lock(cache_mutex_);
        price_cache_[symbol] = price;
    }
}

Result<double> MarketData::getCachedPrice(const std::string& symbol) const {
    if (cache_enabled_) {
        std::lock_guard<std::mutex> lock(cache_mutex_);
        auto it = price_cache_.find(symbol);
        if (it != price_cache_.end()) {
            return Result<double>(it->second);
        }
    }
    return Result<double>(ErrorCode::DATA_SYMBOL_NOT_FOUND, "Symbol not found in cache: " + symbol);
}

// Configuration
void MarketData::setDatabaseConnection(std::unique_ptr<DatabaseConnection> db_conn) {
    db_connection_ = std::move(db_conn);
    clearCache();
}

void MarketData::enableCache(bool enable) {
    cache_enabled_ = enable;
    if (!enable) {
        clearCache();
    }
}

bool MarketData::isConnected() const {
    return db_connection_ && db_connection_->isConnected();
}

// Basic price access
Result<double> MarketData::getLatestPrice(const std::string& symbol) const {
    // Check cache first
    if (cache_enabled_) {
        auto cached = getCachedPrice(symbol);
        if (cached.isSuccess()) {
            return cached;
        }
    }
    
    auto conn_result = ensureConnection();
    if (conn_result.isError()) {
        return Result<double>(conn_result.getError());
    }
    
    // Query for the latest price
    std::string query = "SELECT close FROM stock_prices_daily "
                       "WHERE symbol = $1 "
                       "ORDER BY time DESC LIMIT 1;";
    
    std::vector<std::string> params = {symbol};
    auto results = db_connection_->executePreparedQuery(query, params);
    
    if (results.isError()) {
        return Result<double>(results.getError());
    }
    
    const auto& result_data = results.getValue();
    if (!result_data.empty()) {
        auto it = result_data[0].find("close");
        if (it != result_data[0].end() && !it->second.empty()) {
            try {
                double price = std::stod(it->second);
                cachePrice(symbol, price);
                return Result<double>(price);
            } catch (const std::exception& e) {
                return Result<double>(ErrorCode::DATA_PARSING_FAILED, 
                                    "Failed to parse price data: " + std::string(e.what()));
            }
        }
    }
    
    return Result<double>(ErrorCode::DATA_SYMBOL_NOT_FOUND, "Symbol not found: " + symbol);
}

Result<std::map<std::string, double>> MarketData::getCurrentPrices() const {
    Logger::debug("MarketData::getCurrentPrices called");
    
    auto symbols_result = getAvailableSymbols();
    if (symbols_result.isError()) {
        Logger::error("Error in MarketData::getCurrentPrices: ", symbols_result.getErrorMessage());
        return Result<std::map<std::string, double>>(symbols_result.getError());
    }
    
    auto result = getCurrentPrices(symbols_result.getValue());
    if (result.isError()) {
        Logger::error("Error in MarketData::getCurrentPrices: ", result.getErrorMessage());
    }
    return result;
}

Result<std::map<std::string, double>> MarketData::getCurrentPrices(const std::vector<std::string>& symbols) const {
    std::map<std::string, double> prices;
    
    for (const auto& symbol : symbols) {
        auto price_result = getLatestPrice(symbol);
        if (price_result.isSuccess()) {
            prices[symbol] = price_result.getValue();
        } else {
            // Check if it's a symbol not found error (continue) or database error (stop)
            if (price_result.getErrorCode() == ErrorCode::DATA_SYMBOL_NOT_FOUND) {
                // Log warning but continue with other symbols
                std::cerr << "Warning: " << price_result.getErrorMessage() << std::endl;
            } else {
                // Database or other critical errors - return error
                return Result<std::map<std::string, double>>(price_result.getError());
            }
        }
    }
    
    return Result<std::map<std::string, double>>(std::move(prices));
}

// Historical data access
Result<std::vector<std::map<std::string, std::string>>> MarketData::getHistoricalPrices(
    const std::string& symbol,
    const std::string& start_date,
    const std::string& end_date) const {
    
    Logger::debug("MarketData::getHistoricalPrices called for symbol=", symbol, 
                 " from ", start_date, " to ", end_date);
    
    auto conn_result = ensureConnection();
    if (conn_result.isError()) {
        Logger::error("Error in MarketData::getHistoricalPrices: ", conn_result.getErrorMessage());
        return Result<std::vector<std::map<std::string, std::string>>>(conn_result.getError());
    }
    
    auto result = db_connection_->getStockPrices(symbol, start_date, end_date);
    if (result.isError()) {
        Logger::error("Error in MarketData::getHistoricalPrices: ", result.getErrorMessage());
    }
    return result;
}

Result<std::map<std::string, std::vector<std::map<std::string, std::string>>>> MarketData::getHistoricalPrices(
    const std::vector<std::string>& symbols,
    const std::string& start_date,
    const std::string& end_date) const {
    
    std::map<std::string, std::vector<std::map<std::string, std::string>>> all_prices;
    
    for (const auto& symbol : symbols) {
        auto prices_result = getHistoricalPrices(symbol, start_date, end_date);
        if (prices_result.isError()) {
            return Result<std::map<std::string, std::vector<std::map<std::string, std::string>>>>(prices_result.getError());
        }
        all_prices[symbol] = prices_result.getValue();
    }
    
    return Result<std::map<std::string, std::vector<std::map<std::string, std::string>>>>(std::move(all_prices));
}

// Date range utilities
Result<std::vector<std::map<std::string, std::string>>> MarketData::getPricesForDateRange(
    const std::string& symbol,
    const std::string& start_date,
    const std::string& end_date) const {
    
    return getHistoricalPrices(symbol, start_date, end_date);
}

Result<std::map<std::string, std::string>> MarketData::getPriceForDate(const std::string& symbol, const std::string& date) const {
    auto prices_result = getHistoricalPrices(symbol, date, date);
    
    if (prices_result.isError()) {
        return Result<std::map<std::string, std::string>>(prices_result.getError());
    }
    
    const auto& prices = prices_result.getValue();
    if (!prices.empty()) {
        return Result<std::map<std::string, std::string>>(prices[0]);
    }
    
    return Result<std::map<std::string, std::string>>(ErrorCode::DATA_SYMBOL_NOT_FOUND, 
                                                     "No price data found for symbol " + symbol + " on date " + date);
}

// Symbol validation and discovery
Result<bool> MarketData::symbolExists(const std::string& symbol) const {
    auto conn_result = ensureConnection();
    if (conn_result.isError()) {
        return Result<bool>(conn_result.getError());
    }
    
    return db_connection_->checkSymbolExists(symbol);
}

Result<std::vector<std::string>> MarketData::getAvailableSymbols() const {
    auto conn_result = ensureConnection();
    if (conn_result.isError()) {
        return Result<std::vector<std::string>>(conn_result.getError());
    }
    
    return db_connection_->getAvailableSymbols();
}

// Data validation and statistics
Result<int> MarketData::getDataPointCount(const std::string& symbol, 
                                        const std::string& start_date, 
                                        const std::string& end_date) const {
    
    auto conn_result = ensureConnection();
    if (conn_result.isError()) {
        return Result<int>(conn_result.getError());
    }
    
    std::string query = "SELECT COUNT(*) as count FROM stock_prices_daily "
                       "WHERE symbol = $1 "
                       "AND time >= $2 "
                       "AND time <= $3;";
    
    std::vector<std::string> params = {symbol, start_date, end_date};
    auto results = db_connection_->executePreparedQuery(query, params);
    
    if (results.isError()) {
        return Result<int>(results.getError());
    }
    
    const auto& result_data = results.getValue();
    if (!result_data.empty()) {
        auto it = result_data[0].find("count");
        if (it != result_data[0].end()) {
            try {
                int count = std::stoi(it->second);
                return Result<int>(count);
            } catch (const std::exception& e) {
                return Result<int>(ErrorCode::DATA_PARSING_FAILED, 
                                 "Failed to parse count result: " + std::string(e.what()));
            }
        }
    }
    
    return Result<int>(ErrorCode::DATA_SYMBOL_NOT_FOUND, "No count result returned for query");
}

Result<std::pair<std::string, std::string>> MarketData::getDateRange(const std::string& symbol) const {
    auto conn_result = ensureConnection();
    if (conn_result.isError()) {
        return Result<std::pair<std::string, std::string>>(conn_result.getError());
    }
    
    std::string query = "SELECT MIN(time) as min_date, MAX(time) as max_date "
                       "FROM stock_prices_daily WHERE symbol = $1;";
    
    std::vector<std::string> params = {symbol};
    auto results = db_connection_->executePreparedQuery(query, params);
    
    if (results.isError()) {
        return Result<std::pair<std::string, std::string>>(results.getError());
    }
    
    const auto& result_data = results.getValue();
    if (!result_data.empty()) {
        auto min_it = result_data[0].find("min_date");
        auto max_it = result_data[0].find("max_date");
        
        if (min_it != result_data[0].end() && max_it != result_data[0].end()) {
            try {
                std::string min_date = min_it->second.substr(0, 10);
                std::string max_date = max_it->second.substr(0, 10);
                return Result<std::pair<std::string, std::string>>(std::make_pair(min_date, max_date));
            } catch (const std::exception& e) {
                return Result<std::pair<std::string, std::string>>(ErrorCode::DATA_PARSING_FAILED, 
                                                                  "Failed to parse date range: " + std::string(e.what()));
            }
        }
    }
    
    return Result<std::pair<std::string, std::string>>(ErrorCode::DATA_SYMBOL_NOT_FOUND, 
                                                       "No date range found for symbol: " + symbol);
}

// Utility methods
void MarketData::clearCache() {
    std::lock_guard<std::mutex> lock(cache_mutex_);
    price_cache_.clear();
}

Result<nlohmann::json> MarketData::getDataSummary(const std::string& symbol,
                                                  const std::string& start_date,
                                                  const std::string& end_date) const {
    nlohmann::json summary;
    summary["symbol"] = symbol;
    summary["start_date"] = start_date;
    summary["end_date"] = end_date;
    
    // Get data point count
    auto count_result = getDataPointCount(symbol, start_date, end_date);
    if (count_result.isError()) {
        return Result<nlohmann::json>(count_result.getError());
    }
    summary["data_points"] = count_result.getValue();
    
    // Get date range
    auto date_range_result = getDateRange(symbol);
    if (date_range_result.isError()) {
        return Result<nlohmann::json>(date_range_result.getError());
    }
    auto date_range = date_range_result.getValue();
    summary["available_range"] = {
        {"start", date_range.first},
        {"end", date_range.second}
    };
    
    // Check if symbol exists
    auto exists_result = symbolExists(symbol);
    if (exists_result.isError()) {
        return Result<nlohmann::json>(exists_result.getError());
    }
    summary["status"] = exists_result.getValue() ? "success" : "symbol_not_found";
    
    return Result<nlohmann::json>(std::move(summary));
}

// Test methods
Result<void> MarketData::testDatabaseConnection() const {
    if (!db_connection_) {
        return Result<void>(ErrorCode::DATABASE_CONNECTION_FAILED, "No database connection available");
    }
    return db_connection_->testConnection();
}

Result<nlohmann::json> MarketData::getDatabaseInfo() const {
    if (!db_connection_) {
        return Result<nlohmann::json>(ErrorCode::DATABASE_CONNECTION_FAILED, "No database connection available");
    }
    try {
        auto info = db_connection_->getConnectionInfo();
        return Result<nlohmann::json>(std::move(info));
    } catch (const std::exception& e) {
        return Result<nlohmann::json>(ErrorCode::DATABASE_CONNECTION_FAILED, 
                                    "Failed to get database info: " + std::string(e.what()));
    }
}

// Static helper methods
std::string MarketData::getCurrentDate() {
    return DateTimeUtils::getCurrentDate();
}

bool MarketData::isValidDateFormat(const std::string& date) {
    return DateTimeUtils::isValidDateFormat(date);
}

std::string MarketData::formatDate(const std::string& date) {
    return DateTimeUtils::formatDate(date);
}

// Database access for temporal validation
DatabaseConnection* MarketData::getDatabaseConnection() const {
    return db_connection_.get();
}

// Memory optimization methods
void MarketData::optimizeMemory() {
    // Clear price cache to free memory
    {
        std::lock_guard<std::mutex> lock(cache_mutex_);
        price_cache_.clear();
    }
    
    // Note: Connection pool optimization would be handled by DatabaseConnection
    // if it implements IMemoryOptimizable interface
}

size_t MarketData::getMemoryUsage() const {
    size_t total = sizeof(*this);
    
    // Calculate price cache memory usage
    {
        std::lock_guard<std::mutex> lock(cache_mutex_);
        total += price_cache_.size() * (sizeof(std::string) + sizeof(double));
        // Add estimated string storage
        for (const auto& pair : price_cache_) {
            total += pair.first.capacity();
        }
    }
    
    // Add database connection memory (if available)
    if (db_connection_) {
        total += sizeof(*db_connection_);
    }
    
    return total;
}

std::string MarketData::getMemoryReport() const {
    std::ostringstream report;
    report << "MarketData Memory Usage:\n";
    
    size_t cache_size = 0;
    {
        std::lock_guard<std::mutex> lock(cache_mutex_);
        cache_size = price_cache_.size();
    }
    
    report << "  Price cache entries: " << cache_size << "\n";
    report << "  Cache enabled: " << (cache_enabled_ ? "Yes" : "No") << "\n";
    report << "  Database connection: " << (db_connection_ ? "Active" : "None") << "\n";
    report << "  Estimated memory: " << getMemoryUsage() << " bytes\n";
    
    return report.str();
}