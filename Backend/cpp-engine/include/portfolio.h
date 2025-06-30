#pragma once

#include "position.h"
#include <map>
#include <vector>
#include <string>

/**
 * Portfolio class manages a collection of stock positions and cash balance.
 * Handles buying/selling operations and portfolio value calculations.
 */
class Portfolio {
private:
    std::map<std::string, Position> positions_;
    double cash_balance_;
    double initial_capital_;
    
public:
    // Constructors
    Portfolio();
    explicit Portfolio(double initial_cash);
    
    // Copy constructor and assignment (Rule of Five)
    Portfolio(const Portfolio& other);
    Portfolio& operator=(const Portfolio& other);
    
    // Move constructor and assignment
    Portfolio(Portfolio&& other) noexcept;
    Portfolio& operator=(Portfolio&& other) noexcept;
    
    // Cash management
    double getCashBalance() const;
    double getInitialCapital() const;
    void addCash(double amount);
    bool canAfford(double cost) const;
    void reset(); // Reset portfolio to initial state
    
    // Position management
    bool hasPosition(const std::string& symbol) const;
    Position getPosition(const std::string& symbol) const;
    std::vector<std::string> getSymbols() const;
    int getPositionCount() const;
    
    // Trading operations
    bool buyStock(const std::string& symbol, int shares, double price);
    bool sellStock(const std::string& symbol, int shares, double price);
    bool sellAllStock(const std::string& symbol, double price);
    
    // Portfolio value calculations
    double getTotalValue(const std::map<std::string, double>& current_prices) const;
    double getTotalStockValue(const std::map<std::string, double>& current_prices) const;
    double getTotalUnrealizedPnL(const std::map<std::string, double>& current_prices) const;
    double getTotalReturnPercentage(const std::map<std::string, double>& current_prices) const;
    
    // Utility
    std::string toString() const;
    std::string toDetailedString(const std::map<std::string, double>& current_prices) const;
};