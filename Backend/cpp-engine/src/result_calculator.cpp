#include "result_calculator.h"
#include "logger.h"
#include <algorithm>
#include <numeric>
#include <cmath>
#include <set>

void ResultCalculator::calculateTradeMetrics(BacktestResult& result) {
    std::vector<double> buy_prices;
    
    for (const auto& signal : result.signals_generated) {
        if (signal.signal == Signal::BUY) {
            buy_prices.push_back(signal.price);
        } else if (signal.signal == Signal::SELL && !buy_prices.empty()) {
            double buy_price = buy_prices.back();
            buy_prices.pop_back();
            
            if (signal.price > buy_price) {
                result.winning_trades++;
            } else {
                result.losing_trades++;
            }
        }
    }
}

void ResultCalculator::calculatePortfolioMetrics(BacktestResult& result, const Portfolio& portfolio) {
    if (!result.equity_curve.empty()) {
        result.ending_value = result.equity_curve.back();
        result.cash_remaining = portfolio.getCashBalance();
        result.total_return_pct = ((result.ending_value - result.starting_capital) / result.starting_capital) * 100.0;
        
        Logger::debug("Final calculations: Portfolio cash=", result.cash_remaining,
                     ", ending value=", result.ending_value, ", return=", result.total_return_pct, "%");
    } else {
        result.ending_value = result.starting_capital;
        result.cash_remaining = result.starting_capital;
        result.total_return_pct = 0.0;
        Logger::debug("Empty equity curve, using starting capital as ending value");
    }
    
    auto daily_returns = calculateDailyReturns(result.equity_curve);
    result.sharpe_ratio = calculateSharpeRatio(daily_returns);
    result.max_drawdown = calculateMaxDrawdown(result.equity_curve);
}

void ResultCalculator::calculatePerSymbolMetrics(BacktestResult& result, const Portfolio& portfolio) {
    Logger::debug("Calculating per-symbol performance metrics for ", result.symbols.size(), " symbols");
    
    // Map to track trades per symbol
    std::map<std::string, std::vector<double>> symbol_trade_returns;
    std::map<std::string, double> symbol_buy_values;
    std::map<std::string, double> symbol_sell_values;
    
    // Process all signals to calculate per-symbol metrics
    for (const auto& signal : result.signals_generated) {
        // TODO: TradingSignal needs symbol field, using date as placeholder
        const std::string& symbol = signal.date;
        auto& symbol_perf = result.symbol_performance[symbol];
        
        // Add signal to symbol-specific list
        symbol_perf.symbol_signals.push_back(signal);
        
        if (signal.signal == Signal::BUY) {
            symbol_buy_values[symbol] += signal.price;
        } else if (signal.signal == Signal::SELL) {
            symbol_sell_values[symbol] += signal.price;
            
            // Calculate trade return if we have a previous buy
            if (symbol_buy_values[symbol] > 0) {
                double trade_return = (signal.price - symbol_buy_values[symbol]) / symbol_buy_values[symbol];
                symbol_trade_returns[symbol].push_back(trade_return);
                
                if (trade_return > 0) {
                    symbol_perf.winning_trades++;
                } else {
                    symbol_perf.losing_trades++;
                }
                symbol_perf.trades_count++;
            }
        }
    }
    
    // Calculate final metrics for each symbol
    for (auto& [symbol, symbol_perf] : result.symbol_performance) {
        // Calculate win rate for this symbol
        if (symbol_perf.trades_count > 0) {
            symbol_perf.win_rate = (static_cast<double>(symbol_perf.winning_trades) / symbol_perf.trades_count) * 100.0;
        }
        
        // Calculate allocation percentage
        if (portfolio.hasPosition(symbol)) {
            auto position = portfolio.getPosition(symbol);
            symbol_perf.final_position_value = position.getShares() * position.getAveragePrice();
            symbol_perf.symbol_allocation_pct = (symbol_perf.final_position_value / result.ending_value) * 100.0;
        }
        
        // Calculate symbol return if we have trade data
        if (!symbol_trade_returns[symbol].empty()) {
            double total_return = 0.0;
            for (double ret : symbol_trade_returns[symbol]) {
                total_return += ret;
            }
            symbol_perf.total_return_pct = (total_return / symbol_trade_returns[symbol].size()) * 100.0;
        }
        
        Logger::debug("Symbol ", symbol, " metrics: trades=", symbol_perf.trades_count, 
                     ", win_rate=", symbol_perf.win_rate, "%, allocation=", symbol_perf.symbol_allocation_pct, "%");
    }
}

