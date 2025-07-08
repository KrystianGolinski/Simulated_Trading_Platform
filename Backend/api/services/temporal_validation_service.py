# Temporal Validation Service - Advanced Stock Trading Period Validation and Survivorship Bias Prevention
# This module provides comprehensive temporal validation for stock trading periods in the Trading Platform API
# 
# Architecture Overview:
# The TemporalValidationService implements sophisticated validation logic for stock trading periods,
# ensuring that trading simulations account for actual stock availability during specified time periods.
# It provides critical survivorship bias prevention by validating stock existence, IPO dates, and
# delisting dates to ensure realistic and historically accurate trading simulations.
#
# Key Responsibilities:
# 1. Stock trading period validation (IPO to delisting date verification)
# 2. Survivorship bias prevention through temporal eligibility checking
# 3. Batch validation for multiple stocks across specified periods
# 4. Comprehensive error handling and detailed feedback generation
# 5. Business logic integration with repository data access
# 6. Temporal information analysis and warning generation
# 7. Simulation-specific validation with quality assessment
#
# Survivorship Bias Prevention:
# The service addresses survivorship bias by ensuring that:
# - Only stocks that were actually trading during simulation periods are included
# - IPO dates are validated to prevent including stocks that didn't exist yet
# - Delisting dates are checked to avoid including stocks that were no longer trading
# - Dynamic trading periods are supported for realistic historical simulations
#
# Integration with Trading Platform:
# - Provides business logic layer on top of StockDataRepository
# - Integrates with error handling system for comprehensive error management
# - Supports simulation validation with quality metrics and recommendations
# - Enables informed decision-making through detailed temporal analysis
# - Facilitates realistic backtesting with historical accuracy
#
# Validation Quality Assessment:
# The service provides quality metrics for validation results:
# - Rejection rate analysis for validation quality assessment
# - Business warnings for high rejection rates or insufficient valid stocks
# - Period analysis with timeline and duration information
# - IPO proximity warnings for early-stage trading volatility

import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime

from repositories.stock_data_repository import StockDataRepository
from models import ValidationError
from services.error_handler import ErrorHandler, ErrorSeverity

logger = logging.getLogger(__name__)

