#pragma once

#include <map>
#include <string>
#include <vector>

#include "market_data.h"
#include "memory_optimizable.h"
#include "result.h"
#include "trading_strategy.h"

// Helper struct for date range operations
struct DateRange {
    std::string start_date;
    std::string end_date;
    
    DateRange() = default;
    DateRange(const std::string& start, const std::string& end) 
        : start_date(start), end_date(end) {}
};

// Data processing and windowing for backtesting
class DataProcessor : public IMemoryOptimizable {
public:
    DataProcessor() = default;
    ~DataProcessor() = default;
    
    // Delete copy constructor and assignment operator to prevent copying
    DataProcessor(const DataProcessor&) = delete;
    DataProcessor& operator=(const DataProcessor&) = delete;
    
    // Allow move constructor and assignment
    DataProcessor(DataProcessor&&) = default;
    DataProcessor& operator=(DataProcessor&&) = default;
    
    // Data loading and preprocessing
    Result<std::vector<PriceData>> loadHistoricalData(const std::string& symbol, const DateRange& range);
    Result<std::map<std::string, std::vector<PriceData>>> loadMultiSymbolData(const std::vector<std::string>& symbols, 
                                                                              const std::string& start_date, 
                                                                              const std::string& end_date,
                                                                              MarketData* market_data);
    
    // Rolling window management
    std::vector<PriceData> getWindow(const std::string& symbol, int windowSize);
    void updateHistoricalWindows(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data,
                                const std::string& current_date,
                                const std::map<std::string, std::map<std::string, size_t>>& symbol_date_indices,
                                std::map<std::string, std::vector<PriceData>>& historical_windows,
                                std::map<std::string, double>& current_prices);
    
    // Data validation
    Result<void> validateDataConsistency(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data);
    void logDataSummary(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data,
                       const std::vector<std::string>& failed_symbols,
                       const std::vector<std::string>& requested_symbols);
    
    // Data conversion utilities
    std::vector<PriceData> convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data) const;
    
    // Timeline and indexing utilities
    std::vector<std::string> createUnifiedTimeline(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data);
    std::map<std::string, std::map<std::string, size_t>> createDateIndices(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data);
    
    // Memory optimization interface
    void optimizeMemory() override;
    size_t getMemoryUsage() const override;
    std::string getMemoryReport() const override;

private:
    // Helper methods for data processing
    std::string createDataErrorMessage(const std::string& symbol, 
                                      const std::string& start_date, 
                                      const std::string& end_date, 
                                      const std::string& error_type) const;
    
    // Data range validation helpers
    void calculateDataRange(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data,
                           std::string& earliest_date, 
                           std::string& latest_date,
                           size_t& min_data_points, 
                           size_t& max_data_points) const;
    
    void validateDataRange(size_t min_data_points, size_t max_data_points) const;
    
    // Data processing for individual symbols
    Result<std::vector<PriceData>> processSymbolData(const std::string& symbol,
                                                    const std::string& start_date,
                                                    const std::string& end_date,
                                                    MarketData* market_data) const;
};