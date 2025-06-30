import logging
from typing import Dict, Any
from models import PerformanceMetrics

logger = logging.getLogger(__name__)

class PerformanceCalculator:
    # No initialization needed for stateless calculation operations
    
    def calculate_performance_metrics(self, result_data: Dict[str, Any]) -> PerformanceMetrics:
        # Process performance metrics from C++ engine output
        performance_data = result_data.get("performance_metrics", {})
        if not performance_data:
            performance_data = result_data
            
        return PerformanceMetrics(
            # Core metrics
            total_return_pct=performance_data.get("total_return_pct", 0.0),
            sharpe_ratio=performance_data.get("sharpe_ratio"),
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
            
            # Computed metrics (could be calculated here if needed)
            profit_factor=None,  # Could calculate: winning_value / losing_value
            average_win=None,
            average_loss=None,
            annualized_return=None,
            volatility=None
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