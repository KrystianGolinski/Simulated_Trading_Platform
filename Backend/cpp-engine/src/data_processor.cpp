#include "data_processor.h"
#include "data_conversion.h"
#include "logger.h"
#include <algorithm>
#include <set>

Result<std::vector<PriceData>> DataProcessor::loadHistoricalData(const std::string& symbol, const DateRange& range) {
    // TODO: This would typically interface with MarketData but for now is a placeholder
    // Implementation would be similar to single symbol processing in processSymbolData
    return Result<std::vector<PriceData>>(ErrorCode::SYSTEM_UNEXPECTED_ERROR, "Not implemented in this refactor");
}

Result<std::map<std::string, std::vector<PriceData>>> DataProcessor::loadMultiSymbolData(
    const std::vector<std::string>& symbols,
    const std::string& start_date,
    const std::string& end_date,
    MarketData* market_data) {
    
    Logger::debug("Getting historical price data for ", symbols.size(), " symbols:");
    
    std::map<std::string, std::vector<PriceData>> multi_symbol_data;
    std::vector<std::string> failed_symbols;
    
    // Fetch data for each symbol
    for (const auto& symbol : symbols) {
        Logger::debug("Fetching data for symbol: ", symbol);
        
        auto symbol_result = processSymbolData(symbol, start_date, end_date, market_data);
        
        if (symbol_result.isError()) {
            Logger::debug("Failed to process data for symbol ", symbol, ": ", symbol_result.getErrorMessage());
            failed_symbols.push_back(symbol);
            continue;
        }
        
        const auto& price_data = symbol_result.getValue();
        if (price_data.empty()) {
            Logger::debug("No data available for symbol ", symbol, " in date range ", start_date, " to ", end_date);
            failed_symbols.push_back(symbol);
            continue;
        }
        
        multi_symbol_data[symbol] = price_data;
        Logger::debug("Successfully loaded ", price_data.size(), " data points for ", symbol);
    }
    
    // Check if we have data for at least one symbol
    if (multi_symbol_data.empty()) {
        std::string error_msg = "No data available for any of the requested symbols: ";
        for (size_t i = 0; i < symbols.size(); ++i) {
            error_msg += symbols[i];
            if (i < symbols.size() - 1) error_msg += ", ";
        }
        
        return Result<std::map<std::string, std::vector<PriceData>>>(
            ErrorCode::ENGINE_NO_DATA_AVAILABLE, error_msg);
    }
    
    // Log summary of data retrieval
    logDataSummary(multi_symbol_data, failed_symbols, symbols);
    
    // Validate data consistency
    auto validation_result = validateDataConsistency(multi_symbol_data);
    if (validation_result.isError()) {
        return Result<std::map<std::string, std::vector<PriceData>>>(validation_result.getError());
    }
    
    return Result<std::map<std::string, std::vector<PriceData>>>(std::move(multi_symbol_data));
}

std::vector<PriceData> DataProcessor::getWindow(const std::string& symbol, int windowSize) {
    // TODO: Placeholder for windowing logic - would maintain internal state
    // This would return the last N data points for a symbol
    return std::vector<PriceData>();
}

void DataProcessor::updateHistoricalWindows(
    const std::map<std::string, std::vector<PriceData>>& multi_symbol_data,
    const std::string& current_date,
    const std::map<std::string, std::map<std::string, size_t>>& symbol_date_indices,
    std::map<std::string, std::vector<PriceData>>& historical_windows,
    std::map<std::string, double>& current_prices) {
    
    // Update current prices and historical data for each symbol
    for (const auto& [symbol, data] : multi_symbol_data) {
        auto symbol_indices_it = symbol_date_indices.find(symbol);
        if (symbol_indices_it == symbol_date_indices.end()) {
            continue;
        }
        
        auto date_it = symbol_indices_it->second.find(current_date);
        if (date_it != symbol_indices_it->second.end()) {
            // This symbol has data for current date
            const auto& price_point = data[date_it->second];
            current_prices[symbol] = price_point.close;
            historical_windows[symbol].push_back(price_point);
        }
        // If symbol doesn't have data for this date, keep previous price
    }
}

Result<void> DataProcessor::validateDataConsistency(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data) {
    std::string earliest_date, latest_date;
    size_t min_data_points, max_data_points;
    
    calculateDataRange(multi_symbol_data, earliest_date, latest_date, min_data_points, max_data_points);
    
    Logger::debug("Data range validation:");
    Logger::debug("  Earliest date: ", earliest_date);
    Logger::debug("  Latest date: ", latest_date);
    Logger::debug("  Min data points: ", min_data_points);
    Logger::debug("  Max data points: ", max_data_points);
    
    validateDataRange(min_data_points, max_data_points);
    
    return Result<void>(); // Success
}

