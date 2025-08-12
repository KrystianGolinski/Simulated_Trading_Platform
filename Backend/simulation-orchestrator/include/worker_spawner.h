#pragma once

#include <vector>
#include <string>
#include "simulation_config.h"
#include "worker_result.h"

namespace TradingOrchestrator {
    
    class WorkerSpawner {
    public:
        WorkerSpawner(const std::string& worker_executable_path);
        
        // Spawn single worker
        TradingCommon::WorkerResult spawnWorker(const TradingCommon::SimulationConfig& config);
        
        // Spawn multiple workers in parallel
        std::vector<TradingCommon::WorkerResult> spawnParallelWorkers(
            const std::vector<TradingCommon::SimulationConfig>& configs);
        
        // Configuration
        void setMaxWorkers(int max_workers);
        void setWorkerTimeout(int timeout_seconds);
        
    private:
        std::string worker_path_;
        int max_workers_;
        int worker_timeout_seconds_;
        
        // Helper methods
        std::string buildCommandLine(const TradingCommon::SimulationConfig& config) const;
        TradingCommon::WorkerResult executeWorker(const std::string& command) const;
    };
    
} // namespace TradingOrchestrator