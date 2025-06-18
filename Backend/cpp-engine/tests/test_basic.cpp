#include <iostream>
#include <cassert>
#include <cmath>
#include <vector>
#include "position.h"
#include "portfolio.h"
#include "order.h"
#include "technical_indicators.h"
#include "trading_strategy.h"

int tests_run = 0;
int tests_passed = 0;

#define ASSERT_EQ(expected, actual) \
    do { \
        tests_run++; \
        if ((expected) == (actual)) { \
            tests_passed++; \
        } else { \
            std::cout << "FAIL: Expected " << (expected) << ", got " << (actual) << std::endl; \
        } \
    } while(0)

#define ASSERT_TRUE(condition) \
    do { \
        tests_run++; \
        if (condition) { \
            tests_passed++; \
        } else { \
            std::cout << "FAIL: " << #condition << " is false" << std::endl; \
        } \
    } while(0)

#define ASSERT_FALSE(condition) \
    do { \
        tests_run++; \
        if (!(condition)) { \
            tests_passed++; \
        } else { \
            std::cout << "FAIL: " << #condition << " is true" << std::endl; \
        } \
    } while(0)

#define ASSERT_NEAR(expected, actual, tolerance) \
    do { \
        tests_run++; \
        if (std::abs((expected) - (actual)) < (tolerance)) { \
            tests_passed++; \
        } else { \
            std::cout << "FAIL: Expected " << (expected) << " +- " << (tolerance) << ", got " << (actual) << std::endl; \
        } \
    } while(0)

void test_position_basic() {
    std::cout << "Testing Position Class..." << std::endl;
    
    // Test default constructor
    Position empty_pos;
    ASSERT_TRUE(empty_pos.isEmpty());
    ASSERT_EQ(0, empty_pos.getShares());
    
    // Test parameterized constructor
    Position pos("AAPL", 100, 150.0);
    ASSERT_EQ("AAPL", pos.getSymbol());
    ASSERT_EQ(100, pos.getShares());
    ASSERT_NEAR(150.0, pos.getAveragePrice(), 0.01);
    ASSERT_FALSE(pos.isEmpty());
    
    // Test value calculations
    ASSERT_NEAR(15000.0, pos.getCurrentValue(150.0), 0.01);
    ASSERT_NEAR(16000.0, pos.getCurrentValue(160.0), 0.01);
    ASSERT_NEAR(1000.0, pos.getUnrealizedPnL(160.0), 0.01);
    ASSERT_NEAR(-1000.0, pos.getUnrealizedPnL(140.0), 0.01);
    
    // Test buying more shares
    pos.buyShares(50, 160.0);
    ASSERT_EQ(150, pos.getShares());
    // New average: (100*150 + 50*160) / 150 = 153.33
    ASSERT_NEAR(153.33, pos.getAveragePrice(), 0.01);
    
    // Test selling shares
    ASSERT_TRUE(pos.canSell(50));
    ASSERT_FALSE(pos.canSell(200));
    pos.sellShares(50, 170.0);
    ASSERT_EQ(100, pos.getShares());
    // Average price should remain the same after selling
    ASSERT_NEAR(153.33, pos.getAveragePrice(), 0.01);
}

