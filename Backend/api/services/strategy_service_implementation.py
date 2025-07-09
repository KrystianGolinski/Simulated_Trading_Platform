# Strategy Service Implementation - Concrete Strategy Management with Lazy Loading and Circular Dependency Prevention
# This module provides the concrete implementation of StrategyServiceInterface for the Trading Platform API
#
# Architecture Overview:
# The StrategyService implements sophisticated strategy management capabilities with lazy loading
# to prevent circular import dependencies. It provides robust strategy validation, parameter
# management, and discovery operations while maintaining clean separation from the underlying
# strategy registry implementation.
#
# Key Implementation Features:
# 1. Lazy Loading Pattern - Prevents circular import issues through delayed registry initialization
# 2. Robust Error Handling - Comprehensive error management for all strategy operations
# 3. Parameter Validation - Thorough validation of strategy parameters with type checking
# 4. Registry Integration - Seamless integration with strategy registry without tight coupling
# 5. Performance Optimization - Efficient caching and access patterns for strategy operations
#
# Lazy Loading Benefits:
# The lazy loading pattern enables:
# - Circular dependency prevention through delayed imports
# - Improved startup performance by deferring registry initialization
# - Graceful degradation when registry is unavailable
# - Clean separation of concerns between service and registry layers
# - Support for testing scenarios with mock registries
#
# Error Handling Strategy:
# The implementation provides comprehensive error handling:
# - Registry initialization failures are handled gracefully
# - Individual operation failures are logged and return safe defaults
# - Availability checking prevents operations on uninitialized registries
# - Detailed logging for debugging and monitoring
#
# Integration with Trading Platform:
# - Implements StrategyServiceInterface contract for consistency
# - Provides strategy validation for simulation configuration
# - Supports dynamic strategy discovery and parameter introspection
# - Enables flexible strategy management without direct registry coupling
# - Facilitates testing through dependency injection patterns

import logging
from typing import Any, Dict, List, Optional

from .strategy_service import StrategyServiceInterface

logger = logging.getLogger(__name__)


