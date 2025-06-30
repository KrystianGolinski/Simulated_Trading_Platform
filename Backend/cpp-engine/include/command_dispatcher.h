#pragma once

#include "argument_parser.h"
#include <string>

class CommandDispatcher {
public:
    CommandDispatcher();
    
    int execute(int argc, char* argv[]);
    
private:
    int executeTest(const SimulationConfig& config);
    int executeBacktest(const SimulationConfig& config);
    int executeSimulation(const SimulationConfig& config);
    int executeSimulationFromConfig(const std::string& config_file);
    int executeStatus();
    int showHelp(const char* program_name);
    
    void printHeader();
    void testDatabase(const std::string& symbol, const std::string& start_date, const std::string& end_date);
    void runBacktest(const SimulationConfig& config);
    bool runSimulationFromConfig(const std::string& config_file);
    
    ArgumentParser arg_parser;
};