#include <iostream>
#include <map>

#include "error_utils.h"
#include "json_helpers.h"
#include "logger.h"
#include "progress_service.h"

void ProgressService::setProgressCallback(std::function<void(const std::string&)> callback) {
    progress_callback_ = callback;
}

void ProgressService::setProgressReporting(bool enabled) {
    enable_progress_reporting_ = enabled;
}

Result<void> ProgressService::setProgressInterval(int interval) {
    if (interval <= 0) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_INTERVAL,
                           "Progress interval must be positive, got: " + std::to_string(interval));
    }
    progress_interval_ = interval;
    return Result<void>();
}

Result<void> ProgressService::reportProgress(size_t current_step, 
                                           size_t total_steps, 
                                           const PriceData& data_point, 
                                           const std::string& symbol,
                                           const Portfolio& portfolio) {
    // Validate inputs
    if (symbol.empty()) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_SYMBOL,
                           "Symbol cannot be empty for progress reporting");
    }
    
    if (total_steps == 0) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_TOTAL_STEPS,
                           "Total steps cannot be zero for progress reporting");
    }
    
    if (current_step >= total_steps) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_CURRENT_STEP,
                           "Current step (" + std::to_string(current_step) + 
                           ") must be less than total steps (" + std::to_string(total_steps) + ")");
    }
    
    if (data_point.date.empty()) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_DATE,
                           "Data point date cannot be empty for progress reporting");
    }
    
    if (!enable_progress_reporting_ || !shouldReportProgress(current_step, total_steps)) {
        return Result<void>(); // Success but no action needed
    }
    
    double progress_pct = calculateProgressPercentage(current_step, total_steps);
    
    // Calculate current portfolio value
    std::map<std::string, double> current_prices;
    current_prices[symbol] = data_point.close;
    double current_value = portfolio.getTotalValue(current_prices);
    
    // Format progress message
    std::string progress_json = formatProgressJson(
        progress_pct, 
        data_point.date, 
        current_value, 
        data_point.close,
        static_cast<int>(current_step), 
        static_cast<int>(total_steps)
    );
    
    outputProgress(progress_json);
    return Result<void>();
}

Result<void> ProgressService::reportSimulationStart(const std::string& symbol, 
                                                   const std::string& start_date, 
                                                   const std::string& end_date,
                                                   double starting_capital) {
    // Validate inputs
    if (symbol.empty()) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_SYMBOL,
                           "Symbol cannot be empty for simulation start reporting");
    }
    
    if (start_date.empty()) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_DATE,
                           "Start date cannot be empty for simulation start reporting");
    }
    
    if (end_date.empty()) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_DATE,
                           "End date cannot be empty for simulation start reporting");
    }
    
    if (starting_capital <= 0.0) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_CAPITAL,
                           "Starting capital must be positive, got: " + std::to_string(starting_capital));
    }
    
    if (!enable_progress_reporting_) {
        return Result<void>(); // Success but no action needed
    }
    
    Logger::info("Simulation started for ", symbol, " from ", start_date, " to ", end_date, 
                " with capital ", starting_capital);
    
    if (progress_callback_) {
        std::string message = "Simulation started for " + symbol + 
                             " (Capital: " + std::to_string(starting_capital) + ")";
        progress_callback_(message);
    }
    
    return Result<void>();
}

Result<void> ProgressService::reportSimulationEnd(const std::string& symbol,
                                                 double ending_value,
                                                 double return_pct,
                                                 int total_trades) {
    // Validate inputs
    if (symbol.empty()) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_SYMBOL,
                           "Symbol cannot be empty for simulation end reporting");
    }
    
    if (ending_value < 0.0) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_VALUE,
                           "Ending value cannot be negative, got: " + std::to_string(ending_value));
    }
    
    if (total_trades < 0) {
        return Result<void>(ErrorCode::PROGRESS_INVALID_TRADES,
                           "Total trades cannot be negative, got: " + std::to_string(total_trades));
    }
    
    if (!enable_progress_reporting_) {
        return Result<void>(); // Success but no action needed
    }
    
    Logger::info("Simulation completed for ", symbol, ": Final value=", ending_value, 
                " Return=", return_pct, "% Trades=", total_trades);
    
    if (progress_callback_) {
        std::string message = "Simulation completed for " + symbol + 
                             " (Return: " + std::to_string(return_pct) + "%)";
        progress_callback_(message);
    }
    
    return Result<void>();
}

void ProgressService::reportError(const std::string& error_message) {
    Logger::error("ProgressService: ", error_message);
    
    if (progress_callback_) {
        progress_callback_("Error: " + error_message);
    }
}

double ProgressService::calculateProgressPercentage(size_t current, size_t total) const {
    if (total == 0) {
        return 0.0;
    }
    return (static_cast<double>(current) / (total - 1)) * 100.0;
}

std::string ProgressService::formatProgressJson(double progress_pct,
                                               const std::string& date,
                                               double portfolio_value,
                                               double stock_price,
                                               int current_day,
                                               int total_days) const {
    // Use existing JSON helper if available, otherwise create simple JSON
    try {
        nlohmann::json progress = JsonHelpers::createProgressJson(
            progress_pct, date, portfolio_value, stock_price, current_day, total_days
        );
        return progress.dump();
    } catch (const std::exception& e) {
        // Fallback to simple string format if JSON helper fails
        return "{\"progress\":" + std::to_string(progress_pct) + 
               ",\"date\":\"" + date + "\"" +
               ",\"portfolio_value\":" + std::to_string(portfolio_value) + 
               ",\"stock_price\":" + std::to_string(stock_price) + "}";
    }
}

void ProgressService::outputProgress(const std::string& message) {
    if (progress_callback_) {
        progress_callback_(message);
    } else {
        // Default output to stderr as in original implementation
        std::cerr << message << std::endl;
    }
}

bool ProgressService::shouldReportProgress(size_t current, size_t total) const {
    if (total <= progress_interval_) {
        return true; // Report all progress for small datasets
    }
    
    // Report at regular intervals or at the end
    return (current % (total / progress_interval_) == 0) || (current == total - 1);
}