#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>

#include "position.h"

// Default constructor
Position::Position() : symbol_(""), shares_(0), average_price_(0.0) {}

// Parameterized constructor
Position::Position(const std::string& symbol, int shares, double price) 
    : symbol_(symbol), shares_(shares), average_price_(price) {
    if (shares < 0) {
        throw std::invalid_argument("Shares cannot be negative");
    }
    if (price < 0) {
        throw std::invalid_argument("Price cannot be negative");
    }
}

// Copy constructor
Position::Position(const Position& other) 
    : symbol_(other.symbol_), 
      shares_(other.shares_), 
      average_price_(other.average_price_) {}

// Copy assignment operator
Position& Position::operator=(const Position& other) {
    if (this != &other) {
        symbol_ = other.symbol_;
        shares_ = other.shares_;
        average_price_ = other.average_price_;
    }
    return *this;
}

// Move constructor
Position::Position(Position&& other) noexcept 
    : symbol_(std::move(other.symbol_)), 
      shares_(other.shares_), 
      average_price_(other.average_price_) {
    // Reset the moved-from object
    other.shares_ = 0;
    other.average_price_ = 0.0;
}

// Move assignment operator
Position& Position::operator=(Position&& other) noexcept {
    if (this != &other) {
        symbol_ = std::move(other.symbol_);
        shares_ = other.shares_;
        average_price_ = other.average_price_;
        
        // Reset the moved-from object
        other.shares_ = 0;
        other.average_price_ = 0.0;
    }
    return *this;
}

// Getters
std::string Position::getSymbol() const {
    return symbol_;
}

int Position::getShares() const {
    return shares_;
}

double Position::getAveragePrice() const {
    return average_price_;
}

double Position::getCurrentValue(double current_price) const {
    return shares_ * current_price;
}

double Position::getUnrealizedPnL(double current_price) const {
    return (current_price - average_price_) * shares_;
}

double Position::getTotalCost() const {
    return shares_ * average_price_;
}

// Position management
void Position::buyShares(int shares, double price) {
    if (shares <= 0) {
        throw std::invalid_argument("Cannot buy zero or negative shares");
    }
    if (price < 0) {
        throw std::invalid_argument("Price cannot be negative");
    }
    
    // Calculate new average price using weighted average
    double total_cost = getTotalCost() + (shares * price);
    int total_shares = shares_ + shares;
    
    if (total_shares > 0) {
        average_price_ = total_cost / total_shares;
    }
    
    shares_ = total_shares;
}

void Position::sellShares(int shares, double price) {
    if (shares <= 0) {
        throw std::invalid_argument("Cannot sell zero or negative shares");
    }
    if (price < 0) {
        throw std::invalid_argument("Price cannot be negative");
    }
    if (!canSell(shares)) {
        throw std::invalid_argument("Cannot sell more shares than owned");
    }
    
    shares_ -= shares;
    
    // If all shares sold, reset average price
    if (shares_ == 0) {
        average_price_ = 0.0;
    }
    // Note: We keep the same average price for remaining shares
}

bool Position::canSell(int shares) const {
    return shares <= shares_ && shares > 0;
}

// Utility
bool Position::isEmpty() const {
    return shares_ == 0;
}

std::string Position::toString() const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2);
    oss << symbol_ << ": " << shares_ << " shares @ $" << average_price_ 
        << " (Total: $" << getTotalCost() << ")";
    return oss.str();
}