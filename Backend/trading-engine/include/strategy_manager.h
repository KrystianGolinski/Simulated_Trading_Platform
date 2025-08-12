#pragma once

#include <map>
#include <memory>
#include <string>

#include "result.h"
#include "trading_strategy.h"

// Forward declaration
struct TradingConfig;

// Strategy management and factory for trading strategies
class StrategyManager {
public:
    StrategyManager() = default;
    ~StrategyManager() = default;
    
    // Delete copy constructor and assignment operator to prevent copying
    StrategyManager(const StrategyManager&) = delete;
    StrategyManager& operator=(const StrategyManager&) = delete;
    
    // Allow move constructor and assignment
    StrategyManager(StrategyManager&&) = default;
    StrategyManager& operator=(StrategyManager&&) = default;
    
    // Strategy factory methods
    std::unique_ptr<TradingStrategy> createMovingAverageStrategy(int short_period = 20, int long_period = 50);
    std::unique_ptr<TradingStrategy> createRSIStrategy(int period = 14, double oversold = 30.0, double overbought = 70.0);
    
    // Strategy configuration and validation
    Result<std::unique_ptr<TradingStrategy>> createStrategyFromConfig(const TradingConfig& config);
    Result<void> validateStrategyConfig(const TradingConfig& config) const;
    
    // Strategy management
    void setCurrentStrategy(std::unique_ptr<TradingStrategy> strategy);
    TradingStrategy* getCurrentStrategy() const;
    bool hasStrategy() const;
    
    // Strategy information
    std::string getCurrentStrategyName() const;
    std::map<std::string, double> getCurrentStrategyParameters() const;
    
    // Strategy validation and configuration
    Result<void> validateStrategy(const std::string& strategy_name) const;
    Result<StrategyConfig> buildStrategyConfig(const TradingConfig& config) const;
    
    // Strategy lifecycle management
    void resetStrategy();
    void clearStrategy();
    
    // Default strategy initialization
    void initializeDefaultStrategy();
    
private:
    std::unique_ptr<TradingStrategy> current_strategy_;
    std::string current_strategy_name_;
    std::map<std::string, double> current_strategy_parameters_;
    
    // Helper methods for strategy creation
    Result<std::unique_ptr<TradingStrategy>> createStrategyByName(const std::string& name, const std::map<std::string, double>& parameters);
    
    // Strategy parameter validation
    Result<void> validateMovingAverageParameters(const std::map<std::string, double>& parameters) const;
    Result<void> validateRSIParameters(const std::map<std::string, double>& parameters) const;
    
    // Strategy parameter extraction
    std::map<std::string, double> extractStrategyParameters(const TradingConfig& config) const;
    
    // Strategy name utilities
    std::string normalizeStrategyName(const std::string& name) const;
    bool isValidStrategyName(const std::string& name) const;
};