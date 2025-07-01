#pragma once

#include "technical_indicators.h"
#include "portfolio.h"
#include "market_data.h"
#include <memory>
#include <string>
#include <vector>
#include <map>

struct StrategyConfig {
    std::map<std::string, double> parameters;
    double max_position_size = 0.1;
    double stop_loss_pct = -0.05;
    double take_profit_pct = 0.15;
    bool enable_risk_management = true;
    
    // Position increase configuration
    bool allow_position_increases = true;
    double max_position_percentage = 0.3;  // Max 30% of portfolio in single position
    double position_increase_size = 0.05;  // 5% of portfolio per increase
    int max_position_increases = 3;        // Maximum number of increases per position
    
    // Portfolio rebalancing configuration
    bool enable_rebalancing = false;
    double rebalancing_threshold = 0.05;   // Rebalance when allocation drifts 5%
    int rebalancing_frequency = 30;        // Rebalance every 30 days
    
    void setParameter(const std::string& key, double value) {
        parameters[key] = value;
    }
    
    double getParameter(const std::string& key, double default_value = 0.0) const {
        auto it = parameters.find(key);
        return it != parameters.end() ? it->second : default_value;
    }
};

// Per-symbol performance metrics for multi-symbol backtesting
struct SymbolPerformance {
    std::string symbol;                          // Symbol ticker
    int trades_count;                            // Number of trades for this symbol
    int winning_trades;                          // Number of profitable trades
    int losing_trades;                           // Number of losing trades
    double win_rate;                             // Win rate percentage for this symbol
    double total_return_pct;                     // Return percentage for this symbol
    double symbol_allocation_pct;                // Percentage of portfolio allocated to this symbol
    double final_position_value;                 // Final value of position in this symbol
    std::vector<TradingSignal> symbol_signals;   // All signals generated for this symbol
    
    SymbolPerformance() : trades_count(0), winning_trades(0), losing_trades(0),
                         win_rate(0.0), total_return_pct(0.0), symbol_allocation_pct(0.0),
                         final_position_value(0.0) {}
    
    SymbolPerformance(const std::string& sym) : symbol(sym), trades_count(0), winning_trades(0), 
                                               losing_trades(0), win_rate(0.0), total_return_pct(0.0),
                                               symbol_allocation_pct(0.0), final_position_value(0.0) {}
};

struct BacktestResult {
    // Multi-symbol portfolio: all symbols processed in this backtest
    std::vector<std::string> symbols;            // All symbols included in backtest
    
    // Portfolio-wide performance metrics
    double starting_capital;                     // Initial capital
    double ending_value;                         // Final portfolio value
    double total_return_pct;                     // Total portfolio return percentage
    double cash_remaining;                       // Cash balance at end
    
    // Trade statistics (across all symbols)
    int total_trades;                            // Total number of trades executed
    int winning_trades;                          // Total number of profitable trades
    int losing_trades;                           // Total number of losing trades
    double win_rate;                             // Overall win rate percentage
    
    // Risk and performance metrics
    double max_drawdown;                         // Maximum drawdown percentage
    double sharpe_ratio;                         // Risk-adjusted return metric
    double volatility;                           // Portfolio volatility
    double profit_factor;                        // Ratio of gross profit to gross loss
    double average_win;                          // Average winning trade amount
    double average_loss;                         // Average losing trade amount
    
    // Time series data
    std::vector<TradingSignal> signals_generated; // All signals generated across all symbols
    std::vector<double> equity_curve;            // Portfolio value over time
    
    // Per-symbol performance breakdown
    std::map<std::string, SymbolPerformance> symbol_performance; // Individual symbol metrics
    
    // Additional metrics for comprehensive analysis
    double annualized_return;                    // Annualized return percentage
    int signals_generated_count;                 // Total signals generated (including HOLD)
    double portfolio_diversification_ratio;     // Measure of diversification effectiveness
    
