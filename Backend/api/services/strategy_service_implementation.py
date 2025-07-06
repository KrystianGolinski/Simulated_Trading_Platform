# Strategy Service Implementation
# Concrete implementation of StrategyServiceInterface with lazy loading
# Provides strategy validation and management operations without creating circular dependencies

import logging
from typing import Dict, List, Any, Optional

from .strategy_service import StrategyServiceInterface

logger = logging.getLogger(__name__)


class StrategyService(StrategyServiceInterface):
    """
    Concrete implementation of StrategyServiceInterface.
    Uses lazy loading to avoid circular import issues and provides
    proper error handling for strategy operations.
    """

    def __init__(self):
        # Initialize with lazy loading to avoid circular imports
        self._registry = None
        self._initialized = False

    @property
    def registry(self):
        """
        Lazy-loaded strategy registry property.
        Only imports and initializes the registry when first accessed.
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
        Checks if the strategy registry is available and initialized.
        
        Returns:
            bool: True if registry is available, False otherwise
        """
        return self.registry is not None and self._initialized

    async def validate_strategy(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """
        Validates whether a strategy exists and its parameters are valid.
        
        Args:
            strategy_name: The name of the strategy to validate
            params: Dictionary containing strategy parameters to validate
            
        Returns:
            bool: True if strategy and parameters are valid, False otherwise
        """
        if not self._is_available():
            logger.warning("Strategy registry not available for validation")
            return False

        try:
            # Check if strategy exists
            if not await self.strategy_exists(strategy_name):
                logger.warning(f"Strategy '{strategy_name}' does not exist")
                return False

            # Validate strategy parameters using registry
            validation_errors = self.registry.validate_strategy_config(strategy_name, params)
            
            if validation_errors:
                logger.warning(f"Strategy '{strategy_name}' validation failed: {validation_errors}")
                return False

            logger.debug(f"Strategy '{strategy_name}' validation passed")
            return True

        except Exception as e:
            logger.error(f"Error validating strategy '{strategy_name}': {e}")
            return False

    async def get_available_strategies(self) -> List[str]:
        """
        Retrieves a list of all available strategy names.
        
        Returns:
            List[str]: List of available strategy names
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

    async def get_strategy_parameters(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the required parameters for a given strategy.
        
        Args:
            strategy_name: The name of the strategy
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary describing required parameters,
                                    or None if strategy doesn't exist
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
                    'type': param.param_type.__name__ if hasattr(param.param_type, '__name__') else str(param.param_type),
                    'default': param.default,
                    'min_value': param.min_value,
                    'max_value': param.max_value,
                    'description': param.description,
                    'required': param.required
                }

            logger.debug(f"Retrieved {len(param_dict)} parameters for strategy '{strategy_name}'")
            return param_dict

        except Exception as e:
            logger.error(f"Error getting parameters for strategy '{strategy_name}': {e}")
            return None

    async def strategy_exists(self, strategy_name: str) -> bool:
        """
        Checks if a strategy with the given name exists.
        
        Args:
            strategy_name: The name of the strategy to check
            
        Returns:
            bool: True if strategy exists, False otherwise
        """
        if not self._is_available():
            logger.warning("Strategy registry not available for checking strategy existence")
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
        Refreshes the strategy registry by discovering new strategies.
        
        Returns:
            int: Number of strategies discovered and registered
        """
        if not self._is_available():
            logger.warning("Strategy registry not available for refresh")
            return 0

        try:
            from strategy_registry import refresh_strategy_registry
            discovered_count = refresh_strategy_registry()
            logger.info(f"Strategy registry refreshed. Discovered {discovered_count} strategies")
            return discovered_count

        except Exception as e:
            logger.error(f"Error refreshing strategy registry: {e}")
            return 0