void ResultCalculator::calculateComprehensiveMetrics(BacktestResult& result) {
    // Calculate signals generated count
    result.signals_generated_count = result.signals_generated.size();
    
    // Calculate annualized return
    calculateAnnualizedReturn(result);
    
    // Calculate volatility
    calculateVolatility(result);
    
    // Calculate profit factor and win/loss metrics
    calculateProfitFactor(result);
    calculateWinLossMetrics(result);
    
    Logger::debug("Metrics calculated: annualized_return=", result.annualized_return, 
                 "%, volatility=", result.volatility, "%, profit_factor=", result.profit_factor);
}

void ResultCalculator::calculateDiversificationMetrics(BacktestResult& result) {
    // Calculate portfolio diversification ratio
    // Simple diversification measure: how evenly capital is distributed across symbols
    
    if (result.symbols.size() <= 1) {
        result.portfolio_diversification_ratio = 0.0; // No diversification with single symbol
        return;
    }
    
    std::vector<double> allocations;
    double total_allocation = 0.0;
    
    for (const auto& [symbol, symbol_perf] : result.symbol_performance) {
        double allocation = symbol_perf.symbol_allocation_pct / 100.0;
        allocations.push_back(allocation);
        total_allocation += allocation;
    }
    
    // Calculate Herfindahl-Hirschman Index (HHI) for diversification
    // Lower HHI indicates better diversification
    double hhi = 0.0;
    for (double allocation : allocations) {
        hhi += allocation * allocation;
    }
    
    // Convert to diversification ratio (1 = perfectly diversified, 0 = concentrated)
    double max_diversification = 1.0 / result.symbols.size(); // Equal allocation across all symbols
    result.portfolio_diversification_ratio = (max_diversification - hhi) / max_diversification;
    
    Logger::debug("Diversification metrics: HHI=", hhi, ", diversification_ratio=", result.portfolio_diversification_ratio);
}

double ResultCalculator::calculateSharpeRatio(const std::vector<double>& returns, double risk_free_rate) const {
    if (returns.empty()) return 0.0;
    
    double mean_return = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    
    double variance = 0.0;
    for (double ret : returns) {
        variance += (ret - mean_return) * (ret - mean_return);
    }
    variance /= returns.size();
    
    double std_dev = std::sqrt(variance);
    if (std_dev == 0.0) return 0.0;
    
    double annualized_return = mean_return * 252; // 252 trading days per year
    double annualized_std = std_dev * std::sqrt(252);
    
    return (annualized_return - risk_free_rate) / annualized_std;
}

double ResultCalculator::calculateMaxDrawdown(const std::vector<double>& equity_curve) const {
    if (equity_curve.empty()) return 0.0;
    
    double max_drawdown = 0.0;
    double peak = equity_curve[0];
    
    for (double value : equity_curve) {
        if (value > peak) {
            peak = value;
        }
        double drawdown = (peak - value) / peak;
        max_drawdown = std::max(max_drawdown, drawdown);
    }
    
    return max_drawdown * 100.0; // Return as percentage
}

std::vector<double> ResultCalculator::calculateDailyReturns(const std::vector<double>& equity_curve) const {
    std::vector<double> returns;
    
    for (size_t i = 1; i < equity_curve.size(); ++i) {
        if (equity_curve[i-1] > 0) {
            double ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1];
            returns.push_back(ret);
        }
    }
    
    return returns;
}

PerformanceMetrics ResultCalculator::calculateMetrics(const std::vector<TradingSignal>& trades, double initialCapital) const {
    PerformanceMetrics metrics;
    
    // Calculate basic metrics from trades
    metrics.total_trades = trades.size();
    
    // Calculate win rate and returns
    int winning_trades = 0;
    double total_profit = 0.0;
    double total_loss = 0.0;
    
    for (const auto& trade : trades) {
        if (trade.signal == Signal::SELL) {
            // TODO: Simplified calculation - would need buy/sell pairs in real implementation
            double profit = trade.price - initialCapital / trades.size();
            if (profit > 0) {
                winning_trades++;
                total_profit += profit;
            } else {
                total_loss += std::abs(profit);
            }
        }
    }
    
    metrics.win_rate = (metrics.total_trades > 0) ? 
        (static_cast<double>(winning_trades) / metrics.total_trades) * 100.0 : 0.0;
    
    metrics.profit_factor = (total_loss > 0) ? total_profit / total_loss : 0.0;
    metrics.average_win = (winning_trades > 0) ? total_profit / winning_trades : 0.0;
    metrics.average_loss = (metrics.total_trades - winning_trades > 0) ? 
        total_loss / (metrics.total_trades - winning_trades) : 0.0;
    
    return metrics;
}

