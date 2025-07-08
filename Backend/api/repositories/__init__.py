# Repositories Package - Data Access Layer for Domain Entities
# This package provides the data access layer for the Trading Platform API
# Following the Repository Pattern to encapsulate data access logic and provide clean interfaces
#
# Package Contents:
# - StockDataRepository: Comprehensive stock data access with caching and validation
#
# Architecture Features:
# - Repository pattern for clean separation between business logic and data access
# - Integration with db_components for query execution and caching
# - Domain-specific data access methods with optimized queries
# - Comprehensive caching strategy to reduce database load
# - Batch operations for efficient multi-symbol data retrieval
# - Temporal validation for stock trading eligibility
# - Data validation and symbol existence checking
# - Pagination support for large result sets
# - Error handling with fallback mechanisms
#
# Integration Points:
# - Used by services/ layer for business logic implementation
# - Integrates with db_components/ for low-level database operations
# - Provides caching layer through CacheManager integration
# - Supports both single and batch data operations
# - Enables temporal validation for stock trading periods

from .stock_data_repository import StockDataRepository

__all__ = ['StockDataRepository']