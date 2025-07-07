#pragma once

#include "argument_parser.h"
#include <string>

// Forward declarations
class TradingEngine;

class CommandDispatcher {
public:
    CommandDispatcher();
    
    int execute(int argc, char* argv[]);
    
private:
    int executeTest(const TradingConfig& config);
    int executeBacktest(const TradingConfig& config);
    int executeSimulation(const TradingConfig& config);
    int executeSimulationFromConfig(const std::string& config_file);
    int executeStatus();
    int executeMemoryReport();
    int showHelp(const char* program_name);
    
    void printHeader();
    void testDatabase(const std::string& symbol, const std::string& start_date, const std::string& end_date);
    
    // Common execution methods to eliminate duplication
    void setupStrategy(TradingEngine& engine, const TradingConfig& config, bool verbose = false);
    int executeCommonSimulation(const TradingConfig& config, bool verbose = false);
    TradingConfig loadConfigFromFile(const std::string& config_file);
    
    ArgumentParser arg_parser;
};