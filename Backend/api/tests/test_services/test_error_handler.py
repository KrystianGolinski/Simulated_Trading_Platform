import pytest
from unittest.mock import patch
from services.error_handler import ErrorHandler, ErrorCode, ErrorSeverity, SimulationError

class TestErrorHandler:
    
    def test_init(self):
        # Test ErrorHandler initialization
        handler = ErrorHandler()
        assert handler.error_history == []
    
    def test_create_engine_validation_error(self):
        # Test engine validation error creation
        handler = ErrorHandler()
        validation_result = {
            'error_code': 'ENGINE_NOT_CONFIGURED',
            'error': 'Engine path not configured',
            'suggestions': ['Set engine path in configuration']
        }
        
        error = handler.create_engine_validation_error(validation_result)
        
        assert error.error_code == ErrorCode.ENGINE_NOT_CONFIGURED
        assert error.message == 'Engine path not configured'
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.suggestions == ['Set engine path in configuration']
        assert len(handler.error_history) == 1
    
    def test_create_engine_validation_error_unknown(self):
        # Test engine validation error with unknown error code
        handler = ErrorHandler()
        validation_result = {
            'error_code': 'UNKNOWN_CODE',
            'error': 'Unknown error'
        }
        
        error = handler.create_engine_validation_error(validation_result)
        
        assert error.error_code == ErrorCode.UNKNOWN_ERROR
        assert error.message == 'Unknown error'
    
    def test_categorize_cpp_timeout_error(self):
        # Test C++ timeout error categorization
        handler = ErrorHandler()
        
        error = handler.categorize_cpp_engine_error(
            return_code=-9,
            stdout="",
            stderr="Process killed"
        )
        
        assert error.error_code == ErrorCode.PROCESS_TIMEOUT
        assert "timeout" in error.message.lower()
        assert error.severity == ErrorSeverity.HIGH
        assert "resource-intensive" in error.suggestions[0]
        assert error.context["return_code"] == -9
        assert error.context["cpp_stderr"] == "Process killed"
    
    def test_categorize_cpp_file_not_found_error(self):
        # Test C++ file not found error categorization
        handler = ErrorHandler()
        
        error = handler.categorize_cpp_engine_error(
            return_code=127,
            stdout="",
            stderr="command not found"
        )
        
        assert error.error_code == ErrorCode.ENGINE_FILE_NOT_FOUND
        assert "executable not found" in error.message
        assert error.severity == ErrorSeverity.CRITICAL
        assert "compiled successfully" in error.suggestions[0]
    
    def test_categorize_cpp_permission_error(self):
        # Test C++ permission error categorization
        handler = ErrorHandler()
        
        error = handler.categorize_cpp_engine_error(
            return_code=1,
            stdout="",
            stderr="Permission denied when executing"
        )
        
        assert error.error_code == ErrorCode.PERMISSION_ERROR
        assert "permission denied" in error.message.lower()
        assert error.severity == ErrorSeverity.HIGH
        assert "permissions" in error.suggestions[0]
    
    def test_categorize_cpp_memory_error(self):
        # Test C++ memory error categorization
        handler = ErrorHandler()
        
        error = handler.categorize_cpp_engine_error(
            return_code=1,
            stdout="",
            stderr="std::bad_alloc: out of memory"
        )
        
        assert error.error_code == ErrorCode.MEMORY_ERROR
        assert "out of memory" in error.message
        assert error.severity == ErrorSeverity.HIGH
        assert "memory limits" in error.suggestions[1]
    
    def test_categorize_cpp_generic_error(self):
        # Test generic C++ error categorization
        handler = ErrorHandler()
        
        error = handler.categorize_cpp_engine_error(
            return_code=1,
            stdout="Some output",
            stderr="Generic error occurred"
        )
        
        assert error.error_code == ErrorCode.PROCESS_EXECUTION_FAILED
        assert "return code 1" in error.message
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.context["cpp_stdout"] == "Some output"
        assert error.context["cpp_stderr"] == "Generic error occurred"
    
    def test_create_json_parse_error(self):
        # Test JSON parse error creation
        handler = ErrorHandler()
        json_error = "Expecting ',' delimiter: line 1 column 25"
        raw_output = '{"key": "value" "invalid": true}'
        
        error = handler.create_json_parse_error(json_error, raw_output)
        
        assert error.error_code == ErrorCode.JSON_PARSE_ERROR
        assert json_error in error.message
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.context["raw_output_preview"] == raw_output
        assert "valid JSON" in error.suggestions[0]
    
    def test_create_validation_error(self):
        # Test validation error creation
        handler = ErrorHandler()
        validation_message = "Invalid win rate value"
        context = {"field": "win_rate", "value": -0.5}
        
        error = handler.create_validation_error(validation_message, context)
        
        assert error.error_code == ErrorCode.INVALID_RESULT_DATA
        assert error.message == validation_message
        assert error.context == context
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_create_generic_error(self):
        # Test generic error creation
        handler = ErrorHandler()
        message = "Unexpected system error"
        context = {"system": "linux"}
        severity = ErrorSeverity.HIGH
        
        error = handler.create_generic_error(message, context, severity)
        
        assert error.error_code == ErrorCode.UNKNOWN_ERROR
        assert error.message == message
        assert error.context == context
        assert error.severity == severity
        assert "Contact support" in error.suggestions[0]
    
    def test_get_error_statistics_empty(self):
        # Test error statistics with no errors
        handler = ErrorHandler()
        stats = handler.get_error_statistics()
        
        assert stats["total_errors"] == 0
        assert "error_codes" not in stats
    
    def test_get_error_statistics_with_errors(self):
        # Test error statistics with multiple errors
        handler = ErrorHandler()
        
        # Create multiple errors
        handler.create_generic_error("Error 1", severity=ErrorSeverity.HIGH)
        handler.create_json_parse_error("JSON error", "invalid json")
        handler.create_generic_error("Error 2", severity=ErrorSeverity.HIGH)
        
        stats = handler.get_error_statistics()
        
        assert stats["total_errors"] == 3
        assert stats["error_codes"]["UNKNOWN_ERROR"] == 2
        assert stats["error_codes"]["JSON_PARSE_ERROR"] == 1
        assert stats["severity_distribution"]["high"] == 2
        assert stats["severity_distribution"]["medium"] == 1
        assert stats["latest_error"] is not None
    
    def test_clear_error_history(self):
        # Test clearing error history
        handler = ErrorHandler()
        handler.create_generic_error("Test error")
        
        assert len(handler.error_history) == 1
        
        handler.clear_error_history()
        
        assert len(handler.error_history) == 0
    
    def test_extract_cpp_error_details_exception(self):
        # Test C++ error detail extraction with standard exception via CppErrorExtractor
        handler = ErrorHandler()
        stderr = "terminate called after throwing an instance of 'std::runtime_error'\nwhat(): Database connection failed"
        
        details = handler.cpp_error_extractor.extract_cpp_error_details(stderr, "")
        
        assert details["exception_type"] == "std::runtime_error"
        assert details["error_message"] == "Database connection failed"
    
    def test_extract_cpp_error_details_memory_error(self):
        # Test C++ error detail extraction with memory error
        handler = ErrorHandler()
        stderr = "std::bad_alloc: out of memory allocation failed"
        
        details = handler.cpp_error_extractor.extract_cpp_error_details(stderr, "")
        
        assert details["exception_type"] == "bad_alloc"
        assert any("memory" in suggestion.lower() for suggestion in details["suggestions"])
    
    def test_extract_cpp_error_details_segfault(self):
        # Test C++ error detail extraction with segmentation fault
        handler = ErrorHandler()
        stderr = "Segmentation fault (core dumped)"
        
        details = handler.cpp_error_extractor.extract_cpp_error_details(stderr, "")
        
        assert details["exception_type"] == "Segmentation fault"
        assert "null pointer" in details["suggestions"][0]
    
    def test_extract_cpp_error_details_file_location(self):
        # Test C++ error detail extraction with file location
        handler = ErrorHandler()
        stderr = "Error at trading_engine.cpp:145 in function calculateProfit"
        
        details = handler.cpp_error_extractor.extract_cpp_error_details(stderr, "")
        
        assert details["file_location"] == "trading_engine.cpp"
        assert details["line_number"] == "145"
    
    def test_extract_cpp_error_details_json_error(self):
        # Test C++ error detail extraction with JSON-related error
        handler = ErrorHandler()
        stderr = "JSON parsing failed: invalid format"
        
        details = handler.cpp_error_extractor.extract_cpp_error_details(stderr, "")
        
        assert any("JSON" in suggestion for suggestion in details["suggestions"])
    
    def test_simulation_error_to_dict(self):
        # Test SimulationError to_dict conversion
        error = SimulationError(
            error_code=ErrorCode.JSON_PARSE_ERROR,
            message="Test error",
            severity=ErrorSeverity.HIGH,
            context={"test": "value"},
            suggestions=["Test suggestion"]
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_code"] == "JSON_PARSE_ERROR"
        assert error_dict["message"] == "Test error"
        assert error_dict["severity"] == "high"
        assert error_dict["context"] == {"test": "value"}
        assert error_dict["suggestions"] == ["Test suggestion"]
        assert "timestamp" in error_dict
    
    @patch('services.error_handler.logger')
    def test_log_error_levels(self, mock_logger):
        # Test different error logging levels
        handler = ErrorHandler()
        
        # Test critical error logging
        error_critical = SimulationError(
            ErrorCode.ENGINE_NOT_CONFIGURED,
            "Critical error",
            ErrorSeverity.CRITICAL
        )
        handler._log_error(error_critical)
        mock_logger.critical.assert_called()
        
        # Test high error logging
        error_high = SimulationError(
            ErrorCode.MEMORY_ERROR,
            "High error",
            ErrorSeverity.HIGH
        )
        handler._log_error(error_high)
        mock_logger.error.assert_called()
        
        # Test medium error logging
        error_medium = SimulationError(
            ErrorCode.JSON_PARSE_ERROR,
            "Medium error",
            ErrorSeverity.MEDIUM
        )
        handler._log_error(error_medium)
        mock_logger.warning.assert_called()
        
        # Test low error logging
        error_low = SimulationError(
            ErrorCode.UNKNOWN_ERROR,
            "Low error",
            ErrorSeverity.LOW
        )
        handler._log_error(error_low)
        mock_logger.info.assert_called()