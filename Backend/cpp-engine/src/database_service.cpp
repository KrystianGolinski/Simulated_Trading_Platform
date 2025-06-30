#include "database_service.h"
#include "logger.h"
#include "error_utils.h"

Result<std::vector<std::map<std::string, std::string>>> DatabaseService::getHistoricalPrices(
    const std::string& symbol, 
    const std::string& start_date, 
    const std::string& end_date) {
    
    Logger::debug("DatabaseService::getHistoricalPrices called for symbol=", symbol, 
                 " from ", start_date, " to ", end_date);
    
    auto result = market_data_.getHistoricalPrices(symbol, start_date, end_date);
    if (result.isError()) {
        Logger::error("Error in DatabaseService::getHistoricalPrices: ", result.getErrorMessage());
    }
    return result;
}

Result<std::map<std::string, double>> DatabaseService::getCurrentPrices() {
    Logger::debug("DatabaseService::getCurrentPrices called");
    
    auto result = market_data_.getCurrentPrices();
    if (result.isError()) {
        Logger::error("Error in DatabaseService::getCurrentPrices: ", result.getErrorMessage());
    }
    return result;
}

Result<bool> DatabaseService::isConnectionHealthy() const {
    // Simple health check by attempting to test database connection
    auto result = market_data_.testDatabaseConnection();
    if (result.isError()) {
        return Result<bool>(false);
    }
    return Result<bool>(true);
}