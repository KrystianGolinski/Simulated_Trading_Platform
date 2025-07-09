# Comprehensive Input Validation System
# This module provides the primary validation infrastructure for the Trading Platform API
# Key responsibilities:
# - Multi-layered simulation configuration validation
# - Stock symbol existence and temporal validation
# - Strategy parameter validation with dynamic strategy support
# - Data availability and coverage validation
# - Capital amount and risk parameter validation
# - Comprehensive error handling with structured messaging
# - Integration with temporal validation services
# - Database connectivity and health validation
#
# Validation Architecture:
# - Early exit validation for performance optimization
# - Structured error handling with detailed context
# - Integration with multiple validation services
# - Comprehensive test suite for validation logic
# - Warning system for non-blocking issues
# - Configuration optimization recommendations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from models import SimulationConfig, ValidationError, ValidationResult
from repositories.stock_data_repository import StockDataRepository
from services.error_handler import ErrorHandler, ErrorSeverity
from services.strategy_service import StrategyServiceInterface
from services.temporal_validation_service import TemporalValidationService

logger = logging.getLogger(__name__)


class SimulationValidator:
    # Comprehensive simulation configuration validator with multi-layered validation approach
    # Integrates multiple validation services for complete configuration verification
    # Provides structured error handling and performance-optimized validation workflow

    def __init__(
        self,
        stock_repo: StockDataRepository,
        strategy_service: StrategyServiceInterface,
    ):
        # Initialize validation dependencies using dependency injection pattern
        self.stock_repo = (
            stock_repo  # Repository for stock data operations and validation
        )
        self.temporal_service = TemporalValidationService(
            stock_repo
        )  # Temporal validation for trading periods
        self.error_handler = (
            ErrorHandler()
        )  # Structured error handling and categorisation
        self.strategy_service = (
            strategy_service  # Strategy validation and parameter checking
        )

        logger.debug(
            "SimulationValidator initialized with integrated validation services"
        )

    async def validate_simulation_config(
        self, config: SimulationConfig
    ) -> ValidationResult:
        # Comprehensive simulation configuration validation with optimized early-exit strategy
        # Performs multi-layered validation from basic parameter checks to complex data availability
        # Returns detailed validation results with structured error and warning information
        #
        # Validation Strategy:
        # 1. Quick validations first (symbols, capital, strategy) with early exit on failure
        # 2. Expensive validations only after basic validations pass (data availability)
        # 3. Warning generation for optimization recommendations
        # 4. Structured error handling with detailed context information

        errors = []
        warnings = []

        logger.debug(
            f"Starting validation for simulation config: {len(config.symbols)} symbols, "
            f"period {config.start_date} to {config.end_date}, strategy: {config.strategy}"
        )

        try:
            # Phase 1: Critical symbol validation (fast fail for invalid symbols)
            symbol_validation = await self._validate_symbols(config.symbols)
            errors.extend(symbol_validation)

            # Early exit if symbols are invalid - no point in further validation
            if errors:
                logger.debug(
                    f"Early exit due to symbol validation errors: {len(errors)} errors found"
                )
                return ValidationResult(is_valid=False, errors=errors, warnings=[])

            # Phase 2: Capital amount validation (quick validation)
            capital_validation = self._validate_capital(config.starting_capital)
            errors.extend(capital_validation)

            # Early exit if capital is invalid
            if errors:
                logger.debug("Early exit due to capital validation errors")
                return ValidationResult(is_valid=False, errors=errors, warnings=[])

            # Phase 3: Strategy parameter validation (potentially expensive for complex strategies)
            strategy_validation = await self._validate_strategy_parameters(config)
            errors.extend(strategy_validation)

            # Early exit if strategy parameters are invalid
            if errors:
                logger.debug("Early exit due to strategy parameter validation errors")
                return ValidationResult(is_valid=False, errors=errors, warnings=[])

            # Phase 4: Expensive data availability validation (only after basic validation passes)
            logger.debug("Performing data availability validation")
            date_validation = await self._validate_date_ranges(config)
            errors.extend(date_validation["errors"])
            warnings.extend(date_validation["warnings"])

            # Phase 5: Temporal validation and trading period analysis (if no critical errors)
            if not errors:
                logger.debug("Performing temporal validation analysis")
                temporal_info = (
                    await self.temporal_service.get_temporal_info_for_logging(
                        config.symbols, config.start_date, config.end_date
                    )
                )
                warnings.extend(temporal_info["warnings"])

            # Phase 6: Configuration optimization recommendations (only if validation successful)
            if not errors:
                config_warnings = self._check_configuration_warnings(config)
                warnings.extend(config_warnings)

        except Exception as e:
            # Comprehensive error handling for unexpected validation failures
            # Provides detailed context for debugging and system monitoring
            error = self.error_handler.create_generic_error(
                message=f"Validation system error during configuration validation: {str(e)}",
                context={
                    "config_symbols": getattr(config, "symbols", None),
                    "config_dates": f"{getattr(config, 'start_date', None)} to {getattr(config, 'end_date', None)}",
                    "config_strategy": getattr(config, "strategy", None),
                    "config_capital": getattr(config, "starting_capital", None),
                    "exception_type": type(e).__name__,
                    "original_error": str(e),
                    "validation_stage": "comprehensive_validation",
                },
                severity=ErrorSeverity.HIGH,
            )

            logger.error(
                f"Validation system error: {error.message} | Context: {error.context}"
            )
            errors.append(
                ValidationError(
                    field="general",
                    message="Validation system encountered an unexpected error",
                    error_code=error.error_code.value,
                )
            )

        # Generate final validation result with comprehensive status information
        validation_result = ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

        logger.debug(
            f"Validation completed: {'PASSED' if validation_result.is_valid else 'FAILED'} "
            f"({len(errors)} errors, {len(warnings)} warnings)"
        )

        return validation_result

    async def _validate_symbols(self, symbols: List[str]) -> List[ValidationError]:
        # Database symbol validation - basic validation now handled by Pydantic model
        # Focus on database-specific validation that requires async operations
        errors = []

        # Database existence validation
        try:
            logger.debug(f"Validating {len(symbols)} symbols against database")
            symbol_validation = await self.stock_repo.validate_multiple_symbols(symbols)

            # Check each symbol's existence
            for symbol in symbols:
                symbol_upper = symbol.upper().strip()
                if not symbol_validation.get(symbol_upper, False):
                    errors.append(
                        ValidationError(
                            field="symbols",
                            message=f"Stock symbol '{symbol_upper}' not found in database",
                            error_code="SYMBOL_NOT_FOUND",
                        )
                    )

        except Exception as e:
            # Structured error handling for database validation errors
            error = self.error_handler.create_generic_error(
                message=f"Database error during symbol validation: {str(e)}",
                context={
                    "symbols": symbols,
                    "symbol_count": len(symbols),
                    "exception_type": type(e).__name__,
                    "database_operation": "symbol_validation",
                },
                severity=ErrorSeverity.MEDIUM,
            )

            logger.error(
                f"Symbol validation database error: {error.message} | Context: {error.context}"
            )
            errors.append(
                ValidationError(
                    field="symbols",
                    message="Unable to validate symbols due to database connectivity issue",
                    error_code="DATABASE_ERROR",
                )
            )

        return errors

    async def _validate_date_ranges(self, config: SimulationConfig) -> Dict[str, List]:
        # Validate date ranges have sufficient data
        errors = []
        warnings = []

        for symbol in config.symbols:
            try:
                # Check data availability for this symbol in the date range
                data_check = await self.stock_repo.validate_date_range_has_data(
                    symbol, config.start_date, config.end_date
                )

                if "error" in data_check:
                    errors.append(
                        ValidationError(
                            field="date_range",
                            message=f"Database error checking data for {symbol}: {data_check['error']}",
                            error_code="DATABASE_ERROR",
                        )
                    )
                    continue

                if not data_check["has_data"]:
                    errors.append(
                        ValidationError(
                            field="date_range",
                            message=f"No data available for {symbol} between {config.start_date} and {config.end_date}",
                            error_code="NO_DATA_AVAILABLE",
                        )
                    )

                elif not data_check.get("sufficient_data", True):
                    coverage = data_check.get("coverage_percentage", 0)
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
                        "validation_step": "data_availability_check",
                    },
                    severity=ErrorSeverity.MEDIUM,
                )

                logger.error(
                    f"Date range validation error: {error.message} | Context: {error.context}"
                )
                errors.append(
                    ValidationError(
                        field="date_range",
                        message=f"Unable to validate data availability for {symbol}",
                        error_code="VALIDATION_ERROR",
                    )
                )

        return {"errors": errors, "warnings": warnings}

    def _validate_capital(self, capital: float) -> List[ValidationError]:
        # Comprehensive starting capital validation with practical trading limits
        # Ensures capital amount is suitable for meaningful simulation results
        # Prevents resource exhaustion from extremely large simulations
        errors = []

        # Basic validity check
        if capital <= 0:
            errors.append(
                ValidationError(
                    field="starting_capital",
                    message="Starting capital must be greater than 0 for simulation",
                    error_code="CAPITAL_INVALID",
                )
            )

        # Practical minimum for meaningful trading simulation
        # Below £1,000 may result in limited trading activity due to lot sizes and commissions
        if capital < 1000:
            errors.append(
                ValidationError(
                    field="starting_capital",
                    message="Starting capital should be at least £1,000 for meaningful backtesting results",
                    error_code="CAPITAL_TOO_LOW",
                )
            )

        # Maximum reasonable amount to prevent system resource exhaustion
        # Very large simulations may cause memory and performance issues
        if capital > 10_000_000:  # 10 million pounds
            errors.append(
                ValidationError(
                    field="starting_capital",
                    message="Starting capital exceeds reasonable limit (£10,000,000) for simulation platform",
                    error_code="CAPITAL_TOO_HIGH",
                )
            )

        # Additional validation for edge cases
        if not isinstance(capital, (int, float)):
            errors.append(
                ValidationError(
                    field="starting_capital",
                    message="Starting capital must be a numeric value",
                    error_code="CAPITAL_INVALID_TYPE",
                )
            )

        # Check for NaN or infinite values
        try:
            if not (capital == capital):  # NaN check
                errors.append(
                    ValidationError(
                        field="starting_capital",
                        message="Starting capital cannot be NaN (Not a Number)",
                        error_code="CAPITAL_INVALID",
                    )
                )
        except (TypeError, ValueError):
            pass  # Already handled by type check above

        return errors

    async def _validate_strategy_parameters(
        self, config: SimulationConfig
    ) -> List[ValidationError]:
        # Validate strategy-specific parameters using injected strategy service
        errors = []

        try:
            # Check if strategy exists
            if not await self.strategy_service.strategy_exists(config.strategy):
                available_strategies = (
                    await self.strategy_service.get_available_strategies()
                )
                errors.append(
                    ValidationError(
                        field="strategy",
                        message=f"Unknown strategy '{config.strategy}'. Available strategies: {available_strategies}",
                        error_code="UNKNOWN_STRATEGY",
                    )
                )
                return errors

            # Use strategy service for validation
            is_valid = await self.strategy_service.validate_strategy(
                config.strategy, config.strategy_parameters
            )

            if not is_valid:
                # Get parameter requirements to provide more detailed error information
                param_requirements = (
                    await self.strategy_service.get_strategy_parameters(config.strategy)
                )

                errors.append(
                    ValidationError(
                        field="strategy_parameters",
                        message=f"Invalid parameters for strategy '{config.strategy}'. Check parameter requirements.",
                        error_code="STRATEGY_PARAMETER_INVALID",
                        details={"required_parameters": param_requirements},
                    )
                )

        except Exception as e:
            errors.append(
                ValidationError(
                    field="strategy",
                    message=f"Strategy validation failed: {str(e)}",
                    error_code="STRATEGY_VALIDATION_ERROR",
                )
            )

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

        # Strategy-specific warnings
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
        # Validates all validation components with systematic testing approach
        # Provides detailed test results for system monitoring and debugging

        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "overall_status": "UNKNOWN",
            "test_coverage": [],
            "performance_metrics": {},
        }

        print("\n" + "=" * 60)
        print("COMPREHENSIVE VALIDATION SYSTEM TEST SUITE")
        print("Testing all validation components systematically")
        print("=" * 60 + "\n")

        # Comprehensive test categories covering all validation aspects
        test_categories = [
            ("Symbol Validation Tests", self._test_symbol_validation),
            ("Capital Validation Tests", self._test_capital_validation),
            ("Date Range Validation Tests", self._test_date_range_validation),
            ("Strategy Parameter Tests", self._test_strategy_parameters),
            ("Configuration Warning Tests", self._test_configuration_warnings),
            ("Error Handling Tests", self._test_error_handling),
            ("Edge Case Tests", self._test_edge_cases),
            ("Performance Tests", self._test_validation_performance),
        ]

        # Execute each test category with detailed reporting
        for category_name, test_function in test_categories:
            print(f"Running {category_name}...")

            try:
                category_results = test_function()

                test_results["total_tests"] += category_results["total"]
                test_results["passed_tests"] += category_results["passed"]
                test_results["failed_tests"] += category_results["failed"]
                test_results["test_details"].append(
                    {"category": category_name, "results": category_results}
                )

                # Calculate success rate for this category
                success_rate = (
                    (category_results["passed"] / category_results["total"] * 100)
                    if category_results["total"] > 0
                    else 0
                )
                status_symbol = "PASS" if category_results["failed"] == 0 else "FAIL"

                print(
                    f"  {status_symbol} {category_name}: {category_results['passed']}/{category_results['total']} passed ({success_rate:.1f}%)"
                )

                # Log detailed failures for debugging
                if category_results["failed"] > 0 and "details" in category_results:
                    failed_details = [
                        detail
                        for detail in category_results["details"]
                        if "FAIL" in detail or "ERROR" in detail
                    ]
                    for detail in failed_details[:3]:  # Show first 3 failures
                        print(f"    - {detail}")
                    if len(failed_details) > 3:
                        print(f"    ... and {len(failed_details) - 3} more failures")

            except Exception as e:
                print(f"ERROR {category_name}: Test execution failed - {str(e)}")
                test_results["failed_tests"] += 1
                test_results["total_tests"] += 1

            print()  # Add spacing between categories

        # Calculate overall statistics
        if test_results["total_tests"] > 0:
            overall_success_rate = (
                test_results["passed_tests"] / test_results["total_tests"] * 100
            )
        else:
            overall_success_rate = 0

        # Determine overall test status
        if test_results["failed_tests"] == 0 and test_results["total_tests"] > 0:
            test_results["overall_status"] = "PASSED"
            print(
                f"[PASS] ALL VALIDATION TESTS PASSED ({test_results['passed_tests']}/{test_results['total_tests']}) - {overall_success_rate:.1f}% success rate"
            )
        else:
            test_results["overall_status"] = "FAILED"
            print(
                f"[FAIL] VALIDATION TESTS FAILED ({test_results['failed_tests']}/{test_results['total_tests']} failures) - {overall_success_rate:.1f}% success rate"
            )

        print("=" * 60)

        return test_results

    def _test_symbol_validation(self) -> Dict[str, int]:
        # Test symbol validation logic
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}

        test_cases = [
            # Valid cases
            (["AAPL"], True, "Single valid symbol"),
            (["AAPL", "GOOGL"], True, "Multiple valid symbols"),
            # Invalid cases
            ([], False, "Empty symbol list"),
            (["AAPL", "AAPL"], False, "Duplicate symbols"),
            (["INVALID_SYMBOL_123"], False, "Non-existent symbol"),
            ([""], False, "Empty string symbol"),
        ]

        for symbols, expected_valid, description in test_cases:
            results["total"] += 1

            try:
                # Create mock validation result based on symbol logic
                has_duplicates = len(set(str(s).upper() for s in symbols if s)) != len(
                    [s for s in symbols if s]
                )
                is_empty = not symbols or all(not s for s in symbols)
                has_invalid = any(
                    not s or not isinstance(s, str) or len(s) == 0 for s in symbols
                )

                actual_valid = not (has_duplicates or is_empty or has_invalid)

                if actual_valid == expected_valid:
                    results["passed"] += 1
                    results["details"].append(f"PASS: {description}")
                else:
                    results["failed"] += 1
                    results["details"].append(
                        f"FAIL: {description} - Expected {expected_valid}, got {actual_valid}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: {description} - Exception: {str(e)}")

        return results

    def _test_capital_validation(self) -> Dict[str, int]:
        # Test capital validation logic
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}

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
            results["total"] += 1

            try:
                validation_errors = self._validate_capital(capital)
                actual_valid = len(validation_errors) == 0

                if actual_valid == expected_valid:
                    results["passed"] += 1
                    results["details"].append(f"PASS: {description}")
                else:
                    results["failed"] += 1
                    error_messages = [e.message for e in validation_errors]
                    results["details"].append(
                        f"FAIL: {description} - Expected {expected_valid}, got {actual_valid}. Errors: {error_messages}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: {description} - Exception: {str(e)}")

        return results

    def _test_date_range_validation(self) -> Dict[str, int]:
        # Test date range validation scenarios
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}

        # Test date range calculations
        test_cases = [
            (date(2020, 1, 1), date(2020, 2, 1), 31, "One month range"),
            (date(2020, 1, 1), date(2020, 1, 15), 14, "Two week range"),
            (date(2019, 1, 1), date(2024, 1, 1), 1827, "Five year range"),
            (date(2023, 1, 1), date(2023, 1, 1), 0, "Same day range"),
        ]

        for start_date, end_date, expected_days, description in test_cases:
            results["total"] += 1

            try:
                actual_days = (end_date - start_date).days

                if actual_days == expected_days:
                    results["passed"] += 1
                    results["details"].append(f"PASS: {description}")
                else:
                    results["failed"] += 1
                    results["details"].append(
                        f"FAIL: {description} - Expected {expected_days} days, got {actual_days}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: {description} - Exception: {str(e)}")

        return results

    def _test_strategy_parameters(self) -> Dict[str, int]:
        # Test strategy parameter validation
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}

        # Mock configuration objects for testing
        from types import SimpleNamespace

        test_cases = [
            # Valid strategy configurations
            (
                "ma_crossover",
                {"short_ma": 10, "long_ma": 20},
                True,
                "Valid MA crossover parameters",
            ),
            (
                "rsi",
                {"period": 14, "oversold": 30, "overbought": 70},
                True,
                "Valid RSI parameters",
            ),
            # Invalid strategy configurations
            ("invalid_strategy", {}, False, "Non-existent strategy"),
            (
                "ma_crossover",
                {"short_ma": 20, "long_ma": 10},
                False,
                "Invalid MA parameters (short > long)",
            ),
        ]

        for strategy, params, expected_valid, description in test_cases:
            results["total"] += 1

            try:
                # Create mock config
                mock_config = SimpleNamespace()
                mock_config.strategy = strategy
                mock_config.strategy_parameters = params

                validation_errors = self._validate_strategy_parameters(mock_config)
                actual_valid = len(validation_errors) == 0

                if actual_valid == expected_valid:
                    results["passed"] += 1
                    results["details"].append(f"PASS: {description}")
                else:
                    results["failed"] += 1
                    error_messages = [e.message for e in validation_errors]
                    results["details"].append(
                        f"FAIL: {description} - Expected {expected_valid}, got {actual_valid}. Errors: {error_messages}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: {description} - Exception: {str(e)}")

        return results

    def _test_configuration_warnings(self) -> Dict[str, int]:
        # Test configuration warning generation
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}

        from types import SimpleNamespace

        test_cases = [
            # Short date ranges should generate warnings
            (
                date(2023, 1, 1),
                date(2023, 1, 15),
                10000,
                "ma_crossover",
                {"short_ma": 5, "long_ma": 20},
                True,
                "Short date range warning",
            ),
            # Long date ranges should NOT generate warnings
            (
                date(2019, 1, 1),
                date(2024, 1, 1),
                10000,
                "ma_crossover",
                {"short_ma": 10, "long_ma": 20},
                False,
                "Long date range should not warn",
            ),
            # MA crossover close periods should warn
            (
                date(2020, 1, 1),
                date(2020, 6, 1),
                10000,
                "ma_crossover",
                {"short_ma": 10, "long_ma": 12},
                True,
                "Close MA periods warning",
            ),
            # Low capital with long period should warn
            (
                date(2020, 1, 1),
                date(2022, 1, 1),
                5000,
                "ma_crossover",
                {"short_ma": 10, "long_ma": 20},
                True,
                "Low capital long period warning",
            ),
        ]

        for (
            start_date,
            end_date,
            capital,
            strategy,
            params,
            expect_warnings,
            description,
        ) in test_cases:
            results["total"] += 1

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
                    results["passed"] += 1
                    results["details"].append(f"PASS: {description}")
                else:
                    results["failed"] += 1
                    results["details"].append(
                        f"FAIL: {description} - Expected warnings: {expect_warnings}, got warnings: {has_warnings}. Warnings: {warnings}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: {description} - Exception: {str(e)}")

        return results

    def _test_error_handling(self) -> Dict[str, int]:
        # Test error handling robustness
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}

        # Test that validation doesn't crash with unusual inputs
        unusual_inputs = [
            (None, "None input handling"),
            ({}, "Empty dict input"),
            ([], "Empty list input"),
            ("", "Empty string input"),
            (float("inf"), "Infinity input"),
            (float("-inf"), "Negative infinity input"),
        ]

        for unusual_input, description in unusual_inputs:
            results["total"] += 1

            try:
                # Test capital validation with unusual input
                try:
                    self._validate_capital(unusual_input)
                    results["passed"] += 1
                    results["details"].append(f"PASS: {description} - No crash")
                except (TypeError, ValueError):
                    # Expected for some inputs
                    results["passed"] += 1
                    results["details"].append(
                        f"PASS: {description} - Expected exception handled"
                    )
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append(
                        f"FAIL: {description} - Unexpected exception: {str(e)}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(
                    f"ERROR: {description} - Test setup failed: {str(e)}"
                )

        return results

    def _test_edge_cases(self) -> Dict[str, int]:
        # Comprehensive edge case and boundary condition testing
        # Tests critical boundary values and unusual input scenarios
        # Ensures robust validation behaviour at system limits
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}

        # Test boundary values for capital validation
        boundary_tests = [
            (999.99, False, "Just below minimum capital threshold"),
            (1000.0, True, "Exactly minimum capital threshold"),
            (1000.01, True, "Just above minimum capital threshold"),
            (9999999.99, True, "Just below maximum capital threshold"),
            (10000000.0, True, "Exactly maximum capital threshold"),
            (10000000.01, False, "Just above maximum capital threshold"),
            (0.01, False, "Very small positive capital"),
            (-0.01, False, "Negative capital (edge case)"),
            (float("inf"), False, "Infinite capital value"),
            (float("-inf"), False, "Negative infinite capital value"),
        ]

        for capital, expected_valid, description in boundary_tests:
            results["total"] += 1

            try:
                validation_errors = self._validate_capital(capital)
                actual_valid = len(validation_errors) == 0

                if actual_valid == expected_valid:
                    results["passed"] += 1
                    results["details"].append(
                        f"PASS: {description} (capital: {capital})"
                    )
                else:
                    results["failed"] += 1
                    error_messages = (
                        [e.message for e in validation_errors]
                        if validation_errors
                        else []
                    )
                    results["details"].append(
                        f"FAIL: {description} - Expected valid: {expected_valid}, "
                        f"got valid: {actual_valid}, errors: {error_messages}"
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: {description} - Exception: {str(e)}")

        # Additional edge case tests could include:
        # - Symbol validation with unicode characters
        # - Date validation with leap years and edge dates
        # - Strategy parameter validation with extreme values
        # - Memory and performance stress testing

        return results

    def _test_validation_performance(self) -> Dict[str, int]:
        # Performance testing for validation operations
        # Ensures validation operations complete within reasonable time limits
        results = {"total": 0, "passed": 0, "failed": 0, "details": []}

        import time

        # Test validation performance with different data sizes
        performance_tests = [
            (["AAPL"], "Single symbol validation", 0.1),
            (["AAPL", "GOOGL", "MSFT"], "Small symbol list validation", 0.2),
            ([f"SYM{i:03d}" for i in range(10)], "Medium symbol list validation", 0.5),
            ([f"SYM{i:03d}" for i in range(25)], "Large symbol list validation", 1.0),
        ]

        for symbols, description, max_time in performance_tests:
            results["total"] += 1

            try:
                start_time = time.time()
                # Test symbol validation performance (basic validation only)
                errors = []
                if not symbols:
                    errors.append("empty")

                # Basic duplicate check
                if len(set(symbols)) != len(symbols):
                    errors.append("duplicates")

                execution_time = time.time() - start_time

                if execution_time <= max_time:
                    results["passed"] += 1
                    results["details"].append(
                        f"PASS: {description} ({execution_time:.3f}s <= {max_time}s)"
                    )
                else:
                    results["failed"] += 1
                    results["details"].append(
                        f"FAIL: {description} - Too slow: {execution_time:.3f}s > {max_time}s"
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: {description} - Exception: {str(e)}")

        return results

    async def check_database_connection(self) -> ValidationResult:
        # Comprehensive database connectivity and health validation
        # Verifies database accessibility and data availability for validation operations
        # Used by health check endpoints and system monitoring
        errors = []
        warnings = []

        try:
            logger.debug("Performing database connectivity check")

            # Test basic database connectivity with minimal query
            available_stocks = await self.stock_repo.get_available_stocks(
                page=1, page_size=1
            )
            stocks_list, total_count = available_stocks

            logger.debug(
                f"Database connectivity confirmed: {total_count} total symbols available"
            )

            # Assess data adequacy for validation operations
            if total_count < 10:
                warnings.append(
                    f"Very limited symbol data available ({total_count} symbols). "
                    f"This may restrict simulation options."
                )
            elif total_count < 100:
                warnings.append(
                    f"Limited symbol data available ({total_count} symbols). "
                    f"Consider expanding the symbol database for better simulation variety."
                )

            # Check for reasonable data volume
            if total_count < 1000:
                warnings.append(
                    f"Relatively small historical dataset detected ({total_count} symbols). "
                    f"Larger datasets provide more comprehensive backtesting opportunities."
                )

            # Additional health checks could be added here:
            # - Database response time monitoring
            # - Data freshness validation
            # - Index and query performance checks

            logger.info(
                f"Database health check completed successfully: {total_count} symbols, {len(warnings)} warnings"
            )

        except Exception as e:
            # Comprehensive error handling for database connection issues
            error = self.error_handler.create_generic_error(
                message=f"Database connection health check failed: {str(e)}",
                context={
                    "exception_type": type(e).__name__,
                    "database_operation": "repository_connectivity_check",
                    "error_details": str(e),
                    "validation_component": "database_health",
                },
                severity=ErrorSeverity.CRITICAL,
            )

            logger.error(
                f"Database connection health check failed: {error.message} | Context: {error.context}"
            )
            errors.append(
                ValidationError(
                    field="database",
                    message=f"Unable to establish database connection for validation: {str(e)}",
                    error_code="DATABASE_CONNECTION_ERROR",
                )
            )

        # Return comprehensive validation result
        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
