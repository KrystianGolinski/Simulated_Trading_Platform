#include "market_data.h"

// Placeholder implementation - will be completed in Phase 2
MarketData::MarketData() {}

double MarketData::getPrice(const std::string& symbol) const {
    // Placeholder: return mock price for testing
    if (symbol == "AAPL") return 150.0;
    if (symbol == "MSFT") return 300.0;
    if (symbol == "GOOGL") return 2500.0;
    return 100.0; // Default price
}

std::map<std::string, double> MarketData::getCurrentPrices() const {
    // Placeholder: return mock prices for testing
    return {
        {"AAPL", 150.0},
        {"MSFT", 300.0},
        {"GOOGL", 2500.0},
        {"AMZN", 3200.0},
        {"TSLA", 800.0}
    };
}