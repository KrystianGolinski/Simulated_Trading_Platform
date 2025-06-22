import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from models import SimulationResults, SimulationStatus, PerformanceMetrics, TradeRecord, SimulationConfig

logger = logging.getLogger(__name__)

class ResultProcessor:
    def __init__(self):
        self.results_storage: Dict[str, SimulationResults] = {}
    
    def initialize_simulation_result(self, simulation_id: str, config: SimulationConfig) -> SimulationResults:
        result = SimulationResults(
            simulation_id=simulation_id,
            status=SimulationStatus.PENDING,
            config=config,
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            performance_metrics=None,
            trades=[],
            error_message=None
        )
        self.results_storage[simulation_id] = result
        return result
    
    def update_simulation_status(self, simulation_id: str, status: SimulationStatus, 
                               started_at: Optional[datetime] = None):
        if simulation_id not in self.results_storage:
            logger.warning(f"Attempting to update status for unknown simulation: {simulation_id}")
            return
        
        self.results_storage[simulation_id].status = status
        if started_at:
            self.results_storage[simulation_id].started_at = started_at
    
    def process_simulation_results(self, simulation_id: str, result_data: Dict[str, Any]):
        if simulation_id not in self.results_storage:
            logger.error(f"Cannot process results for unknown simulation: {simulation_id}")
            return
        
        try:
            simulation_result = self.results_storage[simulation_id]
            
            # Update completion status
            simulation_result.status = SimulationStatus.COMPLETED
            simulation_result.completed_at = datetime.now()
            
            # Update basic results from C++ engine output
            simulation_result.starting_capital = result_data.get("starting_capital")
            simulation_result.ending_value = result_data.get("ending_value")
            simulation_result.total_return_pct = result_data.get("total_return_pct")
            
            # Process performance metrics (use performance_metrics if available, otherwise use top-level fields)
            performance_data = result_data.get("performance_metrics", {})
            if not performance_data:
                # Fallback to top-level fields if performance_metrics not available
                performance_data = result_data
                
            simulation_result.performance_metrics = PerformanceMetrics(
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
            
            # Process signals into proper trade pairs
            signals_data = result_data.get("signals", [])
            simulation_result.trades = self._convert_signals_to_trades(signals_data, result_data)
            
            # Process equity curve
            simulation_result.equity_curve = result_data.get("equity_curve", [])
            
            logger.info(f"Successfully processed results for simulation {simulation_id}")
            
        except Exception as e:
            logger.error(f"Error processing simulation results for {simulation_id}: {e}")
            self.mark_simulation_failed(simulation_id, f"Result processing error: {str(e)}")
    
    def mark_simulation_failed(self, simulation_id: str, error_message: str):
        if simulation_id not in self.results_storage:
            logger.warning(f"Attempting to mark unknown simulation as failed: {simulation_id}")
            return
        
        self.results_storage[simulation_id].status = SimulationStatus.FAILED
        self.results_storage[simulation_id].error_message = error_message
        self.results_storage[simulation_id].completed_at = datetime.now()
        
        logger.error(f"Simulation {simulation_id} marked as failed: {error_message}")
    
    def get_simulation_result(self, simulation_id: str) -> Optional[SimulationResults]:
        return self.results_storage.get(simulation_id)
    
    def get_all_simulation_results(self) -> Dict[str, SimulationResults]:
        return self.results_storage.copy()
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for simulation_id, result in self.results_storage.items():
            if result.created_at < cutoff_time:
                to_remove.append(simulation_id)
        
        for simulation_id in to_remove:
            del self.results_storage[simulation_id]
            logger.info(f"Cleaned up old simulation result: {simulation_id}")
        
        return len(to_remove)
    
    def _convert_signals_to_trades(self, signals_data: List[Dict[str, Any]], result_data: Dict[str, Any]) -> List[TradeRecord]:
        # Convert trading signals into proper trade pairs with profit/loss calculations
        trades = []
        open_positions = {}  # symbol -> {entry_signal, shares}
        symbol = result_data.get("symbol", "UNKNOWN")
        
        for signal in signals_data:
            if not isinstance(signal, dict):
                continue
                
            signal_type = signal.get("signal", "").upper()
            price = signal.get("price", 0.0)
            date_str = signal.get("date", datetime.now().isoformat())
            
            if signal_type == "BUY":
                # Open a new position
                shares = self._calculate_position_size(price, result_data)
                open_positions[symbol] = {
                    "entry_date": date_str,
                    "entry_price": price,
                    "shares": shares
                }
                
            elif signal_type == "SELL" and symbol in open_positions:
                # Close the position and create a trade record
                position = open_positions[symbol]
                entry_price = position["entry_price"]
                shares = position["shares"]
                
                # Calculate profit/loss
                total_entry_value = entry_price * shares
                total_exit_value = price * shares
                profit_loss = total_exit_value - total_entry_value
                profit_loss_pct = (profit_loss / total_entry_value) * 100 if total_entry_value > 0 else 0.0
                
                # Create trade record for the completed trade
                trade = TradeRecord(
                    date=f"{position['entry_date']} -> {date_str}",  # Show entry and exit dates
                    symbol=symbol,
                    action=f"BUY@{entry_price:.2f} -> SELL@{price:.2f} ({profit_loss_pct:+.2f}%)",
                    shares=shares,
                    price=entry_price,  # Entry price
                    total_value=profit_loss  # Profit/loss as total value
                )
                trades.append(trade)
                
                # Remove the closed position
                del open_positions[symbol]
        
        # Handle any remaining open positions as incomplete trades
        for symbol, position in open_positions.items():
            trade = TradeRecord(
                date=f"{position['entry_date']} (OPEN)",
                symbol=symbol,
                action=f"BUY@{position['entry_price']:.2f} (POSITION OPEN)",
                shares=position["shares"],
                price=position["entry_price"],
                total_value=0.0  # No profit/loss for open positions
            )
            trades.append(trade)
        
        return trades
    
    def _calculate_position_size(self, price: float, result_data: Dict[str, Any]) -> int:
        # Calculate how many shares to buy based on available capital and strategy
        starting_capital = result_data.get("starting_capital", 10000.0)
        
        # Simple strategy: use a fixed percentage of capital per trade
        position_size_pct = 0.1  # 10% of capital per position
        available_capital = starting_capital * position_size_pct
        
        if price > 0:
            shares = int(available_capital / price)
            return max(1, shares)  # At least 1 share
        return 1
    
    def parse_json_result(self, json_text: str) -> Dict[str, Any]:
        # Parse and validate JSON result from C++ engine with comprehensive error handling
        try:
            if not json_text.strip():
                raise json.JSONDecodeError("Empty output", "", 0)
            
            # Pre-validation: Check for common malformed JSON patterns
            self._pre_validate_json_text(json_text)
            
            # Parse JSON
            result_data = json.loads(json_text)
            
            # Post-parse validation
            self._validate_parsed_json_structure(result_data)
            
            return result_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON result: {e}")
            raise
        except ValueError as e:
            logger.error(f"JSON validation error: {e}")
            raise json.JSONDecodeError(str(e), json_text, 0)
    
    def validate_result_data(self, result_data: Dict[str, Any]) -> bool:
        # Comprehensive validation of C++ engine result data structure and content
        try:
            # Check for basic required fields
            required_fields = ["ending_value", "starting_capital"]
            for field in required_fields:
                if field not in result_data:
                    logger.error(f"Missing required field in result data: {field}")
                    return False
            
            # Validate numeric fields
            numeric_validations = [
                ("ending_value", float, lambda x: x >= 0),
                ("starting_capital", float, lambda x: x > 0),
                ("total_return_pct", float, None),  # Can be negative
            ]
            
            for field, _, validator in numeric_validations:
                if field in result_data:
                    value = result_data[field]
                    if not isinstance(value, (int, float)):
                        logger.error(f"Field '{field}' must be numeric, got {type(value)}")
                        return False
                    if validator and not validator(value):
                        logger.error(f"Field '{field}' failed validation: {value}")
                        return False
            
            # Validate performance_metrics structure
            if "performance_metrics" in result_data:
                if not self._validate_performance_metrics(result_data["performance_metrics"]):
                    return False
            
            # Validate signals structure
            if "signals" in result_data:
                if not self._validate_signals(result_data["signals"]):
                    return False
            
            # Validate equity_curve structure
            if "equity_curve" in result_data:
                if not self._validate_equity_curve(result_data["equity_curve"]):
                    return False
            
            # Cross-field validation
            if not self._validate_cross_field_consistency(result_data):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Exception during result data validation: {e}")
            return False
    
    def _pre_validate_json_text(self, json_text: str):
        # Lightweight pre-validation checks for obvious JSON corruption
        
        # Check for C++ runtime errors in output
        if "terminate called" in json_text or "segmentation fault" in json_text:
            raise ValueError("JSON contains C++ runtime error messages")
        
        # Check for incomplete JSON (common with crashed processes)
        if not json_text.strip().startswith('{'):
            if any(error_indicator in json_text.lower() for error_indicator in 
                   ["error:", "exception:", "failed:", "abort", "crash"]):
                raise ValueError("Output contains error messages instead of JSON")
        
        # Simple brace/bracket balance check
        brace_count = json_text.count('{') - json_text.count('}')
        bracket_count = json_text.count('[') - json_text.count(']')
        
        if brace_count != 0:
            raise ValueError(f"Unbalanced braces in JSON (difference: {brace_count})")
        if bracket_count != 0:
            raise ValueError(f"Unbalanced brackets in JSON (difference: {bracket_count})")
    
    def _validate_parsed_json_structure(self, result_data: Dict[str, Any]):
        # Validate the basic structure of parsed JSON data
        if not isinstance(result_data, dict):
            raise ValueError(f"Root JSON must be object/dict, got {type(result_data)}")
        
        if len(result_data) == 0:
            raise ValueError("JSON object is empty")
        
        # Check for obvious corruption indicators
        for key, value in result_data.items():
            if not isinstance(key, str):
                raise ValueError(f"JSON key must be string, got {type(key)}: {key}")
            
            # Check for null/undefined values that shouldn't be there
            if value is None and key in ["ending_value", "starting_capital"]:
                raise ValueError(f"Critical field '{key}' is null")
    
    def _validate_performance_metrics(self, performance_metrics: Any) -> bool:
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
    
    def _validate_signals(self, signals: Any) -> bool:
        # Validate signals array structure and content
        if not isinstance(signals, list):
            logger.error("signals must be a list")
            return False
        
        for i, signal in enumerate(signals):
            if not isinstance(signal, dict):
                logger.error(f"Signal {i} must be a dictionary")
                return False
            
            # Required signal fields
            required_signal_fields = ["signal", "price", "date"]
            for field in required_signal_fields:
                if field not in signal:
                    logger.error(f"Signal {i} missing required field: {field}")
                    return False
            
            # Validate signal values
            signal_type = signal.get("signal", "").upper()
            if signal_type not in ["BUY", "SELL"]:
                logger.error(f"Signal {i} has invalid signal type: {signal_type}")
                return False
            
            price = signal.get("price")
            if not isinstance(price, (int, float)) or price <= 0:
                logger.error(f"Signal {i} has invalid price: {price}")
                return False
            
            # Validate date format (basic check)
            date_str = signal.get("date")
            if not isinstance(date_str, str) or len(date_str) < 8:
                logger.error(f"Signal {i} has invalid date format: {date_str}")
                return False
        
        return True
    
    def _validate_equity_curve(self, equity_curve: Any) -> bool:
        # Validate equity_curve array structure and content
        if not isinstance(equity_curve, list):
            logger.error("equity_curve must be a list")
            return False
        
        for i, point in enumerate(equity_curve):
            if not isinstance(point, dict):
                logger.error(f"Equity curve point {i} must be a dictionary")
                return False
            
            # Required equity curve fields
            required_fields = ["date", "value"]
            for field in required_fields:
                if field not in point:
                    logger.error(f"Equity curve point {i} missing required field: {field}")
                    return False
            
            # Validate values
            value = point.get("value")
            if not isinstance(value, (int, float)) or value < 0:
                logger.error(f"Equity curve point {i} has invalid value: {value}")
                return False
            
            date_str = point.get("date")
            if not isinstance(date_str, str):
                logger.error(f"Equity curve point {i} has invalid date format: {date_str}")
                return False
        
        return True
    
    def _validate_cross_field_consistency(self, result_data: Dict[str, Any]) -> bool:
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