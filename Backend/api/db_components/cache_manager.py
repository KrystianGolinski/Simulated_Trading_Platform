# Cache Manager - Multi-Tiered TTL-Based Database Result Caching System
# This module provides comprehensive caching capabilities for database results in the Trading Platform
# Key responsibilities:
# - Multi-tiered caching with different TTL strategies based on data volatility
# - Stock data caching with configurable TTL for frequently accessed OHLCV data
# - Validation result caching to reduce redundant validation operations
# - Temporal data caching for IPO/delisting dates and trading session information
# - Date range caching for stock availability lookups
# - Cache statistics and monitoring for performance optimization
# - Selective cache invalidation for specific data types
#
# Architecture Features:
# - Separate cache pools for different data types with optimized TTL values
# - TTL-based automatic expiration to ensure data freshness
# - Comprehensive cache statistics for monitoring and tuning
# - Selective cache clearing operations for targeted invalidation
# - Debug logging for cache hit/miss tracking and performance analysis
# - Memory-efficient caching using cachetools library
#
# Cache Strategy:
# - Stock data: 5-minute TTL (frequently accessed, moderately volatile)
# - Stocks list: 5-minute TTL (comprehensive stock symbol list)
# - Validation results: 10-minute TTL (stable for short periods)
# - Date ranges: 10-minute TTL (stock availability periods)
# - Temporal data: 30-minute TTL (IPO/delisting dates, rarely changes)

