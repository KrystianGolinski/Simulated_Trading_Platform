#pragma once

#include <string>
#include <vector>

struct SimulationConfig {
    std::vector<std::string> symbols;
    std::string start_date;
    std::string end_date;
    double capital;
    std::string strategy;
    int short_ma;
    int long_ma;
    int rsi_period; 
    double rsi_oversold;
    double rsi_overbought;
    
    SimulationConfig() 
        : capital(10000.0), strategy("ma_crossover"), short_ma(20), long_ma(50),
          rsi_period(14), rsi_oversold(30.0), rsi_overbought(70.0) {}
};

class ArgumentParser {
public:
    ArgumentParser();
    
    SimulationConfig parseArguments(int argc, char* argv[]);
    
private:
    void parseSymbols(const std::string& symbol_list, std::vector<std::string>& symbols);
    void parseKeyValueFormat(const std::string& arg, SimulationConfig& config);
    void parseKeyValuePairFormat(const std::string& key, const std::string& value, SimulationConfig& config);
    void setDefaults(SimulationConfig& config);
    void debugPrintConfig(const SimulationConfig& config);
    
    std::string trimWhitespace(const std::string& str);
};