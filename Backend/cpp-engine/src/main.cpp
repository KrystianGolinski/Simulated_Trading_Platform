#include <iostream>
#include "trading_engine.h"

int main(int argc, char* argv[]) {
    std::cout << "Trading Engine C++ Backend - Phase 1 Implementation" << std::endl;
    
    try {
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
            std::cout << "  " << argv[0] << " --simulate    Run simulation and output JSON" << std::endl;
            std::cout << "  " << argv[0] << " --status      Show portfolio status" << std::endl;
            std::cout << "  " << argv[0] << " --help        Show this help" << std::endl;
            std::cout << "\nPhase 1 Features:" << std::endl;
            std::cout << "  ✓ Position management (buy/sell shares)" << std::endl;
            std::cout << "  ✓ Portfolio tracking (cash + positions)" << std::endl;
            std::cout << "  ✓ Order management (buy/sell orders)" << std::endl;
            std::cout << "  ✓ Basic value calculations" << std::endl;
            std::cout << "  ✓ JSON output for frontend integration" << std::endl;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}