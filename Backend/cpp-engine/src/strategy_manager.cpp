#include "strategy_manager.h"
#include "trading_engine.h"
#include "logger.h"
#include <algorithm>
#include <cctype>

// Strategy factory methods
std::unique_ptr<TradingStrategy> StrategyManager::createMovingAverageStrategy(int short_period, int long_period) {
    return std::make_unique<MovingAverageCrossoverStrategy>(short_period, long_period);
}

std::unique_ptr<TradingStrategy> StrategyManager::createRSIStrategy(int period, double oversold, double overbought) {
    return std::make_unique<RSIStrategy>(period, oversold, overbought);
}

// Strategy configuration and validation
Result<std::unique_ptr<TradingStrategy>> StrategyManager::createStrategyFromConfig(const TradingConfig& config) {
    // Validate strategy configuration first
    auto validation_result = validateStrategyConfig(config);
    if (validation_result.isError()) {
        return Result<std::unique_ptr<TradingStrategy>>(validation_result.getError());
    }
    
    // Extract strategy parameters
    auto parameters = extractStrategyParameters(config);
    
    // Create strategy based on name
    auto strategy_result = createStrategyByName(config.strategy_name, parameters);
    if (strategy_result.isError()) {
        return Result<std::unique_ptr<TradingStrategy>>(strategy_result.getError());
    }
    
    // Update current strategy tracking
    current_strategy_name_ = config.strategy_name;
    current_strategy_parameters_ = parameters;
    
    Logger::debug("Created strategy: ", config.strategy_name);
    return Result<std::unique_ptr<TradingStrategy>>(std::move(strategy_result.getValue()));
}

Result<void> StrategyManager::validateStrategyConfig(const TradingConfig& config) const {
    // Validate strategy name
    if (config.strategy_name.empty()) {
        return Result<void>(ErrorCode::ENGINE_NO_STRATEGY_CONFIGURED, "Strategy name cannot be empty");
    }
    
    // Validate strategy name is supported
    auto name_validation_result = validateStrategy(config.strategy_name);
    if (name_validation_result.isError()) {
        return Result<void>(name_validation_result.getError());
    }
    
    // Validate parameters based on strategy type
    std::string normalized_name = normalizeStrategyName(config.strategy_name);
    
    if (normalized_name == "ma_crossover" || normalized_name == "moving_average") {
        return validateMovingAverageParameters(config.strategy_parameters);
    } else if (normalized_name == "rsi") {
        return validateRSIParameters(config.strategy_parameters);
    }
    
    return Result<void>(); // Success
}

// Strategy management
void StrategyManager::setCurrentStrategy(std::unique_ptr<TradingStrategy> strategy) {
    current_strategy_ = std::move(strategy);
}

TradingStrategy* StrategyManager::getCurrentStrategy() const {
    return current_strategy_.get();
}

bool StrategyManager::hasStrategy() const {
    return current_strategy_ != nullptr;
}

// Strategy information
std::string StrategyManager::getCurrentStrategyName() const {
    return current_strategy_name_;
}

std::map<std::string, double> StrategyManager::getCurrentStrategyParameters() const {
    // Return the stored parameters from when the strategy was created
    return current_strategy_parameters_;
}

// Strategy validation and configuration
Result<void> StrategyManager::validateStrategy(const std::string& strategy_name) const {
    if (!isValidStrategyName(strategy_name)) {
        return Result<void>(ErrorCode::ENGINE_NO_STRATEGY_CONFIGURED, 
                           "Unsupported strategy: " + strategy_name);
    }
    
    return Result<void>(); // Success
}

Result<StrategyConfig> StrategyManager::buildStrategyConfig(const TradingConfig& config) const {
    StrategyConfig strategy_config;
    
    // Copy parameters from TradingConfig
    strategy_config.parameters = config.strategy_parameters;
    
    // Set default risk management parameters if not provided
    if (strategy_config.parameters.find("max_position_size") == strategy_config.parameters.end()) {
        strategy_config.max_position_size = 0.1; // 10% default
    } else {
        strategy_config.max_position_size = strategy_config.parameters["max_position_size"];
    }
    
    if (strategy_config.parameters.find("stop_loss_pct") == strategy_config.parameters.end()) {
        strategy_config.stop_loss_pct = -0.05; // -5% default
    } else {
        strategy_config.stop_loss_pct = strategy_config.parameters["stop_loss_pct"];
    }
    
    if (strategy_config.parameters.find("take_profit_pct") == strategy_config.parameters.end()) {
        strategy_config.take_profit_pct = 0.15; // 15% default
    } else {
        strategy_config.take_profit_pct = strategy_config.parameters["take_profit_pct"];
    }
    
    return Result<StrategyConfig>(strategy_config);
}

