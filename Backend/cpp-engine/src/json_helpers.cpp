#include <algorithm>

#include "json_helpers.h"
#include "market_data.h"
#include "trading_strategy.h"

namespace JsonHelpers {

nlohmann::json backTestResultToJson(const BacktestResult& result) {
    nlohmann::json json_result;
    
    json_result["starting_capital"] = result.starting_capital;
    json_result["ending_value"] = result.ending_value;
    json_result["total_return_pct"] = result.total_return_pct;
    json_result["trades"] = result.total_trades;
    json_result["winning_trades"] = result.winning_trades;
    json_result["losing_trades"] = result.losing_trades;
    json_result["win_rate"] = result.win_rate;
    json_result["max_drawdown"] = result.max_drawdown;
    json_result["sharpe_ratio"] = result.sharpe_ratio;
    json_result["signals_generated"] = result.signals_generated.size();
    json_result["start_date"] = result.start_date;
    json_result["end_date"] = result.end_date;
    json_result["profit_factor"] = result.profit_factor;
    json_result["average_win"] = result.average_win;
    json_result["average_loss"] = result.average_loss;
    json_result["volatility"] = result.volatility;
    json_result["annualized_return"] = result.annualized_return;
    
    json_result["performance_metrics"] = createPerformanceMetricsJson(result);
    json_result["signals"] = tradingSignalsToJsonArray(result.signals_generated);
    
    return json_result;
}

nlohmann::json tradingSignalToJson(const TradingSignal& signal) {
    nlohmann::json sig;
    sig["signal"] = (signal.signal == Signal::BUY) ? "BUY" : "SELL";
    sig["price"] = signal.price;
    sig["date"] = signal.date;
    sig["reason"] = signal.reason;
    sig["confidence"] = signal.confidence;
    return sig;
}

nlohmann::json tradingSignalsToJsonArray(const std::vector<TradingSignal>& signals) {
    nlohmann::json signals_array = nlohmann::json::array();
    for (const auto& signal : signals) {
        signals_array.push_back(tradingSignalToJson(signal));
    }
    return signals_array;
}

nlohmann::json createEquityCurveJson(const std::vector<double>& equity_curve,
                                    const std::vector<PriceData>& price_data,
                                    const std::string& start_date) {
    nlohmann::json equity_array = nlohmann::json::array();
    
    for (size_t i = 0; i < equity_curve.size() && i < price_data.size(); ++i) {
        nlohmann::json point;
        point["date"] = (i < price_data.size()) ? price_data[i].date : start_date;
        point["value"] = equity_curve[i];
        equity_array.push_back(point);
    }
    
    return equity_array;
}

nlohmann::json createPerformanceMetricsJson(const BacktestResult& result) {
    nlohmann::json performance_metrics;
    performance_metrics["total_return_pct"] = result.total_return_pct;
    performance_metrics["sharpe_ratio"] = result.sharpe_ratio;
    performance_metrics["max_drawdown_pct"] = result.max_drawdown;
    performance_metrics["win_rate"] = result.win_rate;
    performance_metrics["total_trades"] = result.total_trades;
    performance_metrics["winning_trades"] = result.winning_trades;
    performance_metrics["losing_trades"] = result.losing_trades;
    performance_metrics["profit_factor"] = result.profit_factor;
    performance_metrics["average_win"] = result.average_win;
    performance_metrics["average_loss"] = result.average_loss;
    performance_metrics["volatility"] = result.volatility;
    performance_metrics["annualized_return"] = result.annualized_return;
    
    return performance_metrics;
}

nlohmann::json createProgressJson(double progress_pct, 
                                 const std::string& current_date,
                                 double current_value,
                                 double current_price,
                                 int day,
                                 int total_days) {
    nlohmann::json progress;
    progress["type"] = "progress";
    progress["progress_pct"] = progress_pct;
    progress["current_date"] = current_date;
    progress["current_value"] = current_value;
    progress["current_price"] = current_price;
    progress["day"] = day;
    progress["total_days"] = total_days;
    return progress;
}

template<typename T>
T getJsonValue(const nlohmann::json& json, const std::string& key, const T& default_value) {
    if (json.contains(key)) {
        try {
            return json[key].get<T>();
        } catch (const std::exception&) {
            return default_value;
        }
    }
    return default_value;
}

// Explicit template instantiations for common types
template std::string getJsonValue<std::string>(const nlohmann::json&, const std::string&, const std::string&);
template double getJsonValue<double>(const nlohmann::json&, const std::string&, const double&);
template int getJsonValue<int>(const nlohmann::json&, const std::string&, const int&);
template bool getJsonValue<bool>(const nlohmann::json&, const std::string&, const bool&);

bool validateJsonFields(const nlohmann::json& json, const std::vector<std::string>& required_fields) {
    for (const auto& field : required_fields) {
        if (!json.contains(field)) {
            return false;
        }
    }
    return true;
}

} // namespace JsonHelpers