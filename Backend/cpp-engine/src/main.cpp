#include <iostream>
#include <string>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <vector>
#include <nlohmann/json.hpp>
#include "database_connection.h"
#include "market_data.h"
#include "trading_engine.h"

using json = nlohmann::json;

// Helper function to parse command line arguments
void parseArguments(int argc, char* argv[], std::vector<std::string>& symbols, std::string& start_date, std::string& end_date, double& capital, int& short_ma, int& long_ma, std::string& strategy, int& rsi_period, double& rsi_oversold, double& rsi_overbought) {
    std::cerr << "[DEBUG] Parsing " << argc << " arguments:" << std::endl;
    for (int i = 0; i < argc; ++i) {
        std::cerr << "[DEBUG] argv[" << i << "] = '" << argv[i] << "'" << std::endl;
    }
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        std::cerr << "[DEBUG] Processing argument: '" << arg << "'" << std::endl;
        
        // Handle --key=value format
        if (arg.find("--symbol=") == 0) {
            std::string symbol_list = arg.substr(9); // Remove "--symbol="
            // Parse comma-separated symbols
            std::stringstream ss(symbol_list);
            std::string symbol;
            symbols.clear();
            while (std::getline(ss, symbol, ',')) {
                // Trim whitespace
                symbol.erase(symbol.find_last_not_of(" \t") + 1);
                symbol.erase(0, symbol.find_first_not_of(" \t"));
                if (!symbol.empty()) {
                    symbols.push_back(symbol);
                }
            }
            std::cerr << "[DEBUG] Set symbols = { ";
            for (size_t i = 0; i < symbols.size(); ++i) {
                std::cerr << "'" << symbols[i] << "'";
                if (i < symbols.size() - 1) std::cerr << ", ";
            }
            std::cerr << " }" << std::endl;
        } else if (arg.find("--start=") == 0) {
            start_date = arg.substr(8); // Remove "--start="
            std::cerr << "[DEBUG] Set start_date = '" << start_date << "'" << std::endl;
        } else if (arg.find("--end=") == 0) {
            end_date = arg.substr(6); // Remove "--end="
            std::cerr << "[DEBUG] Set end_date = '" << end_date << "'" << std::endl;
        } else if (arg.find("--capital=") == 0) {
            capital = std::stod(arg.substr(10)); // Remove "--capital="
            std::cerr << "[DEBUG] Set capital = " << capital << std::endl;
        } else if (arg.find("--short-ma=") == 0) {
            short_ma = std::stoi(arg.substr(11)); // Remove "--short-ma="
            std::cerr << "[DEBUG] Set short_ma = " << short_ma << std::endl;
        } else if (arg.find("--long-ma=") == 0) {
            long_ma = std::stoi(arg.substr(10)); // Remove "--long-ma="
            std::cerr << "[DEBUG] Set long_ma = " << long_ma << std::endl;
        } else if (arg.find("--strategy=") == 0) {
            strategy = arg.substr(11); // Remove "--strategy="
            std::cerr << "[DEBUG] Set strategy = '" << strategy << "'" << std::endl;
        } else if (arg.find("--rsi-period=") == 0) {
            rsi_period = std::stoi(arg.substr(13)); // Remove "--rsi-period="
            std::cerr << "[DEBUG] Set rsi_period = " << rsi_period << std::endl;
        } else if (arg.find("--rsi-oversold=") == 0) {
            rsi_oversold = std::stod(arg.substr(15)); // Remove "--rsi-oversold="
            std::cerr << "[DEBUG] Set rsi_oversold = " << rsi_oversold << std::endl;
        } else if (arg.find("--rsi-overbought=") == 0) {
            rsi_overbought = std::stod(arg.substr(17)); // Remove "--rsi-overbought="
            std::cerr << "[DEBUG] Set rsi_overbought = " << rsi_overbought << std::endl;
        }
        // Handle --key value format
        else if (arg == "--symbol" && i + 1 < argc) {
            std::string symbol_list = argv[++i];
            // Parse comma-separated symbols
            std::stringstream ss(symbol_list);
            std::string symbol;
            symbols.clear();
            while (std::getline(ss, symbol, ',')) {
                // Trim whitespace
                symbol.erase(symbol.find_last_not_of(" \t") + 1);
                symbol.erase(0, symbol.find_first_not_of(" \t"));
                if (!symbol.empty()) {
                    symbols.push_back(symbol);
                }
            }
            std::cerr << "[DEBUG] Set symbols = { ";
            for (size_t i = 0; i < symbols.size(); ++i) {
                std::cerr << "'" << symbols[i] << "'";
                if (i < symbols.size() - 1) std::cerr << ", ";
            }
            std::cerr << " }" << std::endl;
        } else if (arg == "--start" && i + 1 < argc) {
            start_date = argv[++i];
            std::cerr << "[DEBUG] Set start_date = '" << start_date << "'" << std::endl;
        } else if (arg == "--end" && i + 1 < argc) {
            end_date = argv[++i];
            std::cerr << "[DEBUG] Set end_date = '" << end_date << "'" << std::endl;
        } else if (arg == "--capital" && i + 1 < argc) {
            capital = std::stod(argv[++i]);
            std::cerr << "[DEBUG] Set capital = " << capital << std::endl;
        } else if (arg == "--short-ma" && i + 1 < argc) {
            short_ma = std::stoi(argv[++i]);
            std::cerr << "[DEBUG] Set short_ma = " << short_ma << std::endl;
        } else if (arg == "--long-ma" && i + 1 < argc) {
            long_ma = std::stoi(argv[++i]);
            std::cerr << "[DEBUG] Set long_ma = " << long_ma << std::endl;
        } else if (arg == "--strategy" && i + 1 < argc) {
            strategy = argv[++i];
            std::cerr << "[DEBUG] Set strategy = '" << strategy << "'" << std::endl;
        } else if (arg == "--rsi-period" && i + 1 < argc) {
            rsi_period = std::stoi(argv[++i]);
            std::cerr << "[DEBUG] Set rsi_period = " << rsi_period << std::endl;
        } else if (arg == "--rsi-oversold" && i + 1 < argc) {
            rsi_oversold = std::stod(argv[++i]);
            std::cerr << "[DEBUG] Set rsi_oversold = " << rsi_oversold << std::endl;
        } else if (arg == "--rsi-overbought" && i + 1 < argc) {
            rsi_overbought = std::stod(argv[++i]);
            std::cerr << "[DEBUG] Set rsi_overbought = " << rsi_overbought << std::endl;
        }
    }
    
    std::cerr << "[DEBUG] Final parsed values:" << std::endl;
    std::cerr << "[DEBUG]   symbols = { ";
    for (size_t i = 0; i < symbols.size(); ++i) {
        std::cerr << "'" << symbols[i] << "'";
        if (i < symbols.size() - 1) std::cerr << ", ";
    }
    std::cerr << " }" << std::endl;
    std::cerr << "[DEBUG]   start_date = '" << start_date << "'" << std::endl;
    std::cerr << "[DEBUG]   end_date = '" << end_date << "'" << std::endl;
    std::cerr << "[DEBUG]   capital = " << capital << std::endl;
    std::cerr << "[DEBUG]   short_ma = " << short_ma << std::endl;
    std::cerr << "[DEBUG]   long_ma = " << long_ma << std::endl;
    std::cerr << "[DEBUG]   strategy = '" << strategy << "'" << std::endl;
    std::cerr << "[DEBUG]   rsi_period = " << rsi_period << std::endl;
    std::cerr << "[DEBUG]   rsi_oversold = " << rsi_oversold << std::endl;
    std::cerr << "[DEBUG]   rsi_overbought = " << rsi_overbought << std::endl;
}

