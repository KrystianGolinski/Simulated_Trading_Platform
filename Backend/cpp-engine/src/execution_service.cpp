#include <map>

#include "error_utils.h"
#include "execution_service.h"
#include "logger.h"

Result<void> ExecutionService::executeSignal(const TradingSignal& signal, 
                                            const std::string& symbol, 
                                            Portfolio& portfolio,
                                            TradingStrategy* strategy) {
    Logger::debug("ExecutionService::executeSignal called: ", 
                 (signal.signal == Signal::BUY ? "BUY" : "SELL"), 
                 " symbol=", symbol, " confidence=", signal.confidence);
    
    // Validate the signal first
    auto validation_result = validateSignal(signal, symbol);
    if (validation_result.isError()) {
        failed_executions_counter_++;
        Logger::warning("ExecutionService: Signal validation failed: ", validation_result.getErrorMessage());
        return validation_result;
    }
    
    Result<void> execution_result;
    
    if (signal.signal == Signal::BUY) {
        execution_result = executeBuySignal(signal, symbol, portfolio, strategy);
    } else if (signal.signal == Signal::SELL) {
        execution_result = executeSellSignal(signal, symbol, portfolio);
    } else {
        return Result<void>(ErrorCode::EXECUTION_INVALID_SIGNAL_TYPE,
                           "Invalid signal type for execution: " + std::to_string(static_cast<int>(signal.signal)));
    }
    
    if (execution_result.isSuccess()) {
        executed_signals_.push_back(signal);
        Logger::debug("ExecutionService: Signal executed successfully");
    } else {
        failed_executions_counter_++;
        Logger::debug("ExecutionService: Signal execution failed: ", execution_result.getErrorMessage());
    }
    
    return execution_result;
}

Result<void> ExecutionService::executeBuySignal(const TradingSignal& signal, 
                                               const std::string& symbol, 
                                               Portfolio& portfolio,
                                               TradingStrategy* strategy) {
    // Allow position increases - can buy regardless of existing position
    bool has_position = portfolio.hasPosition(symbol);
    int current_shares = has_position ? portfolio.getPosition(symbol).getShares() : 0;
    
    Logger::debug("BUY signal - has_position=", has_position, " current_shares=", current_shares);
    
    // Calculate portfolio value for position sizing
    std::map<std::string, double> current_prices;
    current_prices[symbol] = signal.price;
    double portfolio_value = portfolio.getTotalValue(current_prices);
    
    double position_size = 0.0;
    if (strategy) {
        position_size = strategy->calculatePositionSize(portfolio, symbol, signal.price, portfolio_value);
    } else {
        // Fallback position sizing if no strategy provided
        double available_cash = portfolio.getCashBalance();
        position_size = std::min(available_cash * 0.1, available_cash) / signal.price;
    }
    
    Logger::debug("BUY order: cash=", portfolio.getCashBalance(), 
                 " portfolio_value=", portfolio_value, " position_size=", position_size, 
                 " price=", signal.price);
    
    if (position_size <= 0) {
        return Result<void>(ErrorCode::EXECUTION_INSUFFICIENT_FUNDS,
                           "Calculated position size is zero or negative. Available cash: " + 
                           std::to_string(portfolio.getCashBalance()) + ", Price: " + std::to_string(signal.price));
    }
    
    bool success = portfolio.buyStock(symbol, static_cast<int>(position_size), signal.price);
    
    if (!success) {
        return Result<void>(ErrorCode::EXECUTION_ORDER_FAILED,
                           "Buy order failed for " + symbol + ". Shares: " + 
                           std::to_string(static_cast<int>(position_size)) + ", Price: " + std::to_string(signal.price));
    }
    
    Logger::debug("Buy order SUCCESS");
    return Result<void>();
}

Result<void> ExecutionService::executeSellSignal(const TradingSignal& signal, 
                                                const std::string& symbol, 
                                                Portfolio& portfolio) {
    // Only sell if we have a position
    bool has_position = portfolio.hasPosition(symbol);
    int shares_owned = has_position ? portfolio.getPosition(symbol).getShares() : 0;
    
    Logger::debug("SELL signal - has_position=", has_position, " shares_owned=", shares_owned);
    
    if (!has_position || shares_owned <= 0) {
        return Result<void>(ErrorCode::EXECUTION_NO_POSITION,
                           "Cannot sell " + symbol + ": no position or zero shares owned. Shares: " + 
                           std::to_string(shares_owned));
    }
    
    Logger::debug("SELL order: shares_owned=", shares_owned, " price=", signal.price);
    
    bool success = portfolio.sellStock(symbol, shares_owned, signal.price);
    
    if (!success) {
        return Result<void>(ErrorCode::EXECUTION_ORDER_FAILED,
                           "Sell order failed for " + symbol + ". Shares: " + 
                           std::to_string(shares_owned) + ", Price: " + std::to_string(signal.price));
    }
    
    Logger::debug("Sell order SUCCESS");
    return Result<void>();
}

Result<void> ExecutionService::validateSignal(const TradingSignal& signal, const std::string& symbol) const {
    if (symbol.empty()) {
        return Result<void>(ErrorCode::EXECUTION_INVALID_SYMBOL,
                           "Empty symbol provided for signal execution");
    }
    
    if (signal.signal == Signal::HOLD) {
        return Result<void>(ErrorCode::EXECUTION_HOLD_SIGNAL,
                           "HOLD signal does not require execution");
    }
    
    if (signal.price <= 0.0) {
        return Result<void>(ErrorCode::EXECUTION_INVALID_PRICE,
                           "Invalid signal price: " + std::to_string(signal.price));
    }
    
    if (signal.date.empty()) {
        return Result<void>(ErrorCode::EXECUTION_INVALID_DATE,
                           "Signal date cannot be empty");
    }
    
    return Result<void>();
}

std::vector<TradingSignal> ExecutionService::getExecutedSignals() const {
    return executed_signals_;
}

void ExecutionService::clearExecutedSignals() {
    executed_signals_.clear();
    failed_executions_counter_ = 0;
}

void ExecutionService::addExecutedSignal(const TradingSignal& signal) {
    executed_signals_.push_back(signal);
}

int ExecutionService::getTotalExecutions() const {
    return static_cast<int>(executed_signals_.size()) + failed_executions_counter_;
}

int ExecutionService::getSuccessfulExecutions() const {
    // All signals in executed_signals_ are successful by definition
    return static_cast<int>(executed_signals_.size());
}

int ExecutionService::getFailedExecutions() const {
    return failed_executions_counter_;
}

// Memory optimization methods
void ExecutionService::optimizeMemory() {
    // Shrink executed signals vector to fit current size
    executed_signals_.shrink_to_fit();
}

size_t ExecutionService::getMemoryUsage() const {
    size_t total = sizeof(*this);
    // Calculate memory usage of executed signals vector
    total += executed_signals_.capacity() * sizeof(TradingSignal);
    return total;
}

std::string ExecutionService::getMemoryReport() const {
    std::ostringstream report;
    report << "ExecutionService Memory Usage:\n";
    report << "  Executed signals: " << executed_signals_.size() << "\n";
    report << "  Vector capacity: " << executed_signals_.capacity() << "\n";
    report << "  Memory overhead: " << (executed_signals_.capacity() - executed_signals_.size()) * sizeof(TradingSignal) << " bytes\n";
    report << "  Total estimated memory: " << getMemoryUsage() << " bytes\n";
    return report.str();
}
