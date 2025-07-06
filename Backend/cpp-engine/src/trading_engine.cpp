#include "trading_engine.h"
#include "data_conversion.h"
#include "json_helpers.h"
#include "logger.h"
#include "trading_exceptions.h"
#include "error_utils.h"
#include <sstream>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <chrono>
#include <thread>
#include <set>

// Constructors
TradingEngine::TradingEngine() : portfolio_(10000.0), cache_enabled_(false) {
    initializeServices();
    strategy_manager_->initializeDefaultStrategy();
}

TradingEngine::TradingEngine(double initial_capital) : portfolio_(initial_capital), cache_enabled_(false) {
    initializeServices();
    strategy_manager_->initializeDefaultStrategy();
}

// Move constructor
TradingEngine::TradingEngine(TradingEngine&& other) noexcept
    : portfolio_(std::move(other.portfolio_)),
      market_data_(std::move(other.market_data_)),
      execution_service_(std::move(other.execution_service_)),
      progress_service_(std::move(other.progress_service_)),
      portfolio_allocator_(std::move(other.portfolio_allocator_)),
      result_calculator_(std::move(other.result_calculator_)),
      data_processor_(std::move(other.data_processor_)),
      strategy_manager_(std::move(other.strategy_manager_)),
      trading_orchestrator_(std::move(other.trading_orchestrator_)),
      price_data_cache_(std::move(other.price_data_cache_)),
      cache_enabled_(other.cache_enabled_) {}

// Move assignment
TradingEngine& TradingEngine::operator=(TradingEngine&& other) noexcept {
    if (this != &other) {
        portfolio_ = std::move(other.portfolio_);
        market_data_ = std::move(other.market_data_);
        execution_service_ = std::move(other.execution_service_);
        progress_service_ = std::move(other.progress_service_);
        portfolio_allocator_ = std::move(other.portfolio_allocator_);
        result_calculator_ = std::move(other.result_calculator_);
        data_processor_ = std::move(other.data_processor_);
        strategy_manager_ = std::move(other.strategy_manager_);
        trading_orchestrator_ = std::move(other.trading_orchestrator_);
        price_data_cache_ = std::move(other.price_data_cache_);
        cache_enabled_ = other.cache_enabled_;
    }
    return *this;
}

// Strategy manager access
StrategyManager* TradingEngine::getStrategyManager() const {
    return strategy_manager_.get();
}

// Trading orchestrator access
TradingOrchestrator* TradingEngine::getTradingOrchestrator() const {
    return trading_orchestrator_.get();
}

Portfolio& TradingEngine::getPortfolio() {
    return portfolio_;
}

const Portfolio& TradingEngine::getPortfolio() const {
    return portfolio_;
}

// Service initialization
void TradingEngine::initializeServices() {
    market_data_ = std::make_unique<MarketData>();
    execution_service_ = std::make_unique<ExecutionService>();
    progress_service_ = std::make_unique<ProgressService>();
    result_calculator_ = std::make_unique<ResultCalculator>();
    data_processor_ = std::make_unique<DataProcessor>();
    strategy_manager_ = std::make_unique<StrategyManager>();
    trading_orchestrator_ = std::make_unique<TradingOrchestrator>();
    
    // Initialize portfolio allocator with default equal weight strategy
    AllocationConfig default_config;
    default_config.strategy = AllocationStrategy::EQUAL_WEIGHT;
    default_config.max_position_weight = 0.08; // Max 8% per position for better diversification
    default_config.min_position_weight = 0.02; // Min 2% per position
    default_config.enable_rebalancing = true;  // Allow portfolio rebalancing
    default_config.cash_reserve_pct = 0.05;    // Keep 5% cash reserve
    portfolio_allocator_ = std::make_unique<PortfolioAllocator>(default_config);
}

// Service accessors
MarketData* TradingEngine::getMarketData() const {
    return market_data_.get();
}

ExecutionService* TradingEngine::getExecutionService() const {
    return execution_service_.get();
}

ProgressService* TradingEngine::getProgressService() const {
    return progress_service_.get();
}

DataProcessor* TradingEngine::getDataProcessor() const {
    return data_processor_.get();
}

ResultCalculator* TradingEngine::getResultCalculator() const {
    return result_calculator_.get();
}

PortfolioAllocator* TradingEngine::getPortfolioAllocator() const {
    return portfolio_allocator_.get();
}

// Memory optimization methods
void TradingEngine::optimizeMemoryUsage() {
    Logger::info("Optimizing memory usage...");
    
    // Clear caches
    clearCache();
    
    // TODO: Shrink internal containers to fit their current size
    // portfolio_.optimizeMemory();
    
    Logger::info("Memory optimization complete.");
}

void TradingEngine::clearCache() {
    price_data_cache_.clear();
    Logger::info("Price data cache cleared.");
}