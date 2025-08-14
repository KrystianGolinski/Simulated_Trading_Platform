#include <iostream>
#include <string>
#include "simulation_config.h"
#include "worker_spawner.h"
#include "execution_planner.h"

using namespace TradingCommon;
using namespace TradingOrchestrator;

void printUsage(const char* program_name) {
    std::cout << "Usage: " << program_name << " [OPTIONS]" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  --config-json <json>    Configuration as JSON string" << std::endl;
    std::cout << "  --worker-path <path>    Path to trading engine executable" << std::endl;
    std::cout << "  --test                  Run with test configuration" << std::endl;
    std::cout << "  --help                  Show this help message" << std::endl;
}

SimulationConfig createTestConfig() {
    SimulationConfig config;
    config.symbols = {"AAPL", "MSFT", "GOOGL", "TSLA"};
    config.start_date = "2023-01-01";
    config.end_date = "2023-12-31";
    config.starting_capital = 10000.0;
    config.strategy = "ma_crossover";
    config.strategy_parameters["short_ma"] = "20";
    config.strategy_parameters["long_ma"] = "50";
    return config;
}

int main(int argc, char* argv[]) {
    std::cout << "Simulation Orchestrator v0.2.0" << std::endl;
    
    std::string config_json;
    std::string worker_path = "/shared/trading_engine";
    bool test_mode = false;
    
    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (std::string(argv[i]) == "--config-json" && i + 1 < argc) {
            config_json = argv[i + 1];
            i++;
        } else if (std::string(argv[i]) == "--worker-path" && i + 1 < argc) {
            worker_path = argv[i + 1];
            i++;
        } else if (std::string(argv[i]) == "--test") {
            test_mode = true;
        } else if (std::string(argv[i]) == "--help") {
            printUsage(argv[0]);
            return 0;
        }
    }
    
    try {
        SimulationConfig config;
        
        if (test_mode) {
            std::cout << "Running in test mode with sample configuration..." << std::endl;
            config = createTestConfig();
        } else if (!config_json.empty()) {
            std::cout << "Parsing configuration from JSON..." << std::endl;
            config = SimulationConfig::fromJson(config_json);
        } else {
            std::cerr << "Error: No configuration provided. Use --config-json or --test" << std::endl;
            printUsage(argv[0]);
            return 1;
        }
        
        if (!config.isValid()) {
            std::cerr << "Error: Invalid configuration - " << config.getValidationError() << std::endl;
            return 1;
        }
        
        std::cout << "Configuration loaded successfully:" << std::endl;
        std::cout << "  Symbols: " << config.symbols.size() << std::endl;
        std::cout << "  Strategy: " << config.strategy << std::endl;
        std::cout << "  Date Range: " << config.start_date << " to " << config.end_date << std::endl;
        
        // Create execution plan
        ExecutionPlanner planner;
        ExecutionPlan plan = planner.createExecutionPlan(config);
        
        std::cout << "\nExecution plan created:" << std::endl;
        std::cout << plan.toJson() << std::endl;
        
        // Initialize worker spawner
        WorkerSpawner spawner(worker_path);
        
        if (plan.execution_mode == "parallel") {
            // Execute workers in parallel
            std::cout << "\nExecuting " << plan.worker_configs.size() << " workers in parallel..." << std::endl;
            auto results = spawner.spawnParallelWorkers(plan.worker_configs);
            
            // Process results
            bool all_successful = true;
            for (size_t i = 0; i < results.size(); i++) {
                std::cout << "\nWorker " << i << " results:" << std::endl;
                std::cout << results[i].toJson() << std::endl;
                
                if (!results[i].isSuccess()) {
                    all_successful = false;
                    std::cerr << "Worker " << i << " failed: " << results[i].getErrorMessage() << std::endl;
                }
            }
            
            return all_successful ? 0 : 1;
            
        } else {
            // Execute single worker
            std::cout << "\nExecuting single worker..." << std::endl;
            auto result = spawner.spawnWorker(config);
            
            std::cout << "\nWorker result:" << std::endl;
            std::cout << result.toJson() << std::endl;
            
            if (!result.isSuccess()) {
                std::cerr << "Worker failed: " << result.getErrorMessage() << std::endl;
                return 1;
            }
            
            return 0;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}