import logging
from typing import Any, Dict, Optional

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class CacheManager:
    # Multi-tiered database result caching system with TTL-based expiration
    # Provides optimized caching strategies for different data types based on volatility
    # Handles cache statistics, selective invalidation, and comprehensive monitoring

    def __init__(self):
        # Initialize TTL caches with different TTL times based on data volatility
        self._stock_data_cache = TTLCache(
            maxsize=1024, ttl=300
        )  # 5-minute TTL for frequently accessed, volatile stock data.
        self._stocks_list_cache = TTLCache(
            maxsize=1, ttl=300
        )  # 5-minute TTL for the complete list of available stocks.
        self._validation_cache = TTLCache(
            maxsize=256, ttl=600
        )  # 10-minute TTL for validation results, which are stable for short periods.
        self._date_range_cache = TTLCache(
            maxsize=512, ttl=600
        )  # 10-minute TTL for date range lookups.
        self._temporal_cache = TTLCache(
            maxsize=128, ttl=1800
        )  # 30-minute TTL for temporal data (like IPO dates), which rarely changes.

    def get_stock_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        # Retrieve cached stock data (OHLCV data, price history) using cache key
        # Returns None if not cached or expired, enabling fallback to database query
        # Logs cache hits for performance monitoring and optimization analysis
        result = self._stock_data_cache.get(cache_key)
        if result:
            logger.debug(f"Cache hit for stock data: {cache_key}")
        return result

    def set_stock_data(self, cache_key: str, data: Dict[str, Any]) -> None:
        # Cache stock data with 5-minute TTL for frequently accessed OHLCV data
        # Balances data freshness with performance optimization
        # Logs cache operations for monitoring and debugging
        self._stock_data_cache[cache_key] = data
        logger.debug(f"Cached stock data: {cache_key}")

    def get_stocks_list(self, cache_key: str) -> Optional[Dict[str, Any]]:
        # Retrieve cached complete stock symbol list for pagination and filtering
        # Reduces database load for frequently accessed stock listings
        # Returns None if cache miss, enabling database fallback
        result = self._stocks_list_cache.get(cache_key)
        if result:
            logger.debug(f"Cache hit for stocks list: {cache_key}")
        return result

    def set_stocks_list(self, cache_key: str, data: Dict[str, Any]) -> None:
        # Cache complete stock symbol list with 5-minute TTL
        # Optimizes performance for stock listing and symbol validation operations
        # Single cache entry for comprehensive stock list data
        self._stocks_list_cache[cache_key] = data
        logger.debug(f"Cached stocks list: {cache_key}")

    def get_validation_result(self, cache_key: str) -> Optional[Any]:
        # Retrieve cached validation result for symbol validation and configuration checks
        # Reduces redundant validation operations for frequently validated configurations
        # Uses 'is not None' check to handle cached False/empty results correctly
        result = self._validation_cache.get(cache_key)
        if result is not None:
            logger.debug(f"Cache hit for validation: {cache_key}")
        return result

    def set_validation_result(self, cache_key: str, result: Any) -> None:
        # Cache validation result with 10-minute TTL for stable validation outcomes
        # Handles various validation result types including boolean, ValidationResult objects
        # Optimizes performance for repeated validation of same configurations
        self._validation_cache[cache_key] = result
        logger.debug(f"Cached validation result: {cache_key}")

    def get_date_range(self, cache_key: str) -> Optional[Dict[str, Any]]:
        # Retrieve cached date range data for stock availability periods
        # Caches min/max dates for stocks to optimize temporal validation queries
        # Returns None if cache miss, enabling database fallback for date range lookup
        result = self._date_range_cache.get(cache_key)
        if result:
            logger.debug(f"Cache hit for date range: {cache_key}")
        return result

    def set_date_range(self, cache_key: str, data: Dict[str, Any]) -> None:
        # Cache date range data with 10-minute TTL for stock availability periods
        # Optimizes temporal validation by caching earliest/latest trading dates
        # Reduces database queries for frequently accessed date range information
        self._date_range_cache[cache_key] = data
        logger.debug(f"Cached date range: {cache_key}")

    def get_temporal_validation(self, cache_key: str) -> Optional[Any]:
        # Retrieve cached temporal validation result for IPO/delisting date checks
        # Caches trading eligibility results for specific dates and symbols
        # Uses 'is not None' check to handle cached False results correctly
        result = self._temporal_cache.get(cache_key)
        if result is not None:
            logger.debug(f"Cache hit for temporal validation: {cache_key}")
        return result

    def set_temporal_validation(self, cache_key: str, result: Any) -> None:
        # Cache temporal validation result with 30-minute TTL for stable historical data
        # Handles IPO dates, delisting dates, and trading session eligibility
        # Longer TTL appropriate for historical data that rarely changes
        self._temporal_cache[cache_key] = result
        logger.debug(f"Cached temporal validation: {cache_key}")

    def clear_all_caches(self) -> None:
        # Clear all cached data across all cache pools for complete cache invalidation
        # Used for system maintenance, testing, or when data integrity requires refresh
        # Comprehensive cache clearing ensures no stale data remains
        self._stock_data_cache.clear()
        self._stocks_list_cache.clear()
        self._validation_cache.clear()
        self._date_range_cache.clear()
        self._temporal_cache.clear()
        logger.info("All database caches cleared")

    def clear_stock_data_cache(self) -> None:
        # Clear only stock data cache while preserving other cache types
        # Selective invalidation for stock price data updates or market data refresh
        # Maintains validation and temporal cache data for continued performance
        self._stock_data_cache.clear()
        logger.info("Stock data cache cleared")

    def clear_validation_cache(self) -> None:
        # Clear validation and temporal caches while preserving stock data cache
        # Selective invalidation for validation logic updates or temporal data changes
        # Maintains stock price cache for continued performance optimization
        self._validation_cache.clear()
        self._temporal_cache.clear()
        logger.info("Validation caches cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        # Get comprehensive cache statistics for monitoring and performance analysis
        # Provides current size, maximum capacity, and TTL settings for each cache pool
        # Used by performance monitoring endpoints and cache optimization analysis
        return {
            "stock_data_cache": {
                "size": len(self._stock_data_cache),
                "maxsize": self._stock_data_cache.maxsize,
                "ttl": self._stock_data_cache.ttl,
            },
            "stocks_list_cache": {
                "size": len(self._stocks_list_cache),
                "maxsize": self._stocks_list_cache.maxsize,
                "ttl": self._stocks_list_cache.ttl,
            },
            "validation_cache": {
                "size": len(self._validation_cache),
                "maxsize": self._validation_cache.maxsize,
                "ttl": self._validation_cache.ttl,
            },
            "date_range_cache": {
                "size": len(self._date_range_cache),
                "maxsize": self._date_range_cache.maxsize,
                "ttl": self._date_range_cache.ttl,
            },
            "temporal_cache": {
                "size": len(self._temporal_cache),
                "maxsize": self._temporal_cache.maxsize,
                "ttl": self._temporal_cache.ttl,
            },
        }
