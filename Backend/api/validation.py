"""
Comprehensive validation system for Phase 3 implementation
Handles input validation, error messaging, and data availability checks
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from database import DatabaseManager
from models import SimulationConfig, ValidationError, ValidationResult, StrategyType

logger = logging.getLogger(__name__)

class SimulationValidator:
    """Comprehensive validator for simulation configurations"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def validate_simulation_config(self, config: SimulationConfig) -> ValidationResult:
        """
        Comprehensive validation of simulation configuration
        Returns ValidationResult with detailed error information
        """
        errors = []
        warnings = []
        
        try:
            # 1. Validate stock symbols
            symbol_validation = await self._validate_symbols(config.symbols)
            errors.extend(symbol_validation)
            
            # 2. Validate date ranges and data availability
            if not errors:  # Only check data if symbols are valid
                date_validation = await self._validate_date_ranges(config)
                errors.extend(date_validation['errors'])
                warnings.extend(date_validation['warnings'])
            
            # 3. Validate capital amount
            capital_validation = self._validate_capital(config.starting_capital)
            errors.extend(capital_validation)
            
            # 4. Validate strategy parameters
            strategy_validation = self._validate_strategy_parameters(config)
            errors.extend(strategy_validation)
            
            # 5. Check for potential issues (warnings)
            config_warnings = self._check_configuration_warnings(config)
            warnings.extend(config_warnings)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            errors.append(ValidationError(
                field="general",
                message=f"Validation system error: {str(e)}",
                error_code="VALIDATION_SYSTEM_ERROR"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_symbols(self, symbols: List[str]) -> List[ValidationError]:
        """Validate stock symbols exist in database"""
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
                    # Get suggestion for similar symbols
                    suggestion = await self._get_symbol_suggestion(symbol_upper)
                    message = f"Stock symbol '{symbol_upper}' not found in database"
                    if suggestion:
                        message += f". Did you mean '{suggestion}'?"
                    
                    errors.append(ValidationError(
                        field="symbols",
                        message=message,
                        error_code="SYMBOL_NOT_FOUND"
                    ))
                    
        except Exception as e:
            logger.error(f"Error validating symbols: {e}")
            errors.append(ValidationError(
                field="symbols",
                message="Unable to validate symbols due to database error",
                error_code="DATABASE_ERROR"
            ))
        
        return errors
    
    async def _validate_date_ranges(self, config: SimulationConfig) -> Dict[str, List]:
        """Validate date ranges have sufficient data"""
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
                    # Get available date range for suggestion
                    available_range = await self.db.get_symbol_date_range(symbol)
                    message = f"No data available for {symbol} between {config.start_date} and {config.end_date}"
                    
                    if available_range:
                        message += f". Available data: {available_range['earliest_date']} to {available_range['latest_date']}"
                    
                    errors.append(ValidationError(
                        field="date_range",
                        message=message,
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
                logger.error(f"Error validating date range for {symbol}: {e}")
                errors.append(ValidationError(
                    field="date_range",
                    message=f"Unable to validate data availability for {symbol}",
                    error_code="VALIDATION_ERROR"
                ))
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_capital(self, capital: float) -> List[ValidationError]:
        """Validate starting capital amount"""
        errors = []
        
        # Basic range validation (already handled by Pydantic, but double-check)
        if capital <= 0:
            errors.append(ValidationError(
                field="starting_capital",
                message="Starting capital must be greater than 0",
                error_code="CAPITAL_INVALID"
            ))
        
        # Practical minimum for meaningful trading
        if capital < 1000:
            errors.append(ValidationError(
                field="starting_capital",
                message="Starting capital should be at least $1,000 for meaningful backtesting",
                error_code="CAPITAL_TOO_LOW"
            ))
        
        # Maximum reasonable amount
        if capital > 10_000_000:  # 10 million
            errors.append(ValidationError(
                field="starting_capital",
                message="Starting capital exceeds reasonable limit ($10,000,000)",
                error_code="CAPITAL_TOO_HIGH"
            ))
        
        return errors
    
    def _validate_strategy_parameters(self, config: SimulationConfig) -> List[ValidationError]:
        """Validate strategy-specific parameters"""
        errors = []
        
        if config.strategy == StrategyType.MA_CROSSOVER:
            # Validate MA periods
            if config.short_ma and config.short_ma < 5:
                errors.append(ValidationError(
                    field="short_ma",
                    message="Short moving average period should be at least 5",
                    error_code="SHORT_MA_TOO_LOW"
                ))
            
            if config.long_ma and config.long_ma > 200:
                errors.append(ValidationError(
                    field="long_ma",
                    message="Long moving average period should not exceed 200",
                    error_code="LONG_MA_TOO_HIGH"
                ))
        
        elif config.strategy == StrategyType.RSI:
            # Validate RSI parameters
            if config.rsi_period and config.rsi_period < 5:
                errors.append(ValidationError(
                    field="rsi_period",
                    message="RSI period should be at least 5",
                    error_code="RSI_PERIOD_TOO_LOW"
                ))
            
            if config.rsi_oversold and config.rsi_oversold < 10:
                errors.append(ValidationError(
                    field="rsi_oversold",
                    message="RSI oversold threshold should be at least 10",
                    error_code="RSI_OVERSOLD_TOO_LOW"
                ))
            
            if config.rsi_overbought and config.rsi_overbought > 90:
                errors.append(ValidationError(
                    field="rsi_overbought",
                    message="RSI overbought threshold should not exceed 90",
                    error_code="RSI_OVERBOUGHT_TOO_HIGH"
                ))
        
        return errors
    
    def _check_configuration_warnings(self, config: SimulationConfig) -> List[str]:
        """Check for potential configuration issues that don't prevent execution"""
        warnings = []
        
        # Check date range length
        date_range_days = (config.end_date - config.start_date).days
        
        if date_range_days < 30:
            warnings.append(
                f"Short date range ({date_range_days} days). Consider using at least 30 days for more reliable results."
            )
        
        if date_range_days > 1825:  # 5 years
            warnings.append(
                f"Very long date range ({date_range_days} days). Consider shorter periods for faster execution."
            )
        
        # Check if end date is recent (might affect strategy performance)
        days_since_end = (date.today() - config.end_date).days
        if days_since_end > 365:
            warnings.append(
                f"End date is {days_since_end} days ago. Consider using more recent data for relevant results."
            )
        
        # Strategy-specific warnings
        if config.strategy == StrategyType.MA_CROSSOVER:
            if config.short_ma and config.long_ma:
                ratio = config.long_ma / config.short_ma
                if ratio < 1.5:
                    warnings.append(
                        f"MA periods are close ({config.short_ma}, {config.long_ma}). "
                        f"Consider using more separated periods for clearer signals."
                    )
        
        # Capital vs strategy warnings
        if config.starting_capital < 10000 and date_range_days > 365:
            warnings.append(
                "Low starting capital with long time period may result in limited trading activity."
            )
        
        return warnings
    
    async def _get_symbol_suggestion(self, invalid_symbol: str) -> Optional[str]:
        """Get suggestion for similar symbol"""
        try:
            # Get all available symbols
            all_symbols = await self.db.get_available_stocks()
            
            # Simple similarity check - look for symbols that start with the same letters
            prefix = invalid_symbol[:3] if len(invalid_symbol) >= 3 else invalid_symbol[:2]
            
            suggestions = [s for s in all_symbols if s.startswith(prefix)]
            return suggestions[0] if suggestions else None
            
        except Exception as e:
            logger.error(f"Error getting symbol suggestion: {e}")
            return None
    
    async def check_database_connection(self) -> ValidationResult:
        """Check if database is accessible and contains required data"""
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
            logger.error(f"Database connection check failed: {e}")
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