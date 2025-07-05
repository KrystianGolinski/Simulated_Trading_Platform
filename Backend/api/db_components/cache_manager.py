from typing import Optional, Any, Dict
import logging
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class CacheManager:
    # Handles database result caching only
    # Single responsibility: Cache management
    
    def __init__(self):
        # Initialize TTL caches with different TTL times based on data volatility
        self._stock_data_cache = TTLCache(maxsize=1024, ttl=300)  # 5-minute TTL for frequently accessed, volatile stock data.
        self._stocks_list_cache = TTLCache(maxsize=1, ttl=300)    # 5-minute TTL for the complete list of available stocks.
        self._validation_cache = TTLCache(maxsize=256, ttl=600)   # 10-minute TTL for validation results, which are stable for short periods.
        self._date_range_cache = TTLCache(maxsize=512, ttl=600)   # 10-minute TTL for date range lookups.
        self._temporal_cache = TTLCache(maxsize=128, ttl=1800)    # 30-minute TTL for temporal data (like IPO dates), which rarely changes.
    
    def get_stock_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        # Get cached stock data
        result = self._stock_data_cache.get(cache_key)
        if result:
            logger.debug(f"Cache hit for stock data: {cache_key}")
        return result
    
    def set_stock_data(self, cache_key: str, data: Dict[str, Any]) -> None:
        # Cache stock data
        self._stock_data_cache[cache_key] = data
        logger.debug(f"Cached stock data: {cache_key}")
    
    def get_stocks_list(self, cache_key: str) -> Optional[Dict[str, Any]]:
        # Get cached stocks list
        result = self._stocks_list_cache.get(cache_key)
        if result:
            logger.debug(f"Cache hit for stocks list: {cache_key}")
        return result
    
    def set_stocks_list(self, cache_key: str, data: Dict[str, Any]) -> None:
        # Cache stocks list
        self._stocks_list_cache[cache_key] = data
        logger.debug(f"Cached stocks list: {cache_key}")
    
    def get_validation_result(self, cache_key: str) -> Optional[Any]:
        # Get cached validation result
        result = self._validation_cache.get(cache_key)
        if result is not None:
            logger.debug(f"Cache hit for validation: {cache_key}")
        return result
    
    def set_validation_result(self, cache_key: str, result: Any) -> None:
        # Cache validation result
        self._validation_cache[cache_key] = result
        logger.debug(f"Cached validation result: {cache_key}")
    
    def get_date_range(self, cache_key: str) -> Optional[Dict[str, Any]]:
        # Get cached date range
        result = self._date_range_cache.get(cache_key)
        if result:
            logger.debug(f"Cache hit for date range: {cache_key}")
        return result
    
    def set_date_range(self, cache_key: str, data: Dict[str, Any]) -> None:
        # Cache date range
        self._date_range_cache[cache_key] = data
        logger.debug(f"Cached date range: {cache_key}")
    
    def get_temporal_validation(self, cache_key: str) -> Optional[Any]:
        # Get cached temporal validation result
        result = self._temporal_cache.get(cache_key)
        if result is not None:
            logger.debug(f"Cache hit for temporal validation: {cache_key}")
        return result
    
    def set_temporal_validation(self, cache_key: str, result: Any) -> None:
        # Cache temporal validation result
        self._temporal_cache[cache_key] = result
        logger.debug(f"Cached temporal validation: {cache_key}")
    
    def clear_all_caches(self) -> None:
        # Clear all cached data
        self._stock_data_cache.clear()
        self._stocks_list_cache.clear()
        self._validation_cache.clear()
        self._date_range_cache.clear()
        self._temporal_cache.clear()
        logger.info("All database caches cleared")
    
    def clear_stock_data_cache(self) -> None:
        # Clear only stock data cache
        self._stock_data_cache.clear()
        logger.info("Stock data cache cleared")
    
    def clear_validation_cache(self) -> None:
        # Clear validation and temporal caches
        self._validation_cache.clear()
        self._temporal_cache.clear()
        logger.info("Validation caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        # Get cache statistics
        return {
            "stock_data_cache": {
                "size": len(self._stock_data_cache),
                "maxsize": self._stock_data_cache.maxsize,
                "ttl": self._stock_data_cache.ttl
            },
            "stocks_list_cache": {
                "size": len(self._stocks_list_cache),
                "maxsize": self._stocks_list_cache.maxsize,
                "ttl": self._stocks_list_cache.ttl
            },
            "validation_cache": {
                "size": len(self._validation_cache),
                "maxsize": self._validation_cache.maxsize,
                "ttl": self._validation_cache.ttl
            },
            "date_range_cache": {
                "size": len(self._date_range_cache),
                "maxsize": self._date_range_cache.maxsize,
                "ttl": self._date_range_cache.ttl
            },
            "temporal_cache": {
                "size": len(self._temporal_cache),
                "maxsize": self._temporal_cache.maxsize,
                "ttl": self._temporal_cache.ttl
            }
        }