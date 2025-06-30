import logging
import math
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from models import PerformanceMetrics

logger = logging.getLogger(__name__)

def _sanitize_float(value: Optional[float]) -> Optional[float]:
    # Converts non-JSON-compliant floats (inf, -inf, NaN) to None
    if value is None or not isinstance(value, (int, float)) or math.isfinite(value):
        return value
    logger.warning(f"Sanitizing non-finite float value: {value}")
    return None

class PerformanceCalculator:
    # No initialization needed for stateless calculation operations
    
    def calculate_performance_metrics(self, result_data: Dict[str, Any]) -> PerformanceMetrics:
        # Process performance metrics from C++ engine output
        performance_data = result_data.get("performance_metrics", {})
        if not performance_data:
            performance_data = result_data
        
        # Calculate additional metrics from available data
        profit_factor = self._calculate_profit_factor(result_data)
        average_win, average_loss = self._calculate_average_win_loss(result_data)
        annualized_return = self._calculate_annualized_return(result_data)
        volatility = self._calculate_volatility(result_data)
        
        # Sanitize all potentially non-finite float values
        sharpe_ratio = _sanitize_float(performance_data.get("sharpe_ratio"))
        profit_factor = _sanitize_float(profit_factor)
        average_win = _sanitize_float(average_win)
        average_loss = _sanitize_float(average_loss)
        annualized_return = _sanitize_float(annualized_return)
        volatility = _sanitize_float(volatility)

        return PerformanceMetrics(
            # Core metrics
            total_return_pct=performance_data.get("total_return_pct", 0.0),
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=performance_data.get("max_drawdown_pct", performance_data.get("max_drawdown", 0.0)),
            win_rate=performance_data.get("win_rate", 0.0),
            total_trades=performance_data.get("total_trades", performance_data.get("trades", 0)),
            winning_trades=performance_data.get("winning_trades", 0),
            losing_trades=performance_data.get("losing_trades", 0),
            
            # Additional metrics from C++ engine
            final_balance=result_data.get("ending_value"),
            starting_capital=result_data.get("starting_capital"),
            max_drawdown=performance_data.get("max_drawdown"),  # Absolute value
            
            # Signals data
            signals_generated=len(result_data.get("signals", [])),
            
            # Computed metrics - now calculated and sanitized
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            annualized_return=annualized_return,
            volatility=volatility
        )
    
    def validate_performance_metrics(self, performance_metrics: Any) -> bool:
        # Validate performance_metrics structure and content
        if not isinstance(performance_metrics, dict):
            logger.error("performance_metrics must be a dictionary")
            return False
        
        # Expected numeric fields with validation rules (flexible)
        metric_validations = [
            ("total_return_pct", float, None),  # Can be negative
            ("sharpe_ratio", float, None),      # Can be negative  
            ("max_drawdown_pct", float, lambda x: x >= 0),  # Drawdown as positive percentage
            ("win_rate", float, lambda x: x >= 0),     # Win rate can be percentage or ratio
            ("total_trades", int, lambda x: x >= 0),
            ("winning_trades", int, lambda x: x >= 0),
            ("losing_trades", int, lambda x: x >= 0),
        ]
        
        for field, field_type, validator in metric_validations:
            if field in performance_metrics:
                value = performance_metrics[field]
                if field_type == float and not isinstance(value, (int, float)):
                    logger.error(f"Performance metric '{field}' must be numeric, got {type(value)}")
                    return False
                elif field_type == int and not isinstance(value, int):
                    logger.error(f"Performance metric '{field}' must be integer, got {type(value)}")
                    return False
                
                if validator and not validator(value):
                    logger.error(f"Performance metric '{field}' failed validation: {value}")
                    return False
        
        # Cross-field validation within performance metrics (flexible trade counting)
        if "winning_trades" in performance_metrics and "losing_trades" in performance_metrics and "total_trades" in performance_metrics:
            winning = performance_metrics["winning_trades"]
            losing = performance_metrics["losing_trades"]
            total = performance_metrics["total_trades"]
            
            # Allow for neutral trades, open positions, or different counting methodologies
            if winning + losing > total:
                logger.error(f"Trade count impossible: winning({winning}) + losing({losing}) > total({total})")
                return False
            elif winning + losing < total:
                # This is acceptable - there might be neutral trades or open positions
                logger.info(f"Trade count info: winning({winning}) + losing({losing}) < total({total}) - may include neutral/open trades")
        
        return True
    
    def validate_cross_field_consistency(self, result_data: Dict[str, Any]) -> bool:
        # Validate consistency between different fields in the result data
        try:
            # Validate starting vs ending capital consistency
            starting_capital = result_data.get("starting_capital")
            ending_value = result_data.get("ending_value")
            total_return_pct = result_data.get("total_return_pct")
            
            if starting_capital and ending_value and total_return_pct is not None:
                expected_return = ((ending_value - starting_capital) / starting_capital) * 100
                if abs(expected_return - total_return_pct) > 0.01:  # Allow small floating point differences
                    logger.warning(f"Return percentage inconsistency: expected {expected_return:.2f}%, got {total_return_pct:.2f}%")
            
            # Validate equity curve consistency
            if "equity_curve" in result_data:
                equity_curve = result_data["equity_curve"]
                if equity_curve and len(equity_curve) > 0:
                    final_equity_value = equity_curve[-1].get("value")
                    if final_equity_value and ending_value:
                        if abs(final_equity_value - ending_value) > 0.01:
                            logger.warning(f"Equity curve final value ({final_equity_value}) doesn't match ending_value ({ending_value})")
            
            return True
            
        except Exception as e:
            logger.error(f"Cross-field validation error: {e}")
            return False
    
    def _calculate_profit_factor(self, result_data: Dict[str, Any]) -> Optional[float]:
        # Calculate profit factor: total winning value / total losing value
        try:
            signals = result_data.get("signals", [])
            if not signals or len(signals) < 2:
                return None
            
            total_winning_value = 0.0
            total_losing_value = 0.0
            open_positions = {}
            
            for signal in signals:
                signal_type = signal.get("signal", "").upper()
                price = signal.get("price", 0.0)
                symbol = result_data.get("symbol", "UNKNOWN")
                
                if signal_type == "BUY":
                    # Calculate position size based on available capital
                    starting_capital = result_data.get("starting_capital", 10000.0)
                    position_size_pct = 0.1  # 10% position size
                    available_capital = starting_capital * position_size_pct
                    shares = int(available_capital / price) if price > 0 else 0
                    
                    open_positions[symbol] = {
                        "entry_price": price,
                        "shares": shares
                    }
                    
                elif signal_type == "SELL" and symbol in open_positions:
                    position = open_positions[symbol]
                    entry_price = position["entry_price"]
                    shares = position["shares"]
                    
                    total_entry_value = entry_price * shares
                    total_exit_value = price * shares
                    profit_loss = total_exit_value - total_entry_value
                    
                    if profit_loss > 0:
                        total_winning_value += profit_loss
                    else:
                        total_losing_value += abs(profit_loss)
                    
                    del open_positions[symbol]
            
            if total_losing_value > 0:
                return total_winning_value / total_losing_value
            elif total_winning_value > 0:
                return float('inf')  # All wins, no losses
            else:
                return None  # No completed trades
                
        except Exception as e:
            logger.error(f"Error calculating profit factor: {e}")
            return None
    
    def _calculate_average_win_loss(self, result_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        # Calculate average winning and losing trade values
        try:
            signals = result_data.get("signals", [])
            if not signals or len(signals) < 2:
                return None, None
            
            winning_trades = []
            losing_trades = []
            open_positions = {}
            
            for signal in signals:
                signal_type = signal.get("signal", "").upper()
                price = signal.get("price", 0.0)
                symbol = result_data.get("symbol", "UNKNOWN")
                
                if signal_type == "BUY":
                    # Calculate position size based on available capital
                    starting_capital = result_data.get("starting_capital", 10000.0)
                    position_size_pct = 0.1  # 10% position size
                    available_capital = starting_capital * position_size_pct
                    shares = int(available_capital / price) if price > 0 else 0
                    
                    open_positions[symbol] = {
                        "entry_price": price,
                        "shares": shares
                    }
                    
                elif signal_type == "SELL" and symbol in open_positions:
                    position = open_positions[symbol]
                    entry_price = position["entry_price"]
                    shares = position["shares"]
                    
                    total_entry_value = entry_price * shares
                    total_exit_value = price * shares
                    profit_loss = total_exit_value - total_entry_value
                    
                    if profit_loss > 0:
                        winning_trades.append(profit_loss)
                    else:
                        losing_trades.append(abs(profit_loss))
                    
                    del open_positions[symbol]
            
            average_win = sum(winning_trades) / len(winning_trades) if winning_trades else None
            average_loss = sum(losing_trades) / len(losing_trades) if losing_trades else None
            
            return average_win, average_loss
            
        except Exception as e:
            logger.error(f"Error calculating average win/loss: {e}")
            return None, None
    
    def _calculate_annualized_return(self, result_data: Dict[str, Any]) -> Optional[float]:
        # Calculate annualised return based on total return and time period
        try:
            total_return_pct = result_data.get("total_return_pct")
            start_date = result_data.get("start_date")
            end_date = result_data.get("end_date")
            
            if total_return_pct is None or not start_date or not end_date:
                return None
            
            # Parse dates to calculate time period
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Calculate years between dates
            time_delta = end_dt - start_dt
            years = time_delta.days / 365.25
            
            if years <= 0:
                return None
            
            # Convert percentage return to decimal
            total_return_decimal = total_return_pct / 100.0
            
            # Calculate annualised return: (1 + total_return)^(1/years) - 1
            annualized_return = ((1 + total_return_decimal) ** (1 / years)) - 1
            
            # Convert back to percentage
            return annualized_return * 100.0
            
        except Exception as e:
            logger.error(f"Error calculating annualised return: {e}")
            return None
    
    def _calculate_volatility(self, result_data: Dict[str, Any]) -> Optional[float]:
        # Calculate volatility from equity curve daily returns
        try:
            equity_curve = result_data.get("equity_curve", [])
            if not equity_curve or len(equity_curve) < 2:
                return None
            
            # Extract values from equity curve
            if isinstance(equity_curve[0], dict):
                values = [point.get("value", 0) for point in equity_curve]
            else:
                values = equity_curve
            
            if len(values) < 2:
                return None
            
            # Calculate daily returns
            daily_returns = []
            for i in range(1, len(values)):
                if values[i-1] > 0:
                    daily_return = (values[i] - values[i-1]) / values[i-1]
                    daily_returns.append(daily_return)
            
            if not daily_returns:
                return None
            
            # Calculate standard deviation of daily returns
            mean_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
            daily_volatility = math.sqrt(variance)
            
            # Annualise volatility (assuming 252 trading days per year)
            annualized_volatility = daily_volatility * math.sqrt(252)
            
            # Convert to percentage
            return annualized_volatility * 100.0
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return None