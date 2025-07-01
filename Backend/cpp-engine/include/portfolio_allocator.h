#pragma once

#include "portfolio.h"
#include "trading_strategy.h"
#include "result.h"
#include <string>
#include <vector>
#include <map>

// Portfolio allocation strategies for multi-symbol portfolios
enum class AllocationStrategy {
    EQUAL_WEIGHT,           // Equal allocation across all symbols
    MARKET_CAP_WEIGHT,      // Allocation based on market capitalisation (future)
    VOLATILITY_ADJUSTED,    // Allocation inversely proportional to volatility
    MOMENTUM_BASED,         // Allocation based on recent performance
    RISK_PARITY,            // Equal risk contribution from each position
    CUSTOM                  // User-defined allocation percentages
};

// Configuration for portfolio allocation
struct AllocationConfig {
    AllocationStrategy strategy;                    // Primary allocation strategy
    std::map<std::string, double> custom_weights;   // Custom allocation weights (sum should = 1.0)
    double max_position_weight;                     // Maximum weight per symbol (e.g., 0.3 = 30%)
    double min_position_weight;                     // Minimum weight per symbol (e.g., 0.05 = 5%)
    bool enable_rebalancing;                        // Enable periodic rebalancing
    double rebalancing_threshold;                   // Trigger rebalancing when allocation drifts by this %
    int rebalancing_frequency_days;                 // Rebalance every N days
    double cash_reserve_pct;                        // Percentage to keep as cash (e.g., 0.05 = 5%)
    
    // Risk management
    double max_sector_concentration;                // Maximum allocation to single sector
    double correlation_limit;                       // Maximum correlation between symbols
    bool enable_momentum_filtering;                 // Filter symbols based on momentum
    
    AllocationConfig() : strategy(AllocationStrategy::EQUAL_WEIGHT), 
                        max_position_weight(0.3), min_position_weight(0.05),
                        enable_rebalancing(true), rebalancing_threshold(0.05),
                        rebalancing_frequency_days(30), cash_reserve_pct(0.05),
                        max_sector_concentration(0.4), correlation_limit(0.8),
                        enable_momentum_filtering(false) {}
};

// Result of portfolio allocation calculation
struct AllocationResult {
    std::map<std::string, double> target_weights;    // Target allocation percentages per symbol
    std::map<std::string, double> target_values;     // Target dollar amounts per symbol
    std::map<std::string, int> target_shares;        // Target number of shares per symbol
    double total_allocated_capital;                  // Total capital to be allocated
    double cash_reserved;                            // Cash to keep in reserve
    bool rebalancing_needed;                         // Whether rebalancing is recommended
    std::vector<std::string> excluded_symbols;       // Symbols excluded from allocation
    std::string allocation_reason;                   // Reason for allocation decisions
    
    AllocationResult() : total_allocated_capital(0.0), cash_reserved(0.0), 
                        rebalancing_needed(false) {}
};

class PortfolioAllocator {
private:
    AllocationConfig config_;
    std::map<std::string, std::vector<double>> price_history_;  // For volatility/momentum calculations
    std::map<std::string, double> last_rebalance_weights_;      // Last rebalancing allocation
    std::string last_rebalance_date_;                           // Date of last rebalancing
    std::map<std::string, double> current_target_weights_;      // Current target allocation weights
    double initial_capital_;                                    // Initial capital for allocation-based position sizing
    
public:
    explicit PortfolioAllocator(const AllocationConfig& config = AllocationConfig());
    
    // Main allocation methods
    Result<AllocationResult> calculateAllocation(
        const std::vector<std::string>& symbols,
        double total_capital,
        const Portfolio& current_portfolio,
        const std::map<std::string, double>& current_prices,
        const std::string& current_date = ""
    );
    
    // Strategy-specific allocation methods
    AllocationResult calculateEqualWeightAllocation(
        const std::vector<std::string>& symbols,
        double total_capital
    );
    
    AllocationResult calculateVolatilityAdjustedAllocation(
        const std::vector<std::string>& symbols,
        double total_capital,
        const std::map<std::string, double>& current_prices
    );
    
    AllocationResult calculateMomentumBasedAllocation(
        const std::vector<std::string>& symbols,
        double total_capital,
        const std::map<std::string, double>& current_prices
    );
    
    AllocationResult calculateRiskParityAllocation(
        const std::vector<std::string>& symbols,
        double total_capital,
        const std::map<std::string, double>& current_prices
    );
    
    // Rebalancing logic
    bool shouldRebalance(
        const Portfolio& current_portfolio,
        const std::map<std::string, double>& current_prices,
        const std::string& current_date
    );
    
    Result<AllocationResult> calculateRebalancing(
        const Portfolio& current_portfolio,
        const std::map<std::string, double>& current_prices,
        double total_portfolio_value
    );
    
    // Position sizing for individual trades
    Result<double> calculatePositionSize(
        const std::string& symbol,
        const Portfolio& portfolio,
        double stock_price,
        double portfolio_value,
        Signal signal_type,
        const std::map<std::string, double>& target_weights = {},
        double initial_capital = 0.0
    );
    
    // Configuration and data management
    void updateConfig(const AllocationConfig& config);
    void updatePriceHistory(const std::string& symbol, const std::vector<double>& prices);
    void updatePriceHistory(const std::map<std::string, std::vector<double>>& all_prices);
    void setTargetAllocation(const std::map<std::string, double>& target_weights, double initial_capital);
    
    // Analytics and reporting
    double calculateAllocationDrift(
        const Portfolio& current_portfolio,
        const std::map<std::string, double>& current_prices
    );
    
    std::map<std::string, double> getCurrentWeights(
        const Portfolio& portfolio,
        const std::map<std::string, double>& current_prices
    );
    
    AllocationConfig getConfig() const { return config_; }
    
private:
    // Helper methods for calculations
    double calculateVolatility(const std::vector<double>& prices) const;
    double calculateMomentum(const std::vector<double>& prices) const;
    double calculateCorrelation(const std::vector<double>& prices1, const std::vector<double>& prices2) const;
    std::vector<std::string> applyRiskFilters(const std::vector<std::string>& symbols, const std::map<std::string, double>& current_prices) const;
    void enforceConstraints(AllocationResult& result) const;
    bool isRebalancingDue(const std::string& current_date) const;
};