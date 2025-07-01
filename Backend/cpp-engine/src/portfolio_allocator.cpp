#include "portfolio_allocator.h"
#include "logger.h"
#include "trading_exceptions.h"
#include <algorithm>
#include <cmath>
#include <numeric>

PortfolioAllocator::PortfolioAllocator(const AllocationConfig& config) : config_(config), initial_capital_(0.0) {
    Logger::debug("PortfolioAllocator initialized with strategy: ", static_cast<int>(config_.strategy));
}

Result<AllocationResult> PortfolioAllocator::calculateAllocation(
    const std::vector<std::string>& symbols,
    double total_capital,
    const Portfolio& current_portfolio,
    const std::map<std::string, double>& current_prices,
    const std::string& current_date
) {
    Logger::debug("Calculating portfolio allocation for ", symbols.size(), " symbols with capital: $", total_capital);
    
    if (symbols.empty()) {
        return Result<AllocationResult>(ErrorCode::ENGINE_INVALID_SYMBOL, "No symbols provided for allocation");
    }
    
    if (total_capital <= 0) {
        return Result<AllocationResult>(ErrorCode::EXECUTION_INSUFFICIENT_FUNDS, "Total capital must be positive");
    }
    
    // Apply risk filters to exclude problematic symbols
    std::vector<std::string> filtered_symbols = applyRiskFilters(symbols, current_prices);
    
    if (filtered_symbols.empty()) {
        return Result<AllocationResult>(ErrorCode::ENGINE_INVALID_SYMBOL, 
                                       "All symbols filtered out by risk management");
    }
    
    AllocationResult result;
    
    // Calculate allocation based on selected strategy
    switch (config_.strategy) {
        case AllocationStrategy::EQUAL_WEIGHT:
            result = calculateEqualWeightAllocation(filtered_symbols, total_capital);
            break;
            
        case AllocationStrategy::VOLATILITY_ADJUSTED:
            result = calculateVolatilityAdjustedAllocation(filtered_symbols, total_capital, current_prices);
            break;
            
        case AllocationStrategy::MOMENTUM_BASED:
            result = calculateMomentumBasedAllocation(filtered_symbols, total_capital, current_prices);
            break;
            
        case AllocationStrategy::RISK_PARITY:
            result = calculateRiskParityAllocation(filtered_symbols, total_capital, current_prices);
            break;
            
        case AllocationStrategy::CUSTOM:
            if (config_.custom_weights.empty()) {
                Logger::debug("Custom allocation strategy selected but no custom weights provided, falling back to equal weight");
                result = calculateEqualWeightAllocation(filtered_symbols, total_capital);
            } else {
                result = calculateEqualWeightAllocation(filtered_symbols, total_capital); // TODO: Implement custom allocation
            }
            break;
            
        default:
            result = calculateEqualWeightAllocation(filtered_symbols, total_capital);
            break;
    }
    
    // Apply allocation constraints and limits
    enforceConstraints(result);
    
    // Calculate target share counts based on current prices
    for (const auto& [symbol, target_value] : result.target_values) {
        auto price_it = current_prices.find(symbol);
        if (price_it != current_prices.end() && price_it->second > 0) {
            result.target_shares[symbol] = static_cast<int>(std::floor(target_value / price_it->second));
        }
    }
    
    // Check if rebalancing is needed
    if (config_.enable_rebalancing && !current_date.empty()) {
        result.rebalancing_needed = shouldRebalance(current_portfolio, current_prices, current_date);
    }
    
    // Store excluded symbols
    for (const auto& symbol : symbols) {
        if (std::find(filtered_symbols.begin(), filtered_symbols.end(), symbol) == filtered_symbols.end()) {
            result.excluded_symbols.push_back(symbol);
        }
    }
    
    Logger::debug("Portfolio allocation completed. Allocated: $", result.total_allocated_capital, 
                 ", Reserved: $", result.cash_reserved, ", Symbols: ", result.target_weights.size());
    
    return Result<AllocationResult>(result);
}

AllocationResult PortfolioAllocator::calculateEqualWeightAllocation(
    const std::vector<std::string>& symbols,
    double total_capital
) {
    AllocationResult result;
    result.allocation_reason = "Equal weight allocation across " + std::to_string(symbols.size()) + " symbols";
    
    // Reserve cash according to configuration
    result.cash_reserved = total_capital * config_.cash_reserve_pct;
    result.total_allocated_capital = total_capital - result.cash_reserved;
    
    // Calculate equal weight for each symbol
    double weight_per_symbol = 1.0 / symbols.size();
    double value_per_symbol = result.total_allocated_capital * weight_per_symbol;
    
    for (const auto& symbol : symbols) {
        result.target_weights[symbol] = weight_per_symbol;
        result.target_values[symbol] = value_per_symbol;
    }
    
    Logger::debug("Equal weight allocation: ", weight_per_symbol * 100, "% per symbol, $", 
                 value_per_symbol, " per symbol");
    
    return result;
}

