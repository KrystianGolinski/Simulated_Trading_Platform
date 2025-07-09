#include <iomanip>
#include <sstream>
#include <utility>

#include "order.h"

// Constructors
Order::Order() : symbol_(""), type_(OrderType::BUY), shares_(0), price_(0.0), 
                 status_(OrderStatus::PENDING), timestamp_(""), reject_reason_("") {}

Order::Order(const std::string& symbol, OrderType type, int shares, double price)
    : symbol_(symbol), type_(type), shares_(shares), price_(price), 
      status_(OrderStatus::PENDING), timestamp_(""), reject_reason_("") {}

// Copy constructor
Order::Order(const Order& other) 
    : symbol_(other.symbol_),
      type_(other.type_),
      shares_(other.shares_),
      price_(other.price_),
      status_(other.status_),
      timestamp_(other.timestamp_),
      reject_reason_(other.reject_reason_) {}

// Copy assignment operator
Order& Order::operator=(const Order& other) {
    if (this != &other) {
        symbol_ = other.symbol_;
        type_ = other.type_;
        shares_ = other.shares_;
        price_ = other.price_;
        status_ = other.status_;
        timestamp_ = other.timestamp_;
        reject_reason_ = other.reject_reason_;
    }
    return *this;
}

// Move constructor
Order::Order(Order&& other) noexcept 
    : symbol_(std::move(other.symbol_)),
      type_(other.type_),
      shares_(other.shares_),
      price_(other.price_),
      status_(other.status_),
      timestamp_(std::move(other.timestamp_)),
      reject_reason_(std::move(other.reject_reason_)) {
    // Reset the moved-from object
    other.type_ = OrderType::BUY;
    other.shares_ = 0;
    other.price_ = 0.0;
    other.status_ = OrderStatus::PENDING;
}

// Move assignment operator
Order& Order::operator=(Order&& other) noexcept {
    if (this != &other) {
        symbol_ = std::move(other.symbol_);
        type_ = other.type_;
        shares_ = other.shares_;
        price_ = other.price_;
        status_ = other.status_;
        timestamp_ = std::move(other.timestamp_);
        reject_reason_ = std::move(other.reject_reason_);
        
        // Reset the moved-from object
        other.type_ = OrderType::BUY;
        other.shares_ = 0;
        other.price_ = 0.0;
        other.status_ = OrderStatus::PENDING;
    }
    return *this;
}

// Getters
std::string Order::getSymbol() const {
    return symbol_;
}

OrderType Order::getType() const {
    return type_;
}

int Order::getShares() const {
    return shares_;
}

double Order::getPrice() const {
    return price_;
}

OrderStatus Order::getStatus() const {
    return status_;
}

std::string Order::getTimestamp() const {
    return timestamp_;
}

std::string Order::getRejectReason() const {
    return reject_reason_;
}

double Order::getTotalValue() const {
    return shares_ * price_;
}

// Setters
void Order::setStatus(OrderStatus status) {
    status_ = status;
}

void Order::setRejectReason(const std::string& reason) {
    reject_reason_ = reason;
    status_ = OrderStatus::REJECTED;
}

void Order::setTimestamp(const std::string& timestamp) {
    timestamp_ = timestamp;
}

// Utility
bool Order::isBuyOrder() const {
    return type_ == OrderType::BUY;
}

bool Order::isSellOrder() const {
    return type_ == OrderType::SELL;
}

bool Order::isPending() const {
    return status_ == OrderStatus::PENDING;
}

bool Order::isFilled() const {
    return status_ == OrderStatus::FILLED;
}

bool Order::isRejected() const {
    return status_ == OrderStatus::REJECTED;
}

std::string Order::getTypeString() const {
    switch (type_) {
        case OrderType::BUY: return "BUY";
        case OrderType::SELL: return "SELL";
        default: return "UNKNOWN";
    }
}

std::string Order::getStatusString() const {
    switch (status_) {
        case OrderStatus::PENDING: return "PENDING";
        case OrderStatus::FILLED: return "FILLED";
        case OrderStatus::REJECTED: return "REJECTED";
        case OrderStatus::CANCELLED: return "CANCELLED";
        default: return "UNKNOWN";
    }
}

std::string Order::toString() const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2);
    oss << getTypeString() << " " << shares_ << " shares of " << symbol_ 
        << " @ $" << price_ << " (Total: $" << getTotalValue() << ") "
        << "[" << getStatusString() << "]";
    
    if (!timestamp_.empty()) {
        oss << " at " << timestamp_;
    }
    
    if (isRejected() && !reject_reason_.empty()) {
        oss << " - Reason: " << reject_reason_;
    }
    
    return oss.str();
}

// Validation
bool Order::isValid() const {
    if (symbol_.empty()) return false;
    if (shares_ <= 0) return false;
    if (price_ < 0) return false;
    return true;
}