void DataProcessor::logDataSummary(
    const std::map<std::string, std::vector<PriceData>>& multi_symbol_data,
    const std::vector<std::string>& failed_symbols,
    const std::vector<std::string>& requested_symbols) {
    
    Logger::debug("Successfully loaded data for ", multi_symbol_data.size(), " out of ", requested_symbols.size(), " symbols");
    if (!failed_symbols.empty()) {
        Logger::debug("Failed to load data for symbols: ");
        for (size_t i = 0; i < failed_symbols.size(); ++i) {
            Logger::debug("  - ", failed_symbols[i]);
        }
    }
}

std::vector<PriceData> DataProcessor::convertToTechnicalData(const std::vector<std::map<std::string, std::string>>& db_data) const {
    return DataConversion::convertToTechnicalData(db_data);
}

std::vector<std::string> DataProcessor::createUnifiedTimeline(const std::map<std::string, std::vector<PriceData>>& multi_symbol_data) {
    // Create unified timeline by merging all symbol dates
    std::set<std::string> all_dates;
    for (const auto& [symbol, data] : multi_symbol_data) {
        for (const auto& price_point : data) {
            all_dates.insert(price_point.date);
        }
    }
    
    // Convert to sorted vector for chronological processing
    std::vector<std::string> timeline(all_dates.begin(), all_dates.end());
    Logger::debug("Created unified timeline with ", timeline.size(), " trading days");
    if (!timeline.empty()) {
        Logger::debug("Date range: ", timeline.front(), " to ", timeline.back());
    }
    
    return timeline;
}

std::map<std::string, std::map<std::string, size_t>> DataProcessor::createDateIndices(
    const std::map<std::string, std::vector<PriceData>>& multi_symbol_data) {
    
    // Create symbol-to-data-index mappings for efficient lookups
    std::map<std::string, std::map<std::string, size_t>> symbol_date_indices;
    for (const auto& [symbol, data] : multi_symbol_data) {
        for (size_t i = 0; i < data.size(); ++i) {
            symbol_date_indices[symbol][data[i].date] = i;
        }
        Logger::debug("Indexed ", data.size(), " data points for ", symbol);
    }
    
    return symbol_date_indices;
}

std::string DataProcessor::createDataErrorMessage(
    const std::string& symbol,
    const std::string& start_date,
    const std::string& end_date,
    const std::string& error_type) const {
    
    if (error_type == "no_data") {
        return "No historical price data available for symbol " + symbol + " in date range " + start_date + " to " + end_date;
    } else if (error_type == "conversion_failed") {
        return "Failed to convert price data for symbol " + symbol;
    }
    return "Data error for symbol " + symbol;
}

void DataProcessor::calculateDataRange(
    const std::map<std::string, std::vector<PriceData>>& multi_symbol_data,
    std::string& earliest_date,
    std::string& latest_date,
    size_t& min_data_points,
    size_t& max_data_points) const {
    
    min_data_points = SIZE_MAX;
    max_data_points = 0;
    earliest_date.clear();
    latest_date.clear();
    
    for (const auto& [symbol, data] : multi_symbol_data) {
        if (!data.empty()) {
            if (earliest_date.empty() || data.front().date < earliest_date) {
                earliest_date = data.front().date;
            }
            if (latest_date.empty() || data.back().date > latest_date) {
                latest_date = data.back().date;
            }
            min_data_points = std::min(min_data_points, data.size());
            max_data_points = std::max(max_data_points, data.size());
        }
    }
}

void DataProcessor::validateDataRange(size_t min_data_points, size_t max_data_points) const {
    // Warn if there are significant differences in data availability between symbols
    if (max_data_points > min_data_points * 1.1) {
        Logger::debug("Significant variation in data availability between symbols");
        Logger::debug("This may cause issues during multi-symbol simulation");
    }
}

Result<std::vector<PriceData>> DataProcessor::processSymbolData(
    const std::string& symbol,
    const std::string& start_date,
    const std::string& end_date,
    MarketData* market_data) const {
    
    auto symbol_result = market_data->getHistoricalPrices(symbol, start_date, end_date);
    
    if (symbol_result.isError()) {
        return Result<std::vector<PriceData>>(symbol_result.getError());
    }
    
    const auto& price_data_raw = symbol_result.getValue();
    if (price_data_raw.empty()) {
        std::string error_msg = createDataErrorMessage(symbol, start_date, end_date, "no_data");
        return Result<std::vector<PriceData>>(ErrorCode::ENGINE_NO_DATA_AVAILABLE, error_msg);
    }
    
    try {
        auto price_data = convertToTechnicalData(price_data_raw);
        if (price_data.empty()) {
            std::string error_msg = createDataErrorMessage(symbol, start_date, end_date, "conversion_failed");
            return Result<std::vector<PriceData>>(ErrorCode::DATA_PARSING_FAILED, error_msg);
        }
        
        return Result<std::vector<PriceData>>(std::move(price_data));
        
    } catch (const std::exception& e) {
        Logger::error("Error converting price data for ", symbol, ": ", e.what());
        std::string error_msg = createDataErrorMessage(symbol, start_date, end_date, "conversion_failed");
        return Result<std::vector<PriceData>>(ErrorCode::DATA_PARSING_FAILED, error_msg);
    }
}