AllocationResult PortfolioAllocator::calculateVolatilityAdjustedAllocation(
    const std::vector<std::string>& symbols,
    double total_capital,
    const std::map<std::string, double>& current_prices
) {
    AllocationResult result;
    result.allocation_reason = "Volatility-adjusted allocation (inverse volatility weighting)";
    
    // Reserve cash
    result.cash_reserved = total_capital * config_.cash_reserve_pct;
    result.total_allocated_capital = total_capital - result.cash_reserved;
    
    // Calculate volatility for each symbol
    std::map<std::string, double> volatilities;
    double total_inverse_vol = 0.0;
    
    for (const auto& symbol : symbols) {
        double volatility = 0.15; // Default volatility if no price history available
        
        auto price_hist_it = price_history_.find(symbol);
        if (price_hist_it != price_history_.end() && price_hist_it->second.size() > 1) {
            volatility = calculateVolatility(price_hist_it->second);
            volatility = std::max(volatility, 0.01); // Minimum volatility to avoid division by zero
        }
        
        volatilities[symbol] = volatility;
        total_inverse_vol += 1.0 / volatility;
    }
    
    // Calculate weights inversely proportional to volatility
    for (const auto& symbol : symbols) {
        double inverse_vol = 1.0 / volatilities[symbol];
        double weight = inverse_vol / total_inverse_vol;
        double value = result.total_allocated_capital * weight;
        
        result.target_weights[symbol] = weight;
        result.target_values[symbol] = value;
        
        Logger::debug("Symbol ", symbol, ": volatility=", volatilities[symbol] * 100, 
                     "%, weight=", weight * 100, "%, value=$", value);
    }
    
    return result;
}

AllocationResult PortfolioAllocator::calculateMomentumBasedAllocation(
    const std::vector<std::string>& symbols,
    double total_capital,
    const std::map<std::string, double>& current_prices
) {
    AllocationResult result;
    result.allocation_reason = "Momentum-based allocation (higher allocation to trending symbols)";
    
    // Reserve cash
    result.cash_reserved = total_capital * config_.cash_reserve_pct;
    result.total_allocated_capital = total_capital - result.cash_reserved;
    
    // Calculate momentum for each symbol
    std::map<std::string, double> momentum_scores;
    double total_positive_momentum = 0.0;
    
    for (const auto& symbol : symbols) {
        double momentum = 0.0; // Default neutral momentum
        
        auto price_hist_it = price_history_.find(symbol);
        if (price_hist_it != price_history_.end() && price_hist_it->second.size() > 1) {
            momentum = calculateMomentum(price_hist_it->second);
        }
        
        // Use only positive momentum for allocation (negative momentum gets minimum allocation)
        double positive_momentum = std::max(momentum, 0.1); // Minimum momentum score
        momentum_scores[symbol] = positive_momentum;
        total_positive_momentum += positive_momentum;
    }
    
    // Calculate weights proportional to positive momentum
    for (const auto& symbol : symbols) {
        double weight = momentum_scores[symbol] / total_positive_momentum;
        double value = result.total_allocated_capital * weight;
        
        result.target_weights[symbol] = weight;
        result.target_values[symbol] = value;
        
        Logger::debug("Symbol ", symbol, ": momentum=", momentum_scores[symbol], 
                     ", weight=", weight * 100, "%, value=$", value);
    }
    
    return result;
}

