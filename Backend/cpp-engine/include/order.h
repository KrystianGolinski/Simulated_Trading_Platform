#pragma once

#include <string>

/**
 * Order class represents a buy or sell instruction for a stock.
 * Used by trading strategies to communicate trading decisions.
 */
enum class OrderType {
    BUY,
    SELL
};

enum class OrderStatus {
    PENDING,
    FILLED,
    REJECTED,
    CANCELLED
};

class Order {
private:
    std::string symbol_;
    OrderType type_;
    int shares_;
    double price_;
    OrderStatus status_;
    std::string timestamp_;
    std::string reject_reason_;
    
public:
    // Constructors
    Order();
    Order(const std::string& symbol, OrderType type, int shares, double price);
    
    // Copy constructor and assignment (Rule of Five)
    Order(const Order& other);
    Order& operator=(const Order& other);
    
    // Move constructor and assignment
    Order(Order&& other) noexcept;
    Order& operator=(Order&& other) noexcept;
    
    // Getters
    std::string getSymbol() const;
    OrderType getType() const;
    int getShares() const;
    double getPrice() const;
    OrderStatus getStatus() const;
    std::string getTimestamp() const;
    std::string getRejectReason() const;
    double getTotalValue() const;
    
    // Setters
    void setStatus(OrderStatus status);
    void setRejectReason(const std::string& reason);
    void setTimestamp(const std::string& timestamp);
    
    // Utility
    bool isBuyOrder() const;
    bool isSellOrder() const;
    bool isPending() const;
    bool isFilled() const;
    bool isRejected() const;
    std::string getTypeString() const;
    std::string getStatusString() const;
    std::string toString() const;
    
    // Validation
    bool isValid() const;
};