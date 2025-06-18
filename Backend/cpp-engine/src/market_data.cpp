#include "market_data.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <ctime>
#include <algorithm>
#include <stdexcept>

// MarketData implementation
MarketData::MarketData() 
    : db_connection_(std::make_unique<DatabaseConnection>(DatabaseConnection::createFromEnvironment())),
      cache_enabled_(true) {
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
bool MarketData::ensureConnection() const {
    if (!db_connection_) {
        return false;
    }
    return db_connection_->isConnected() || db_connection_->connect();
}

void MarketData::cachePrice(const std::string& symbol, double price) const {
    if (cache_enabled_) {
        price_cache_[symbol] = price;
    }
}

double MarketData::getCachedPrice(const std::string& symbol) const {
    if (cache_enabled_) {
        auto it = price_cache_.find(symbol);
        if (it != price_cache_.end()) {
            return it->second;
        }
    }
    return 0.0;
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
double MarketData::getPrice(const std::string& symbol) const {
    return getLatestPrice(symbol);
}

double MarketData::getLatestPrice(const std::string& symbol) const {
    // Check cache first
    if (cache_enabled_) {
        double cached = getCachedPrice(symbol);
        if (cached > 0.0) {
            return cached;
        }
    }
    
    if (!ensureConnection()) {
        std::cerr << "Database connection failed" << std::endl;
        return 0.0;
    }
    
    // Query for the latest price
    std::stringstream query;
    query << "SELECT close FROM stock_prices_daily "
          << "WHERE symbol = '" << symbol << "' "
          << "ORDER BY time DESC LIMIT 1;";
    
    auto results = db_connection_->selectQuery(query.str());
    
    if (!results.empty()) {
        auto it = results[0].find("close");
        if (it != results[0].end() && !it->second.empty()) {
            double price = std::stod(it->second);
            cachePrice(symbol, price);
            return price;
        }
    }
    
    return 0.0;
}

std::map<std::string, double> MarketData::getCurrentPrices() const {
    auto symbols = getAvailableSymbols();
    return getCurrentPrices(symbols);
}

std::map<std::string, double> MarketData::getCurrentPrices(const std::vector<std::string>& symbols) const {
    std::map<std::string, double> prices;
    
    for (const auto& symbol : symbols) {
        double price = getLatestPrice(symbol);
        if (price > 0.0) {
            prices[symbol] = price;
        }
    }
    
    return prices;
}

// Historical data access
std::vector<std::map<std::string, std::string>> MarketData::getHistoricalPrices(
    const std::string& symbol,
    const std::string& start_date,
    const std::string& end_date) const {
    
    std::vector<std::map<std::string, std::string>> prices;
    
    if (!ensureConnection()) {
        std::cerr << "Database connection failed" << std::endl;
        return prices;
    }
    
    auto results = db_connection_->getStockPrices(symbol, start_date, end_date);
    
    return results;
}

std::map<std::string, std::vector<std::map<std::string, std::string>>> MarketData::getHistoricalPrices(
    const std::vector<std::string>& symbols,
    const std::string& start_date,
    const std::string& end_date) const {
    
    std::map<std::string, std::vector<std::map<std::string, std::string>>> all_prices;
    
    for (const auto& symbol : symbols) {
        all_prices[symbol] = getHistoricalPrices(symbol, start_date, end_date);
    }
    
    return all_prices;
}

// Date range utilities
std::vector<std::map<std::string, std::string>> MarketData::getPricesForDateRange(
    const std::string& symbol,
    const std::string& start_date,
    const std::string& end_date) const {
    
    return getHistoricalPrices(symbol, start_date, end_date);
}

std::map<std::string, std::string> MarketData::getPriceForDate(const std::string& symbol, const std::string& date) const {
    auto prices = getHistoricalPrices(symbol, date, date);
    
    if (!prices.empty()) {
        return prices[0];
    }
    
    return std::map<std::string, std::string>(); // Return empty price data
}

// Symbol validation and discovery
bool MarketData::symbolExists(const std::string& symbol) const {
    if (!ensureConnection()) {
        return false;
    }
    
    return db_connection_->checkSymbolExists(symbol);
}

std::vector<std::string> MarketData::getAvailableSymbols() const {
    if (!ensureConnection()) {
        return {};
    }
    
    return db_connection_->getAvailableSymbols();
}

// Data validation and statistics
int MarketData::getDataPointCount(const std::string& symbol, 
                                 const std::string& start_date, 
                                 const std::string& end_date) const {
    
    if (!ensureConnection()) {
        return 0;
    }
    
    std::stringstream query;
    query << "SELECT COUNT(*) as count FROM stock_prices_daily "
          << "WHERE symbol = '" << symbol << "' "
          << "AND time >= '" << start_date << "' "
          << "AND time <= '" << end_date << "';";
    
    auto results = db_connection_->selectQuery(query.str());
    
    if (!results.empty()) {
        auto it = results[0].find("count");
        if (it != results[0].end()) {
            return std::stoi(it->second);
        }
    }
    
    return 0;
}

std::pair<std::string, std::string> MarketData::getDateRange(const std::string& symbol) const {
    if (!ensureConnection()) {
        return {"", ""};
    }
    
    std::stringstream query;
    query << "SELECT MIN(time) as min_date, MAX(time) as max_date "
          << "FROM stock_prices_daily WHERE symbol = '" << symbol << "';";
    
    auto results = db_connection_->selectQuery(query.str());
    
    if (!results.empty()) {
        auto min_it = results[0].find("min_date");
        auto max_it = results[0].find("max_date");
        
        if (min_it != results[0].end() && max_it != results[0].end()) {
            std::string min_date = min_it->second.substr(0, 10);
            std::string max_date = max_it->second.substr(0, 10);
            return {min_date, max_date};
        }
    }
    
    return {"", ""};
}

// Utility methods
void MarketData::clearCache() {
    price_cache_.clear();
}

nlohmann::json MarketData::getDataSummary(const std::string& symbol,
                                         const std::string& start_date,
                                         const std::string& end_date) const {
    nlohmann::json summary;
    summary["symbol"] = symbol;
    summary["start_date"] = start_date;
    summary["end_date"] = end_date;
    summary["data_points"] = getDataPointCount(symbol, start_date, end_date);
    
    auto date_range = getDateRange(symbol);
    summary["available_range"] = {
        {"start", date_range.first},
        {"end", date_range.second}
    };
    
    summary["status"] = symbolExists(symbol) ? "success" : "symbol_not_found";
    
    return summary;
}

// Test methods
bool MarketData::testDatabaseConnection() const {
    if (!db_connection_) {
        return false;
    }
    return db_connection_->testConnection();
}

nlohmann::json MarketData::getDatabaseInfo() const {
    if (!db_connection_) {
        return nlohmann::json::object();
    }
    return db_connection_->getConnectionInfo();
}

// Static helper methods
std::string MarketData::getCurrentDate() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d");
    return ss.str();
}

bool MarketData::isValidDateFormat(const std::string& date) {
    if (date.length() != 10) return false;
    if (date[4] != '-' || date[7] != '-') return false;
    
    try {
        int year = std::stoi(date.substr(0, 4));
        int month = std::stoi(date.substr(5, 2));
        int day = std::stoi(date.substr(8, 2));
        
        return (year >= 1900 && year <= 2100 && 
                month >= 1 && month <= 12 && 
                day >= 1 && day <= 31);
    } catch (const std::exception&) {
        return false;
    }
}

std::string MarketData::formatDate(const std::string& date) {
    if (isValidDateFormat(date)) {
        return date;
    }
    return getCurrentDate();
}