#include <iostream>
#include <string>
#include <algorithm>
#include "database_connection.h"
#include "market_data.h"
#include "trading_engine.h"

// Helper function to parse command line arguments
void parseArguments(int argc, char* argv[], std::string& symbol, std::string& start_date, std::string& end_date, double& capital) {
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        
        // Handle --key=value format
        if (arg.find("--symbol=") == 0) {
            symbol = arg.substr(9); // Remove "--symbol="
        } else if (arg.find("--start=") == 0) {
            start_date = arg.substr(8); // Remove "--start="
        } else if (arg.find("--end=") == 0) {
            end_date = arg.substr(6); // Remove "--end="
        } else if (arg.find("--capital=") == 0) {
            capital = std::stod(arg.substr(10)); // Remove "--capital="
        }
        // Handle --key value format
        else if (arg == "--symbol" && i + 1 < argc) {
            symbol = argv[++i];
        } else if (arg == "--start" && i + 1 < argc) {
            start_date = argv[++i];
        } else if (arg == "--end" && i + 1 < argc) {
            end_date = argv[++i];
        } else if (arg == "--capital" && i + 1 < argc) {
            capital = std::stod(argv[++i]);
        }
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
    std::cout << "Trading Engine C++ Backend - Phase 3 Implementation" << std::endl;
    
    try {
        if (argc > 1) {
            std::string command = argv[1];
            
            if (command == "--test-db") {
                // Parse additional arguments for database testing
                std::string symbol, start_date, end_date;
                double capital = 10000.0;
                parseArguments(argc, argv, symbol, start_date, end_date, capital);
                
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
                parseArguments(argc, argv, symbol, start_date, end_date, capital);
                
                // Set defaults if not provided
                if (symbol.empty()) symbol = "AAPL";
                if (start_date.empty()) start_date = "2023-01-01";
                if (end_date.empty()) end_date = "2023-12-31";
                
                runBacktest(symbol, start_date, end_date, capital);
                return 0;
            }
        }
        
        // Create trading engine with $10,000 initial capital
        TradingEngine engine(10000.0);
        
        if (argc > 1 && std::string(argv[1]) == "--simulate") {
            // Run simulation and output JSON
            std::string result = engine.runSimulation();
            std::cout << result << std::endl;
        } else if (argc > 1 && std::string(argv[1]) == "--status") {
            // Show portfolio status
            std::cout << engine.getPortfolioStatus() << std::endl;
        } else {
            // Show help
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
            std::cout << "\nPhase 3 Features:" << std::endl;
            std::cout << "  [DONE] Technical indicators (SMA, EMA, RSI)" << std::endl;
            std::cout << "  [DONE] Moving average crossover strategy" << std::endl;
            std::cout << "  [DONE] RSI-based trading strategy" << std::endl;
            std::cout << "  [DONE] Backtesting engine with performance metrics" << std::endl;
            std::cout << "  [DONE] Signal generation and execution" << std::endl;
            std::cout << "  [DONE] Risk management and position sizing" << std::endl;
            std::cout << "\nPhase 2 Features:" << std::endl;
            std::cout << "  [DONE] PostgreSQL/TimescaleDB connection" << std::endl;
            std::cout << "  [DONE] Historical stock data access" << std::endl;
            std::cout << "  [DONE] Real-time price queries" << std::endl;
            std::cout << "  [DONE] Data validation and caching" << std::endl;
            std::cout << "  [DONE] JSON output for frontend integration" << std::endl;
            std::cout << "\nPrevious Features:" << std::endl;
            std::cout << "  ✓ Position management (buy/sell shares)" << std::endl;
            std::cout << "  ✓ Portfolio tracking (cash + positions)" << std::endl;
            std::cout << "  ✓ Order management (buy/sell orders)" << std::endl;
            std::cout << "  ✓ Basic value calculations" << std::endl;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}