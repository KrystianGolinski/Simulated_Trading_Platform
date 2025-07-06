#pragma once

#include "trading_strategy.h"
#include "portfolio.h"
#include <vector>
#include <map>

// Structs for organized metrics
struct PerformanceMetrics {
    double total_return_pct;
    double sharpe_ratio;
    double max_drawdown_pct;
    double win_rate;
    int total_trades;
    double final_balance;
    double annualized_return;
    double volatility;
    double profit_factor;
    double average_win;
    double average_loss;
    
    PerformanceMetrics() : total_return_pct(0.0), sharpe_ratio(0.0), max_drawdown_pct(0.0),
                          win_rate(0.0), total_trades(0), final_balance(0.0), 
                          annualized_return(0.0), volatility(0.0), profit_factor(0.0),
                          average_win(0.0), average_loss(0.0) {}
};

struct RiskMetrics {
    double max_drawdown;
    double sharpe_ratio;
    double volatility;
    double value_at_risk;
    double expected_shortfall;
    
    RiskMetrics() : max_drawdown(0.0), sharpe_ratio(0.0), volatility(0.0),
                   value_at_risk(0.0), expected_shortfall(0.0) {}
};

// Performance metrics calculation for backtesting results
class ResultCalculator {
public:
    ResultCalculator() = default;
    ~ResultCalculator() = default;
    
    // Delete copy constructor and assignment operator to prevent copying
    ResultCalculator(const ResultCalculator&) = delete;
    ResultCalculator& operator=(const ResultCalculator&) = delete;
    
    // Allow move constructor and assignment
    ResultCalculator(ResultCalculator&&) = default;
    ResultCalculator& operator=(ResultCalculator&&) = default;
    
    // Main calculation methods
    void calculateTradeMetrics(BacktestResult& result);
    void calculatePortfolioMetrics(BacktestResult& result, const Portfolio& portfolio);
    void calculatePerSymbolMetrics(BacktestResult& result, const Portfolio& portfolio);
    void calculateComprehensiveMetrics(BacktestResult& result);
    void calculateDiversificationMetrics(BacktestResult& result);
    
    // Risk metrics calculation
    double calculateSharpeRatio(const std::vector<double>& returns, double risk_free_rate = 0.02) const;
    double calculateMaxDrawdown(const std::vector<double>& equity_curve) const;
    std::vector<double> calculateDailyReturns(const std::vector<double>& equity_curve) const;
    
    // Performance metrics calculation
    PerformanceMetrics calculateMetrics(const std::vector<TradingSignal>& trades, double initialCapital) const;
    RiskMetrics calculateRiskMetrics(const std::vector<double>& returns) const;
    
    // Complete result finalization
    void finalizeResults(BacktestResult& result, const Portfolio& portfolio);
    
private:
    // Helper methods for specific calculations
    void calculateAnnualizedReturn(BacktestResult& result) const;
    void calculateVolatility(BacktestResult& result) const;
    void calculateProfitFactor(BacktestResult& result) const;
    void calculateWinLossMetrics(BacktestResult& result) const;
    void calculateDiversificationRatio(BacktestResult& result) const;
    
    // Trade analysis helpers
    void analyzeTradeReturns(const std::vector<TradingSignal>& signals, 
                           std::vector<double>& win_returns, 
                           std::vector<double>& loss_returns) const;
    
    // Portfolio analysis helpers
    void analyzePortfolioAllocation(const BacktestResult& result, 
                                   std::map<std::string, double>& allocations) const;
};