void test_portfolio_basic() {
    std::cout << "Testing Portfolio Class..." << std::endl;
    
    // Test constructor
    Portfolio portfolio(100000.0);
    ASSERT_NEAR(100000.0, portfolio.getCashBalance(), 0.01);
    ASSERT_NEAR(100000.0, portfolio.getInitialCapital(), 0.01);
    ASSERT_EQ(0, portfolio.getPositionCount());
    
    // Test buying stocks
    ASSERT_TRUE(portfolio.canAfford(15000.0));
    ASSERT_TRUE(portfolio.buyStock("AAPL", 100, 150.0));
    ASSERT_NEAR(85000.0, portfolio.getCashBalance(), 0.01);
    ASSERT_EQ(1, portfolio.getPositionCount());
    ASSERT_TRUE(portfolio.hasPosition("AAPL"));
    ASSERT_FALSE(portfolio.hasPosition("MSFT"));
    
    // Test buying another stock
    ASSERT_TRUE(portfolio.buyStock("MSFT", 50, 300.0));
    ASSERT_NEAR(70000.0, portfolio.getCashBalance(), 0.01);
    ASSERT_EQ(2, portfolio.getPositionCount());
    
    // Test insufficient funds
    ASSERT_FALSE(portfolio.buyStock("GOOGL", 1000, 2500.0)); // Would cost $2.5M
    ASSERT_NEAR(70000.0, portfolio.getCashBalance(), 0.01); // Should be unchanged
    
    // Test selling stocks
    ASSERT_TRUE(portfolio.sellStock("AAPL", 50, 160.0));
    ASSERT_NEAR(78000.0, portfolio.getCashBalance(), 0.01); // 70000 + 50*160
    
    Position aapl_pos = portfolio.getPosition("AAPL");
    ASSERT_EQ(50, aapl_pos.getShares());
    
    // Test portfolio value calculation
    std::map<std::string, double> prices = {{"AAPL", 160.0}, {"MSFT", 320.0}};
    // Cash: 78000, AAPL: 50*160=8000, MSFT: 50*320=16000, Total: 102000
    ASSERT_NEAR(102000.0, portfolio.getTotalValue(prices), 0.01);
    ASSERT_NEAR(2.0, portfolio.getTotalReturnPercentage(prices), 0.01); // 2% return
}

void test_order_basic() {
    std::cout << "Testing Order Class..." << std::endl;
    
    // Test buy order
    Order buy_order("AAPL", OrderType::BUY, 100, 150.0);
    ASSERT_EQ("AAPL", buy_order.getSymbol());
    ASSERT_TRUE(buy_order.isBuyOrder());
    ASSERT_FALSE(buy_order.isSellOrder());
    ASSERT_EQ(100, buy_order.getShares());
    ASSERT_NEAR(150.0, buy_order.getPrice(), 0.01);
    ASSERT_NEAR(15000.0, buy_order.getTotalValue(), 0.01);
    ASSERT_TRUE(buy_order.isPending());
    ASSERT_TRUE(buy_order.isValid());
    
    // Test sell order
    Order sell_order("MSFT", OrderType::SELL, 50, 300.0);
    ASSERT_TRUE(sell_order.isSellOrder());
    ASSERT_FALSE(sell_order.isBuyOrder());
    ASSERT_EQ("SELL", sell_order.getTypeString());
    
    // Test status changes
    sell_order.setStatus(OrderStatus::FILLED);
    ASSERT_TRUE(sell_order.isFilled());
    ASSERT_FALSE(sell_order.isPending());
    
    sell_order.setRejectReason("Insufficient funds");
    ASSERT_TRUE(sell_order.isRejected());
    ASSERT_EQ("Insufficient funds", sell_order.getRejectReason());
    
    // Test invalid order
    Order invalid_order("", OrderType::BUY, 0, -10.0);
    ASSERT_FALSE(invalid_order.isValid());
}