AllocationResult PortfolioAllocator::calculateRiskParityAllocation(
    const std::vector<std::string>& symbols,
    double total_capital,
    const std::map<std::string, double>& current_prices
) {
    AllocationResult result;
    result.allocation_reason = "Risk parity allocation (equal risk contribution per symbol)";
    
    // Reserve cash
    result.cash_reserved = total_capital * config_.cash_reserve_pct;
    result.total_allocated_capital = total_capital - result.cash_reserved;
    
    // For simplicity, approximate risk parity using inverse volatility weighting
    // A more sophisticated implementation would use optimisation to achieve equal risk contribution
    
    std::map<std::string, double> volatilities;
    double total_inverse_vol = 0.0;
    
    for (const auto& symbol : symbols) {
        double volatility = 0.15; // Default volatility
        
        auto price_hist_it = price_history_.find(symbol);
        if (price_hist_it != price_history_.end() && price_hist_it->second.size() > 1) {
            volatility = calculateVolatility(price_hist_it->second);
            volatility = std::max(volatility, 0.01);
        }
        
        volatilities[symbol] = volatility;
        total_inverse_vol += 1.0 / volatility;
    }
    
    // Calculate weights for approximately equal risk contribution
    for (const auto& symbol : symbols) {
        double inverse_vol = 1.0 / volatilities[symbol];
        double weight = inverse_vol / total_inverse_vol;
        double value = result.total_allocated_capital * weight;
        
        result.target_weights[symbol] = weight;
        result.target_values[symbol] = value;
        
        Logger::debug("Symbol ", symbol, ": risk-adjusted weight=", weight * 100, "%, value=$", value);
    }
    
    return result;
}

bool PortfolioAllocator::shouldRebalance(
    const Portfolio& current_portfolio,
    const std::map<std::string, double>& current_prices,
    const std::string& current_date
) {
    // Check if rebalancing frequency has passed
    if (isRebalancingDue(current_date)) {
        Logger::debug("Rebalancing due to time frequency");
        return true;
    }
    
    // Check if allocation drift exceeds threshold
    double allocation_drift = calculateAllocationDrift(current_portfolio, current_prices);
    if (allocation_drift > config_.rebalancing_threshold) {
        Logger::debug("Rebalancing due to allocation drift: ", allocation_drift * 100, "%");
        return true;
    }
    
    return false;
}

Result<AllocationResult> PortfolioAllocator::calculateRebalancing(
    const Portfolio& current_portfolio,
    const std::map<std::string, double>& current_prices,
    double total_portfolio_value
) {
    Logger::debug("Calculating portfolio rebalancing for total value: $", total_portfolio_value);
    
    // Get current symbols from portfolio
    std::vector<std::string> current_symbols = current_portfolio.getSymbols();
    
    if (current_symbols.empty()) {
        return Result<AllocationResult>(ErrorCode::ENGINE_INVALID_SYMBOL, "No symbols in current portfolio for rebalancing");
    }
    
    // Calculate target allocation for current symbols
    auto target_allocation_result = calculateAllocation(current_symbols, total_portfolio_value, current_portfolio, current_prices);
    
    if (target_allocation_result.isError()) {
        return target_allocation_result;
    }
    
    auto target_allocation = target_allocation_result.getValue();
    target_allocation.allocation_reason = "Rebalancing to target allocation";
    target_allocation.rebalancing_needed = true;
    
    // Store this as the new target allocation for drift calculation
    last_rebalance_weights_ = target_allocation.target_weights;
    
    Logger::debug("Rebalancing calculation completed for ", current_symbols.size(), " symbols");
    
    return Result<AllocationResult>(target_allocation);
}

