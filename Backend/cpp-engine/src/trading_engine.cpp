#include "trading_engine.h"
#include <sstream>

// Constructors
TradingEngine::TradingEngine() : portfolio_(10000.0) {} // Default $10,000

TradingEngine::TradingEngine(double initial_capital) : portfolio_(initial_capital) {}

// Placeholder methods
std::string TradingEngine::runSimulation() {
    // Phase 1: Simple simulation with mock trading
    std::ostringstream oss;
    
    // Execute some mock trades
    bool trade1 = portfolio_.buyStock("AAPL", 10, market_data_.getPrice("AAPL"));
    bool trade2 = portfolio_.buyStock("MSFT", 5, market_data_.getPrice("MSFT"));
    
    auto current_prices = market_data_.getCurrentPrices();
    
    // Count successful trades
    int total_trades = (trade1 ? 1 : 0) + (trade2 ? 1 : 0);
    
    oss << "{\n";
    oss << "  \"simulation_id\": \"test_sim_1\",\n";
    oss << "  \"starting_capital\": " << portfolio_.getInitialCapital() << ",\n";
    oss << "  \"final_portfolio_value\": " << portfolio_.getTotalValue(current_prices) << ",\n";
    oss << "  \"total_return_percentage\": " << portfolio_.getTotalReturnPercentage(current_prices) << ",\n";
    oss << "  \"total_trades\": " << total_trades << ",\n";
    oss << "  \"winning_trades\": 1,\n";
    oss << "  \"losing_trades\": " << (total_trades - 1) << ",\n";
    oss << "  \"equity_curve\": [\n";
    oss << "    {\"date\": \"2024-01-01\", \"value\": " << portfolio_.getInitialCapital() << "},\n";
    oss << "    {\"date\": \"2024-06-01\", \"value\": " << portfolio_.getTotalValue(current_prices) << "},\n";
    oss << "    {\"date\": \"2024-12-31\", \"value\": " << portfolio_.getTotalValue(current_prices) << "}\n";
    oss << "  ],\n";
    oss << "  \"config\": {\n";
    oss << "    \"start_date\": \"2024-01-01\",\n";
    oss << "    \"end_date\": \"2024-12-31\",\n";
    oss << "    \"selected_stocks\": [\"AAPL\", \"MSFT\"],\n";
    oss << "    \"short_ma_period\": 20,\n";
    oss << "    \"long_ma_period\": 50\n";
    oss << "  },\n";
    oss << "  \"status\": \"completed\"\n";
    oss << "}";
    
    return oss.str();
}

std::string TradingEngine::getPortfolioStatus() {
    auto current_prices = market_data_.getCurrentPrices();
    return portfolio_.toDetailedString(current_prices);
}

Portfolio& TradingEngine::getPortfolio() {
    return portfolio_;
}

const Portfolio& TradingEngine::getPortfolio() const {
    return portfolio_;
}