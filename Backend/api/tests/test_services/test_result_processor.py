import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from services.result_processor import ResultProcessor
from models import SimulationResults, SimulationStatus, PerformanceMetrics, TradeRecord, SimulationConfig, StrategyType

class TestResultProcessor:
    
    def test_init(self):
        # Test ResultProcessor initialization
        processor = ResultProcessor()
        assert processor.results_storage == {}
    
    def test_initialize_simulation_result(self, sample_simulation_config):
        # Test simulation result initialization
        processor = ResultProcessor()
        simulation_id = "test-sim-123"
        
        result = processor.initialize_simulation_result(simulation_id, sample_simulation_config)
        
        assert result.simulation_id == simulation_id
        assert result.status == SimulationStatus.PENDING
        assert result.config == sample_simulation_config
        assert result.created_at is not None
        assert result.started_at is None
        assert result.completed_at is None
        assert result.performance_metrics is None
        assert result.trades == []
        assert result.error_message is None
        assert simulation_id in processor.results_storage
    
    def test_update_simulation_status(self, sample_simulation_config):
        # Test simulation status update
        processor = ResultProcessor()
        simulation_id = "test-sim-123"
        
        # Initialize simulation
        processor.initialize_simulation_result(simulation_id, sample_simulation_config)
        
        # Update status
        started_at = datetime.now()
        processor.update_simulation_status(simulation_id, SimulationStatus.RUNNING, started_at)
        
        result = processor.results_storage[simulation_id]
        assert result.status == SimulationStatus.RUNNING
        assert result.started_at == started_at
    
    def test_update_simulation_status_unknown_id(self):
        # Test updating status for unknown simulation ID
        processor = ResultProcessor()
        
        with patch('services.result_processor.logger') as mock_logger:
            processor.update_simulation_status("unknown-id", SimulationStatus.RUNNING)
            mock_logger.warning.assert_called_with("Attempting to update status for unknown simulation: unknown-id")
    
    def test_process_simulation_results(self, sample_simulation_config, sample_cpp_output):
        # Test processing successful simulation results
        processor = ResultProcessor()
        simulation_id = "test-sim-123"
        
        # Initialize simulation
        processor.initialize_simulation_result(simulation_id, sample_simulation_config)
        
        # Process results
        result_data = {
            "starting_capital": 10000.0,
            "ending_value": 11550.0,
            "total_return_pct": 15.5,
            "performance_metrics": {
                "total_return_pct": 15.5,
                "sharpe_ratio": 1.34,
                "max_drawdown_pct": 8.2,
                "win_rate": 65.0,
                "total_trades": 25,
                "winning_trades": 16,
                "losing_trades": 9
            },
            "signals": [
                {"signal": "BUY", "price": 150.0, "date": "2023-01-15"},
                {"signal": "SELL", "price": 160.0, "date": "2023-01-20"}
            ],
            "equity_curve": [
                {"date": "2023-01-01", "value": 10000.0},
                {"date": "2023-01-31", "value": 11550.0}
            ]
        }
        
        processor.process_simulation_results(simulation_id, result_data)
        
        result = processor.results_storage[simulation_id]
        assert result.status == SimulationStatus.COMPLETED
        assert result.completed_at is not None
        assert result.starting_capital == 10000.0
        assert result.ending_value == 11550.0
        assert result.total_return_pct == 15.5
        
        # Check performance metrics
        metrics = result.performance_metrics
        assert metrics.total_return_pct == 15.5
        assert metrics.sharpe_ratio == 1.34
        assert metrics.max_drawdown_pct == 8.2
        assert metrics.win_rate == 65.0
        assert metrics.total_trades == 25
        assert metrics.winning_trades == 16
        assert metrics.losing_trades == 9
        
        # Check trades were processed
        assert len(result.trades) == 1  # One complete buy-sell pair
        trade = result.trades[0]
        assert trade.symbol == "UNKNOWN"  # Default when not in result_data
        assert "BUY@150.00 -> SELL@160.00" in trade.action
        
        # Check equity curve
        assert len(result.equity_curve) == 2
    
    def test_process_simulation_results_unknown_id(self):
        # Test processing results for unknown simulation ID
        processor = ResultProcessor()
        
        with patch('services.result_processor.logger') as mock_logger:
            processor.process_simulation_results("unknown-id", {})
            mock_logger.error.assert_called_with("Cannot process results for unknown simulation: unknown-id")
    
    def test_process_simulation_results_error(self, sample_simulation_config):
        # Test processing results with exception
        processor = ResultProcessor()
        simulation_id = "test-sim-123"
        
        processor.initialize_simulation_result(simulation_id, sample_simulation_config)
        
        # Pass invalid data that will cause exception in processing
        invalid_data = None  # This will definitely cause an exception
        
        with patch('services.result_processor.logger') as mock_logger:
            processor.process_simulation_results(simulation_id, invalid_data)
            
            # Should mark simulation as failed
            result = processor.results_storage[simulation_id]
            assert result.status == SimulationStatus.FAILED
            assert result.error_message is not None
            mock_logger.error.assert_called()
    
    def test_mark_simulation_failed(self, sample_simulation_config):
        # Test marking simulation as failed
        processor = ResultProcessor()
        simulation_id = "test-sim-123"
        error_message = "Test error message"
        
        processor.initialize_simulation_result(simulation_id, sample_simulation_config)
        processor.mark_simulation_failed(simulation_id, error_message)
        
        result = processor.results_storage[simulation_id]
        assert result.status == SimulationStatus.FAILED
        assert result.error_message == error_message
        assert result.completed_at is not None
    
    def test_mark_simulation_failed_unknown_id(self):
        # Test marking unknown simulation as failed
        processor = ResultProcessor()
        
        with patch('services.result_processor.logger') as mock_logger:
            processor.mark_simulation_failed("unknown-id", "Error")
            mock_logger.warning.assert_called_with("Attempting to mark unknown simulation as failed: unknown-id")
    
    def test_get_simulation_result(self, sample_simulation_config):
        # Test getting simulation result
        processor = ResultProcessor()
        simulation_id = "test-sim-123"
        
        # Test getting non-existent result
        result = processor.get_simulation_result("non-existent")
        assert result is None
        
        # Test getting existing result
        original_result = processor.initialize_simulation_result(simulation_id, sample_simulation_config)
        retrieved_result = processor.get_simulation_result(simulation_id)
        assert retrieved_result == original_result
    
    def test_get_all_simulation_results(self, sample_simulation_config):
        # Test getting all simulation results
        processor = ResultProcessor()
        
        # Test empty results
        all_results = processor.get_all_simulation_results()
        assert all_results == {}
        
        # Add some results
        sim1 = processor.initialize_simulation_result("sim1", sample_simulation_config)
        sim2 = processor.initialize_simulation_result("sim2", sample_simulation_config)
        
        all_results = processor.get_all_simulation_results()
        assert len(all_results) == 2
        assert "sim1" in all_results
        assert "sim2" in all_results
        assert all_results["sim1"] == sim1
        assert all_results["sim2"] == sim2
    
    def test_cleanup_old_results(self, sample_simulation_config):
        # Test cleanup of old simulation results
        processor = ResultProcessor()
        
        # Create some results with different ages
        old_result = processor.initialize_simulation_result("old-sim", sample_simulation_config)
        old_result.created_at = datetime.now() - timedelta(hours=25)  # Older than 24 hours
        
        recent_result = processor.initialize_simulation_result("recent-sim", sample_simulation_config)
        recent_result.created_at = datetime.now() - timedelta(hours=1)  # Recent
        
        # Cleanup old results
        removed_count = processor.cleanup_old_results(max_age_hours=24)
        
        assert removed_count == 1
        assert "old-sim" not in processor.results_storage
        assert "recent-sim" in processor.results_storage
    
    def test_convert_signals_to_trades(self, sample_simulation_config):
        # Test conversion of signals to trade records via TradeConverter
        processor = ResultProcessor()
        
        signals_data = [
            {"signal": "BUY", "price": 100.0, "date": "2023-01-01"},
            {"signal": "SELL", "price": 110.0, "date": "2023-01-05"},
            {"signal": "BUY", "price": 105.0, "date": "2023-01-10"},
            # No corresponding SELL - should create open position trade
        ]
        
        result_data = {
            "symbol": "AAPL",
            "starting_capital": 10000.0
        }
        
        trades = processor.trade_converter.convert_signals_to_trades(signals_data, result_data)
        
        assert len(trades) == 2
        
        # First trade (complete buy-sell pair)
        completed_trade = trades[0]
        assert completed_trade.symbol == "AAPL"
        assert "BUY@100.00 -> SELL@110.00" in completed_trade.action
        assert "+10.00%" in completed_trade.action  # 10% profit
        assert completed_trade.total_value > 0  # Profit
        
        # Second trade (open position)
        open_trade = trades[1]
        assert open_trade.symbol == "AAPL"
        assert "POSITION OPEN" in open_trade.action
        assert "BUY@105.00" in open_trade.action
        assert open_trade.total_value == 0.0  # No profit/loss for open positions
    
    def test_calculate_position_size(self):
        # Test position size calculation via TradeConverter
        processor = ResultProcessor()
        
        result_data = {"starting_capital": 10000.0}
        
        # Test normal case
        position_size = processor.trade_converter._calculate_position_size(100.0, result_data)
        expected_shares = int((10000.0 * 0.1) / 100.0)  # 10% of capital / price
        assert position_size == max(1, expected_shares)
        
        # Test edge case with very high price
        position_size = processor.trade_converter._calculate_position_size(10000.0, result_data)
        assert position_size == 1  # At least 1 share
        
        # Test edge case with zero price
        position_size = processor.trade_converter._calculate_position_size(0.0, result_data)
        assert position_size == 1  # At least 1 share
    
    def test_parse_json_result_valid(self, sample_cpp_output):
        # Test parsing valid JSON result
        processor = ResultProcessor()
        
        result = processor.parse_json_result(sample_cpp_output["stdout"])
        
        assert isinstance(result, dict)
        assert "total_return" in result
        assert "win_rate" in result
        assert result["win_rate"] == 0.65
    
    def test_parse_json_result_empty(self):
        # Test parsing empty JSON result
        processor = ResultProcessor()
        
        with pytest.raises(json.JSONDecodeError):
            processor.parse_json_result("")
    
    def test_parse_json_result_malformed(self):
        # Test parsing malformed JSON result
        processor = ResultProcessor()
        
        malformed_json = '{"key": "value", "incomplete":'
        
        with pytest.raises(json.JSONDecodeError):
            processor.parse_json_result(malformed_json)
    
    def test_parse_json_result_with_errors(self):
        # Test parsing JSON with C++ error content
        processor = ResultProcessor()
        
        error_json = 'terminate called after throwing exception {"valid": "json"}'
        
        with pytest.raises(json.JSONDecodeError):
            processor.parse_json_result(error_json)
    
    def test_validate_result_data_valid(self):
        # Test validation of valid result data
        processor = ResultProcessor()
        
        valid_data = {
            "starting_capital": 10000.0,
            "ending_value": 11000.0,
            "total_return_pct": 10.0,
            "performance_metrics": {
                "total_return_pct": 10.0,
                "sharpe_ratio": 1.5,
                "max_drawdown_pct": 5.0,
                "win_rate": 60.0,
                "total_trades": 10,
                "winning_trades": 6,
                "losing_trades": 4
            },
            "signals": [
                {"signal": "BUY", "price": 100.0, "date": "2023-01-01"},
                {"signal": "SELL", "price": 110.0, "date": "2023-01-05"}
            ],
            "equity_curve": [
                {"date": "2023-01-01", "value": 10000.0},
                {"date": "2023-01-31", "value": 11000.0}
            ]
        }
        
        assert processor.validate_result_data(valid_data) is True
    
    def test_validate_result_data_missing_required(self):
        # Test validation with missing required fields
        processor = ResultProcessor()
        
        invalid_data = {
            "ending_value": 11000.0
            # Missing starting_capital
        }
        
        assert processor.validate_result_data(invalid_data) is False
    
    def test_validate_result_data_invalid_types(self):
        # Test validation with invalid data types
        processor = ResultProcessor()
        
        invalid_data = {
            "starting_capital": "10000",  # Should be numeric
            "ending_value": 11000.0,
        }
        
        assert processor.validate_result_data(invalid_data) is False
    
    def test_validate_result_data_invalid_performance_metrics(self):
        # Test validation with invalid performance metrics
        processor = ResultProcessor()
        
        invalid_data = {
            "starting_capital": 10000.0,
            "ending_value": 11000.0,
            "performance_metrics": {
                "win_rate": -10.0,  # Invalid negative win rate
                "total_trades": -5   # Invalid negative trade count
            }
        }
        
        assert processor.validate_result_data(invalid_data) is False
    
    def test_validate_result_data_invalid_signals(self):
        # Test validation with invalid signals
        processor = ResultProcessor()
        
        invalid_data = {
            "starting_capital": 10000.0,
            "ending_value": 11000.0,
            "signals": [
                {"signal": "INVALID", "price": 100.0, "date": "2023-01-01"},  # Invalid signal type
                {"price": 100.0, "date": "2023-01-01"}  # Missing signal field
            ]
        }
        
        assert processor.validate_result_data(invalid_data) is False
    
    def test_validate_result_data_impossible_trade_counts(self):
        # Test validation with impossible trade count combinations
        processor = ResultProcessor()
        
        invalid_data = {
            "starting_capital": 10000.0,
            "ending_value": 11000.0,
            "performance_metrics": {
                "total_trades": 5,
                "winning_trades": 6,  # More winning trades than total
                "losing_trades": 2
            }
        }
        
        assert processor.validate_result_data(invalid_data) is False
    
    def test_validate_result_data_acceptable_trade_counts(self):
        # Test validation with acceptable trade count combinations (neutral trades
        processor = ResultProcessor()
        
        valid_data = {
            "starting_capital": 10000.0,
            "ending_value": 11000.0,
            "performance_metrics": {
                "total_trades": 10,
                "winning_trades": 4,
                "losing_trades": 3  # 3 neutral/open trades - acceptable
            }
        }
        
        assert processor.validate_result_data(valid_data) is True
    
    def test_pre_validate_json_text_cpp_errors(self):
        # Test pre-validation catches C++ runtime errors
        processor = ResultProcessor()
        
        cpp_error_text = "terminate called after throwing an exception"
        
        with pytest.raises(ValueError, match="C\\+\\+ runtime error"):
            processor._pre_validate_json_text(cpp_error_text)
    
    def test_pre_validate_json_text_error_messages(self):
        # Test pre-validation catches error messages
        processor = ResultProcessor()
        
        error_text = "Error: failed to connect to database"
        
        with pytest.raises(ValueError, match="error messages instead of JSON"):
            processor._pre_validate_json_text(error_text)
    
    def test_pre_validate_json_text_unbalanced_braces(self):
        # Test pre-validation catches unbalanced braces
        processor = ResultProcessor()
        
        unbalanced_json = '{"key": "value", "nested": {"incomplete"'
        
        with pytest.raises(ValueError, match="Unbalanced braces"):
            processor._pre_validate_json_text(unbalanced_json)
    
    def test_validate_cross_field_consistency_return_calculation(self):
        # Test cross-field validation for return percentage calculation
        processor = ResultProcessor()
        
        # Test consistent data
        consistent_data = {
            "starting_capital": 10000.0,
            "ending_value": 11000.0,
            "total_return_pct": 10.0  # (11000 - 10000) / 10000 * 100 = 10%
        }
        
        assert processor.performance_calculator.validate_cross_field_consistency(consistent_data) is True
        
        # Test inconsistent data
        inconsistent_data = {
            "starting_capital": 10000.0,
            "ending_value": 11000.0,
            "total_return_pct": 20.0  # Should be 10%, not 20%
        }
        
        with patch('services.performance_calculator.logger') as mock_logger:
            result = processor.performance_calculator.validate_cross_field_consistency(inconsistent_data)
            assert result is True  # Should still pass but log warning
            mock_logger.warning.assert_called()
    
    def test_validate_parsed_json_structure_invalid_root(self):
        # Test validation of parsed JSON structure with invalid root type
        processor = ResultProcessor()
        
        with pytest.raises(ValueError, match="Root JSON must be object"):
            processor._validate_parsed_json_structure([])  # Array instead of object
    
    def test_validate_parsed_json_structure_empty(self):
        # Test validation of empty JSON object
        processor = ResultProcessor()
        
        with pytest.raises(ValueError, match="JSON object is empty"):
            processor._validate_parsed_json_structure({})
    
    def test_validate_parsed_json_structure_null_critical_fields(self):
        # Test validation with null critical fields
        processor = ResultProcessor()
        
        with pytest.raises(ValueError, match="Critical field .* is null"):
            processor._validate_parsed_json_structure({
                "starting_capital": None,  # Critical field is null
                "other_field": "value"
            })