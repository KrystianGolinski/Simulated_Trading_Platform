#include "worker_spawner.h"
#include <iostream>
#include <sstream>
#include <fstream>
#include <cstdlib>
#include <ctime>
#include <unistd.h>
#include <sys/wait.h>
#include <chrono>
#include <cmath>
#include <uuid/uuid.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

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
    // Create temporary JSON config file
    std::string config_file = createConfigFile(config);
    
    // Build command using --simulate --config format (matches working main branch)
    std::stringstream cmd;
    cmd << worker_path_;
    cmd << " --simulate --config " << config_file;
    
    return cmd.str();
}

std::string WorkerSpawner::createConfigFile(const TradingCommon::SimulationConfig& config) const {
    // Create JSON config matching the format expected by the working main branch
    json config_data = json::object();
    
    // Basic configuration  
    if (config.symbols.empty()) {
        config_data["symbols"] = json::array({"AAPL"});
    } else {
        config_data["symbols"] = config.symbols;  // nlohmann/json automatically converts std::vector to JSON array
    }
    config_data["start_date"] = config.start_date;
    config_data["end_date"] = config.end_date;
    config_data["starting_capital"] = config.starting_capital;
    config_data["cleanup"] = true;
    
    // Strategy configuration - API now sends pre-merged strategy parameters
    if (!config.strategy.empty()) {
        config_data["strategy"] = config.strategy;
        
        // Strategy parameters are already merged in the JSON by the API (like working main branch)
        // The API now sends strategy params at root level, so orchestrator just passes them through
        for (const auto& param : config.strategy_parameters) {
            // Convert string parameters to appropriate types
            try {
                // Try to convert to double first (handles both int and float)
                double value = std::stod(param.second);
                
                // Check if it's an integer value
                if (value == std::floor(value)) {
                    config_data[param.first] = static_cast<int>(value);
                } else {
                    config_data[param.first] = value;
                }
            } catch (const std::exception&) {
                // If conversion fails, keep as string
                config_data[param.first] = param.second;
            }
        }
    }
    
    // Generate unique temporary filename
    uuid_t uuid;
    uuid_generate(uuid);
    char uuid_str[37];
    uuid_unparse(uuid, uuid_str);
    
    std::string config_file = "/tmp/sim_config_" + std::string(uuid_str, 8) + ".json";
    
    // Write JSON to file
    try {
        std::ofstream file(config_file);
        file << config_data.dump(2);
        file.close();
        
        std::cout << "Created config file: " << config_file << " for strategy: " << config.strategy << std::endl;
        std::cout << "Config content: " << config_data.dump(2) << std::endl;
        return config_file;
    } catch (const std::exception& e) {
        std::cerr << "Failed to create config file: " << e.what() << std::endl;
        throw;
    }
}

TradingCommon::WorkerResult WorkerSpawner::executeWorker(const std::string& command) const {
    TradingCommon::WorkerResult result;
    auto start_time = std::chrono::high_resolution_clock::now();
    
    std::cout << "Executing: " << command << std::endl;
    std::cout << "============= TRADING ENGINE DEBUG =============" << std::endl;
    
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
    
    // Debug output
    std::cout << "STDOUT (" << result.stdout_data.length() << " chars):" << std::endl;
    std::cout << result.stdout_data << std::endl;
    std::cout << "STDERR (" << result.stderr_data.length() << " chars):" << std::endl;
    std::cout << result.stderr_data << std::endl;
    std::cout << "EXIT CODE: " << result.return_code << std::endl;
    std::cout << "============= END DEBUG =============" << std::endl;
    
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