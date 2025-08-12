#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <set>
#include <sstream>
#include <thread>

#include "data_conversion.h"
#include "error_utils.h"
#include "json_helpers.h"
#include "logger.h"
#include "trading_engine.h"
#include "trading_exceptions.h"

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
    
    // Optimize memory usage across all services
    portfolio_.optimizeMemory();
    
    if (market_data_) {
        market_data_->optimizeMemory();
    }
    
    if (execution_service_) {
        execution_service_->optimizeMemory();
    }
    
    if (data_processor_) {
        data_processor_->optimizeMemory();
    }
    
    if (portfolio_allocator_) {
        portfolio_allocator_->optimizeMemory();
    }
    
    if (result_calculator_) {
        // Note: ResultCalculator doesn't implement IMemoryOptimizable yet
        // result_calculator_->optimizeMemory();
    }
    
    if (trading_orchestrator_) {
        // Note: TradingOrchestrator doesn't implement IMemoryOptimizable yet
        // trading_orchestrator_->optimizeMemoryUsage();
    }
    
    // Shrink cache containers
    price_data_cache_.clear();
    
    Logger::info("All service memory optimization complete");
}

void TradingEngine::clearCache() {
    // Clear price data cache and shrink to fit
    price_data_cache_.clear();
    
    // Also clear caches in services if they support it
    if (market_data_) {
        market_data_->clearCache();
    }
    
    Logger::info("All caches cleared and optimized.");
}

// Memory reporting methods
std::string TradingEngine::getMemoryReport() const {
    std::ostringstream report;
    report << "=== TradingEngine Memory Report ===\n";
    
    // Portfolio memory report
    report << portfolio_.getMemoryReport() << "\n";
    
    // Price data cache memory
    size_t total_cache_memory = 0;
    for (const auto& [symbol, data] : price_data_cache_) {
        total_cache_memory += symbol.capacity() + (data.capacity() * sizeof(PriceData));
    }
    
    report << "Price Data Cache:\n";
    report << "  Cached symbols: " << price_data_cache_.size() << "\n";
    report << "  Estimated memory: " << total_cache_memory << " bytes\n\n";
    
    // Service memory reports
    if (market_data_) {
        report << market_data_->getMemoryReport() << "\n";
    }
    
    if (execution_service_) {
        report << execution_service_->getMemoryReport() << "\n";
    }
    
    if (data_processor_) {
        report << data_processor_->getMemoryReport() << "\n";
    }
    
    if (portfolio_allocator_) {
        report << portfolio_allocator_->getMemoryReport() << "\n";
    }
    
    // Total memory summary
    report << "Total Engine Memory: " << getTotalMemoryUsage() << " bytes\n";
    
    return report.str();
}

size_t TradingEngine::getTotalMemoryUsage() const {
    size_t total = sizeof(*this);
    
    // Portfolio memory
    total += portfolio_.getMemoryUsage();
    
    // Cache memory
    for (const auto& [symbol, data] : price_data_cache_) {
        total += symbol.capacity() + (data.capacity() * sizeof(PriceData));
    }
    
    // Service memory
    if (market_data_) {
        total += market_data_->getMemoryUsage();
    }
    
    if (execution_service_) {
        total += execution_service_->getMemoryUsage();
    }
    
    if (data_processor_) {
        total += data_processor_->getMemoryUsage();
    }
    
    if (portfolio_allocator_) {
        total += portfolio_allocator_->getMemoryUsage();
    }
    
    // Add estimated memory for unique_ptr overhead
    total += 6 * sizeof(std::unique_ptr<void>);
    
    return total;
}