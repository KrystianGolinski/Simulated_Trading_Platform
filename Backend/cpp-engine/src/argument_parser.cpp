#include "argument_parser.h"
#include "trading_engine.h"  // Include for TradingConfig definition
#include "logger.h"
#include <sstream>
#include <algorithm>
#include <iostream>

ArgumentParser::ArgumentParser() {}

TradingConfig ArgumentParser::parseArguments(int argc, char* argv[]) {
    TradingConfig config;
    
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

void ArgumentParser::parseKeyValueFormat(const std::string& arg, TradingConfig& config) {
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
        config.starting_capital = std::stod(arg.substr(10));
        Logger::debug("Set starting_capital = ", config.starting_capital);
    } else if (arg.find("--strategy=") == 0) {
        config.strategy_name = arg.substr(11);
        Logger::debug("Set strategy_name = '", config.strategy_name, "'");
    } else if (arg.find("--short-ma=") == 0) {
        config.setParameter("short_ma", std::stod(arg.substr(11)));
        Logger::debug("Set short_ma = ", config.getDoubleParameter("short_ma"));
    } else if (arg.find("--long-ma=") == 0) {
        config.setParameter("long_ma", std::stod(arg.substr(10)));
        Logger::debug("Set long_ma = ", config.getDoubleParameter("long_ma"));
    } else if (arg.find("--rsi-period=") == 0) {
        config.setParameter("rsi_period", std::stod(arg.substr(13)));
        Logger::debug("Set rsi_period = ", config.getDoubleParameter("rsi_period"));
    } else if (arg.find("--rsi-oversold=") == 0) {
        config.setParameter("rsi_oversold", std::stod(arg.substr(15)));
        Logger::debug("Set rsi_oversold = ", config.getDoubleParameter("rsi_oversold"));
    } else if (arg.find("--rsi-overbought=") == 0) {
        config.setParameter("rsi_overbought", std::stod(arg.substr(17)));
        Logger::debug("Set rsi_overbought = ", config.getDoubleParameter("rsi_overbought"));
    }
}

void ArgumentParser::parseKeyValuePairFormat(const std::string& key, const std::string& value, TradingConfig& config) {
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
        config.starting_capital = std::stod(value);
        Logger::debug("Set starting_capital = ", config.starting_capital);
    } else if (key == "--strategy") {
        config.strategy_name = value;
        Logger::debug("Set strategy_name = '", config.strategy_name, "'");
    } else if (key == "--short-ma") {
        config.setParameter("short_ma", std::stod(value));
        Logger::debug("Set short_ma = ", config.getDoubleParameter("short_ma"));
    } else if (key == "--long-ma") {
        config.setParameter("long_ma", std::stod(value));
        Logger::debug("Set long_ma = ", config.getDoubleParameter("long_ma"));
    } else if (key == "--rsi-period") {
        config.setParameter("rsi_period", std::stod(value));
        Logger::debug("Set rsi_period = ", config.getDoubleParameter("rsi_period"));
    } else if (key == "--rsi-oversold") {
        config.setParameter("rsi_oversold", std::stod(value));
        Logger::debug("Set rsi_oversold = ", config.getDoubleParameter("rsi_oversold"));
    } else if (key == "--rsi-overbought") {
        config.setParameter("rsi_overbought", std::stod(value));
        Logger::debug("Set rsi_overbought = ", config.getDoubleParameter("rsi_overbought"));
    }
}

void ArgumentParser::setDefaults(TradingConfig& config) {
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

void ArgumentParser::debugPrintConfig(const TradingConfig& config) {
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
    Logger::debug("  starting_capital = ", config.starting_capital);
    Logger::debug("  strategy_name = '", config.strategy_name, "'");
    
    // Print all strategy parameters dynamically
    Logger::debug("  strategy_parameters = {");
    for (const auto& param : config.strategy_parameters) {
        Logger::debug("    ", param.first, " = ", param.second);
    }
    Logger::debug("  }");
}

std::string ArgumentParser::trimWhitespace(const std::string& str) {
    size_t start = str.find_first_not_of(" \t");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t");
    return str.substr(start, end - start + 1);
}