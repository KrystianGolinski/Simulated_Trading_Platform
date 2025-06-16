#ifndef MARKET_DATA_H
#define MARKET_DATA_H

#include <string>
#include <map>

/**
 * MarketData class will handle price data access in Phase 2.
 * For now, this is a placeholder to satisfy compilation.
 */
class MarketData {
public:
    MarketData();
    
    // Placeholder methods - will be implemented in Phase 2
    double getPrice(const std::string& symbol) const;
    std::map<std::string, double> getCurrentPrices() const;
};

#endif // MARKET_DATA_H