RiskMetrics ResultCalculator::calculateRiskMetrics(const std::vector<double>& returns) const {
    RiskMetrics risk_metrics;
    
    if (returns.empty()) return risk_metrics;
    
    // Calculate volatility
    double mean_return = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    double variance = 0.0;
    for (double ret : returns) {
        variance += (ret - mean_return) * (ret - mean_return);
    }
    variance /= returns.size();
    risk_metrics.volatility = std::sqrt(variance) * std::sqrt(252) * 100.0; // Annualized volatility
    
    // Calculate Sharpe ratio
    risk_metrics.sharpe_ratio = calculateSharpeRatio(returns);
    
    // Calculate max drawdown using equity curve approximation
    std::vector<double> equity_curve;
    double cumulative_value = 100.0; // Start with 100 for percentage calculation
    equity_curve.push_back(cumulative_value);
    
    for (double ret : returns) {
        cumulative_value *= (1.0 + ret);
        equity_curve.push_back(cumulative_value);
    }
    
    risk_metrics.max_drawdown = calculateMaxDrawdown(equity_curve);
    
    return risk_metrics;
}

void ResultCalculator::finalizeResults(BacktestResult& result, const Portfolio& portfolio) {
    // Calculate portfolio performance metrics
    calculatePortfolioMetrics(result, portfolio);
    
    // Calculate trade performance metrics
    calculateTradeMetrics(result);
    
    // Calculate per-symbol performance metrics
    calculatePerSymbolMetrics(result, portfolio);
    
    // Calculate overall win rate
    result.win_rate = result.total_trades > 0 ? 
        (static_cast<double>(result.winning_trades) / result.total_trades) * 100.0 : 0.0;
    
    // Calculate additional metrics
    calculateComprehensiveMetrics(result);
    
    // Calculate portfolio diversification ratio
    calculateDiversificationMetrics(result);
    
    Logger::debug("Finalized backtest results for ", result.symbols.size(), " symbols");
    Logger::debug("Total trades: ", result.total_trades, ", Win rate: ", result.win_rate, "%");
    Logger::debug("Total return: ", result.total_return_pct, "%, Sharpe ratio: ", result.sharpe_ratio);
}

void ResultCalculator::calculateAnnualizedReturn(BacktestResult& result) const {
    if (!result.start_date.empty() && !result.end_date.empty()) {
        // Simple approximation: assume 252 trading days per year
        int trading_days = result.equity_curve.size();
        double years = trading_days / 252.0;
        
        if (years > 0) {
            result.annualized_return = (std::pow((result.ending_value / result.starting_capital), (1.0 / years)) - 1.0) * 100.0;
        }
    }
}

void ResultCalculator::calculateVolatility(BacktestResult& result) const {
    auto daily_returns = calculateDailyReturns(result.equity_curve);
    
    if (!daily_returns.empty()) {
        double mean_return = std::accumulate(daily_returns.begin(), daily_returns.end(), 0.0) / daily_returns.size();
        double variance = 0.0;
        
        for (double ret : daily_returns) {
            variance += (ret - mean_return) * (ret - mean_return);
        }
        variance /= daily_returns.size();
        result.volatility = std::sqrt(variance) * std::sqrt(252) * 100.0; // Annualized volatility as percentage
    }
}

void ResultCalculator::calculateProfitFactor(BacktestResult& result) const {
    double total_wins = 0.0;
    double total_losses = 0.0;
    
    auto daily_returns = calculateDailyReturns(result.equity_curve);
    for (double daily_return : daily_returns) {
        if (daily_return > 0) {
            total_wins += daily_return;
        } else if (daily_return < 0) {
            total_losses += std::abs(daily_return);
        }
    }
    
    result.profit_factor = total_losses > 0 ? total_wins / total_losses : 0.0;
}

void ResultCalculator::calculateWinLossMetrics(BacktestResult& result) const {
    double total_wins = 0.0;
    double total_losses = 0.0;
    int win_count = 0;
    int loss_count = 0;
    
    auto daily_returns = calculateDailyReturns(result.equity_curve);
    for (double daily_return : daily_returns) {
        if (daily_return > 0) {
            total_wins += daily_return;
            win_count++;
        } else if (daily_return < 0) {
            total_losses += std::abs(daily_return);
            loss_count++;
        }
    }
    
    result.average_win = win_count > 0 ? (total_wins / win_count) * result.starting_capital : 0.0;
    result.average_loss = loss_count > 0 ? (total_losses / loss_count) * result.starting_capital : 0.0;
}