Result<double> PortfolioAllocator::calculatePositionSize(
    const std::string& symbol,
    const Portfolio& portfolio,
    double stock_price,
    double portfolio_value,
    Signal signal_type,
    const std::map<std::string, double>& target_weights,
    double initial_capital
) {
    if (stock_price <= 0 || portfolio_value <= 0) {
        return Result<double>(ErrorCode::EXECUTION_INVALID_PRICE, "Invalid price or portfolio value");
    }
    
    // Use provided target weights and initial capital, or fall back to stored values
    std::map<std::string, double> weights = target_weights.empty() ? current_target_weights_ : target_weights;
    double capital = (initial_capital > 0) ? initial_capital : initial_capital_;
    
    // Calculate current position value
    double current_position_value = 0.0;
    if (portfolio.hasPosition(symbol)) {
        const Position& position = portfolio.getPosition(symbol);
        current_position_value = position.getShares() * stock_price;
    }
    
    // For buy signals, use allocation-based position sizing
    if (signal_type == Signal::BUY) {
        // Find target weight for this symbol
        auto weight_it = weights.find(symbol);
        if (weight_it == weights.end()) {
            Logger::debug("No target weight found for ", symbol, ", using equal weight fallback");
            // Fallback: assume equal weight allocation
            double fallback_weight = 1.0 / std::max(1.0, static_cast<double>(weights.size()));
            weights[symbol] = fallback_weight;
            weight_it = weights.find(symbol);
        }
        
        double target_weight = weight_it->second;
        
        // INITIAL CAPITAL-RELATIVE POSITION SIZING: Scale with initial capital to prevent compounding trade sizes
        
        // Calculate maximum allowed position value as percentage of INITIAL portfolio value
        double max_position_pct = 0.06; // 6% of initial portfolio maximum
        double max_allowed_position_value = initial_capital_ * max_position_pct;
        
        // If current position already exceeds limit, don't add more
        if (current_position_value >= max_allowed_position_value) {
            Logger::debug("Position for ", symbol, " already at maximum relative size: current=$", 
                         current_position_value, ", max allowed=$", max_allowed_position_value);
            return Result<double>(0.0);
        }
        
        // Trade size: small percentage of initial capital to keep trades balanced
        double trade_size_pct = 0.008; // 0.8% of initial capital per trade
        double trade_amount = initial_capital_ * trade_size_pct;
        
        // Ensure minimum trade size but cap at remaining position capacity
        trade_amount = std::max(trade_amount, 100.0); // Minimum $100 trade
        double remaining_capacity = max_allowed_position_value - current_position_value;
        trade_amount = std::min(trade_amount, remaining_capacity);
        
        // Convert to shares
        double max_shares = std::floor(trade_amount / stock_price);
        
        // Ensure we have sufficient cash
        if (portfolio.getCashBalance() < trade_amount) {
            return Result<double>(0.0); // Not enough cash
        }
        
        Logger::debug("Initial capital-relative position sizing for ", symbol, ":");
        Logger::debug("  Target weight: ", target_weight * 100, "% of initial capital ($", capital, ")");
        Logger::debug("  Current position value: $", current_position_value);
        Logger::debug("  Max allowed position: $", max_allowed_position_value);
        Logger::debug("  Trade amount: $", trade_amount);
        Logger::debug("  Current position value: $", current_position_value);
        Logger::debug("  Additional shares needed: ", max_shares);
        
        return Result<double>(std::max(0.0, max_shares));
    }
    
    // For sell signals, sell incrementally to avoid large single trades
    if (signal_type == Signal::SELL) {
        if (!portfolio.hasPosition(symbol)) {
            return Result<double>(0.0); // No position to sell
        }
        
        const Position& position = portfolio.getPosition(symbol);
        
        // PORTFOLIO-RELATIVE SELLING: Match the buy approach for consistency
        double trade_size_pct = 0.008; // 0.8% of current portfolio per trade (matches buy)
        double sell_amount = portfolio_value * trade_size_pct;
        sell_amount = std::max(sell_amount, 100.0); // Minimum $100 sell
        
        double sell_shares_by_value = std::floor(sell_amount / stock_price);
        
        // Also limit to reasonable percentage of position
        double max_percentage_shares = std::floor(position.getShares() * 0.3); // 30% max
        
        // Use the smaller constraint
        double shares_to_sell = std::min(sell_shares_by_value, max_percentage_shares);
        
        // Ensure minimum meaningful trade
        if (shares_to_sell * stock_price < 50.0) { // Minimum $50 sell
            shares_to_sell = 0;
        }
        
        Logger::debug("Fixed dollar position reduction for ", symbol, ": selling ", shares_to_sell, " shares ($", 
                     shares_to_sell * stock_price, " value)");
        
        return Result<double>(shares_to_sell);
    }
    
    return Result<double>(0.0);
}

// Helper methods implementation
double PortfolioAllocator::calculateVolatility(const std::vector<double>& prices) const {
    if (prices.size() < 2) return 0.15; // Default volatility
    
    // Calculate daily returns
    std::vector<double> returns;
    for (size_t i = 1; i < prices.size(); ++i) {
        if (prices[i-1] > 0) {
            double return_rate = (prices[i] - prices[i-1]) / prices[i-1];
            returns.push_back(return_rate);
        }
    }
    
    if (returns.empty()) return 0.15;
    
    // Calculate standard deviation of returns
    double mean = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    double variance = 0.0;
    
    for (double ret : returns) {
        variance += (ret - mean) * (ret - mean);
    }
    variance /= returns.size();
    
    double volatility = std::sqrt(variance) * std::sqrt(252); // Annualized volatility
    return volatility;
}

double PortfolioAllocator::calculateMomentum(const std::vector<double>& prices) const {
    if (prices.size() < 2) return 0.0;
    
    // Simple momentum: total return over the period
    double momentum = (prices.back() - prices.front()) / prices.front();
    return momentum;
}

