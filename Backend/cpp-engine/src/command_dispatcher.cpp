#include "command_dispatcher.h"
#include "trading_engine.h"
#include "market_data.h"
#include "error_utils.h"
#include "result.h"
#include <iostream>
#include <fstream>
#include <algorithm>
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
                TradingConfig config = arg_parser.parseArguments(argc, argv);
                return executeTest(config);
            } else if (command == "--backtest") {
                TradingConfig config = arg_parser.parseArguments(argc, argv);
                return executeBacktest(config);
            } else if (command == "--simulate") {
                if (argc > 3 && std::string(argv[2]) == "--config") {
                    return executeSimulationFromConfig(argv[3]);
                } else {
                    TradingConfig config = arg_parser.parseArguments(argc, argv);
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

int CommandDispatcher::executeTest(const TradingConfig& config) {
    testDatabase(config.symbols.empty() ? "AAPL" : config.symbols[0], 
                config.start_date, config.end_date);
    return 0;
}

int CommandDispatcher::executeBacktest(const TradingConfig& config) {
    // Print backtest information
    std::cout << "Running backtest..." << std::endl;
    std::cout << "Symbols: ";
    for (size_t i = 0; i < config.symbols.size(); ++i) {
        std::cout << config.symbols[i];
        if (i < config.symbols.size() - 1) std::cout << ", ";
    }
    std::cout << std::endl;
    std::cout << "Period: " << config.start_date << " to " << config.end_date << std::endl;
    std::cout << "Starting Capital: $" << config.starting_capital << std::endl;
    std::cout << "Strategy: " << config.strategy_name << std::endl;
    
    // Print strategy parameters
    if (config.strategy_name == "ma_crossover") {
        int short_ma = config.getIntParameter("short_ma", 20);
        int long_ma = config.getIntParameter("long_ma", 50);
        std::cout << "MA Crossover Parameters: Short=" << short_ma << ", Long=" << long_ma << std::endl;
    } else if (config.strategy_name == "rsi") {
        int rsi_period = config.getIntParameter("rsi_period", 14);
        double rsi_oversold = config.getDoubleParameter("rsi_oversold", 30.0);
        double rsi_overbought = config.getDoubleParameter("rsi_overbought", 70.0);
        std::cout << "RSI Parameters: Period=" << rsi_period << ", Oversold=" << rsi_oversold << ", Overbought=" << rsi_overbought << std::endl;
    } else {
        std::cout << "Unknown strategy, defaulting to MA Crossover" << std::endl;
    }
    
    // Handle single-symbol backtest with proper BacktestConfig structure
    if (config.symbols.size() == 1) {
        try {
            TradingEngine engine(config.starting_capital);
            setupStrategy(engine, config);
            
            // For single-symbol backtests, ensure we have exactly one symbol
            TradingConfig backtest_config = config;
            if (backtest_config.symbols.size() != 1) {
                backtest_config.symbols = {config.symbols[0]}; // Take only the first symbol
            }
            
            auto backtest_result = engine.getTradingOrchestrator()->runBacktest(backtest_config, engine.getPortfolio(), engine.getMarketData(), engine.getExecutionService(), engine.getProgressService(), engine.getPortfolioAllocator(), engine.getDataProcessor(), engine.getStrategyManager(), engine.getResultCalculator());
            if (backtest_result.isError()) {
                std::cout << "[ERROR] Backtest failed: " << backtest_result.getErrorMessage() << std::endl;
                return 1;
            }
            
            auto json_result = engine.getTradingOrchestrator()->getBacktestResultsAsJson(backtest_result.getValue(), engine.getMarketData(), engine.getDataProcessor());
            if (json_result.isError()) {
                std::cout << "[ERROR] Failed to generate backtest results: " << json_result.getErrorMessage() << std::endl;
                return 1;
            }
            std::cout << json_result.getValue().dump(2) << std::endl;
            
        } catch (const std::exception& e) {
            std::cout << "[ERROR] Backtest failed: " << e.what() << std::endl;
            return 1;
        }
    } else {
        // Use common method for multi-symbol backtests
        return executeCommonSimulation(config, false);
    }
    
    return 0;
}

int CommandDispatcher::executeSimulation(const TradingConfig& config) {
    // Print debug information about the simulation configuration
    std::cerr << "[DEBUG] About to run simulation with:" << std::endl;
    std::cerr << "[DEBUG]   symbols = { ";
    for (size_t i = 0; i < config.symbols.size(); ++i) {
        std::cerr << "'" << config.symbols[i] << "'";
        if (i < config.symbols.size() - 1) std::cerr << ", ";
    }
    std::cerr << " }" << std::endl;
    std::cerr << "[DEBUG]   start_date = '" << config.start_date << "'" << std::endl;
    std::cerr << "[DEBUG]   end_date = '" << config.end_date << "'" << std::endl;
    std::cerr << "[DEBUG]   capital = " << config.starting_capital << std::endl;
    std::cerr << "[DEBUG]   strategy = '" << config.strategy_name << "'" << std::endl;
    
    // Print all strategy parameters dynamically
    std::cerr << "[DEBUG]   strategy_parameters = {" << std::endl;
    for (const auto& param : config.strategy_parameters) {
        std::cerr << "[DEBUG]     " << param.first << " = " << param.second << std::endl;
    }
    std::cerr << "[DEBUG]   }" << std::endl;
    
    // Use common execution method with verbose output
    return executeCommonSimulation(config, true);
}

int CommandDispatcher::executeSimulationFromConfig(const std::string& config_file) {
    std::cerr << "[DEBUG] Using JSON config file: " << config_file << std::endl;
    
    try {
        // Load configuration from file using common method
        TradingConfig config = loadConfigFromFile(config_file);
        
        // Print debug information about loaded configuration
        std::cerr << "[DEBUG] Config loaded successfully:" << std::endl;
        std::cerr << "[DEBUG]   symbols = { ";
        for (size_t i = 0; i < config.symbols.size(); ++i) {
            std::cerr << "'" << config.symbols[i] << "'";
            if (i < config.symbols.size() - 1) std::cerr << ", ";
        }
        std::cerr << " }" << std::endl;
        std::cerr << "[DEBUG]   start_date = '" << config.start_date << "'" << std::endl;
        std::cerr << "[DEBUG]   end_date = '" << config.end_date << "'" << std::endl;
        std::cerr << "[DEBUG]   capital = " << config.starting_capital << std::endl;
        std::cerr << "[DEBUG]   strategy = '" << config.strategy_name << "'" << std::endl;
        
        // Print strategy-specific parameters
        if (config.strategy_name == "ma_crossover") {
            std::cerr << "[DEBUG]   short_ma = " << config.getIntParameter("short_ma", 20) << std::endl;
            std::cerr << "[DEBUG]   long_ma = " << config.getIntParameter("long_ma", 50) << std::endl;
        } else if (config.strategy_name == "rsi") {
            std::cerr << "[DEBUG]   rsi_period = " << config.getIntParameter("rsi_period", 14) << std::endl;
            std::cerr << "[DEBUG]   rsi_oversold = " << config.getDoubleParameter("rsi_oversold", 30.0) << std::endl;
            std::cerr << "[DEBUG]   rsi_overbought = " << config.getDoubleParameter("rsi_overbought", 70.0) << std::endl;
        }
        
        // Execute simulation using common method
        int result = executeCommonSimulation(config, false);
        
        // Clean up config file if requested (check original file for cleanup flag)
        std::ifstream file(config_file);
        if (file.is_open()) {
            json file_config;
            file >> file_config;
            file.close();
            
            if (file_config.value("cleanup", true)) {
                std::remove(config_file.c_str());
                std::cerr << "[DEBUG] Config file cleaned up" << std::endl;
            }
        }
        
        return result;
        
    } catch (const std::exception& e) {
        std::cerr << "Error: Failed to run simulation from config file: " << e.what() << std::endl;
        return 1;
    }
}

int CommandDispatcher::executeStatus() {
    try {
        TradingEngine engine(10000.0);
        auto prices_result = engine.getMarketData()->getCurrentPrices();
        if (prices_result.isError()) {
            std::cerr << "Error getting current prices for portfolio status: " << prices_result.getErrorMessage() << std::endl;
            return 1;
        }
        std::cout << engine.getPortfolio().toDetailedString(prices_result.getValue()) << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Unexpected error: " << e.what() << std::endl;
        return 1;
    }
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
        
        auto conn_test = market_data.testDatabaseConnection();
        if (conn_test.isError()) {
            std::cout << "[FAIL] Database connection failed: " << conn_test.getErrorMessage() << std::endl;
            return;
        }
        std::cout << "[PASS] Database connection successful" << std::endl;
        
        if (!symbol.empty()) {
            auto exists_result = market_data.symbolExists(symbol);
            if (exists_result.isError()) {
                std::cout << "[ERROR] Failed to check symbol: " << exists_result.getErrorMessage() << std::endl;
            } else if (exists_result.getValue()) {
                std::cout << "[PASS] Symbol " << symbol << " exists in database" << std::endl;
                
                auto summary_result = market_data.getDataSummary(symbol, start_date, end_date);
                if (summary_result.isError()) {
                    std::cout << "[ERROR] Failed to get data summary: " << summary_result.getErrorMessage() << std::endl;
                } else {
                    std::cout << "Data Summary:" << std::endl;
                    std::cout << summary_result.getValue().dump(2) << std::endl;
                }
                
            } else {
                std::cout << "[FAIL] Symbol " << symbol << " not found in database" << std::endl;
            }
        }
        
        auto symbols_result = market_data.getAvailableSymbols();
        if (symbols_result.isError()) {
            std::cout << "[ERROR] Failed to get available symbols: " << symbols_result.getErrorMessage() << std::endl;
        } else {
            const auto& symbols = symbols_result.getValue();
            std::cout << "Available symbols (" << symbols.size() << " total):" << std::endl;
            for (size_t i = 0; i < std::min(symbols.size(), size_t(10)); ++i) {
                std::cout << "  - " << symbols[i] << std::endl;
            }
            if (symbols.size() > 10) {
                std::cout << "  ... and " << (symbols.size() - 10) << " more" << std::endl;
            }
        }
        
        auto db_info_result = market_data.getDatabaseInfo();
        if (db_info_result.isError()) {
            std::cout << "[ERROR] Failed to get database info: " << db_info_result.getErrorMessage() << std::endl;
        } else {
            std::cout << "Database Info:" << std::endl;
            std::cout << db_info_result.getValue().dump(2) << std::endl;
        }
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Database test failed: " << e.what() << std::endl;
    }
}

void CommandDispatcher::setupStrategy(TradingEngine& engine, const TradingConfig& config, bool verbose) {
    if (config.strategy_name == "ma_crossover") {
        int short_ma = config.getIntParameter("short_ma", 20);
        int long_ma = config.getIntParameter("long_ma", 50);
        if (verbose) {
            std::cerr << "[DEBUG]   Using MA crossover: short=" << short_ma << ", long=" << long_ma << std::endl;
        }
        auto strategy = engine.getStrategyManager()->createMovingAverageStrategy(short_ma, long_ma);
        engine.getStrategyManager()->setCurrentStrategy(std::move(strategy));
    } else if (config.strategy_name == "rsi") {
        int rsi_period = config.getIntParameter("rsi_period", 14);
        double rsi_oversold = config.getDoubleParameter("rsi_oversold", 30.0);
        double rsi_overbought = config.getDoubleParameter("rsi_overbought", 70.0);
        if (verbose) {
            std::cerr << "[DEBUG]   Using RSI: period=" << rsi_period << ", oversold=" << rsi_oversold << ", overbought=" << rsi_overbought << std::endl;
        }
        auto strategy = engine.getStrategyManager()->createRSIStrategy(rsi_period, rsi_oversold, rsi_overbought);
        engine.getStrategyManager()->setCurrentStrategy(std::move(strategy));
    } else {
        if (verbose) {
            std::cerr << "[DEBUG] Unknown strategy '" << config.strategy_name << "', defaulting to MA crossover" << std::endl;
        }
        int short_ma = config.getIntParameter("short_ma", 20);
        int long_ma = config.getIntParameter("long_ma", 50);
        auto strategy = engine.getStrategyManager()->createMovingAverageStrategy(short_ma, long_ma);
        engine.getStrategyManager()->setCurrentStrategy(std::move(strategy));
    }
}

int CommandDispatcher::executeCommonSimulation(const TradingConfig& config, bool verbose) {
    TradingEngine engine(config.starting_capital);
    setupStrategy(engine, config, verbose);
    
    try {
        // Use unified runSimulation method for all cases
        auto result = engine.getTradingOrchestrator()->runSimulation(config, engine.getPortfolio(), engine.getMarketData(), engine.getDataProcessor(), engine.getStrategyManager(), engine.getResultCalculator());
        if (result.isError()) {
            std::cerr << "Error: " << result.getErrorMessage() << std::endl;
            if (!result.getErrorDetails().empty()) {
                std::cerr << "Details: " << result.getErrorDetails() << std::endl;
            }
            return 1;
        }
        
        std::cout << result.getValue() << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Unexpected error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}

TradingConfig CommandDispatcher::loadConfigFromFile(const std::string& config_file) {
    std::ifstream file(config_file);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open config file: " + config_file);
    }
    
    json config;
    file >> config;
    file.close();
    
    TradingConfig sim_config;
    
    // Clear default symbols from constructor and load from config
    sim_config.symbols.clear();
    if (config.contains("symbols") && config["symbols"].is_array()) {
        for (const auto& s : config["symbols"]) {
            sim_config.symbols.push_back(s.get<std::string>());
        }
    } else if (config.contains("symbol")) {
        sim_config.symbols.push_back(config.value("symbol", "AAPL"));
    } else {
        sim_config.symbols.push_back("AAPL");
    }
    
    // Load basic configuration
    sim_config.start_date = config.value("start_date", "2023-01-01");
    sim_config.end_date = config.value("end_date", "2023-12-31");
    sim_config.starting_capital = config.value("starting_capital", 10000.0);
    sim_config.strategy_name = config.value("strategy", "ma_crossover");
    
    // Load strategy parameters
    if (config.contains("strategy_parameters") && config["strategy_parameters"].is_object()) {
        for (const auto& param : config["strategy_parameters"].items()) {
            sim_config.strategy_parameters[param.key()] = param.value().get<double>();
        }
    } else {
        // Fallback to individual parameter keys for backward compatibility
        if (config.contains("short_ma")) {
            sim_config.strategy_parameters["short_ma"] = config["short_ma"].get<double>();
        }
        if (config.contains("long_ma")) {
            sim_config.strategy_parameters["long_ma"] = config["long_ma"].get<double>();
        }
        if (config.contains("rsi_period")) {
            sim_config.strategy_parameters["rsi_period"] = config["rsi_period"].get<double>();
        }
        if (config.contains("rsi_oversold")) {
            sim_config.strategy_parameters["rsi_oversold"] = config["rsi_oversold"].get<double>();
        }
        if (config.contains("rsi_overbought")) {
            sim_config.strategy_parameters["rsi_overbought"] = config["rsi_overbought"].get<double>();
        }
    }
    
    return sim_config;
}