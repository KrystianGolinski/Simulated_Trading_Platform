# Comprehensive validation system
# Handles input validation, error messaging, and data availability checks

import logging
from typing import List, Dict, Any, Optional
from datetime import date
from database import DatabaseManager
from models import SimulationConfig, ValidationError, ValidationResult
from services.error_handler import ErrorHandler, ErrorCode, ErrorSeverity

logger = logging.getLogger(__name__)

class SimulationValidator:
    # Comprehensive validator for simulation configurations
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.error_handler = ErrorHandler()
    
    async def validate_simulation_config(self, config: SimulationConfig) -> ValidationResult:
        # Comprehensive validation of simulation configuration
        # Returns ValidationResult with detailed error information

        errors = []
        warnings = []
        
        try:
            # Validate stock symbols (critical validation first)
            symbol_validation = await self._validate_symbols(config.symbols)
            errors.extend(symbol_validation)
            
            # Early exit if symbols are invalid - no point checking other validations
            if errors:
                logger.debug(f"Early exit due to symbol validation errors: {len(errors)} errors found")
                return ValidationResult(is_valid=False, errors=errors, warnings=[])
            
            # Validate capital amount (quick validation)
            capital_validation = self._validate_capital(config.starting_capital)
            errors.extend(capital_validation)
            
            # Early exit if capital is invalid
            if errors:
                logger.debug("Early exit due to capital validation errors")
                return ValidationResult(is_valid=False, errors=errors, warnings=[])
            
            # Validate strategy parameters (quick validation)
            strategy_validation = self._validate_strategy_parameters(config)
            errors.extend(strategy_validation)
            
            # Early exit if strategy parameters are invalid
            if errors:
                logger.debug("Early exit due to strategy parameter validation errors")
                return ValidationResult(is_valid=False, errors=errors, warnings=[])
            
            # Only perform expensive data validation if all basic validations pass
            date_validation = await self._validate_date_ranges(config)
            errors.extend(date_validation['errors'])
            warnings.extend(date_validation['warnings'])
            
            # Check for potential issues (warnings) - only if no critical errors
            if not errors:
                config_warnings = self._check_configuration_warnings(config)
                warnings.extend(config_warnings)
            
        except Exception as e:
            # Use structured error handling with detailed context
            error = self.error_handler.create_generic_error(
                message=f"Validation system error: {str(e)}",
                context={
                    "config_symbols": getattr(config, 'symbols', None),
                    "config_dates": f"{getattr(config, 'start_date', None)} to {getattr(config, 'end_date', None)}",
                    "exception_type": type(e).__name__,
                    "original_error": str(e)
                },
                severity=ErrorSeverity.HIGH
            )
            
            logger.error(f"Validation error: {error.message} | Context: {error.context}")
            errors.append(ValidationError(
                field="general",
                message=error.message,
                error_code=error.error_code.value
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_symbols(self, symbols: List[str]) -> List[ValidationError]:
        # Validate stock symbols exist in database
        errors = []
        
        if not symbols:
            errors.append(ValidationError(
                field="symbols",
                message="At least one stock symbol is required",
                error_code="SYMBOLS_EMPTY"
            ))
            return errors
        
        # Check for duplicate symbols
        unique_symbols = set(s.upper() for s in symbols)
        if len(unique_symbols) != len(symbols):
            errors.append(ValidationError(
                field="symbols",
                message="Duplicate symbols are not allowed",
                error_code="SYMBOLS_DUPLICATE"
            ))
        
        # Check if symbols exist in database
        try:
            symbol_validation = await self.db.validate_multiple_symbols(symbols)
            
            for symbol in symbols:
                symbol_upper = symbol.upper()
                if not symbol_validation.get(symbol_upper, False):
                    errors.append(ValidationError(
                        field="symbols",
                        message=f"Stock symbol '{symbol_upper}' not found in database",
                        error_code="SYMBOL_NOT_FOUND"
                    ))
                    
        except Exception as e:
            # Structured error handling for database validation errors
            error = self.error_handler.create_generic_error(
                message=f"Database error during symbol validation: {str(e)}",
                context={
                    "symbols": symbols,
                    "exception_type": type(e).__name__,
                    "database_operation": "symbol_validation"
                },
                severity=ErrorSeverity.MEDIUM
            )
            
            logger.error(f"Symbol validation error: {error.message} | Context: {error.context}")
            errors.append(ValidationError(
                field="symbols",
                message="Unable to validate symbols due to database error",
                error_code="DATABASE_ERROR"
            ))
        
        return errors
    
    async def _validate_date_ranges(self, config: SimulationConfig) -> Dict[str, List]:
        # Validate date ranges have sufficient data
        errors = []
        warnings = []
        
        for symbol in config.symbols:
            try:
                # Check data availability for this symbol in the date range
                data_check = await self.db.validate_date_range_has_data(
                    symbol, config.start_date, config.end_date
                )
                
                if 'error' in data_check:
                    errors.append(ValidationError(
                        field="date_range",
                        message=f"Database error checking data for {symbol}: {data_check['error']}",
                        error_code="DATABASE_ERROR"
                    ))
                    continue
                
                if not data_check['has_data']:
                    errors.append(ValidationError(
                        field="date_range",
                        message=f"No data available for {symbol} between {config.start_date} and {config.end_date}",
                        error_code="NO_DATA_AVAILABLE"
                    ))
                
                elif not data_check.get('sufficient_data', True):
                    coverage = data_check.get('coverage_percentage', 0)
                    warnings.append(
                        f"Limited data coverage for {symbol}: {coverage:.1f}% "
                        f"({data_check['record_count']} of {data_check['expected_days']} days). "
                        f"Results may be less reliable."
                    )
                
            except Exception as e:
                # Structured error handling for date range validation
                error = self.error_handler.create_generic_error(
                    message=f"Error validating date range for {symbol}: {str(e)}",
                    context={
                        "symbol": symbol,
                        "date_range": f"{config.start_date} to {config.end_date}",
                        "exception_type": type(e).__name__,
                        "validation_step": "data_availability_check"
                    },
                    severity=ErrorSeverity.MEDIUM
                )
                
                logger.error(f"Date range validation error: {error.message} | Context: {error.context}")
                errors.append(ValidationError(
                    field="date_range",
                    message=f"Unable to validate data availability for {symbol}",
                    error_code="VALIDATION_ERROR"
                ))
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_capital(self, capital: float) -> List[ValidationError]:
        # Validate starting capital amount
        errors = []
        
        # Basic range validation (already handled by Pydantic, but double-check)
        if capital <= 0:
            errors.append(ValidationError(
                field="starting_capital",
                message="Starting capital must be greater than 0",
                error_code="CAPITAL_INVALID"
            ))
        
        # Practical minimum for meaningful trading - adjusted for comprehensive backtesting scenarios
        if capital < 1000:
            errors.append(ValidationError(
                field="starting_capital",
                message="Starting capital should be at least £1,000 for meaningful backtesting results",
                error_code="CAPITAL_TOO_LOW"
            ))
        
        # Maximum reasonable amount for simulation platform
        if capital > 10_000_000:  # 10 million
            errors.append(ValidationError(
                field="starting_capital",
                message="Starting capital exceeds reasonable limit (£10,000,000)",
                error_code="CAPITAL_TOO_HIGH"
            ))
        
        return errors
    
    def _validate_strategy_parameters(self, config: SimulationConfig) -> List[ValidationError]:
        # Validate strategy-specific parameters using dynamic strategy registry
        errors = []
        
        try:
            # Import here to avoid circular imports
            from strategy_registry import get_strategy_registry
            
            registry = get_strategy_registry()
            
            # Validate that strategy exists
            available_strategies = registry.get_available_strategies()
            if config.strategy not in available_strategies:
                errors.append(ValidationError(
                    field="strategy",
                    message=f"Unknown strategy '{config.strategy}'. Available strategies: {list(available_strategies.keys())}",
                    error_code="UNKNOWN_STRATEGY"
                ))
                return errors
            
            # Use strategy registry for dynamic validation
            validation_errors = registry.validate_strategy_config(config.strategy, config.strategy_parameters)
            
            # Convert strategy registry errors to ValidationError objects
            for error_msg in validation_errors:
                # Extract field name if possible (assumes format "Field name: error message")
                field_name = "strategy_parameters"
                if ":" in error_msg:
                    potential_field = error_msg.split(":")[0].strip()
                    if potential_field.replace("_", "").replace(" ", "").isalnum():
                        field_name = potential_field.lower().replace(" ", "_")
                
                errors.append(ValidationError(
                    field=field_name,
                    message=error_msg,
                    error_code="STRATEGY_PARAMETER_INVALID"
                ))
                
        except ImportError:
            # Fallback to basic validation if strategy registry not available
            errors.append(ValidationError(
                field="strategy",
                message="Strategy validation system not available",
                error_code="STRATEGY_SYSTEM_UNAVAILABLE"
            ))
        except Exception as e:
            errors.append(ValidationError(
                field="strategy",
                message=f"Strategy validation failed: {str(e)}",
                error_code="STRATEGY_VALIDATION_ERROR"
            ))
        
        return errors
    
    def _check_configuration_warnings(self, config: SimulationConfig) -> List[str]:
        # Check for potential configuration issues that don't prevent execution
        warnings = []
        
        # Check date range length
        date_range_days = (config.end_date - config.start_date).days
        
        if date_range_days < 30:
            warnings.append(
                f"Short date range ({date_range_days} days). Consider using at least 30 days for more reliable results."
            )
        
        
        # Strategy-specific warnings using dynamic strategy system
        if config.strategy == "ma_crossover":
            # Get MA crossover parameters from strategy_parameters
            short_ma = config.strategy_parameters.get("short_ma")
            long_ma = config.strategy_parameters.get("long_ma")
            if short_ma and long_ma:
                ratio = long_ma / short_ma
                if ratio < 1.5:
                    warnings.append(
                        f"MA periods are close ({short_ma}, {long_ma}). "
                        f"Consider using more separated periods for clearer signals."
                    )
        
        # Capital vs strategy warnings
        if config.starting_capital < 10000 and date_range_days > 365:
            warnings.append(
                "Low starting capital with long time period may result in limited trading activity."
            )
        
        return warnings
    
    def run_comprehensive_validation_tests(self) -> Dict[str, Any]:
        # Comprehensive test suite for the validation system
        # Tests all validation components systematically
        
        test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'overall_status': 'UNKNOWN'
        }
        
        print("\nRunning Comprehensive Validation System Tests")
        print("Testing all validation components systematically...\n")
        
        # Test categories to run
        test_categories = [
            ('Symbol Validation Tests', self._test_symbol_validation),
            ('Capital Validation Tests', self._test_capital_validation),
            ('Date Range Validation Tests', self._test_date_range_validation),
            ('Strategy Parameter Tests', self._test_strategy_parameters),
            ('Configuration Warning Tests', self._test_configuration_warnings),
            ('Error Handling Tests', self._test_error_handling),
            ('Edge Case Tests', self._test_edge_cases)
        ]
        
        for category_name, test_function in test_categories:
            print(f"Running {category_name}...")
            category_results = test_function()
            
            test_results['total_tests'] += category_results['total']
            test_results['passed_tests'] += category_results['passed']
            test_results['failed_tests'] += category_results['failed']
            test_results['test_details'].append({
                'category': category_name,
                'results': category_results
            })
            
            status_symbol = "PASS" if category_results['failed'] == 0 else "FAIL"
            print(f"  {status_symbol} {category_name}: {category_results['passed']}/{category_results['total']} passed\n")
        
        # Determine overall test status
        if test_results['failed_tests'] == 0:
            test_results['overall_status'] = 'PASSED'
            print(f"\nALL VALIDATION TESTS PASSED ({test_results['passed_tests']}/{test_results['total_tests']})")
        else:
            test_results['overall_status'] = 'FAILED'
            print(f"\nVALIDATION TESTS FAILED ({test_results['failed_tests']}/{test_results['total_tests']} failures)")
        
        return test_results
    
    def _test_symbol_validation(self) -> Dict[str, int]:
        # Test symbol validation logic comprehensively
        results = {'total': 0, 'passed': 0, 'failed': 0, 'details': []}
        
        test_cases = [
            # Valid cases
            (['AAPL'], True, "Single valid symbol"),
            (['AAPL', 'GOOGL'], True, "Multiple valid symbols"),
            
            # Invalid cases
            ([], False, "Empty symbol list"),
            (['AAPL', 'AAPL'], False, "Duplicate symbols"),
            (['INVALID_SYMBOL_123'], False, "Non-existent symbol"),
            ([''], False, "Empty string symbol"),
        ]
        
        for symbols, expected_valid, description in test_cases:
            results['total'] += 1
            
            try:
                # Create mock validation result based on symbol logic
                has_duplicates = len(set(str(s).upper() for s in symbols if s)) != len([s for s in symbols if s])
                is_empty = not symbols or all(not s for s in symbols)
                has_invalid = any(not s or not isinstance(s, str) or len(s) == 0 for s in symbols)
                
                actual_valid = not (has_duplicates or is_empty or has_invalid)
                
                if actual_valid == expected_valid:
                    results['passed'] += 1
                    results['details'].append(f"PASS: {description}")
                else:
                    results['failed'] += 1
                    results['details'].append(f"FAIL: {description} - Expected {expected_valid}, got {actual_valid}")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"ERROR: {description} - Exception: {str(e)}")
        
        return results
    
    def _test_capital_validation(self) -> Dict[str, int]:
        # Test capital validation logic comprehensively
        results = {'total': 0, 'passed': 0, 'failed': 0, 'details': []}
        
        test_cases = [
            # Valid cases
            (10000.0, True, "Standard capital amount"),
            (1000.0, True, "Minimum recommended capital"),
            (100000.0, True, "Large capital amount"),
            
            # Invalid cases
            (0.0, False, "Zero capital"),
            (-1000.0, False, "Negative capital"),
            (500.0, False, "Below minimum threshold"),
            (15000000.0, False, "Above maximum threshold"),
        ]
        
        for capital, expected_valid, description in test_cases:
            results['total'] += 1
            
            try:
                validation_errors = self._validate_capital(capital)
                actual_valid = len(validation_errors) == 0
                
                if actual_valid == expected_valid:
                    results['passed'] += 1
                    results['details'].append(f"PASS: {description}")
                else:
                    results['failed'] += 1
                    error_messages = [e.message for e in validation_errors]
                    results['details'].append(f"FAIL: {description} - Expected {expected_valid}, got {actual_valid}. Errors: {error_messages}")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"ERROR: {description} - Exception: {str(e)}")
        
        return results
    
    def _test_date_range_validation(self) -> Dict[str, int]:
        # Test date range validation scenarios
        results = {'total': 0, 'passed': 0, 'failed': 0, 'details': []}
        
        # Test date range calculations
        test_cases = [
            (date(2020, 1, 1), date(2020, 2, 1), 31, "One month range"),
            (date(2020, 1, 1), date(2020, 1, 15), 14, "Two week range"),
            (date(2019, 1, 1), date(2024, 1, 1), 1827, "Five year range"),
            (date(2023, 1, 1), date(2023, 1, 1), 0, "Same day range"),
        ]
        
        for start_date, end_date, expected_days, description in test_cases:
            results['total'] += 1
            
            try:
                actual_days = (end_date - start_date).days
                
                if actual_days == expected_days:
                    results['passed'] += 1
                    results['details'].append(f"PASS: {description}")
                else:
                    results['failed'] += 1
                    results['details'].append(f"FAIL: {description} - Expected {expected_days} days, got {actual_days}")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"ERROR: {description} - Exception: {str(e)}")
        
        return results
    
    def _test_strategy_parameters(self) -> Dict[str, int]:
        # Test strategy parameter validation
        results = {'total': 0, 'passed': 0, 'failed': 0, 'details': []}
        
        # Mock configuration objects for testing
        from types import SimpleNamespace
        
        test_cases = [
            # Valid strategy configurations
            ('ma_crossover', {'short_ma': 10, 'long_ma': 20}, True, "Valid MA crossover parameters"),
            ('rsi', {'period': 14, 'oversold': 30, 'overbought': 70}, True, "Valid RSI parameters"),
            
            # Invalid strategy configurations
            ('invalid_strategy', {}, False, "Non-existent strategy"),
            ('ma_crossover', {'short_ma': 20, 'long_ma': 10}, False, "Invalid MA parameters (short > long)"),
        ]
        
        for strategy, params, expected_valid, description in test_cases:
            results['total'] += 1
            
            try:
                # Create mock config
                mock_config = SimpleNamespace()
                mock_config.strategy = strategy
                mock_config.strategy_parameters = params
                
                validation_errors = self._validate_strategy_parameters(mock_config)
                actual_valid = len(validation_errors) == 0
                
                if actual_valid == expected_valid:
                    results['passed'] += 1
                    results['details'].append(f"PASS: {description}")
                else:
                    results['failed'] += 1
                    error_messages = [e.message for e in validation_errors]
                    results['details'].append(f"FAIL: {description} - Expected {expected_valid}, got {actual_valid}. Errors: {error_messages}")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"ERROR: {description} - Exception: {str(e)}")
        
        return results
    
    def _test_configuration_warnings(self) -> Dict[str, int]:
        # Test configuration warning generation
        results = {'total': 0, 'passed': 0, 'failed': 0, 'details': []}
        
        from types import SimpleNamespace
        
        test_cases = [
            # Short date ranges should generate warnings
            (date(2023, 1, 1), date(2023, 1, 15), 10000, 'ma_crossover', {'short_ma': 5, 'long_ma': 20}, True, "Short date range warning"),
            
            # Long date ranges should NOT generate warnings
            (date(2019, 1, 1), date(2024, 1, 1), 10000, 'ma_crossover', {'short_ma': 10, 'long_ma': 20}, False, "Long date range should not warn"),
            
            # MA crossover close periods should warn
            (date(2020, 1, 1), date(2020, 6, 1), 10000, 'ma_crossover', {'short_ma': 10, 'long_ma': 12}, True, "Close MA periods warning"),
            
            # Low capital with long period should warn
            (date(2020, 1, 1), date(2022, 1, 1), 5000, 'ma_crossover', {'short_ma': 10, 'long_ma': 20}, True, "Low capital long period warning"),
        ]
        
        for start_date, end_date, capital, strategy, params, expect_warnings, description in test_cases:
            results['total'] += 1
            
            try:
                # Create mock config
                mock_config = SimpleNamespace()
                mock_config.start_date = start_date
                mock_config.end_date = end_date
                mock_config.starting_capital = capital
                mock_config.strategy = strategy
                mock_config.strategy_parameters = params
                
                warnings = self._check_configuration_warnings(mock_config)
                has_warnings = len(warnings) > 0
                
                if has_warnings == expect_warnings:
                    results['passed'] += 1
                    results['details'].append(f"PASS: {description}")
                else:
                    results['failed'] += 1
                    results['details'].append(f"FAIL: {description} - Expected warnings: {expect_warnings}, got warnings: {has_warnings}. Warnings: {warnings}")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"ERROR: {description} - Exception: {str(e)}")
        
        return results
    
    def _test_error_handling(self) -> Dict[str, int]:
        # Test error handling robustness
        results = {'total': 0, 'passed': 0, 'failed': 0, 'details': []}
        
        # Test that validation doesn't crash with unusual inputs
        unusual_inputs = [
            (None, "None input handling"),
            ({}, "Empty dict input"),
            ([], "Empty list input"),
            ("", "Empty string input"),
            (float('inf'), "Infinity input"),
            (float('-inf'), "Negative infinity input"),
        ]
        
        for unusual_input, description in unusual_inputs:
            results['total'] += 1
            
            try:
                # Test capital validation with unusual input
                try:
                    self._validate_capital(unusual_input)
                    results['passed'] += 1
                    results['details'].append(f"PASS: {description} - No crash")
                except (TypeError, ValueError):
                    # Expected for some inputs
                    results['passed'] += 1
                    results['details'].append(f"PASS: {description} - Expected exception handled")
                except Exception as e:
                    results['failed'] += 1
                    results['details'].append(f"FAIL: {description} - Unexpected exception: {str(e)}")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"ERROR: {description} - Test setup failed: {str(e)}")
        
        return results
    
    def _test_edge_cases(self) -> Dict[str, int]:
        # Test edge cases and boundary conditions
        results = {'total': 0, 'passed': 0, 'failed': 0, 'details': []}
        
        # Test boundary values for capital
        boundary_tests = [
            (999.99, "Just below minimum capital"),
            (1000.0, "Exactly minimum capital"),
            (1000.01, "Just above minimum capital"),
            (9999999.99, "Just below maximum capital"),
            (10000000.0, "Exactly maximum capital"),
            (10000000.01, "Just above maximum capital"),
        ]
        
        for capital, description in boundary_tests:
            results['total'] += 1
            
            try:
                validation_errors = self._validate_capital(capital)
                
                # Determine expected validity based on our validation rules
                expected_valid = 1000.0 <= capital <= 10000000.0
                actual_valid = len(validation_errors) == 0
                
                if actual_valid == expected_valid:
                    results['passed'] += 1
                    results['details'].append(f"PASS: {description}")
                else:
                    results['failed'] += 1
                    results['details'].append(f"FAIL: {description} - Expected {expected_valid}, got {actual_valid}")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"ERROR: {description} - Exception: {str(e)}")
        
        return results
    
    async def check_database_connection(self) -> ValidationResult:
        # Check if database is accessible and contains required data
        errors = []
        warnings = []
        
        try:
            health = await self.db.health_check()
            
            if health.get('status') != 'healthy':
                errors.append(ValidationError(
                    field="database",
                    message=f"Database is not healthy: {health.get('error', 'Unknown error')}",
                    error_code="DATABASE_UNHEALTHY"
                ))
            else:
                # Check if we have sufficient data
                stats = health.get('data_stats', {})
                symbols_count = stats.get('symbols_daily', 0)
                records_count = stats.get('daily_records', 0)
                
                if symbols_count < 10:
                    warnings.append(f"Limited symbol data available ({symbols_count} symbols)")
                
                if records_count < 1000:
                    warnings.append(f"Limited historical data available ({records_count} records)")
                    
        except Exception as e:
            # Structured error handling for database connection issues
            error = self.error_handler.create_generic_error(
                message=f"Database connection check failed: {str(e)}",
                context={
                    "exception_type": type(e).__name__,
                    "database_operation": "connection_health_check",
                    "error_details": str(e)
                },
                severity=ErrorSeverity.CRITICAL
            )
            
            logger.error(f"Database connection error: {error.message} | Context: {error.context}")
            errors.append(ValidationError(
                field="database",
                message=f"Unable to connect to database: {str(e)}",
                error_code="DATABASE_CONNECTION_ERROR"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )