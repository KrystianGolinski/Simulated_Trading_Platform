# Strategy Service Interface
# Defines the contract for strategy validation and management operations
# Used to decouple validation logic from direct strategy registry access

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class StrategyServiceInterface(ABC):
    """
    Abstract interface for strategy validation and management operations.
    This interface allows for dependency injection and better testability
    by decoupling validation logic from direct strategy registry access.
    """

    @abstractmethod
    async def validate_strategy(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """
        Validates whether a strategy exists and its parameters are valid.
        
        Args:
            strategy_name: The name of the strategy to validate
            params: Dictionary containing strategy parameters to validate
            
        Returns:
            bool: True if strategy and parameters are valid, False otherwise
        """
        pass

    @abstractmethod
    async def get_available_strategies(self) -> List[str]:
        """
        Retrieves a list of all available strategy names.
        
        Returns:
            List[str]: List of available strategy names
        """
        pass

    @abstractmethod
    async def get_strategy_parameters(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the required parameters for a given strategy.
        
        Args:
            strategy_name: The name of the strategy
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary describing required parameters,
                                    or None if strategy doesn't exist
        """
        pass

    @abstractmethod
    async def strategy_exists(self, strategy_name: str) -> bool:
        """
        Checks if a strategy with the given name exists.
        
        Args:
            strategy_name: The name of the strategy to check
            
        Returns:
            bool: True if strategy exists, False otherwise
        """
        pass