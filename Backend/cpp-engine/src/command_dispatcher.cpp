#include "command_dispatcher.h"
#include "trading_engine.h"
#include "market_data.h"
#include <iostream>
#include <fstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

CommandDispatcher::CommandDispatcher() {}

int CommandDispatcher::execute(int argc, char* argv[]) {
    try {
        if (argc > 1) {
            std::string command = argv[1];
            
            if (command != "--simulate") {
                printHeader();
            }
            
            if (command == "--test-db") {
                SimulationConfig config = arg_parser.parseArguments(argc, argv);
                return executeTest(config);
            } else if (command == "--backtest") {
                SimulationConfig config = arg_parser.parseArguments(argc, argv);
                return executeBacktest(config);
            } else if (command == "--simulate") {
                if (argc > 3 && std::string(argv[2]) == "--config") {
                    return executeSimulationFromConfig(argv[3]);
                } else {
                    SimulationConfig config = arg_parser.parseArguments(argc, argv);
                    return executeSimulation(config);
                }
            } else if (command == "--status") {
                return executeStatus();
            } else {
                return showHelp(argv[0]);
            }
        } else {
            return showHelp(argv[0]);
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}

int CommandDispatcher::executeTest(const SimulationConfig& config) {
    testDatabase(config.symbols.empty() ? "AAPL" : config.symbols[0], 
                config.start_date, config.end_date);
    return 0;
}

int CommandDispatcher::executeBacktest(const SimulationConfig& config) {
    runBacktest(config);
    return 0;
}

int CommandDispatcher::executeSimulation(const SimulationConfig& config) {
    std::cerr << "[DEBUG] About to run simulation with:" << std::endl;
    std::cerr << "[DEBUG]   symbols = { ";
    for (size_t i = 0; i < config.symbols.size(); ++i) {
        std::cerr << "'" << config.symbols[i] << "'";
        if (i < config.symbols.size() - 1) std::cerr << ", ";
    }
    std::cerr << " }" << std::endl;
    std::cerr << "[DEBUG]   start_date = '" << config.start_date << "'" << std::endl;
    std::cerr << "[DEBUG]   end_date = '" << config.end_date << "'" << std::endl;
    std::cerr << "[DEBUG]   capital = " << config.capital << std::endl;
    std::cerr << "[DEBUG]   strategy = '" << config.strategy << "'" << std::endl;
    
    TradingEngine engine(config.capital);
    
    if (config.strategy == "ma_crossover") {
        std::cerr << "[DEBUG]   short_ma = " << config.short_ma << std::endl;
        std::cerr << "[DEBUG]   long_ma = " << config.long_ma << std::endl;
        engine.setMovingAverageStrategy(config.short_ma, config.long_ma);
    } else if (config.strategy == "rsi") {
        std::cerr << "[DEBUG]   rsi_period = " << config.rsi_period << std::endl;
        std::cerr << "[DEBUG]   rsi_oversold = " << config.rsi_oversold << std::endl;
        std::cerr << "[DEBUG]   rsi_overbought = " << config.rsi_overbought << std::endl;
        engine.setRSIStrategy(config.rsi_period, config.rsi_oversold, config.rsi_overbought);
    } else {
        std::cerr << "[DEBUG] Unknown strategy '" << config.strategy << "', defaulting to MA crossover" << std::endl;
        engine.setMovingAverageStrategy(config.short_ma, config.long_ma);
    }
    
    std::string result;
    if (config.symbols.size() == 1) {
        result = engine.runSimulationWithParams(config.symbols[0], config.start_date, config.end_date, config.capital);
    } else {
        BacktestResult backtest_result = engine.runBacktestMultiSymbol(config.symbols, config.start_date, config.end_date, config.capital);
        nlohmann::json json_result = engine.getBacktestResultsAsJson(backtest_result);
        result = json_result.dump(2);
    }
    std::cout << result << std::endl;
    
    return 0;
}

int CommandDispatcher::executeSimulationFromConfig(const std::string& config_file) {
    std::cerr << "[DEBUG] Using JSON config file: " << config_file << std::endl;
    
    if (!runSimulationFromConfig(config_file)) {
        std::cerr << "Error: Failed to run simulation from config file" << std::endl;
        return 1;
    }
    return 0;
}

int CommandDispatcher::executeStatus() {
    TradingEngine engine(10000.0);
    std::cout << engine.getPortfolioStatus() << std::endl;
    return 0;
}

int CommandDispatcher::showHelp(const char* program_name) {
    printHeader();
    std::cout << "\nUsage:" << std::endl;
    std::cout << "  " << program_name << " --simulate              Run simulation and output JSON" << std::endl;
    std::cout << "  " << program_name << " --status                Show portfolio status" << std::endl;
    std::cout << "  " << program_name << " --test-db [options]     Test database connectivity" << std::endl;
    std::cout << "  " << program_name << " --backtest [options]    Run backtest with moving average strategy" << std::endl;
    std::cout << "  " << program_name << " --help                  Show this help" << std::endl;
    std::cout << "\nOptions:" << std::endl;
    std::cout << "  --symbol SYMBOL(S) Stock symbol(s) to analyze, comma-separated for multi-symbol (default: AAPL)" << std::endl;
    std::cout << "  --start DATE      Start date (default: 2023-01-01)" << std::endl;
    std::cout << "  --end DATE        End date (default: 2023-12-31)" << std::endl;
    std::cout << "  --capital AMOUNT  Starting capital (default: 10000)" << std::endl;
    return 0;
}

void CommandDispatcher::printHeader() {
    std::cout << "Trading Engine C++ Backend" << std::endl;
}

void CommandDispatcher::testDatabase(const std::string& symbol, const std::string& start_date, const std::string& end_date) {
    std::cout << "Testing database connectivity..." << std::endl;
    
    try {
        MarketData market_data;
        
        if (!market_data.testDatabaseConnection()) {
            std::cout << "[FAIL] Database connection failed" << std::endl;
            return;
        }
        std::cout << "[PASS] Database connection successful" << std::endl;
        
        if (!symbol.empty()) {
            if (market_data.symbolExists(symbol)) {
                std::cout << "[PASS] Symbol " << symbol << " exists in database" << std::endl;
                
                auto summary = market_data.getDataSummary(symbol, start_date, end_date);
                std::cout << "Data Summary:" << std::endl;
                std::cout << summary.dump(2) << std::endl;
                
            } else {
                std::cout << "[FAIL] Symbol " << symbol << " not found in database" << std::endl;
            }
        }
        
        auto symbols = market_data.getAvailableSymbols();
        std::cout << "Available symbols (" << symbols.size() << " total):" << std::endl;
        for (size_t i = 0; i < std::min(symbols.size(), size_t(10)); ++i) {
            std::cout << "  - " << symbols[i] << std::endl;
        }
        if (symbols.size() > 10) {
            std::cout << "  ... and " << (symbols.size() - 10) << " more" << std::endl;
        }
        
        auto db_info = market_data.getDatabaseInfo();
        std::cout << "Database Info:" << std::endl;
        std::cout << db_info.dump(2) << std::endl;
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Database test failed: " << e.what() << std::endl;
    }
}

void CommandDispatcher::runBacktest(const SimulationConfig& config) {
    std::cout << "Running backtest..." << std::endl;
    std::cout << "Symbols: ";
    for (size_t i = 0; i < config.symbols.size(); ++i) {
        std::cout << config.symbols[i];
        if (i < config.symbols.size() - 1) std::cout << ", ";
    }
    std::cout << std::endl;
    std::cout << "Period: " << config.start_date << " to " << config.end_date << std::endl;
    std::cout << "Starting Capital: $" << config.capital << std::endl;
    std::cout << "Strategy: " << config.strategy << std::endl;
    
    try {
        TradingEngine engine(config.capital);
        
        if (config.strategy == "ma_crossover") {
            std::cout << "MA Crossover Parameters: Short=" << config.short_ma << ", Long=" << config.long_ma << std::endl;
            engine.setMovingAverageStrategy(config.short_ma, config.long_ma);
        } else if (config.strategy == "rsi") {
            std::cout << "RSI Parameters: Period=" << config.rsi_period << ", Oversold=" << config.rsi_oversold << ", Overbought=" << config.rsi_overbought << std::endl;
            engine.setRSIStrategy(config.rsi_period, config.rsi_oversold, config.rsi_overbought);
        } else {
            std::cout << "Unknown strategy, defaulting to MA Crossover" << std::endl;
            engine.setMovingAverageStrategy(config.short_ma, config.long_ma);
        }
        
        BacktestResult result;
        if (config.symbols.size() == 1) {
            BacktestConfig backtest_config;
            backtest_config.symbol = config.symbols[0];
            backtest_config.start_date = config.start_date;
            backtest_config.end_date = config.end_date;
            backtest_config.starting_capital = config.capital;
            backtest_config.strategy_name = config.strategy;
            
            if (config.strategy == "ma_crossover") {
                backtest_config.strategy_config.setParameter("short_period", config.short_ma);
                backtest_config.strategy_config.setParameter("long_period", config.long_ma);
            } else if (config.strategy == "rsi") {
                backtest_config.strategy_config.setParameter("rsi_period", config.rsi_period);
                backtest_config.strategy_config.setParameter("oversold_threshold", config.rsi_oversold);
                backtest_config.strategy_config.setParameter("overbought_threshold", config.rsi_overbought);
            }
            backtest_config.strategy_config.max_position_size = 0.1;
            backtest_config.strategy_config.enable_risk_management = true;
            
            result = engine.runBacktest(backtest_config);
        } else {
            result = engine.runBacktestMultiSymbol(config.symbols, config.start_date, config.end_date, config.capital);
        }
        
        nlohmann::json json_result = engine.getBacktestResultsAsJson(result);
        std::cout << json_result.dump(2) << std::endl;
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Backtest failed: " << e.what() << std::endl;
    }
}

bool CommandDispatcher::runSimulationFromConfig(const std::string& config_file) {
    try {
        std::ifstream file(config_file);
        if (!file.is_open()) {
            std::cerr << "Error: Cannot open config file: " << config_file << std::endl;
            return false;
        }
        
        json config;
        file >> config;
        file.close();
        
        std::vector<std::string> symbols;
        if (config.contains("symbols") && config["symbols"].is_array()) {
            for (const auto& s : config["symbols"]) {
                symbols.push_back(s.get<std::string>());
            }
        } else if (config.contains("symbol")) {
            symbols.push_back(config.value("symbol", "AAPL"));
        } else {
            symbols.push_back("AAPL");
        }
        
        std::string start_date = config.value("start_date", "2023-01-01");
        std::string end_date = config.value("end_date", "2023-12-31");
        double capital = config.value("starting_capital", 10000.0);
        std::string strategy = config.value("strategy", "ma_crossover");
        
        int short_ma = config.value("short_ma", 20);
        int long_ma = config.value("long_ma", 50);
        int rsi_period = config.value("rsi_period", 14);
        double rsi_oversold = config.value("rsi_oversold", 30.0);
        double rsi_overbought = config.value("rsi_overbought", 70.0);
        
        std::cerr << "[DEBUG] Config loaded successfully:" << std::endl;
        std::cerr << "[DEBUG]   symbols = { ";
        for (size_t i = 0; i < symbols.size(); ++i) {
            std::cerr << "'" << symbols[i] << "'";
            if (i < symbols.size() - 1) std::cerr << ", ";
        }
        std::cerr << " }" << std::endl;
        std::cerr << "[DEBUG]   start_date = '" << start_date << "'" << std::endl;
        std::cerr << "[DEBUG]   end_date = '" << end_date << "'" << std::endl;
        std::cerr << "[DEBUG]   capital = " << capital << std::endl;
        std::cerr << "[DEBUG]   strategy = '" << strategy << "'" << std::endl;
        
        TradingEngine engine(capital);
        
        if (strategy == "ma_crossover") {
            engine.setMovingAverageStrategy(short_ma, long_ma);
            std::cerr << "[DEBUG]   short_ma = " << short_ma << std::endl;
            std::cerr << "[DEBUG]   long_ma = " << long_ma << std::endl;
        } else if (strategy == "rsi") {
            engine.setRSIStrategy(rsi_period, rsi_oversold, rsi_overbought);
            std::cerr << "[DEBUG]   rsi_period = " << rsi_period << std::endl;
            std::cerr << "[DEBUG]   rsi_oversold = " << rsi_oversold << std::endl;
            std::cerr << "[DEBUG]   rsi_overbought = " << rsi_overbought << std::endl;
        }
        
        std::string result;
        if (symbols.size() == 1) {
            result = engine.runSimulationWithParams(symbols[0], start_date, end_date, capital);
        } else {
            BacktestResult backtest_result = engine.runBacktestMultiSymbol(symbols, start_date, end_date, capital);
            nlohmann::json json_result = engine.getBacktestResultsAsJson(backtest_result);
            result = json_result.dump(2);
        }
        std::cout << result << std::endl;
        
        if (config.value("cleanup", true)) {
            std::remove(config_file.c_str());
            std::cerr << "[DEBUG] Config file cleaned up" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing config file: " << e.what() << std::endl;
        return false;
    }
}