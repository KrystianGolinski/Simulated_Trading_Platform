#include "argument_parser.h"
#include "logger.h"
#include <sstream>
#include <algorithm>
#include <iostream>

ArgumentParser::ArgumentParser() {}

SimulationConfig ArgumentParser::parseArguments(int argc, char* argv[]) {
    SimulationConfig config;
    
    Logger::debug("Parsing ", argc, " arguments:");
    for (int i = 0; i < argc; ++i) {
        Logger::debug("argv[", i, "] = '", argv[i], "'");
    }
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        Logger::debug("Processing argument: '", arg, "'");
        
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
        Logger::debug("Set symbols from key=value format");
    } else if (arg.find("--start=") == 0) {
        config.start_date = arg.substr(8);
        Logger::debug("Set start_date = '", config.start_date, "'");
    } else if (arg.find("--end=") == 0) {
        config.end_date = arg.substr(6);
        Logger::debug("Set end_date = '", config.end_date, "'");
    } else if (arg.find("--capital=") == 0) {
        config.capital = std::stod(arg.substr(10));
        Logger::debug("Set capital = ", config.capital);
    } else if (arg.find("--short-ma=") == 0) {
        config.short_ma = std::stoi(arg.substr(11));
        Logger::debug("Set short_ma = ", config.short_ma);
    } else if (arg.find("--long-ma=") == 0) {
        config.long_ma = std::stoi(arg.substr(10));
        Logger::debug("Set long_ma = ", config.long_ma);
    } else if (arg.find("--strategy=") == 0) {
        config.strategy = arg.substr(11);
        Logger::debug("Set strategy = '", config.strategy, "'");
    } else if (arg.find("--rsi-period=") == 0) {
        config.rsi_period = std::stoi(arg.substr(13));
        Logger::debug("Set rsi_period = ", config.rsi_period);
    } else if (arg.find("--rsi-oversold=") == 0) {
        config.rsi_oversold = std::stod(arg.substr(15));
        Logger::debug("Set rsi_oversold = ", config.rsi_oversold);
    } else if (arg.find("--rsi-overbought=") == 0) {
        config.rsi_overbought = std::stod(arg.substr(17));
        Logger::debug("Set rsi_overbought = ", config.rsi_overbought);
    }
}

void ArgumentParser::parseKeyValuePairFormat(const std::string& key, const std::string& value, SimulationConfig& config) {
    if (key == "--symbol") {
        parseSymbols(value, config.symbols);
        Logger::debug("Set symbols from key value format");
    } else if (key == "--start") {
        config.start_date = value;
        Logger::debug("Set start_date = '", config.start_date, "'");
    } else if (key == "--end") {
        config.end_date = value;
        Logger::debug("Set end_date = '", config.end_date, "'");
    } else if (key == "--capital") {
        config.capital = std::stod(value);
        Logger::debug("Set capital = ", config.capital);
    } else if (key == "--short-ma") {
        config.short_ma = std::stoi(value);
        Logger::debug("Set short_ma = ", config.short_ma);
    } else if (key == "--long-ma") {
        config.long_ma = std::stoi(value);
        Logger::debug("Set long_ma = ", config.long_ma);
    } else if (key == "--strategy") {
        config.strategy = value;
        Logger::debug("Set strategy = '", config.strategy, "'");
    } else if (key == "--rsi-period") {
        config.rsi_period = std::stoi(value);
        Logger::debug("Set rsi_period = ", config.rsi_period);
    } else if (key == "--rsi-oversold") {
        config.rsi_oversold = std::stod(value);
        Logger::debug("Set rsi_oversold = ", config.rsi_oversold);
    } else if (key == "--rsi-overbought") {
        config.rsi_overbought = std::stod(value);
        Logger::debug("Set rsi_overbought = ", config.rsi_overbought);
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
    Logger::debug("Final parsed values:");
    
    std::ostringstream symbols_stream;
    symbols_stream << "  symbols = { ";
    for (size_t i = 0; i < config.symbols.size(); ++i) {
        symbols_stream << "'" << config.symbols[i] << "'";
        if (i < config.symbols.size() - 1) symbols_stream << ", ";
    }
    symbols_stream << " }";
    Logger::debug(symbols_stream.str());
    
    Logger::debug("  start_date = '", config.start_date, "'");
    Logger::debug("  end_date = '", config.end_date, "'");
    Logger::debug("  capital = ", config.capital);
    Logger::debug("  short_ma = ", config.short_ma);
    Logger::debug("  long_ma = ", config.long_ma);
    Logger::debug("  strategy = '", config.strategy, "'");
    Logger::debug("  rsi_period = ", config.rsi_period);
    Logger::debug("  rsi_oversold = ", config.rsi_oversold);
    Logger::debug("  rsi_overbought = ", config.rsi_overbought);
}

std::string ArgumentParser::trimWhitespace(const std::string& str) {
    size_t start = str.find_first_not_of(" \t");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t");
    return str.substr(start, end - start + 1);
}