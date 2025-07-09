#pragma once

#include <map>
#include <string>
#include <vector>

// Forward declare TradingConfig - will be included via the implementation file
struct TradingConfig;

class ArgumentParser {
public:
    ArgumentParser();
    
    TradingConfig parseArguments(int argc, char* argv[]);
    
private:
    void parseSymbols(const std::string& symbol_list, std::vector<std::string>& symbols);
    void parseKeyValueFormat(const std::string& arg, TradingConfig& config);
    void parseKeyValuePairFormat(const std::string& key, const std::string& value, TradingConfig& config);
    void setDefaults(TradingConfig& config);
    void debugPrintConfig(const TradingConfig& config);
    
    std::string trimWhitespace(const std::string& str);
};