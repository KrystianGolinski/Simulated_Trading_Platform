#pragma once

#include <string>

/**
 * Position class represents ownership of shares in a single stock.
 * Tracks the number of shares owned and calculates values based on current price.
 */
class Position {
public:
    // Constructors
    Position();
    Position(const std::string& symbol, int shares, double price);
    
    // Copy constructor and assignment (Rule of Five)
    Position(const Position& other);
    Position& operator=(const Position& other);
    
    // Move constructor and assignment
    Position(Position&& other) noexcept;
    Position& operator=(Position&& other) noexcept;
    
    // Getters
    std::string getSymbol() const;
    int getShares() const;
    double getAveragePrice() const;
    double getCurrentValue(double current_price) const;
    double getUnrealizedPnL(double current_price) const;
    double getTotalCost() const;
    
    // Position management
    void buyShares(int shares, double price);
    void sellShares(int shares, double price);
    bool canSell(int shares) const;
    
    // Utility
    bool isEmpty() const;
    std::string toString() const;

private:
    std::string symbol_;
    int shares_;
    double average_price_;
};