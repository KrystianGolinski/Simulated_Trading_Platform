#include <iostream>
#include <string>
#include <algorithm>
#include <fstream>
#include <nlohmann/json.hpp>
#include "database_connection.h"
#include "market_data.h"
#include "trading_engine.h"

using json = nlohmann::json;

// Helper function to parse command line arguments
void parseArguments(int argc, char* argv[], std::string& symbol, std::string& start_date, std::string& end_date, double& capital, int& short_ma, int& long_ma) {
    std::cerr << "[DEBUG] Parsing " << argc << " arguments:" << std::endl;
    for (int i = 0; i < argc; ++i) {
        std::cerr << "[DEBUG] argv[" << i << "] = '" << argv[i] << "'" << std::endl;
    }
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        std::cerr << "[DEBUG] Processing argument: '" << arg << "'" << std::endl;
        
        // Handle --key=value format
        if (arg.find("--symbol=") == 0) {
            symbol = arg.substr(9); // Remove "--symbol="
            std::cerr << "[DEBUG] Set symbol = '" << symbol << "'" << std::endl;
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
        }
        // Handle --key value format
        else if (arg == "--symbol" && i + 1 < argc) {
            symbol = argv[++i];
            std::cerr << "[DEBUG] Set symbol = '" << symbol << "'" << std::endl;
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
        }
    }
    
    std::cerr << "[DEBUG] Final parsed values:" << std::endl;
    std::cerr << "[DEBUG]   symbol = '" << symbol << "'" << std::endl;
    std::cerr << "[DEBUG]   start_date = '" << start_date << "'" << std::endl;
    std::cerr << "[DEBUG]   end_date = '" << end_date << "'" << std::endl;
    std::cerr << "[DEBUG]   capital = " << capital << std::endl;
    std::cerr << "[DEBUG]   short_ma = " << short_ma << std::endl;
    std::cerr << "[DEBUG]   long_ma = " << long_ma << std::endl;
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
        std::string symbol = config.value("symbol", "AAPL");
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
        std::cerr << "[DEBUG]   symbol = '" << symbol << "'" << std::endl;
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
        
        // Run simulation
        std::string result = engine.runSimulationWithParams(symbol, start_date, end_date, capital);
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

// Function to run backtest
void runBacktest(const std::string& symbol, const std::string& start_date, const std::string& end_date, double capital) {
    std::cout << "Running backtest..." << std::endl;
    std::cout << "Symbol: " << symbol << std::endl;
    std::cout << "Period: " << start_date << " to " << end_date << std::endl;
    std::cout << "Starting Capital: $" << capital << std::endl;
    
    try {
        TradingEngine engine(capital);
        
        // Configure backtest
        BacktestConfig config;
        config.symbol = symbol;
        config.start_date = start_date;
        config.end_date = end_date;
        config.starting_capital = capital;
        config.strategy_name = "ma_crossover";
        
        // Set strategy parameters
        config.strategy_config.setParameter("short_period", 20);
        config.strategy_config.setParameter("long_period", 50);
        config.strategy_config.max_position_size = 0.1;
        config.strategy_config.enable_risk_management = true;
        
        // Run backtest
        BacktestResult result = engine.runBacktest(config);
        
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
                std::string symbol, start_date, end_date;
                double capital = 10000.0;
                int short_ma = 20, long_ma = 50;
                bool enable_progress = false;
                parseArguments(argc, argv, symbol, start_date, end_date, capital, short_ma, long_ma);
                
                // Set defaults if not provided
                if (symbol.empty()) symbol = "AAPL";
                if (start_date.empty()) start_date = "2023-01-01";
                if (end_date.empty()) end_date = "2023-12-31";
                
                testDatabase(symbol, start_date, end_date);
                return 0;
            } else if (command == "--backtest") {
                // Parse additional arguments for backtesting
                std::string symbol, start_date, end_date;
                double capital = 10000.0;
                int short_ma = 20, long_ma = 50;
                bool enable_progress = false;
                parseArguments(argc, argv, symbol, start_date, end_date, capital, short_ma, long_ma);
                
                // Set defaults if not provided
                if (symbol.empty()) symbol = "AAPL";
                if (start_date.empty()) start_date = "2023-01-01";
                if (end_date.empty()) end_date = "2023-12-31";
                
                runBacktest(symbol, start_date, end_date, capital);
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
                std::string symbol, start_date, end_date;
                double capital = 10000.0;
                int short_ma = 20, long_ma = 50;
                parseArguments(argc, argv, symbol, start_date, end_date, capital, short_ma, long_ma);
                
                // Create trading engine with parsed capital instead of hardcoded value
                TradingEngine engine(capital);
                
                // Set defaults if not provided
                if (symbol.empty()) symbol = "AAPL";
                if (start_date.empty()) start_date = "2023-01-01";
                if (end_date.empty()) end_date = "2023-12-31";
            
            std::cerr << "[DEBUG] About to run simulation with:" << std::endl;
            std::cerr << "[DEBUG]   symbol = '" << symbol << "'" << std::endl;
            std::cerr << "[DEBUG]   start_date = '" << start_date << "'" << std::endl;
            std::cerr << "[DEBUG]   end_date = '" << end_date << "'" << std::endl;
            std::cerr << "[DEBUG]   capital = " << capital << std::endl;
            std::cerr << "[DEBUG]   short_ma = " << short_ma << std::endl;
            std::cerr << "[DEBUG]   long_ma = " << long_ma << std::endl;
            
            // Configure strategy with parsed parameters
            engine.setMovingAverageStrategy(short_ma, long_ma);
            
            // Run simulation - runSimulationWithParams already includes progress functionality
            std::string result = engine.runSimulationWithParams(symbol, start_date, end_date, capital);
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
            std::cout << "  --symbol SYMBOL   Stock symbol to analyze (default: AAPL)" << std::endl;
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