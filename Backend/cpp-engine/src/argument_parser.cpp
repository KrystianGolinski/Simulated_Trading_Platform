#include "argument_parser.h"
#include <sstream>
#include <algorithm>

ArgumentParser::ArgumentParser() {}

SimulationConfig ArgumentParser::parseArguments(int argc, char* argv[]) {
    SimulationConfig config;
    
    std::cerr << "[DEBUG] Parsing " << argc << " arguments:" << std::endl;
    for (int i = 0; i < argc; ++i) {
        std::cerr << "[DEBUG] argv[" << i << "] = '" << argv[i] << "'" << std::endl;
    }
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        std::cerr << "[DEBUG] Processing argument: '" << arg << "'" << std::endl;
        
        if (arg.find('=') != std::string::npos) {
            parseKeyValueFormat(arg, config);
        } else if (i + 1 < argc && arg.substr(0, 2) == "--") {
            parseKeyValuePairFormat(arg, argv[++i], config);
        }
    }
    
    setDefaults(config);
    debugPrintConfig(config);
    
    return config;
}

void ArgumentParser::parseSymbols(const std::string& symbol_list, std::vector<std::string>& symbols) {
    std::stringstream ss(symbol_list);
    std::string symbol;
    symbols.clear();
    
    while (std::getline(ss, symbol, ',')) {
        symbol = trimWhitespace(symbol);
        if (!symbol.empty()) {
            symbols.push_back(symbol);
        }
    }
}

void ArgumentParser::parseKeyValueFormat(const std::string& arg, SimulationConfig& config) {
    if (arg.find("--symbol=") == 0) {
        std::string symbol_list = arg.substr(9);
        parseSymbols(symbol_list, config.symbols);
        std::cerr << "[DEBUG] Set symbols from key=value format" << std::endl;
    } else if (arg.find("--start=") == 0) {
        config.start_date = arg.substr(8);
        std::cerr << "[DEBUG] Set start_date = '" << config.start_date << "'" << std::endl;
    } else if (arg.find("--end=") == 0) {
        config.end_date = arg.substr(6);
        std::cerr << "[DEBUG] Set end_date = '" << config.end_date << "'" << std::endl;
    } else if (arg.find("--capital=") == 0) {
        config.capital = std::stod(arg.substr(10));
        std::cerr << "[DEBUG] Set capital = " << config.capital << std::endl;
    } else if (arg.find("--short-ma=") == 0) {
        config.short_ma = std::stoi(arg.substr(11));
        std::cerr << "[DEBUG] Set short_ma = " << config.short_ma << std::endl;
    } else if (arg.find("--long-ma=") == 0) {
        config.long_ma = std::stoi(arg.substr(10));
        std::cerr << "[DEBUG] Set long_ma = " << config.long_ma << std::endl;
    } else if (arg.find("--strategy=") == 0) {
        config.strategy = arg.substr(11);
        std::cerr << "[DEBUG] Set strategy = '" << config.strategy << "'" << std::endl;
    } else if (arg.find("--rsi-period=") == 0) {
        config.rsi_period = std::stoi(arg.substr(13));
        std::cerr << "[DEBUG] Set rsi_period = " << config.rsi_period << std::endl;
    } else if (arg.find("--rsi-oversold=") == 0) {
        config.rsi_oversold = std::stod(arg.substr(15));
        std::cerr << "[DEBUG] Set rsi_oversold = " << config.rsi_oversold << std::endl;
    } else if (arg.find("--rsi-overbought=") == 0) {
        config.rsi_overbought = std::stod(arg.substr(17));
        std::cerr << "[DEBUG] Set rsi_overbought = " << config.rsi_overbought << std::endl;
    }
}

void ArgumentParser::parseKeyValuePairFormat(const std::string& key, const std::string& value, SimulationConfig& config) {
    if (key == "--symbol") {
        parseSymbols(value, config.symbols);
        std::cerr << "[DEBUG] Set symbols from key value format" << std::endl;
    } else if (key == "--start") {
        config.start_date = value;
        std::cerr << "[DEBUG] Set start_date = '" << config.start_date << "'" << std::endl;
    } else if (key == "--end") {
        config.end_date = value;
        std::cerr << "[DEBUG] Set end_date = '" << config.end_date << "'" << std::endl;
    } else if (key == "--capital") {
        config.capital = std::stod(value);
        std::cerr << "[DEBUG] Set capital = " << config.capital << std::endl;
    } else if (key == "--short-ma") {
        config.short_ma = std::stoi(value);
        std::cerr << "[DEBUG] Set short_ma = " << config.short_ma << std::endl;
    } else if (key == "--long-ma") {
        config.long_ma = std::stoi(value);
        std::cerr << "[DEBUG] Set long_ma = " << config.long_ma << std::endl;
    } else if (key == "--strategy") {
        config.strategy = value;
        std::cerr << "[DEBUG] Set strategy = '" << config.strategy << "'" << std::endl;
    } else if (key == "--rsi-period") {
        config.rsi_period = std::stoi(value);
        std::cerr << "[DEBUG] Set rsi_period = " << config.rsi_period << std::endl;
    } else if (key == "--rsi-oversold") {
        config.rsi_oversold = std::stod(value);
        std::cerr << "[DEBUG] Set rsi_oversold = " << config.rsi_oversold << std::endl;
    } else if (key == "--rsi-overbought") {
        config.rsi_overbought = std::stod(value);
        std::cerr << "[DEBUG] Set rsi_overbought = " << config.rsi_overbought << std::endl;
    }
}

void ArgumentParser::setDefaults(SimulationConfig& config) {
    if (config.symbols.empty()) {
        config.symbols.push_back("AAPL");
    }
    if (config.start_date.empty()) {
        config.start_date = "2023-01-01";
    }
    if (config.end_date.empty()) {
        config.end_date = "2023-12-31";
    }
}

void ArgumentParser::debugPrintConfig(const SimulationConfig& config) {
    std::cerr << "[DEBUG] Final parsed values:" << std::endl;
    std::cerr << "[DEBUG]   symbols = { ";
    for (size_t i = 0; i < config.symbols.size(); ++i) {
        std::cerr << "'" << config.symbols[i] << "'";
        if (i < config.symbols.size() - 1) std::cerr << ", ";
    }
    std::cerr << " }" << std::endl;
    std::cerr << "[DEBUG]   start_date = '" << config.start_date << "'" << std::endl;
    std::cerr << "[DEBUG]   end_date = '" << config.end_date << "'" << std::endl;
    std::cerr << "[DEBUG]   capital = " << config.capital << std::endl;
    std::cerr << "[DEBUG]   short_ma = " << config.short_ma << std::endl;
    std::cerr << "[DEBUG]   long_ma = " << config.long_ma << std::endl;
    std::cerr << "[DEBUG]   strategy = '" << config.strategy << "'" << std::endl;
    std::cerr << "[DEBUG]   rsi_period = " << config.rsi_period << std::endl;
    std::cerr << "[DEBUG]   rsi_oversold = " << config.rsi_oversold << std::endl;
    std::cerr << "[DEBUG]   rsi_overbought = " << config.rsi_overbought << std::endl;
}

std::string ArgumentParser::trimWhitespace(const std::string& str) {
    size_t start = str.find_first_not_of(" \t");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t");
    return str.substr(start, end - start + 1);
}