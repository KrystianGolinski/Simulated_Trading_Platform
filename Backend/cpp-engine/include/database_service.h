#pragma once

#include "market_data.h"
#include "result.h"
#include <string>
#include <vector>
#include <map>

class DatabaseService {
private:
    MarketData market_data_;
    
public:
    DatabaseService() = default;
    ~DatabaseService() = default;
    
    // Non-copyable but movable
    DatabaseService(const DatabaseService&) = delete;
    DatabaseService& operator=(const DatabaseService&) = delete;
    DatabaseService(DatabaseService&&) = default;
    DatabaseService& operator=(DatabaseService&&) = default;
    
    // Market data operations
    Result<std::vector<std::map<std::string, std::string>>> getHistoricalPrices(
        const std::string& symbol, 
        const std::string& start_date, 
        const std::string& end_date
    );
    
    Result<std::map<std::string, double>> getCurrentPrices();
    
    // Database health check
    Result<bool> isConnectionHealthy() const;
    
};