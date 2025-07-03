#pragma once

#include <string>
#include <map>
#include <vector>
#include <memory>
#include <mutex>
#include <nlohmann/json.hpp>
#include "database_connection.h"
#include "technical_indicators.h"
#include "result.h"
#include "trading_exceptions.h"

/**
 * MarketData class handles historical price data access from DB.
 * Provides methods to fetch stock prices for specific date ranges and symbols.
 */

class MarketData {
private:
    std::unique_ptr<DatabaseConnection> db_connection_;
    mutable std::map<std::string, double> price_cache_;
    mutable std::mutex cache_mutex_;
    bool cache_enabled_;
    
    // Helper methods
    Result<void> ensureConnection() const;
    void cachePrice(const std::string& symbol, double price) const;
    Result<double> getCachedPrice(const std::string& symbol) const;
    
public:
    // Constructors
    MarketData();
    explicit MarketData(std::unique_ptr<DatabaseConnection> db_conn);
    
    // Move constructor and assignment
    MarketData(MarketData&& other) noexcept;
    MarketData& operator=(MarketData&& other) noexcept;
    
    // Disable copy constructor and assignment
    MarketData(const MarketData&) = delete;
    MarketData& operator=(const MarketData&) = delete;
    
    // Destructor
    ~MarketData() = default;
    
    // Configuration
    void setDatabaseConnection(std::unique_ptr<DatabaseConnection> db_conn);
    void enableCache(bool enable = true);
    bool isConnected() const;
    
    // Basic price access
    Result<double> getLatestPrice(const std::string& symbol) const;
    Result<std::map<std::string, double>> getCurrentPrices() const;
    Result<std::map<std::string, double>> getCurrentPrices(const std::vector<std::string>& symbols) const;
    
    // Historical data access (returns database format for conversion to PriceData)
    Result<std::vector<std::map<std::string, std::string>>> getHistoricalPrices(
        const std::string& symbol,
        const std::string& start_date,
        const std::string& end_date
    ) const;
    
    Result<std::map<std::string, std::vector<std::map<std::string, std::string>>>> getHistoricalPrices(
        const std::vector<std::string>& symbols,
        const std::string& start_date,
        const std::string& end_date
    ) const;
    
    // Date range utilities
    Result<std::vector<std::map<std::string, std::string>>> getPricesForDateRange(
        const std::string& symbol,
        const std::string& start_date,
        const std::string& end_date
    ) const;
    
    Result<std::map<std::string, std::string>> getPriceForDate(const std::string& symbol, const std::string& date) const;
    
    // Symbol validation and discovery
    Result<bool> symbolExists(const std::string& symbol) const;
    Result<std::vector<std::string>> getAvailableSymbols() const;
    
    // Data validation and statistics
    Result<int> getDataPointCount(const std::string& symbol, 
                                const std::string& start_date, 
                                const std::string& end_date) const;
    
    Result<std::pair<std::string, std::string>> getDateRange(const std::string& symbol) const;
    
    // Utility methods
    void clearCache();
    Result<nlohmann::json> getDataSummary(const std::string& symbol,
                                         const std::string& start_date,
                                         const std::string& end_date) const;
    
    // Test methods
    Result<void> testDatabaseConnection() const;
    Result<nlohmann::json> getDatabaseInfo() const;
    
    // Database access for temporal validation
    DatabaseConnection* getDatabaseConnection() const;
    
    // Static helper methods
    static std::string getCurrentDate();
    static bool isValidDateFormat(const std::string& date);
    static std::string formatDate(const std::string& date);
};

