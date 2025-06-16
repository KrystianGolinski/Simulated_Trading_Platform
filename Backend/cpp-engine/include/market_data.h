#ifndef MARKET_DATA_H
#define MARKET_DATA_H

#include <string>
#include <map>
#include <vector>
#include <memory>
#include <nlohmann/json.hpp>
#include "database_connection.h"

/**
 * Represents a single price data point
 */
struct PriceData {
    std::string date;
    std::string symbol;
    double open;
    double high;
    double low;
    double close;
    long volume;
    
    // Default constructor
    PriceData() : open(0.0), high(0.0), low(0.0), close(0.0), volume(0) {}
    
    // Constructor from database row
    PriceData(const std::map<std::string, std::string>& row);
    
    // JSON conversion
    nlohmann::json toJson() const;
};

/**
 * MarketData class handles historical price data access from PostgreSQL/TimescaleDB.
 * Provides methods to fetch stock prices for specific date ranges and symbols.
 */
class MarketData {
private:
    std::unique_ptr<DatabaseConnection> db_connection_;
    mutable std::map<std::string, double> price_cache_;
    bool cache_enabled_;
    
    // Helper methods
    bool ensureConnection() const;
    void cachePrice(const std::string& symbol, double price) const;
    double getCachedPrice(const std::string& symbol) const;
    
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
    double getPrice(const std::string& symbol) const;
    double getLatestPrice(const std::string& symbol) const;
    std::map<std::string, double> getCurrentPrices() const;
    std::map<std::string, double> getCurrentPrices(const std::vector<std::string>& symbols) const;
    
    // Historical data access
    std::vector<PriceData> getHistoricalPrices(
        const std::string& symbol,
        const std::string& start_date,
        const std::string& end_date
    ) const;
    
    std::map<std::string, std::vector<PriceData>> getHistoricalPrices(
        const std::vector<std::string>& symbols,
        const std::string& start_date,
        const std::string& end_date
    ) const;
    
    // Date range utilities
    std::vector<PriceData> getPricesForDateRange(
        const std::string& symbol,
        const std::string& start_date,
        const std::string& end_date
    ) const;
    
    PriceData getPriceForDate(const std::string& symbol, const std::string& date) const;
    
    // Symbol validation and discovery
    bool symbolExists(const std::string& symbol) const;
    std::vector<std::string> getAvailableSymbols() const;
    
    // Data validation and statistics
    int getDataPointCount(const std::string& symbol, 
                         const std::string& start_date, 
                         const std::string& end_date) const;
    
    std::pair<std::string, std::string> getDateRange(const std::string& symbol) const;
    
    // Utility methods
    void clearCache();
    nlohmann::json getDataSummary(const std::string& symbol,
                                 const std::string& start_date,
                                 const std::string& end_date) const;
    
    // Test methods
    bool testDatabaseConnection() const;
    nlohmann::json getDatabaseInfo() const;
    
    // Static helper methods
    static std::string getCurrentDate();
    static bool isValidDateFormat(const std::string& date);
    static std::string formatDate(const std::string& date);
};

#endif // MARKET_DATA_H