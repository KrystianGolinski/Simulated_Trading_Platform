#pragma once

#include <string>
#include <vector>
#include <map>

struct SimulationConfig {
    std::vector<std::string> symbols;
    std::string start_date;
    std::string end_date;
    double capital;
    std::string strategy;
    std::map<std::string, double> strategy_parameters;
    
    SimulationConfig() : capital(10000.0), strategy("ma_crossover") {
        // Set default parameters for ma_crossover strategy
        strategy_parameters["short_ma"] = 20.0;
        strategy_parameters["long_ma"] = 50.0;
        // Set default parameters for rsi strategy
        strategy_parameters["rsi_period"] = 14.0;
        strategy_parameters["rsi_oversold"] = 30.0;
        strategy_parameters["rsi_overbought"] = 70.0;
    }
    
    // Helper methods to retrieve strategy parameters with type safety
    int getIntParameter(const std::string& key, int default_value = 0) const {
        auto it = strategy_parameters.find(key);
        return (it != strategy_parameters.end()) ? static_cast<int>(it->second) : default_value;
    }
    
    double getDoubleParameter(const std::string& key, double default_value = 0.0) const {
        auto it = strategy_parameters.find(key);
        return (it != strategy_parameters.end()) ? it->second : default_value;
    }
    
    void setParameter(const std::string& key, double value) {
        strategy_parameters[key] = value;
    }
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