#include "worker_spawner.h"
#include <iostream>
#include <sstream>
#include <cstdlib>
#include <unistd.h>
#include <sys/wait.h>
#include <chrono>

namespace TradingOrchestrator {

WorkerSpawner::WorkerSpawner(const std::string& worker_executable_path)
    : worker_path_(worker_executable_path), max_workers_(4), worker_timeout_seconds_(300) {
}

void WorkerSpawner::setMaxWorkers(int max_workers) {
    max_workers_ = max_workers;
}

void WorkerSpawner::setWorkerTimeout(int timeout_seconds) {
    worker_timeout_seconds_ = timeout_seconds;
}

std::string WorkerSpawner::buildCommandLine(const TradingCommon::SimulationConfig& config) const {
    std::stringstream cmd;
    cmd << worker_path_;
    
    // Use --simulate mode
    cmd << " --simulate";
    
    // Add symbol (trading engine expects --symbol, not --symbols)
    if (!config.symbols.empty()) {
        cmd << " --symbol ";
        for (size_t i = 0; i < config.symbols.size(); i++) {
            cmd << config.symbols[i];
            if (i < config.symbols.size() - 1) cmd << ",";
        }
    }
    
    cmd << " --start " << config.start_date;
    cmd << " --end " << config.end_date;
    cmd << " --capital " << config.starting_capital;
    
    // Add strategy parameters (if supported by trading engine)
    for (const auto& param : config.strategy_parameters) {
        cmd << " --" << param.first << " " << param.second;
    }
    
    return cmd.str();
}

TradingCommon::WorkerResult WorkerSpawner::executeWorker(const std::string& command) const {
    TradingCommon::WorkerResult result;
    auto start_time = std::chrono::high_resolution_clock::now();
    
    std::cout << "Executing: " << command << std::endl;
    
    // Create pipes for stdout and stderr
    int stdout_pipe[2], stderr_pipe[2];
    if (pipe(stdout_pipe) == -1 || pipe(stderr_pipe) == -1) {
        result.return_code = -1;
        result.stderr_data = "Failed to create pipes";
        return result;
    }
    
    pid_t pid = fork();
    if (pid == -1) {
        result.return_code = -1;
        result.stderr_data = "Failed to fork process";
        return result;
    }
    
    if (pid == 0) {
        // Child process
        close(stdout_pipe[0]);
        close(stderr_pipe[0]);
        
        dup2(stdout_pipe[1], STDOUT_FILENO);
        dup2(stderr_pipe[1], STDERR_FILENO);
        
        close(stdout_pipe[1]);
        close(stderr_pipe[1]);
        
        // Execute the command
        execl("/bin/sh", "sh", "-c", command.c_str(), (char*)NULL);
        exit(127); // execl failed
    } else {
        // Parent process
        close(stdout_pipe[1]);
        close(stderr_pipe[1]);
        
        // Read stdout
        char buffer[1024];
        ssize_t bytes_read;
        while ((bytes_read = read(stdout_pipe[0], buffer, sizeof(buffer))) > 0) {
            result.stdout_data.append(buffer, bytes_read);
        }
        
        // Read stderr
        while ((bytes_read = read(stderr_pipe[0], buffer, sizeof(buffer))) > 0) {
            result.stderr_data.append(buffer, bytes_read);
        }
        
        close(stdout_pipe[0]);
        close(stderr_pipe[0]);
        
        // Wait for child process
        int status;
        waitpid(pid, &status, 0);
        result.return_code = WEXITSTATUS(status);
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    result.execution_time_ms = duration.count();
    
    return result;
}

TradingCommon::WorkerResult WorkerSpawner::spawnWorker(const TradingCommon::SimulationConfig& config) {
    std::string command = buildCommandLine(config);
    TradingCommon::WorkerResult result = executeWorker(command);
    result.symbols = config.symbols;
    return result;
}

std::vector<TradingCommon::WorkerResult> WorkerSpawner::spawnParallelWorkers(
    const std::vector<TradingCommon::SimulationConfig>& configs) {
    
    std::vector<TradingCommon::WorkerResult> results;
    results.reserve(configs.size());
    
    std::cout << "Spawning " << configs.size() << " workers in parallel (max " << max_workers_ << ")" << std::endl;
    
    // For now, execute sequentially (parallel execution can be added later with proper thread management)
    for (const auto& config : configs) {
        results.push_back(spawnWorker(config));
    }
    
    return results;
}

} // namespace TradingOrchestrator