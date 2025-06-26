#include "portfolio.h"
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <utility>

// Constructors
Portfolio::Portfolio() : cash_balance_(0.0), initial_capital_(0.0) {}

Portfolio::Portfolio(double initial_cash) : cash_balance_(initial_cash), initial_capital_(initial_cash) {
    if (initial_cash < 0) {
        throw std::invalid_argument("Initial cash cannot be negative");
    }
}

// Copy constructor
Portfolio::Portfolio(const Portfolio& other) 
    : positions_(other.positions_),
      cash_balance_(other.cash_balance_),
      initial_capital_(other.initial_capital_) {}

// Copy assignment operator
Portfolio& Portfolio::operator=(const Portfolio& other) {
    if (this != &other) {
        positions_ = other.positions_;
        cash_balance_ = other.cash_balance_;
        initial_capital_ = other.initial_capital_;
    }
    return *this;
}

// Move constructor
Portfolio::Portfolio(Portfolio&& other) noexcept 
    : positions_(std::move(other.positions_)),
      cash_balance_(other.cash_balance_),
      initial_capital_(other.initial_capital_) {
    // Reset the moved-from object
    other.cash_balance_ = 0.0;
    other.initial_capital_ = 0.0;
}

// Move assignment operator
Portfolio& Portfolio::operator=(Portfolio&& other) noexcept {
    if (this != &other) {
        positions_ = std::move(other.positions_);
        cash_balance_ = other.cash_balance_;
        initial_capital_ = other.initial_capital_;
        
        // Reset the moved-from object
        other.cash_balance_ = 0.0;
        other.initial_capital_ = 0.0;
    }
    return *this;
}

// Cash management
double Portfolio::getCashBalance() const {
    return cash_balance_;
}

double Portfolio::getInitialCapital() const {
    return initial_capital_;
}

void Portfolio::addCash(double amount) {
    cash_balance_ += amount;
}

bool Portfolio::canAfford(double cost) const {
    return cash_balance_ >= cost;
}

void Portfolio::reset() {
    positions_.clear();
    cash_balance_ = initial_capital_;
}

// Position management
bool Portfolio::hasPosition(const std::string& symbol) const {
    auto it = positions_.find(symbol);
    return it != positions_.end() && !it->second.isEmpty();
}

Position Portfolio::getPosition(const std::string& symbol) const {
    auto it = positions_.find(symbol);
    if (it != positions_.end()) {
        return it->second;
    }
    return Position(); // Return empty position if not found
}


std::vector<std::string> Portfolio::getSymbols() const {
    std::vector<std::string> symbols;
    for (const auto& pair : positions_) {
        if (!pair.second.isEmpty()) {
            symbols.push_back(pair.first);
        }
    }
    return symbols;
}

int Portfolio::getPositionCount() const {
    int count = 0;
    for (const auto& pair : positions_) {
        if (!pair.second.isEmpty()) {
            count++;
        }
    }
    return count;
}

// Trading operations
bool Portfolio::buyStock(const std::string& symbol, int shares, double price) {
    if (shares <= 0) {
        return false;
    }
    if (price < 0) {
        return false;
    }
    
    double total_cost = shares * price;
    if (!canAfford(total_cost)) {
        return false;
    }
    
    // Deduct cash
    cash_balance_ -= total_cost;
    
    // Add to position
    auto it = positions_.find(symbol);
    if (it != positions_.end()) {
        it->second.buyShares(shares, price);
    } else {
        positions_[symbol] = Position(symbol, shares, price);
    }
    
    return true;
}

bool Portfolio::sellStock(const std::string& symbol, int shares, double price) {
    if (shares <= 0) {
        return false;
    }
    if (price < 0) {
        return false;
    }
    
    auto it = positions_.find(symbol);
    if (it == positions_.end() || !it->second.canSell(shares)) {
        return false;
    }
    
    // Add cash from sale
    double proceeds = shares * price;
    cash_balance_ += proceeds;
    
    // Sell shares
    it->second.sellShares(shares, price);
    
    return true;
}

bool Portfolio::sellAllStock(const std::string& symbol, double price) {
    auto it = positions_.find(symbol);
    if (it == positions_.end() || it->second.isEmpty()) {
        return false;
    }
    
    int shares_to_sell = it->second.getShares();
    return sellStock(symbol, shares_to_sell, price);
}

// Portfolio value calculations
double Portfolio::getTotalValue(const std::map<std::string, double>& current_prices) const {
    return cash_balance_ + getTotalStockValue(current_prices);
}

double Portfolio::getTotalStockValue(const std::map<std::string, double>& current_prices) const {
    double total_value = 0.0;
    
    for (const auto& pair : positions_) {
        if (!pair.second.isEmpty()) {
            const std::string& symbol = pair.first;
            const Position& position = pair.second;
            
            auto price_it = current_prices.find(symbol);
            if (price_it != current_prices.end()) {
                total_value += position.getCurrentValue(price_it->second);
            }
        }
    }
    
    return total_value;
}

double Portfolio::getTotalUnrealizedPnL(const std::map<std::string, double>& current_prices) const {
    double total_pnl = 0.0;
    
    for (const auto& pair : positions_) {
        if (!pair.second.isEmpty()) {
            const std::string& symbol = pair.first;
            const Position& position = pair.second;
            
            auto price_it = current_prices.find(symbol);
            if (price_it != current_prices.end()) {
                total_pnl += position.getUnrealizedPnL(price_it->second);
            }
        }
    }
    
    return total_pnl;
}

double Portfolio::getTotalReturnPercentage(const std::map<std::string, double>& current_prices) const {
    if (initial_capital_ <= 0) {
        return 0.0;
    }
    
    double current_value = getTotalValue(current_prices);
    return ((current_value - initial_capital_) / initial_capital_) * 100.0;
}

void Portfolio::updateValue(const std::map<std::string, double>& current_prices) {
    // This method can be used to update internal state with current market values
    // For now, it's a placeholder for future functionality like position rebalancing
    // or portfolio optimization based on current prices
    // The actual value calculations are handled by the getter methods
}

// Utility
std::string Portfolio::toString() const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2);
    oss << "Portfolio: $" << cash_balance_ << " cash, " << getPositionCount() << " positions";
    return oss.str();
}

std::string Portfolio::toDetailedString(const std::map<std::string, double>& current_prices) const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2);
    
    oss << "Portfolio Details\n";
    oss << "Cash Balance: $" << cash_balance_ << "\n";
    oss << "Initial Capital: $" << initial_capital_ << "\n";
    oss << "Total Value: $" << getTotalValue(current_prices) << "\n";
    oss << "Total Return: " << getTotalReturnPercentage(current_prices) << "%\n\n";
    
    oss << "Positions:\n";
    for (const auto& pair : positions_) {
        if (!pair.second.isEmpty()) {
            const std::string& symbol = pair.first;
            const Position& position = pair.second;
            
            auto price_it = current_prices.find(symbol);
            double current_price = price_it != current_prices.end() ? price_it->second : 0.0;
            
            oss << "  " << position.toString();
            if (current_price > 0) {
                oss << " | Current: $" << current_price 
                    << " | Value: $" << position.getCurrentValue(current_price)
                    << " | P&L: $" << position.getUnrealizedPnL(current_price);
            }
            oss << "\n";
        }
    }
    
    return oss.str();
}