void test_technical_indicators() {
    std::cout << "Testing Technical Indicators..." << std::endl;
    
    // Create test price data
    std::vector<PriceData> test_data = {
        PriceData(100.0, 105.0, 99.0, 102.0, 1000, "2023-01-01"),
        PriceData(102.0, 106.0, 100.0, 104.0, 1200, "2023-01-02"),
        PriceData(104.0, 108.0, 103.0, 106.0, 1100, "2023-01-03"),
        PriceData(106.0, 109.0, 105.0, 108.0, 1300, "2023-01-04"),
        PriceData(108.0, 110.0, 107.0, 109.0, 1400, "2023-01-05"),
        PriceData(109.0, 111.0, 108.0, 110.0, 1500, "2023-01-06"),
        PriceData(110.0, 112.0, 109.0, 111.0, 1600, "2023-01-07"),
        PriceData(111.0, 113.0, 110.0, 112.0, 1700, "2023-01-08"),
        PriceData(112.0, 114.0, 111.0, 113.0, 1800, "2023-01-09"),
        PriceData(113.0, 115.0, 112.0, 114.0, 1900, "2023-01-10")
    };
    
    TechnicalIndicators indicators(test_data);
    
    // Test basic functionality
    ASSERT_EQ(10, indicators.getDataSize());
    ASSERT_TRUE(indicators.hasEnoughData(5));
    ASSERT_FALSE(indicators.hasEnoughData(15));
    
    // Test Simple Moving Average (5-period)
    auto sma_5 = indicators.calculateSMA(5);
    ASSERT_EQ(6, sma_5.size()); // Should have 6 values for 10 data points with 5-period SMA
    
    // First SMA value: (102+104+106+108+109)/5 = 105.8
    ASSERT_NEAR(105.8, sma_5[0], 0.1);
    
    // Test SMA with insufficient data
    auto sma_15 = indicators.calculateSMA(15);
    ASSERT_EQ(0, sma_15.size());
    
    // Test EMA calculation
    auto ema_5 = indicators.calculateEMA(5);
    ASSERT_EQ(10, ema_5.size()); // EMA returns value for each data point
    ASSERT_NEAR(102.0, ema_5[0], 0.1); // First value should be first close price
    
    // Test RSI calculation
    auto rsi = indicators.calculateRSI(5);
    ASSERT_TRUE(rsi.size() > 0);
    
    // Test Moving Average Crossover detection
    auto crossover_signals = indicators.detectMACrossover(3, 5);
    // With continuously rising prices, we might get buy signals
    
    std::cout << "SMA(5) values: ";
    for (size_t i = 0; i < std::min(sma_5.size(), size_t(3)); ++i) {
        std::cout << sma_5[i] << " ";
    }
    std::cout << std::endl;
}

void test_trading_strategy() {
    std::cout << "Testing Trading Strategy..." << std::endl;
    
    // Test Moving Average Crossover Strategy
    MovingAverageCrossoverStrategy ma_strategy(5, 10);
    ASSERT_TRUE(ma_strategy.validateConfig());
    ASSERT_EQ("Moving Average Crossover", ma_strategy.getName());
    
    auto periods = ma_strategy.getMovingAveragePeriods();
    ASSERT_EQ(5, periods.first);
    ASSERT_EQ(10, periods.second);
    
    // Test strategy configuration
    StrategyConfig config;
    config.setParameter("short_period", 3);
    config.setParameter("long_period", 7);
    config.max_position_size = 0.2;
    
    ma_strategy.configure(config);
    auto new_periods = ma_strategy.getMovingAveragePeriods();
    ASSERT_EQ(3, new_periods.first);
    ASSERT_EQ(7, new_periods.second);
    
    // Test RSI Strategy
    RSIStrategy rsi_strategy(14, 30.0, 70.0);
    ASSERT_TRUE(rsi_strategy.validateConfig());
    ASSERT_EQ("RSI Strategy", rsi_strategy.getName());
    
    // Test position sizing
    double position_size = ma_strategy.calculatePositionSize(10000.0, 100.0);
    ASSERT_TRUE(position_size > 0);
    ASSERT_TRUE(position_size <= 20); // Max 20 shares with 20% position size limit
    
    std::cout << "Strategy tests completed successfully" << std::endl;
}

int main() {
    std::cout << "Running C++ Trading Engine" << std::endl;
    
    test_position_basic();
    test_portfolio_basic();
    test_order_basic();
    test_technical_indicators();
    test_trading_strategy();
    
    std::cout << "\nTest Summary:" << std::endl;
    std::cout << "Tests run: " << tests_run << std::endl;
    std::cout << "Tests passed: " << tests_passed << std::endl;
    std::cout << "Tests failed: " << (tests_run - tests_passed) << std::endl;
    
    if (tests_passed == tests_run) {
        std::cout << "All tests passed!" << std::endl;
        return 0;
    } else {
        std::cout << "Some tests failed!" << std::endl;
        return 1;
    }
}