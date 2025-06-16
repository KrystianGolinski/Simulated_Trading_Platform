#ifndef TRADING_ENGINE_H
#define TRADING_ENGINE_H

#include "portfolio.h"
#include "market_data.h"
#include <string>

/**
 * TradingEngine class will coordinate the simulation in later phases.
 * For now, this is a placeholder to satisfy compilation.
 */
class TradingEngine {
private:
    Portfolio portfolio_;
    MarketData market_data_;
    
public:
    TradingEngine();
    explicit TradingEngine(double initial_capital);
    
    // Placeholder methods - will be implemented in later phases
    std::string runSimulation();
    std::string getPortfolioStatus();
    Portfolio& getPortfolio();
    const Portfolio& getPortfolio() const;
};

#endif // TRADING_ENGINE_H