// Strategy lifecycle management
void StrategyManager::resetStrategy() {
    current_strategy_.reset();
    current_strategy_name_.clear();
    current_strategy_parameters_.clear();
}

void StrategyManager::clearStrategy() {
    resetStrategy();
}

// Default strategy initialization
void StrategyManager::initializeDefaultStrategy() {
    current_strategy_ = createMovingAverageStrategy();
    current_strategy_name_ = "ma_crossover";
    // Set default parameters for the moving average strategy
    current_strategy_parameters_ = {
        {"short_ma", 20.0},
        {"long_ma", 50.0}
    };
}

// Helper methods for strategy creation
Result<std::unique_ptr<TradingStrategy>> StrategyManager::createStrategyByName(
    const std::string& name, 
    const std::map<std::string, double>& parameters) {
    
    std::string normalized_name = normalizeStrategyName(name);
    
    if (normalized_name == "ma_crossover" || normalized_name == "moving_average") {
        int short_period = static_cast<int>(parameters.count("short_ma") ? parameters.at("short_ma") : 20);
        int long_period = static_cast<int>(parameters.count("long_ma") ? parameters.at("long_ma") : 50);
        
        auto strategy = createMovingAverageStrategy(short_period, long_period);
        return Result<std::unique_ptr<TradingStrategy>>(std::move(strategy));
        
    } else if (normalized_name == "rsi") {
        int period = static_cast<int>(parameters.count("rsi_period") ? parameters.at("rsi_period") : 14);
        double oversold = parameters.count("rsi_oversold") ? parameters.at("rsi_oversold") : 30.0;
        double overbought = parameters.count("rsi_overbought") ? parameters.at("rsi_overbought") : 70.0;
        
        auto strategy = createRSIStrategy(period, oversold, overbought);
        return Result<std::unique_ptr<TradingStrategy>>(std::move(strategy));
        
    } else {
        return Result<std::unique_ptr<TradingStrategy>>(
            ErrorCode::ENGINE_NO_STRATEGY_CONFIGURED, 
            "Unsupported strategy: " + name);
    }
}

// Strategy parameter validation
Result<void> StrategyManager::validateMovingAverageParameters(const std::map<std::string, double>& parameters) const {
    double short_ma = parameters.count("short_ma") ? parameters.at("short_ma") : 20;
    double long_ma = parameters.count("long_ma") ? parameters.at("long_ma") : 50;
    
    if (short_ma <= 0 || long_ma <= 0) {
        return Result<void>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER, 
                           "Moving average periods must be positive");
    }
    
    if (short_ma >= long_ma) {
        return Result<void>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER, 
                           "Short moving average period must be less than long period");
    }
    
    return Result<void>(); // Success
}

Result<void> StrategyManager::validateRSIParameters(const std::map<std::string, double>& parameters) const {
    double period = parameters.count("rsi_period") ? parameters.at("rsi_period") : 14;
    double oversold = parameters.count("rsi_oversold") ? parameters.at("rsi_oversold") : 30.0;
    double overbought = parameters.count("rsi_overbought") ? parameters.at("rsi_overbought") : 70.0;
    
    if (period <= 0) {
        return Result<void>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER, 
                           "RSI period must be positive");
    }
    
    if (oversold <= 0 || oversold >= 100) {
        return Result<void>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER, 
                           "RSI oversold threshold must be between 0 and 100");
    }
    
    if (overbought <= 0 || overbought >= 100) {
        return Result<void>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER, 
                           "RSI overbought threshold must be between 0 and 100");
    }
    
    if (oversold >= overbought) {
        return Result<void>(ErrorCode::TECHNICAL_ANALYSIS_INVALID_PARAMETER, 
                           "RSI oversold threshold must be less than overbought threshold");
    }
    
    return Result<void>(); // Success
}

// Strategy parameter extraction
std::map<std::string, double> StrategyManager::extractStrategyParameters(const TradingConfig& config) const {
    return config.strategy_parameters;
}

// Strategy name utilities
std::string StrategyManager::normalizeStrategyName(const std::string& name) const {
    std::string normalized = name;
    std::transform(normalized.begin(), normalized.end(), normalized.begin(), 
                  [](unsigned char c) { return std::tolower(c); });
    return normalized;
}

bool StrategyManager::isValidStrategyName(const std::string& name) const {
    std::string normalized = normalizeStrategyName(name);
    return normalized == "ma_crossover" || 
           normalized == "moving_average" || 
           normalized == "rsi";
}