// Function to run simulation from JSON config file
bool runSimulationFromConfig(const std::string& config_file) {
    try {
        // Read JSON config file
        std::ifstream file(config_file);
        if (!file.is_open()) {
            std::cerr << "Error: Cannot open config file: " << config_file << std::endl;
            return false;
        }
        
        json config;
        file >> config;
        file.close();
        
        // Extract configuration parameters
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
        
        // Strategy-specific parameters
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
        
        // Create trading engine
        TradingEngine engine(capital);
        
        // Configure strategy
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
        
        // Run simulation (multi-symbol or single symbol)
        std::string result;
        if (symbols.size() == 1) {
            result = engine.runSimulationWithParams(symbols[0], start_date, end_date, capital);
        } else {
            // Multi-symbol simulation
            BacktestResult backtest_result = engine.runBacktestMultiSymbol(symbols, start_date, end_date, capital);
            nlohmann::json json_result = engine.getBacktestResultsAsJson(backtest_result);
            result = json_result.dump(2);
        }
        std::cout << result << std::endl;
        
        // Clean up config file (optional)
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

// Function to run backtest (supports multi-symbol)
void runBacktest(const std::vector<std::string>& symbols, const std::string& start_date, const std::string& end_date, double capital, const std::string& strategy, int short_ma, int long_ma, int rsi_period, double rsi_oversold, double rsi_overbought) {
    std::cout << "Running backtest..." << std::endl;
    std::cout << "Symbols: ";
    for (size_t i = 0; i < symbols.size(); ++i) {
        std::cout << symbols[i];
        if (i < symbols.size() - 1) std::cout << ", ";
    }
    std::cout << std::endl;
    std::cout << "Period: " << start_date << " to " << end_date << std::endl;
    std::cout << "Starting Capital: $" << capital << std::endl;
    std::cout << "Strategy: " << strategy << std::endl;
    
    try {
        TradingEngine engine(capital);
        
        // Configure strategy
        if (strategy == "ma_crossover") {
            std::cout << "MA Crossover Parameters: Short=" << short_ma << ", Long=" << long_ma << std::endl;
            engine.setMovingAverageStrategy(short_ma, long_ma);
        } else if (strategy == "rsi") {
            std::cout << "RSI Parameters: Period=" << rsi_period << ", Oversold=" << rsi_oversold << ", Overbought=" << rsi_overbought << std::endl;
            engine.setRSIStrategy(rsi_period, rsi_oversold, rsi_overbought);
        } else {
            std::cout << "Unknown strategy, defaulting to MA Crossover" << std::endl;
            engine.setMovingAverageStrategy(short_ma, long_ma);
        }
        
        BacktestResult result;
        if (symbols.size() == 1) {
            // Single symbol backtest
            BacktestConfig config;
            config.symbol = symbols[0];
            config.start_date = start_date;
            config.end_date = end_date;
            config.starting_capital = capital;
            config.strategy_name = strategy;
            
            // Set strategy parameters based on strategy type
            if (strategy == "ma_crossover") {
                config.strategy_config.setParameter("short_period", short_ma);
                config.strategy_config.setParameter("long_period", long_ma);
            } else if (strategy == "rsi") {
                config.strategy_config.setParameter("rsi_period", rsi_period);
                config.strategy_config.setParameter("oversold_threshold", rsi_oversold);
                config.strategy_config.setParameter("overbought_threshold", rsi_overbought);
            }
            config.strategy_config.max_position_size = 0.1;
            config.strategy_config.enable_risk_management = true;
            
            result = engine.runBacktest(config);
        } else {
            // Multi-symbol backtest
            result = engine.runBacktestMultiSymbol(symbols, start_date, end_date, capital);
        }
        
        // Output results as JSON
        nlohmann::json json_result = engine.getBacktestResultsAsJson(result);
        std::cout << json_result.dump(2) << std::endl;
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Backtest failed: " << e.what() << std::endl;
    }
}

// Function to test database connectivity
void testDatabase(const std::string& symbol, const std::string& start_date, const std::string& end_date) {
    std::cout << "Testing database connectivity..." << std::endl;
    
    try {
        MarketData market_data;
        
        // Test database connection
        if (!market_data.testDatabaseConnection()) {
            std::cout << "[FAIL] Database connection failed" << std::endl;
            return;
        }
        std::cout << "[PASS] Database connection successful" << std::endl;
        
        // Test symbol existence
        if (!symbol.empty()) {
            if (market_data.symbolExists(symbol)) {
                std::cout << "[PASS] Symbol " << symbol << " exists in database" << std::endl;
                
                // Get data summary
                auto summary = market_data.getDataSummary(symbol, start_date, end_date);
                std::cout << "Data Summary:" << std::endl;
                std::cout << summary.dump(2) << std::endl;
                
            } else {
                std::cout << "[FAIL] Symbol " << symbol << " not found in database" << std::endl;
            }
        }
        
        // Show available symbols
        auto symbols = market_data.getAvailableSymbols();
        std::cout << "Available symbols (" << symbols.size() << " total):" << std::endl;
        for (size_t i = 0; i < std::min(symbols.size(), size_t(10)); ++i) {
            std::cout << "  - " << symbols[i] << std::endl;
        }
        if (symbols.size() > 10) {
            std::cout << "  ... and " << (symbols.size() - 10) << " more" << std::endl;
        }
        
        // Show database info
        auto db_info = market_data.getDatabaseInfo();
        std::cout << "Database Info:" << std::endl;
        std::cout << db_info.dump(2) << std::endl;
        
    } catch (const std::exception& e) {
        std::cout << "[ERROR] Database test failed: " << e.what() << std::endl;
    }
}

int main(int argc, char* argv[]) {
    try {
        if (argc > 1) {
            std::string command = argv[1];
            
            // Only print header for non-simulate commands
            if (command != "--simulate") {
                std::cout << "Trading Engine C++ Backend" << std::endl;
            }
            
            if (command == "--test-db") {
                // Parse additional arguments for database testing
                std::vector<std::string> symbols;
                std::string start_date, end_date;
                double capital = 10000.0;
                int short_ma = 20, long_ma = 50;
                std::string strategy = "ma_crossover";
                int rsi_period = 14;
                double rsi_oversold = 30.0, rsi_overbought = 70.0;
                bool enable_progress = false;
                parseArguments(argc, argv, symbols, start_date, end_date, capital, short_ma, long_ma, strategy, rsi_period, rsi_oversold, rsi_overbought);
                
                // Set defaults if not provided
                if (symbols.empty()) symbols.push_back("AAPL");
                if (start_date.empty()) start_date = "2023-01-01";
                if (end_date.empty()) end_date = "2023-12-31";
                
                testDatabase(symbols[0], start_date, end_date);
                return 0;
            } else if (command == "--backtest") {
                // Parse additional arguments for backtesting
                std::vector<std::string> symbols;
                std::string start_date, end_date;
                double capital = 10000.0;
                int short_ma = 20, long_ma = 50;
                std::string strategy = "ma_crossover";
                int rsi_period = 14;
                double rsi_oversold = 30.0, rsi_overbought = 70.0;
                bool enable_progress = false;
                parseArguments(argc, argv, symbols, start_date, end_date, capital, short_ma, long_ma, strategy, rsi_period, rsi_oversold, rsi_overbought);
                
                // Set defaults if not provided
                if (symbols.empty()) symbols.push_back("AAPL");
                if (start_date.empty()) start_date = "2023-01-01";
                if (end_date.empty()) end_date = "2023-12-31";
                
                runBacktest(symbols, start_date, end_date, capital, strategy, short_ma, long_ma, rsi_period, rsi_oversold, rsi_overbought);
                return 0;
            }
        }
        
        if (argc > 1 && std::string(argv[1]) == "--simulate") {
            // Check if using JSON config file
            if (argc > 3 && std::string(argv[2]) == "--config") {
                std::string config_file = argv[3];
                std::cerr << "[DEBUG] Using JSON config file: " << config_file << std::endl;
                
                if (!runSimulationFromConfig(config_file)) {
                    std::cerr << "Error: Failed to run simulation from config file" << std::endl;
                    return 1;
                }
                return 0;
            } else {
                // Fallback to command line arguments for backward compatibility
                std::vector<std::string> symbols;
                std::string start_date, end_date;
                double capital = 10000.0;
                int short_ma = 20, long_ma = 50;
                std::string strategy = "ma_crossover";
                int rsi_period = 14;
                double rsi_oversold = 30.0, rsi_overbought = 70.0;
                parseArguments(argc, argv, symbols, start_date, end_date, capital, short_ma, long_ma, strategy, rsi_period, rsi_oversold, rsi_overbought);
                
                // Create trading engine with parsed capital instead of hardcoded value
                TradingEngine engine(capital);
                
                // Set defaults if not provided
                if (symbols.empty()) symbols.push_back("AAPL");
                if (start_date.empty()) start_date = "2023-01-01";
                if (end_date.empty()) end_date = "2023-12-31";
            
            std::cerr << "[DEBUG] About to run simulation with:" << std::endl;
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
            
            // Configure strategy with parsed parameters
            if (strategy == "ma_crossover") {
                std::cerr << "[DEBUG]   short_ma = " << short_ma << std::endl;
                std::cerr << "[DEBUG]   long_ma = " << long_ma << std::endl;
                engine.setMovingAverageStrategy(short_ma, long_ma);
            } else if (strategy == "rsi") {
                std::cerr << "[DEBUG]   rsi_period = " << rsi_period << std::endl;
                std::cerr << "[DEBUG]   rsi_oversold = " << rsi_oversold << std::endl;
                std::cerr << "[DEBUG]   rsi_overbought = " << rsi_overbought << std::endl;
                engine.setRSIStrategy(rsi_period, rsi_oversold, rsi_overbought);
            } else {
                std::cerr << "[DEBUG] Unknown strategy '" << strategy << "', defaulting to MA crossover" << std::endl;
                engine.setMovingAverageStrategy(short_ma, long_ma);
            }
            
            // Run simulation - supports both single and multi-symbol
            std::string result;
            if (symbols.size() == 1) {
                result = engine.runSimulationWithParams(symbols[0], start_date, end_date, capital);
            } else {
                // Multi-symbol simulation
                BacktestResult backtest_result = engine.runBacktestMultiSymbol(symbols, start_date, end_date, capital);
                nlohmann::json json_result = engine.getBacktestResultsAsJson(backtest_result);
                result = json_result.dump(2);
            }
            std::cout << result << std::endl;
            }
        } else if (argc > 1 && std::string(argv[1]) == "--status") {
            // Create default trading engine for status
            TradingEngine engine(10000.0);
            // Show portfolio status
            std::cout << engine.getPortfolioStatus() << std::endl;
        } else {
            // Show help - print header for help
            std::cout << "Trading Engine C++ Backend" << std::endl;
            std::cout << "\nUsage:" << std::endl;
            std::cout << "  " << argv[0] << " --simulate              Run simulation and output JSON" << std::endl;
            std::cout << "  " << argv[0] << " --status                Show portfolio status" << std::endl;
            std::cout << "  " << argv[0] << " --test-db [options]     Test database connectivity" << std::endl;
            std::cout << "  " << argv[0] << " --backtest [options]    Run backtest with moving average strategy" << std::endl;
            std::cout << "  " << argv[0] << " --help                  Show this help" << std::endl;
            std::cout << "\nOptions:" << std::endl;
            std::cout << "  --symbol SYMBOL(S) Stock symbol(s) to analyze, comma-separated for multi-symbol (default: AAPL)" << std::endl;
            std::cout << "  --start DATE      Start date (default: 2023-01-01)" << std::endl;
            std::cout << "  --end DATE        End date (default: 2023-12-31)" << std::endl;
            std::cout << "  --capital AMOUNT  Starting capital (default: 10000)" << std::endl;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}