    // Metadata
    std::string start_date;                      // Backtest start date
    std::string end_date;                        // Backtest end date
    std::string strategy_name;                   // Strategy used for backtest
    std::string error_message;                   // Error message if backtest failed
    
    // Constructor
    BacktestResult() : starting_capital(0), ending_value(0), total_return_pct(0), 
                      cash_remaining(0), total_trades(0), winning_trades(0), losing_trades(0), 
                      win_rate(0), max_drawdown(0), sharpe_ratio(0), volatility(0), 
                      profit_factor(0), average_win(0), average_loss(0), annualized_return(0), 
                      signals_generated_count(0), portfolio_diversification_ratio(0), error_message("") {}
    
    // Multi-symbol support methods
    void addSymbol(const std::string& symbol) {
        if (std::find(symbols.begin(), symbols.end(), symbol) == symbols.end()) {
            symbols.push_back(symbol);
            symbol_performance[symbol] = SymbolPerformance(symbol);
        }
    }
};

class TradingStrategy {
protected:
    StrategyConfig config_;
    std::string strategy_name_;
    
public:
    explicit TradingStrategy(const std::string& name) : strategy_name_(name) {}
    virtual ~TradingStrategy() = default;
    
    TradingStrategy(const TradingStrategy&) = delete;
    TradingStrategy& operator=(const TradingStrategy&) = delete;
    
    TradingStrategy(TradingStrategy&&) = default;
    TradingStrategy& operator=(TradingStrategy&&) = default;
    
    virtual TradingSignal evaluateSignal(const std::vector<PriceData>& price_data, 
                                       const Portfolio& portfolio,
                                       const std::string& symbol = "") = 0;
    
    virtual void configure(const StrategyConfig& config) { config_ = config; }
    
    virtual std::string getName() const { return strategy_name_; }
    virtual StrategyConfig getConfig() const { return config_; }
    
    virtual bool validateConfig() const = 0;
    virtual std::string getDescription() const = 0;
    
    double calculatePositionSize(double available_capital, double stock_price) const;
    double calculatePositionSize(const Portfolio& portfolio, const std::string& symbol, double stock_price, double portfolio_value) const;
    bool shouldApplyRiskManagement(const Portfolio& portfolio, const std::string& symbol) const;
    
protected:
    double applyRiskManagement(double position_size, const Portfolio& portfolio) const;
};

class MovingAverageCrossoverStrategy : public TradingStrategy {
private:
    int short_period_;
    int long_period_;
    std::unique_ptr<TechnicalIndicators> indicators_;
    
public:
    MovingAverageCrossoverStrategy();
    explicit MovingAverageCrossoverStrategy(int short_period, int long_period);
    
    TradingSignal evaluateSignal(const std::vector<PriceData>& price_data, 
                               const Portfolio& portfolio,
                               const std::string& symbol = "") override;
    
    void configure(const StrategyConfig& config) override;
    bool validateConfig() const override;
    std::string getDescription() const override;
    
    void setMovingAveragePeriods(int short_period, int long_period);
    std::pair<int, int> getMovingAveragePeriods() const;
    
private:
    void updateIndicators(const std::vector<PriceData>& price_data);
    bool hasValidCrossover(const std::vector<double>& short_ma, 
                          const std::vector<double>& long_ma) const;
};

class RSIStrategy : public TradingStrategy {
private:
    int rsi_period_;
    double oversold_threshold_;
    double overbought_threshold_;
    std::unique_ptr<TechnicalIndicators> indicators_;
    
public:
    RSIStrategy();
    explicit RSIStrategy(int period, double oversold = 30.0, double overbought = 70.0);
    
    TradingSignal evaluateSignal(const std::vector<PriceData>& price_data, 
                               const Portfolio& portfolio,
                               const std::string& symbol = "") override;
    
    void configure(const StrategyConfig& config) override;
    bool validateConfig() const override;
    std::string getDescription() const override;
    
    void setRSIParameters(int period, double oversold, double overbought);
    
private:
    void updateIndicators(const std::vector<PriceData>& price_data);
};