std::vector<std::string> PortfolioAllocator::applyRiskFilters(
    const std::vector<std::string>& symbols, 
    const std::map<std::string, double>& current_prices
) const {
    std::vector<std::string> filtered_symbols;
    
    for (const auto& symbol : symbols) {
        // Basic filter: symbol must have a valid current price
        auto price_it = current_prices.find(symbol);
        if (price_it != current_prices.end() && price_it->second > 0) {
            filtered_symbols.push_back(symbol);
        } else {
            Logger::debug("Filtering out symbol ", symbol, " due to invalid price");
        }
    }
    
    return filtered_symbols;
}

void PortfolioAllocator::enforceConstraints(AllocationResult& result) const {
    // Ensure no position exceeds maximum weight
    for (auto& [symbol, weight] : result.target_weights) {
        if (weight > config_.max_position_weight) {
            Logger::debug("Constraining ", symbol, " weight from ", weight * 100, "% to ", 
                         config_.max_position_weight * 100, "%");
            weight = config_.max_position_weight;
        }
        
        if (weight < config_.min_position_weight && weight > 0) {
            Logger::debug("Increasing ", symbol, " weight from ", weight * 100, "% to minimum ", 
                         config_.min_position_weight * 100, "%");
            weight = config_.min_position_weight;
        }
    }
    
    // Renormalise weights to sum to 1.0
    double total_weight = 0.0;
    for (const auto& [symbol, weight] : result.target_weights) {
        total_weight += weight;
    }
    
    if (total_weight > 0 && std::abs(total_weight - 1.0) > 0.01) {
        Logger::debug("Renormalising weights from total: ", total_weight, " to 1.0");
        for (auto& [symbol, weight] : result.target_weights) {
            weight /= total_weight;
            result.target_values[symbol] = result.total_allocated_capital * weight;
        }
    }
}

double PortfolioAllocator::calculateAllocationDrift(
    const Portfolio& current_portfolio,
    const std::map<std::string, double>& current_prices
) {
    auto current_weights = getCurrentWeights(current_portfolio, current_prices);
    
    double max_drift = 0.0;
    for (const auto& [symbol, current_weight] : current_weights) {
        auto target_it = last_rebalance_weights_.find(symbol);
        if (target_it != last_rebalance_weights_.end()) {
            double drift = std::abs(current_weight - target_it->second);
            max_drift = std::max(max_drift, drift);
        }
    }
    
    return max_drift;
}

std::map<std::string, double> PortfolioAllocator::getCurrentWeights(
    const Portfolio& portfolio,
    const std::map<std::string, double>& current_prices
) {
    std::map<std::string, double> weights;
    double total_value = portfolio.getTotalValue(current_prices);
    
    if (total_value <= 0) return weights;
    
    for (const auto& symbol : portfolio.getSymbols()) {
        if (portfolio.hasPosition(symbol)) {
            const Position& position = portfolio.getPosition(symbol);
            auto price_it = current_prices.find(symbol);
            if (price_it != current_prices.end()) {
                double position_value = position.getShares() * price_it->second;
                weights[symbol] = position_value / total_value;
            }
        }
    }
    
    return weights;
}

void PortfolioAllocator::setTargetAllocation(const std::map<std::string, double>& target_weights, double initial_capital) {
    current_target_weights_ = target_weights;
    initial_capital_ = initial_capital;
    
    Logger::debug("Updated target allocation with ", target_weights.size(), " symbols and initial capital: $", initial_capital);
    for (const auto& [symbol, weight] : target_weights) {
        Logger::debug("  ", symbol, ": ", weight * 100, "%");
    }
}

bool PortfolioAllocator::isRebalancingDue(const std::string& current_date) const {
    // Simple date comparison - in production, would use proper date parsing
    if (last_rebalance_date_.empty()) return true;
    
    // For now, assume rebalancing is due every time (simplification)
    return false;
}

void PortfolioAllocator::updateConfig(const AllocationConfig& config) {
    config_ = config;
    Logger::debug("PortfolioAllocator configuration updated");
}

void PortfolioAllocator::updatePriceHistory(const std::string& symbol, const std::vector<double>& prices) {
    price_history_[symbol] = prices;
    Logger::debug("Updated price history for ", symbol, " with ", prices.size(), " data points");
}

void PortfolioAllocator::updatePriceHistory(const std::map<std::string, std::vector<double>>& all_prices) {
    for (const auto& [symbol, prices] : all_prices) {
        price_history_[symbol] = prices;
    }
    Logger::debug("Updated price history for ", all_prices.size(), " symbols");
}