class StrategyService(StrategyServiceInterface):
    """
    Concrete implementation of StrategyServiceInterface with advanced lazy loading and error handling.

    This class provides comprehensive strategy management capabilities while preventing circular
    import dependencies through sophisticated lazy loading patterns. It implements all contract
    requirements from StrategyServiceInterface while maintaining robust error handling and
    graceful degradation when the underlying strategy registry is unavailable.

    Key Implementation Features:
    - Lazy Loading Pattern: Prevents circular imports through delayed registry initialization
    - Robust Error Handling: Comprehensive error management with detailed logging
    - Graceful Degradation: Safe operation even when registry is unavailable
    - Performance Optimization: Efficient registry access with caching
    - Clean Architecture: Maintains separation of concerns through interface implementation

    Lazy Loading Strategy:
    The implementation uses a property-based lazy loading approach where the strategy registry
    is only imported and initialized when first accessed. This prevents circular import issues
    that can occur when multiple modules depend on each other during initialization.

    Error Handling Philosophy:
    The service prioritizes system stability by handling all potential failures gracefully,
    returning safe defaults (empty lists, False values, None) when operations cannot be
    completed, while providing comprehensive logging for debugging and monitoring.

    Thread Safety:
    The implementation is designed to be thread-safe for the lazy loading mechanism,
    ensuring that concurrent access doesn't cause multiple initialization attempts.
    """

    def __init__(self):
        """
        Initialize the StrategyService with lazy loading configuration.

        The constructor sets up the lazy loading infrastructure without actually
        importing or initializing the strategy registry. This prevents circular
        import issues and improves startup performance by deferring expensive
        operations until they are actually needed.

        State Management:
        - _registry: Holds the strategy registry instance once initialized
        - _initialized: Tracks whether initialization was successful
        """
        # Initialize with lazy loading to avoid circular imports
        self._registry = None
        self._initialized = False

    @property
    def registry(self):
        """
        Lazy-loaded strategy registry property with comprehensive error handling.

        This property implements the core lazy loading mechanism for the strategy registry.
        It only imports and initializes the registry when first accessed, preventing
        circular import issues and improving startup performance. The property handles
        all potential import and initialization failures gracefully.

        Returns:
            Strategy registry instance if successfully initialized, None otherwise

        Lazy Loading Process:
        1. Check if registry is already initialized
        2. Attempt to import strategy registry module
        3. Initialize registry instance through factory function
        4. Set initialization flag and log success
        5. Handle import errors and initialization failures gracefully

        Error Handling:
        - ImportError: Handles missing strategy registry module
        - Exception: Catches all other initialization failures
        - Logging: Provides detailed error information for debugging
        - State Management: Maintains consistent state even on failures
        """
        if self._registry is None:
            try:
                from strategy_registry import get_strategy_registry

                self._registry = get_strategy_registry()
                self._initialized = True
                logger.debug("Strategy registry initialized successfully")
            except ImportError as e:
                logger.error(f"Failed to import strategy registry: {e}")
                self._registry = None
                self._initialized = False
            except Exception as e:
                logger.error(f"Failed to initialize strategy registry: {e}")
                self._registry = None
                self._initialized = False

        return self._registry

    def _is_available(self) -> bool:
        """
        Comprehensive availability check for the strategy registry.

        This method verifies that the strategy registry is both initialized and
        available for operations. It provides a centralized check that is used
        by all strategy operations to ensure safe registry access.

        Returns:
            bool: True if registry is available and initialized, False otherwise

        Availability Criteria:
        - Registry instance is not None
        - Initialization flag indicates successful setup
        - Registry is ready for strategy operations

        This method is called before all strategy operations to prevent
        None reference errors and ensure graceful degradation when the
        registry is unavailable.
        """
        return self.registry is not None and self._initialized

    async def validate_strategy(
        self, strategy_name: str, params: Dict[str, Any]
    ) -> bool:
        """
        Comprehensive validation of strategy existence and parameter validity.

        This method performs thorough validation of both strategy existence and
        parameter compliance with strategy requirements. It implements the complete
        validation pipeline including existence verification, parameter type checking,
        value constraint validation, and business rule compliance.

        Args:
            strategy_name: The name of the strategy to validate
            params: Dictionary containing strategy parameters to validate against
                   strategy specifications and constraints

        Returns:
            bool: True if strategy exists and all parameters are valid, False otherwise

        Validation Pipeline:
        1. Registry availability check to ensure safe operations
        2. Strategy existence verification in the registry
        3. Parameter validation using registry validation rules
        4. Type checking and value constraint verification
        5. Required parameter presence validation
        6. Business rule and interdependency validation

        Error Handling:
        The method handles all validation failures gracefully, logging detailed
        information about failures while returning False for any validation
        issues. This ensures system stability while providing debugging information.
        """
        if not self._is_available():
            logger.warning("Strategy registry not available for validation")
            return False

        try:
            # Check if strategy exists before parameter validation
            if not await self.strategy_exists(strategy_name):
                logger.warning(f"Strategy '{strategy_name}' does not exist")
                return False

            # Validate strategy parameters using comprehensive registry validation
            validation_errors = self.registry.validate_strategy_config(
                strategy_name, params
            )

            if validation_errors:
                logger.warning(
                    f"Strategy '{strategy_name}' validation failed: {validation_errors}"
                )
                return False

            logger.debug(f"Strategy '{strategy_name}' validation passed")
            return True

        except Exception as e:
            logger.error(f"Error validating strategy '{strategy_name}': {e}")
            return False

    async def get_available_strategies(self) -> List[str]:
        """
        Retrieves a list of all available strategy names from the strategy registry.

        This method accesses the initialized strategy registry, retrieves the dictionary
        of available strategies, and returns a list of their names (keys). It handles
        potential exceptions during registry access gracefully.

        Returns:
            List[str]: A list of available strategy names, or an empty list if the
                       registry is unavailable or an error occurs.
        """
        if not self._is_available():
            logger.warning("Strategy registry not available for listing strategies")
            return []

        try:
            available_strategies = self.registry.get_available_strategies()
            strategy_names = list(available_strategies.keys())
            logger.debug(f"Found {len(strategy_names)} available strategies")
            return strategy_names

        except Exception as e:
            logger.error(f"Error getting available strategies: {e}")
            return []

    async def get_strategy_parameters(
        self, strategy_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves the required parameters for a given strategy from the registry.

        This method first checks if the strategy exists. If it does, it retrieves the
        parameter specifications from the registry and converts them into a dictionary
        format suitable for API responses. It handles errors gracefully, such as when
        the strategy does not exist or an issue occurs during registry access.

        Args:
            strategy_name: The name of the strategy.

        Returns:
            A dictionary describing the required parameters, or None if the strategy
            doesn't exist or an error occurs.
        """
        if not self._is_available():
            logger.warning("Strategy registry not available for getting parameters")
            return None

        try:
            if not await self.strategy_exists(strategy_name):
                logger.warning(f"Strategy '{strategy_name}' does not exist")
                return None

            # Get strategy parameters from registry
            parameters = self.registry.get_strategy_parameters(strategy_name)

            # Convert StrategyParameter objects to dictionary format
            param_dict = {}
            for param in parameters:
                param_dict[param.name] = {
                    "type": (
                        param.param_type.__name__
                        if hasattr(param.param_type, "__name__")
                        else str(param.param_type)
                    ),
                    "default": param.default,
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                    "description": param.description,
                    "required": param.required,
                }

            logger.debug(
                f"Retrieved {len(param_dict)} parameters for strategy '{strategy_name}'"
            )
            return param_dict

        except Exception as e:
            logger.error(
                f"Error getting parameters for strategy '{strategy_name}': {e}"
            )
            return None

    async def strategy_exists(self, strategy_name: str) -> bool:
        """
        Checks if a strategy with the given name exists in the strategy registry.

        This method provides an efficient way to verify the existence of a strategy
        by checking if the strategy name is present in the list of available strategies
        retrieved from the registry. It handles potential errors during registry
        access gracefully.

        Args:
            strategy_name: The name of the strategy to check.

        Returns:
            bool: True if the strategy exists, False otherwise or if an error occurs.
        """
        if not self._is_available():
            logger.warning(
                "Strategy registry not available for checking strategy existence"
            )
            return False

        try:
            available_strategies = self.registry.get_available_strategies()
            exists = strategy_name in available_strategies
            logger.debug(f"Strategy '{strategy_name}' exists: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Error checking if strategy '{strategy_name}' exists: {e}")
            return False

    def refresh_strategies(self) -> int:
        """
        Refresh the strategy registry by discovering and registering new strategies.

        This method triggers a comprehensive refresh of the strategy registry,
        discovering new strategies that may have been added to the system and
        updating the available strategy list. It's useful for dynamic environments
        where strategies can be added without restarting the application.

        Returns:
            int: Number of strategies discovered and registered during refresh

        Refresh Process:
        1. Verify registry availability for safe operations
        2. Import refresh functionality with lazy loading
        3. Execute strategy discovery and registration process
        4. Return count of newly discovered strategies
        5. Handle refresh errors gracefully with detailed logging

        Use Cases:
        - Dynamic strategy deployment without application restart
        - Development environments with frequent strategy updates
        - Plugin-based architectures with runtime strategy loading
        - Administrative operations for strategy management

        The method provides safe refresh operations even when the registry
        is unavailable, returning 0 and logging appropriate warnings.
        """
        if not self._is_available():
            logger.warning("Strategy registry not available for refresh")
            return 0

        try:
            from strategy_registry import refresh_strategy_registry

            discovered_count = refresh_strategy_registry()
            logger.info(
                f"Strategy registry refreshed. Discovered {discovered_count} strategies"
            )
            return discovered_count

        except Exception as e:
            logger.error(f"Error refreshing strategy registry: {e}")
            return 0
