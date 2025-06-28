import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from models import SimulationResults, SimulationStatus, PerformanceMetrics, TradeRecord, SimulationConfig
from .performance_calculator import PerformanceCalculator
from .trade_converter import TradeConverter
from .equity_processor import EquityProcessor

logger = logging.getLogger(__name__)

class ResultProcessor:
    def __init__(self):
        self.results_storage: Dict[str, SimulationResults] = {}
        self.performance_calculator = PerformanceCalculator()
        self.trade_converter = TradeConverter()
        self.equity_processor = EquityProcessor()
    
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
            
            # Process performance metrics using specialized calculator
            simulation_result.performance_metrics = self.performance_calculator.calculate_performance_metrics(result_data)
            
            # Process signals into proper trade pairs using specialized converter
            signals_data = result_data.get("signals", [])
            simulation_result.trades = self.trade_converter.convert_signals_to_trades(signals_data, result_data)
            
            # Process equity curve using specialized processor
            simulation_result.equity_curve = self.equity_processor.process_equity_curve(result_data)
            
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
            
            # Validate performance_metrics structure using specialized calculator
            if "performance_metrics" in result_data:
                if not self.performance_calculator.validate_performance_metrics(result_data["performance_metrics"]):
                    return False
            
            # Validate signals structure using specialized converter
            if "signals" in result_data:
                if not self.trade_converter.validate_signals(result_data["signals"]):
                    return False
            
            # Validate equity_curve structure using specialized processor
            if "equity_curve" in result_data:
                if not self.equity_processor.validate_equity_curve(result_data["equity_curve"]):
                    return False
            
            # Cross-field validation using specialized calculator
            if not self.performance_calculator.validate_cross_field_consistency(result_data):
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
    
