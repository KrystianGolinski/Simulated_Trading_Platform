# Temporal Validation Service
# Handles IPO/delisting validation, trading period checks, and survivorship bias mitigation
# Provides trading logic layer on top of StockDataRepository for temporal operations

import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime

from repositories.stock_data_repository import StockDataRepository
from models import ValidationError
from services.error_handler import ErrorHandler, ErrorSeverity

logger = logging.getLogger(__name__)

class TemporalValidationService:
    # Service for temporal validation logic and survivorship bias mitigation
    # Handles IPO/delisting validation, trading period checks, and batch temporal validation
    
    def __init__(self, stock_repo: StockDataRepository):
        self.stock_repo = stock_repo
        self.error_handler = ErrorHandler()
    
    async def is_stock_tradeable(self, symbol: str, check_date: date) -> bool:
        # Check if a stock was tradeable on a specific date
        # Wrapper around repository method
        try:
            return await self.stock_repo.validate_stock_tradeable(symbol, check_date)
        except Exception as e:
            logger.error(f"Error checking if stock {symbol} was tradeable on {check_date}: {e}")
            return False
    
    async def validate_period_eligibility(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        # Validate if stocks were trading during specified period
        # Accounts for IPO dates, delisting dates, and provides detailed feedback
        try:
            return await self.stock_repo.validate_symbols_for_period(symbols, start_date, end_date)
        except Exception as e:
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
            return {
                "valid_symbols": [],
                "rejected_symbols": symbols,
                "errors": [f"Temporal validation system error: {str(e)}"],
                "total_requested": len(symbols),
                "total_valid": 0,
                "total_rejected": len(symbols)
            }
    
    async def get_temporal_info_for_logging(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, List[str]]:
        # Get temporal information for logging and user awareness
        # Provides informational warnings about dynamic trading periods
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
        # Validate symbol temporal eligibility with detailed error reporting
        # Provides coherent validation for individual symbols
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
        # Check if simulation starts too close to IPO and return warning if so
        # Business logic for determining IPO proximity warnings
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
        # Get stocks that were eligible for trading during a specific period
        # Uses the correct repository method for this
        try:
            return await self.stock_repo.get_eligible_stocks_for_period(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting eligible stocks for period {start_date} to {end_date}: {e}")
            return []
    
    async def batch_temporal_validation(self, symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
        # Perform batch temporal validation with adequate reporting
        # Combines repository operations with business logic for reporting
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
        # Simulation-specific temporal validation with business logic
        # Determines if a simulation can proceed based on temporal validation results
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