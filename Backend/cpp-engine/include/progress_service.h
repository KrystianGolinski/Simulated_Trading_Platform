#pragma once

#include "result.h"
#include "trading_exceptions.h"
#include "portfolio.h"
#include "technical_indicators.h"
#include <string>
#include <functional>

class ProgressService {
private:
    std::function<void(const std::string&)> progress_callback_;
    bool enable_progress_reporting_;
    int progress_interval_;
    
public:
    ProgressService() : enable_progress_reporting_(true), progress_interval_(20) {}
    ~ProgressService() = default;
    
    // Non-copyable but movable
    ProgressService(const ProgressService&) = delete;
    ProgressService& operator=(const ProgressService&) = delete;
    ProgressService(ProgressService&&) = default;
    ProgressService& operator=(ProgressService&&) = default;
    
    // Progress reporting configuration
    void setProgressCallback(std::function<void(const std::string&)> callback);
    void setProgressReporting(bool enabled);
    Result<void> setProgressInterval(int interval);
    
    // Progress reporting methods
    Result<void> reportProgress(size_t current_step, 
                                size_t total_steps, 
                                const PriceData& data_point, 
                                const std::string& symbol,
                                const Portfolio& portfolio);
    
    Result<void> reportSimulationStart(const std::string& symbol, 
                                       const std::string& start_date, 
                                       const std::string& end_date,
                                       double starting_capital);
    
    Result<void> reportSimulationEnd(const std::string& symbol,
                                     double ending_value,
                                     double return_pct,
                                     int total_trades);
    
    void reportError(const std::string& error_message);
    
private:
    // Internal progress calculation
    double calculateProgressPercentage(size_t current, size_t total) const;
    
    // Progress formatting
    std::string formatProgressJson(double progress_pct,
                                  const std::string& date,
                                  double portfolio_value,
                                  double stock_price,
                                  int current_day,
                                  int total_days) const;
    
    // Output methods
    void outputProgress(const std::string& message);
    bool shouldReportProgress(size_t current, size_t total) const;
};