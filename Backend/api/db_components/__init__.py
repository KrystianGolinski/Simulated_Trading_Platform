# Database Components Package - Low-Level Database Infrastructure
# This package provides modular database components for the Trading Platform API
# Following the single responsibility principle with distinct components for different database operations
#
# Package Contents:
# - CacheManager: Multi-tiered TTL-based caching system for database results
# - DatabaseConnectionManager: Connection pool management and health monitoring
# - QueryExecutor: Raw query execution with retry logic and transaction support
#
# Architecture Features:
# - Modular separation of concerns (caching, connection management, query execution)
# - Retry logic with exponential backoff for concurrent access issues
# - Connection pooling with configurable pool sizes and timeouts
# - Multi-tiered caching with different TTL strategies based on data volatility
# - Environment-aware configuration (test vs production database credentials)
# - Comprehensive health monitoring and statistics tracking
# - Transaction support for atomic operations
#
# Integration Points:
# - Used by repositories/ layer for data access operations
# - Integrated with services/ layer for business logic operations
# - Supports both synchronous and asynchronous query patterns
# - Provides caching layer for frequently accessed stock data and validation results