class TemporalValidationService:
    """
    Advanced Stock Trading Period Validation and Survivorship Bias Prevention Service.
    
    This class provides comprehensive temporal validation for stock trading periods,
    implementing sophisticated logic to ensure trading simulations account for actual
    stock availability during specified time periods. It serves as a critical component
    for preventing survivorship bias in trading simulations and backtesting.
    
    Key Features:
    - Comprehensive stock trading period validation with IPO/delisting verification
    - Survivorship bias prevention through temporal eligibility checking
    - Batch validation capabilities for multiple stocks across periods
    - Business logic integration with detailed error handling and feedback
    - Quality assessment metrics for validation results
    - Dynamic trading period support for realistic historical simulations
    
    Survivorship Bias Prevention:
    The service prevents survivorship bias by ensuring only stocks that were actually
    trading during simulation periods are included, validating IPO dates to prevent
    including non-existent stocks, and checking delisting dates to avoid including
    stocks that were no longer trading.
    
    Architecture Integration:
    The service provides a business logic layer on top of StockDataRepository,
    integrating comprehensive error handling, validation quality assessment, and
    detailed feedback generation for informed decision-making in trading simulations.
    """
    
    def __init__(self, stock_repo: StockDataRepository):
        """
        Initialize the TemporalValidationService with repository and error handling.
        
        Args:
            stock_repo: StockDataRepository instance for data access operations
            
        The service integrates with the stock data repository for temporal information
        access and maintains an error handler for comprehensive error management
        throughout validation operations.
        """
        self.stock_repo = stock_repo
        self.error_handler = ErrorHandler()
    
    async def is_stock_tradeable(self, symbol: str, check_date: date) -> bool:
        """
        Check if a stock was tradeable on a specific date with comprehensive error handling.
        
        This method provides a business logic wrapper around repository functionality
        to determine stock trading availability on a specific date. It accounts for
        IPO dates, delisting dates, and other factors that affect stock tradeability.
        
        Args:
            symbol: Stock symbol to check for trading availability
            check_date: Date to validate stock trading availability
            
        Returns:
            bool: True if stock was tradeable on the specified date, False otherwise
            
        The method provides safe error handling to ensure validation operations
        can continue even if individual stock checks encounter issues, supporting
        robust batch validation operations.
        """
        try:
            return await self.stock_repo.validate_stock_tradeable(symbol, check_date)
        except Exception as e:
            logger.error(f"Error checking if stock {symbol} was tradeable on {check_date}: {e}")
            return False
    
    async def validate_period_eligibility(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Validate stock trading eligibility during a specified period with comprehensive error handling.
        
        This method validates whether stocks were actively trading during the specified
        time period, accounting for IPO dates, delisting dates, and other factors that
        affect stock availability. It provides detailed feedback for validation results
        and comprehensive error handling for system reliability.
        
        Args:
            symbols: List of stock symbols to validate for period eligibility
            start_date: Start date of the period to validate
            end_date: End date of the period to validate
            
        Returns:
            Dict[str, Any]: Comprehensive validation results containing:
                - valid_symbols: List of symbols that were trading during the period
                - rejected_symbols: List of symbols that were not trading during the period
                - errors: List of error messages for rejected symbols
                - total_requested: Total number of symbols requested for validation
                - total_valid: Number of valid symbols
                - total_rejected: Number of rejected symbols
                
        The method provides comprehensive error handling to ensure validation operations
        continue even when encountering system issues, returning appropriate fallback
        responses with detailed error context for debugging and monitoring.
        """
        try:
            return await self.stock_repo.validate_symbols_for_period(symbols, start_date, end_date)
        except Exception as e:
            # Create comprehensive error with detailed context for debugging
            error = self.error_handler.create_generic_error(
                message=f"Temporal validation failed: {str(e)}",
                context={
                    "symbols": symbols,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "exception_type": type(e).__name__
                },
                severity=ErrorSeverity.HIGH
            )
            
            logger.error(f"Temporal validation error: {error.message} | Context: {error.context}")
            
            # Return comprehensive fallback response for system errors
            return {
                "valid_symbols": [],
                "rejected_symbols": symbols,
                "errors": [f"Temporal validation system error: {str(e)}"],
                "total_requested": len(symbols),
                "total_valid": 0,
                "total_rejected": len(symbols)
            }
    
    async def get_temporal_info_for_logging(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, List[str]]:
        """
        Get temporal information for logging and user awareness.

        This method provides informational warnings about dynamic trading periods,
        such as stocks that have a delayed IPO or are delisted during the
        simulation period. For performance reasons, it only checks a sample of
        the provided symbols.

        Args:
            symbols: A list of stock symbols.
            start_date: The start date of the simulation period.
            end_date: The end date of the simulation period.

        Returns:
            A dictionary containing a list of warning messages.
        """
        warnings = []
        
        try:
            # Get basic temporal statistics for user information
            stocks_with_delayed_ipo = []
            stocks_with_early_delisting = []
            
            # Limit to first 10 symbols for performance in large symbol lists
            symbols_to_check = symbols[:10]
            
            for symbol in symbols_to_check:
                try:
                    temporal_info = await self.stock_repo.get_stock_temporal_info(symbol)
                    if temporal_info:
                        ipo_date_str = temporal_info.get('ipo_date')
                        delisting_date_str = temporal_info.get('delisting_date')
                        
                        # Check IPO timing
                        if ipo_date_str:
                            try:
                                ipo_date_obj = datetime.fromisoformat(ipo_date_str).date()
                                
                                # Check if IPO is after simulation start
                                if ipo_date_obj > start_date:
                                    stocks_with_delayed_ipo.append({
                                        'symbol': symbol,
                                        'ipo_date': ipo_date_str
                                    })
                            except (ValueError, TypeError):
                                # Ignore date parsing errors
                                pass
                        
                        # Check delisting timing
                        if delisting_date_str:
                            try:
                                delisting_date_obj = datetime.fromisoformat(delisting_date_str).date()
                                
                                # Check if delisting is before simulation end
                                if delisting_date_obj < end_date:
                                    stocks_with_early_delisting.append({
                                        'symbol': symbol,
                                        'delisting_date': delisting_date_str
                                    })
                            except (ValueError, TypeError):
                                # Ignore date parsing errors
                                pass
                                
                except Exception:
                    # Ignore individual symbol issues for informational warnings
                    continue
            
            # Create informational warnings about dynamic trading
            if stocks_with_delayed_ipo:
                ipo_symbols = [s['symbol'] for s in stocks_with_delayed_ipo[:3]]
                warnings.append(
                    f"Dynamic trading: {len(stocks_with_delayed_ipo)} stocks will start trading after simulation begins "
                    f"(e.g., {', '.join(ipo_symbols)}). These will be traded only when available."
                )
            
            if stocks_with_early_delisting:
                delisted_symbols = [s['symbol'] for s in stocks_with_early_delisting[:3]]
                warnings.append(
                    f"Dynamic trading: {len(stocks_with_early_delisting)} stocks may be delisted during simulation "
                    f"(e.g., {', '.join(delisted_symbols)}). Positions will be automatically closed upon delisting."
                )
            
            # If we sampled stocks and found no issues, provide confirmation
            if not stocks_with_delayed_ipo and not stocks_with_early_delisting and symbols_to_check:
                warnings.append(
                    "Dynamic trading: All sampled stocks appear to be tradeable throughout the simulation period."
                )
                
        except Exception as e:
            # Log error but don't fail the informational process
            logger.warning(f"Could not retrieve temporal information: {e}")
            warnings.append(
                "Dynamic trading enabled: Stocks will be traded only when actually available (IPO to delisting)."
            )
        
        return {"warnings": warnings}
    
    async def validate_temporal_eligibility(self, symbol: str, start_date: date, end_date: date) -> Dict[str, List]:
        """
        Validate the temporal eligibility of a single symbol with detailed error reporting.

        This method provides coherent validation for an individual symbol, checking
        if it was tradeable at the start and end dates of the simulation period.
        It also includes warnings for potential issues, such as starting a
        simulation very close to a stock's IPO date.

        Args:
            symbol: The stock symbol to validate.
            start_date: The start date of the simulation period.
            end_date: The end date of the simulation period.

        Returns:
            A dictionary containing lists of errors and warnings.
        """
        errors = []
        warnings = []
        
        try:
            # Check if stock was tradeable at start date (IPO validation)
            start_tradeable = await self.stock_repo.validate_stock_tradeable(symbol, start_date)
            if not start_tradeable:
                # Get temporal info for detailed error
                temporal_info = await self.stock_repo.get_stock_temporal_info(symbol)
                error_msg = f"Stock {symbol} was not tradeable on {start_date}"
                
                if temporal_info:
                    ipo_date = temporal_info.get('ipo_date')
                    listing_date = temporal_info.get('listing_date')
                    if ipo_date:
                        error_msg += f" - IPO date: {ipo_date}"
                    elif listing_date:
                        error_msg += f" - Listing date: {listing_date}"
                
                errors.append(ValidationError(
                    field="temporal_validation",
                    message=error_msg,
                    error_code="STOCK_NOT_YET_PUBLIC"
                ))
                return {"errors": errors, "warnings": warnings}
            
            # Check if stock was still tradeable at end date (delisting validation)
            end_tradeable = await self.stock_repo.validate_stock_tradeable(symbol, end_date)
            if not end_tradeable:
                # Get temporal info for detailed error
                temporal_info = await self.stock_repo.get_stock_temporal_info(symbol)
                error_msg = f"Stock {symbol} was not tradeable on {end_date}"
                
                if temporal_info:
                    delisting_date = temporal_info.get('delisting_date')
                    if delisting_date:
                        error_msg += f" - Delisted on: {delisting_date}"
                
                errors.append(ValidationError(
                    field="temporal_validation",
                    message=error_msg,
                    error_code="STOCK_DELISTED"
                ))
                return {"errors": errors, "warnings": warnings}
            
            # Check for potential temporal issues that could affect results
            temporal_info = await self.stock_repo.get_stock_temporal_info(symbol)
            if temporal_info:
                ipo_date_str = temporal_info.get('ipo_date')
                if ipo_date_str:
                    try:
                        ipo_date_obj = datetime.fromisoformat(ipo_date_str).date()
                        
                        # Warn if simulation starts very close to IPO
                        days_since_ipo = (start_date - ipo_date_obj).days
                        if 0 <= days_since_ipo <= 90:
                            warnings.append(
                                f"Simulation for {symbol} starts only {days_since_ipo} days after IPO "
                                f"({ipo_date_str}). Early trading data may be volatile."
                            )
                    except (ValueError, TypeError):
                        # Ignore date parsing errors
                        pass
        
        except Exception as e:
            # Handle temporal validation errors gracefully
            error = self.error_handler.create_generic_error(
                message=f"Temporal validation failed for {symbol}: {str(e)}",
                context={
                    "symbol": symbol,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "exception_type": type(e).__name__,
                    "validation_step": "temporal_eligibility_check"
                },
                severity=ErrorSeverity.MEDIUM
            )
            
            logger.error(f"Temporal validation error: {error.message} | Context: {error.context}")
            warnings.append(
                f"Could not verify temporal eligibility for {symbol}. "
                f"Proceeding with caution - results may include survivorship bias."
            )
        
        return {"errors": errors, "warnings": warnings}
    
    async def check_ipo_proximity_warning(self, symbol: str, start_date: date, days_threshold: int = 90) -> Optional[str]:
        """
        Check if a simulation starts too close to a stock's IPO date.

        This method implements the business logic for determining if a warning
        should be issued when a simulation starts within a certain number of days
        following a stock's IPO.

        Args:
            symbol: The stock symbol to check.
            start_date: The start date of the simulation.
            days_threshold: The number of days after the IPO to trigger a warning.

        Returns:
            A warning string if the simulation starts close to the IPO, otherwise None.
        """
        try:
            temporal_info = await self.stock_repo.get_stock_temporal_info(symbol)
            if not temporal_info:
                return None
            
            ipo_date_str = temporal_info.get('ipo_date')
            if not ipo_date_str:
                return None
            
            try:
                ipo_date_obj = datetime.fromisoformat(ipo_date_str).date()
                days_since_ipo = (start_date - ipo_date_obj).days
                
                if 0 <= days_since_ipo <= days_threshold:
                    return (
                        f"Simulation for {symbol} starts only {days_since_ipo} days after IPO "
                        f"({ipo_date_str}). Early trading data may be volatile."
                    )
            except (ValueError, TypeError):
                pass
            
        except Exception as e:
            logger.warning(f"Could not check IPO proximity for {symbol}: {e}")
        
        return None
    
    async def get_eligible_stocks_for_period(self, start_date: date, end_date: date) -> List[str]:
        """
        Get a list of stocks that were eligible for trading during a specific period.

        This method is a direct pass-through to the corresponding repository method.

        Args:
            start_date: The start date of the period.
            end_date: The end date of the period.

        Returns:
            A list of stock symbols that were eligible for trading.
        """
        try:
            return await self.stock_repo.get_eligible_stocks_for_period(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting eligible stocks for period {start_date} to {end_date}: {e}")
            return []
    
    async def batch_temporal_validation(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Perform batch temporal validation with adequate reporting.

        This method combines repository operations with business logic to provide
        a comprehensive report on the temporal validity of a list of symbols
        for a given period. It includes metrics like rejection rate and
        validation quality.

        Args:
            symbols: A list of stock symbols to validate.
            start_date: The start date of the validation period.
            end_date: The end date of the validation period.

        Returns:
            A dictionary containing the validation results and business logic analysis.
        """
        try:
            # Get basic validation from repository
            validation_result = await self.stock_repo.validate_symbols_for_period(symbols, start_date, end_date)
            
            # Add business logic analysis
            rejection_rate = validation_result["total_rejected"] / max(validation_result["total_requested"], 1)
            
            # Determine validation quality
            validation_quality = "excellent"
            if rejection_rate > 0.1:
                validation_quality = "good"
            if rejection_rate > 0.3:
                validation_quality = "fair"
            if rejection_rate > 0.5:
                validation_quality = "poor"
            
            # Add business context
            business_warnings = []
            if rejection_rate > 0.5:
                business_warnings.append(
                    f"High symbol rejection rate ({rejection_rate:.1%}) may indicate issues with "
                    f"the selected time period or symbol list."
                )
            
            if validation_result["total_valid"] < 5:
                business_warnings.append(
                    "Very few valid symbols remaining. Consider adjusting the time period or symbol selection."
                )
            
            return {
                **validation_result,
                "rejection_rate": rejection_rate,
                "validation_quality": validation_quality,
                "business_warnings": business_warnings,
                "period_analysis": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "period_length_days": (end_date - start_date).days
                }
            }
            
        except Exception as e:
            error = self.error_handler.create_generic_error(
                message=f"Batch temporal validation failed: {str(e)}",
                context={
                    "symbols_count": len(symbols),
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "exception_type": type(e).__name__
                },
                severity=ErrorSeverity.HIGH
            )
            
            logger.error(f"Batch temporal validation error: {error.message} | Context: {error.context}")
            
            return {
                "valid_symbols": [],
                "rejected_symbols": symbols,
                "errors": [f"Batch temporal validation system error: {str(e)}"],
                "total_requested": len(symbols),
                "total_valid": 0,
                "total_rejected": len(symbols),
                "rejection_rate": 1.0,
                "validation_quality": "failed",
                "business_warnings": ["Temporal validation system encountered an error"],
                "period_analysis": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "period_length_days": (end_date - start_date).days
                }
            }
    
    async def validate_simulation_temporal(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Perform simulation-specific temporal validation.

        This method determines if a simulation can proceed based on the temporal
        validation results. It checks if there are any valid symbols for the
        specified period and provides a clear indication of whether the
        simulation is valid.

        Args:
            symbols: A list of stock symbols for the simulation.
            start_date: The start date of the simulation.
            end_date: The end date of the simulation.

        Returns:
            A dictionary containing the validation results and a flag indicating
            if the simulation is valid.
        """
        try:
            # Get pure data validation from repository
            validation_result = await self.stock_repo.validate_symbols_for_period(symbols, start_date, end_date)
            
            # Business logic: determine if simulation is valid
            simulation_valid = validation_result["total_valid"] > 0
            simulation_error = None
            
            if not simulation_valid:
                simulation_error = "No valid symbols for the specified period"
            
            # Calculate rejection rate for business analysis
            rejection_rate = validation_result["total_rejected"] / max(validation_result["total_requested"], 1)
            
            # Log high rejection rates for monitoring
            if rejection_rate > 0.5:
                logger.warning(f"High symbol rejection rate: {rejection_rate:.1%} for period {start_date} to {end_date}")
            
            # Combine repository data with business logic results
            return {
                **validation_result,
                "simulation_valid": simulation_valid,
                "simulation_error": simulation_error,
                "rejection_rate": rejection_rate,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat()
            }
            
        except Exception as e:
            error = self.error_handler.create_generic_error(
                message=f"Simulation temporal validation failed: {str(e)}",
                context={
                    "symbols_count": len(symbols),
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "exception_type": type(e).__name__
                },
                severity=ErrorSeverity.HIGH
            )
            
            logger.error(f"Simulation temporal validation error: {error.message} | Context: {error.context}")
            
            return {
                "valid_symbols": [],
                "rejected_symbols": symbols,
                "errors": [f"Simulation temporal validation system error: {str(e)}"],
                "total_requested": len(symbols),
                "total_valid": 0,
                "total_rejected": len(symbols),
                "simulation_valid": False,
                "simulation_error": f"Temporal validation system error: {str(e)}",
                "rejection_rate": 1.0,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat()
            }