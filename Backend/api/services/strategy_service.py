# Strategy Service Interface - Abstract Contract for Strategy Management Operations
# This module defines the comprehensive interface for strategy validation and management in the Trading Platform API
#
# Architecture Overview:
# The StrategyServiceInterface implements an abstract contract that decouples strategy validation
# and management logic from direct strategy registry access. It provides a clean abstraction
# layer that enables dependency injection, improves testability, and maintains separation of
# concerns between strategy operations and the underlying registry implementation.
#
# Key Design Principles:
# 1. Interface Segregation - Focused interface for strategy-specific operations
# 2. Dependency Inversion - Abstracts dependencies to enable flexible implementations
# 3. Single Responsibility - Dedicated to strategy validation and management only
# 4. Open/Closed Principle - Extensible through implementation without modification
#
# Interface Operations:
# 1. Strategy Validation - Comprehensive validation of strategy existence and parameters
# 2. Strategy Discovery - Retrieval of available strategies and their metadata
# 3. Parameter Management - Access to strategy parameter definitions and constraints
# 4. Existence Checking - Efficient strategy existence verification
#
# Integration Benefits:
# - Enables dependency injection for improved testability
# - Provides consistent strategy operations across the platform
# - Allows for multiple implementations (e.g., cached, distributed, local)
# - Supports mock implementations for testing and development
# - Facilitates clean architecture patterns and separation of concerns
#
# Implementation Requirements:
# Concrete implementations must provide robust error handling, parameter validation,
# and efficient strategy discovery while maintaining the contract defined by this interface.

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StrategyServiceInterface(ABC):
    """
    Abstract interface for comprehensive strategy validation and management operations.

    This interface defines the contract for strategy-related operations in the Trading Platform,
    providing a clean abstraction layer that decouples strategy validation and management logic
    from direct strategy registry access. It enables dependency injection, improves testability,
    and maintains separation of concerns between strategy operations and registry implementation.

    Key Design Features:
    - Abstract contract for consistent strategy operations across implementations
    - Asynchronous operations to support scalable and non-blocking strategy management
    - Comprehensive parameter validation and metadata access
    - Efficient strategy discovery and existence checking
    - Flexible architecture supporting multiple implementation patterns

    Implementation Requirements:
    Concrete implementations must provide robust error handling, comprehensive parameter
    validation, efficient strategy discovery, and maintain the asynchronous contract
    defined by this interface. Implementations should also provide appropriate logging
    and monitoring capabilities for production use.

    Usage Patterns:
    This interface supports dependency injection patterns, enabling easy testing through
    mock implementations and flexible deployment through different concrete implementations
    (e.g., local registry, cached registry, distributed registry).
    """

    @abstractmethod
    async def validate_strategy(
        self, strategy_name: str, params: Dict[str, Any]
    ) -> bool:
        """
        Comprehensive validation of strategy existence and parameter validity.

        This method performs thorough validation of both strategy existence and
        parameter compliance with strategy requirements. It ensures that the
        strategy is available and that all provided parameters meet the strategy's
        specifications including type constraints, value ranges, and required fields.

        Args:
            strategy_name: The name of the strategy to validate
            params: Dictionary containing strategy parameters to validate against
                   strategy specifications and constraints

        Returns:
            bool: True if strategy exists and all parameters are valid, False otherwise

        Validation Process:
        1. Verify strategy existence in the registry
        2. Validate parameter types and value constraints
        3. Check required parameter presence and optional parameter defaults
        4. Ensure parameter values fall within acceptable ranges
        5. Validate parameter interdependencies and business rules

        The method should provide comprehensive logging for validation failures
        to enable debugging and parameter correction.
        """
        pass

    @abstractmethod
    async def get_available_strategies(self) -> List[str]:
        """
        Retrieve comprehensive list of all available strategy names.

        This method provides access to all strategies currently available in the
        strategy registry, enabling dynamic strategy discovery and selection.
        The returned list should represent all strategies that can be used for
        trading simulations.

        Returns:
            List[str]: Complete list of available strategy names

        The method should handle registry access errors gracefully and return
        an empty list if the registry is unavailable, with appropriate logging
        to indicate the failure condition.
        """
        pass

    @abstractmethod
    async def get_strategy_parameters(
        self, strategy_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve comprehensive parameter specifications for a given strategy.

        This method provides detailed information about the parameters required
        by a specific strategy, including parameter types, default values, value
        constraints, and descriptions. This information is essential for dynamic
        parameter validation and user interface generation.

        Args:
            strategy_name: The name of the strategy to retrieve parameters for

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing parameter specifications:
                - Parameter names as keys
                - Parameter metadata as values including:
                  - type: Parameter data type
                  - default: Default value (if any)
                  - min_value: Minimum allowed value (for numeric types)
                  - max_value: Maximum allowed value (for numeric types)
                  - description: Human-readable parameter description
                  - required: Boolean indicating if parameter is required
                Returns None if strategy doesn't exist

        Parameter Specification Format:
        The returned dictionary provides comprehensive metadata for each parameter,
        enabling dynamic validation, user interface generation, and documentation
        creation for strategy configuration.
        """
        pass

    @abstractmethod
    async def strategy_exists(self, strategy_name: str) -> bool:
        """
        Efficient verification of strategy existence in the registry.

        This method provides a lightweight check for strategy existence without
        retrieving full strategy metadata. It's optimized for scenarios where
        only existence verification is needed, such as input validation or
        conditional logic branching.

        Args:
            strategy_name: The name of the strategy to check for existence

        Returns:
            bool: True if strategy exists in the registry, False otherwise

        Performance Considerations:
        This method should be implemented efficiently to support high-frequency
        existence checks without impacting system performance. It should provide
        appropriate caching and optimization for repeated checks.
        """
        pass
