# Strategy Registry - Plugin-based Strategy Discovery and Management System
# This module provides the core infrastructure for dynamic strategy loading and management
# Key responsibilities:
# - Dynamic strategy discovery from configured paths
# - Strategy registration and metadata management
# - Plugin architecture support for extensible strategy ecosystem
# - Strategy validation and parameter verification
# - Abstract interface definition for strategy implementations
# - Integration between Python API and C++ trading engine strategies
#
# Architecture Features:
# - Plugin-based architecture allows adding strategies without code changes
# - Abstract interface ensures consistent strategy implementation
# - Comprehensive metadata system for strategy documentation
# - Parameter validation with type checking and range validation
# - Automatic discovery from multiple strategy directories
# - Support for both core and plugin strategies

import importlib
import importlib.util
import inspect
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from models import ApiError, StandardResponse, StrategyType, create_error_response

logger = logging.getLogger(__name__)


@dataclass
class StrategyParameter:
    # Comprehensive strategy parameter definition with validation rules
    # Defines parameter structure for dynamic strategy configuration and validation
    # Used by strategy implementations to specify their configuration requirements
    name: str  # Parameter identifier (used as key in configuration)
    param_type: Type  # Python type for validation (int, float, str, bool)
    default: Any = None  # Default value if parameter not provided
    min_value: Optional[float] = None  # Minimum allowed value for numeric parameters
    max_value: Optional[float] = None  # Maximum allowed value for numeric parameters
    description: str = ""  # Human-readable parameter description
    required: bool = True  # Whether parameter is mandatory for strategy execution


@dataclass
class StrategyMetadata:
    # Comprehensive strategy metadata for registration and documentation
    # Contains all information needed for strategy discovery, validation, and usage
    # Used by strategy factory and API endpoints for strategy management
    strategy_id: str  # Unique strategy identifier
    display_name: str  # Human-readable strategy name
    description: str  # Detailed strategy description
    version: str  # Strategy version for compatibility
    author: str = ""  # Strategy author/maintainer
    parameters: List[StrategyParameter] = field(
        default_factory=list
    )  # Configuration parameters
    category: str = "technical"  # Strategy category (technical, fundamental, etc.)
    risk_level: str = "medium"  # Risk assessment: low, medium, high
    requires_indicators: List[str] = field(
        default_factory=list
    )  # Required technical indicators
    min_data_points: int = 50  # Minimum historical data requirement


class StrategyInterface(ABC):
    # Abstract base interface that all trading strategies must implement
    # Defines the contract for strategy plugins to ensure consistent integration
    # Enables dynamic strategy loading while maintaining type safety and validation

    @abstractmethod
    def get_metadata(self) -> StrategyMetadata:
        # Return comprehensive metadata for strategy registration and documentation
        # Must include all strategy information needed for API endpoints and validation
        # Called during strategy discovery and registration process
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        # Perform strategy-specific parameter validation beyond basic type checking
        # Returns list of error messages for invalid parameters (empty list if valid)
        # Enables custom validation logic for complex parameter relationships
        pass

    @abstractmethod
    def get_cpp_strategy_name(self) -> str:
        # Return the corresponding C++ trading engine strategy identifier
        # Maps Python strategy to C++ implementation for execution
        # Must match exactly with C++ engine strategy registration
        pass

    @abstractmethod
    def transform_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Transform API parameters to C++ engine compatible format
        # Handles parameter name mapping and value transformation as needed
        # Ensures seamless communication between Python API and C++ engine
        pass


class StrategyRegistry:
    # Central registry for dynamic strategy discovery, loading, and management
    # Provides plugin architecture for extensible trading strategy ecosystem
    # Manages strategy lifecycle from discovery to validation and execution

    def __init__(self):
        # Strategy storage and caching
        self._strategies: Dict[str, Type[StrategyInterface]] = (
            {}
        )  # Registered strategy classes
        self._metadata_cache: Dict[str, StrategyMetadata] = (
            {}
        )  # Cached strategy metadata

        # Strategy discovery paths - supports both core and plugin strategies
        self._strategy_paths: List[Path] = [
            Path(__file__).parent / "strategies",  # Core strategies directory
            Path(__file__).parent
            / "plugins"
            / "strategies",  # Plugin strategies directory
        ]

        # Load core strategies immediately to ensure basic functionality
        self._load_core_strategies()

        logger.info(
            f"Strategy registry initialized with {len(self._strategy_paths)} discovery paths"
        )

    def register_strategy(self, strategy_class: Type[StrategyInterface]) -> bool:
        # Register a strategy class with comprehensive validation and metadata caching
        # Performs complete validation of strategy implementation and metadata
        # Returns success status for strategy discovery and loading feedback
        try:
            # Validate strategy class implements required interface
            if not issubclass(strategy_class, StrategyInterface):
                logger.error(
                    f"Strategy {strategy_class.__name__} does not implement StrategyInterface"
                )
                return False

            # Create instance to extract metadata and validate implementation
            try:
                instance = strategy_class()
                metadata = instance.get_metadata()
            except Exception as e:
                logger.error(
                    f"Failed to instantiate strategy {strategy_class.__name__}: {e}"
                )
                return False

            # Validate essential metadata fields
            if not metadata.strategy_id or not metadata.display_name:
                logger.error(
                    f"Strategy {strategy_class.__name__} has invalid metadata: "
                    f"strategy_id='{metadata.strategy_id}', display_name='{metadata.display_name}'"
                )
                return False

            # Validate strategy_id format (should be suitable for API usage)
            if not metadata.strategy_id.replace("_", "").isalnum():
                logger.error(
                    f"Strategy {strategy_class.__name__} has invalid strategy_id format: '{metadata.strategy_id}'"
                )
                return False

            # Check for duplicates and handle appropriately
            if metadata.strategy_id in self._strategies:
                existing_metadata = self._metadata_cache.get(metadata.strategy_id)
                if existing_metadata:
                    logger.warning(
                        f"Strategy {metadata.strategy_id} already registered "
                        f"(v{existing_metadata.version}), overwriting with v{metadata.version}"
                    )
                else:
                    logger.warning(
                        f"Strategy {metadata.strategy_id} already registered, overwriting"
                    )

            # Register strategy class and cache metadata
            self._strategies[metadata.strategy_id] = strategy_class
            self._metadata_cache[metadata.strategy_id] = metadata

            logger.info(
                f"Successfully registered strategy: {metadata.strategy_id} "
                f"({metadata.display_name}) v{metadata.version} by {metadata.author}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Unexpected error registering strategy {strategy_class.__name__}: {e}"
            )
            return False

    def get_strategy(self, strategy_id: str) -> Optional[StrategyInterface]:
        # Create and return strategy instance by ID with error handling
        # Returns None if strategy not found or instantiation fails
        # Used by strategy factory and simulation execution components
        if strategy_id not in self._strategies:
            logger.debug(f"Strategy '{strategy_id}' not found in registry")
            return None

        try:
            # Create new instance of the strategy class
            strategy_instance = self._strategies[strategy_id]()
            logger.debug(f"Successfully instantiated strategy '{strategy_id}'")
            return strategy_instance
        except Exception as e:
            logger.error(f"Failed to instantiate strategy '{strategy_id}': {e}")
            return None

    def get_available_strategies(self) -> Dict[str, StrategyMetadata]:
        # Return all available strategies with their complete metadata
        # Returns copy to prevent external modification of internal cache
        # Used by strategy factory and API endpoints for strategy listing
        return self._metadata_cache.copy()

    def get_strategy_parameters(self, strategy_id: str) -> List[StrategyParameter]:
        # Retrieve parameter definitions for a specific strategy
        # Returns empty list if strategy not found
        # Used for parameter validation and form generation
        if strategy_id not in self._metadata_cache:
            logger.debug(f"Strategy '{strategy_id}' not found for parameter retrieval")
            return []
        return self._metadata_cache[strategy_id].parameters

    def validate_strategy_config(
        self, strategy_id: str, parameters: Dict[str, Any]
    ) -> List[str]:
        # Comprehensive strategy configuration validation with detailed error reporting
        # Performs both metadata-based validation and strategy-specific validation
        # Returns list of human-readable error messages for API response
        errors = []

        # Verify strategy exists and can be instantiated
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            available_strategies = list(self._strategies.keys())
            errors.append(
                f"Unknown strategy: '{strategy_id}'. Available strategies: {', '.join(available_strategies)}"
            )
            return errors

        # Get strategy metadata for parameter validation
        metadata = self._metadata_cache[strategy_id]

        # Validate required parameters are present
        for param in metadata.parameters:
            if param.required and param.name not in parameters:
                errors.append(
                    f"Missing required parameter: '{param.name}' ({param.description})"
                )
                continue

            # Validate provided parameters
            if param.name in parameters:
                value = parameters[param.name]

                # Type validation with special handling for numeric types
                if param.param_type is float:
                    if not isinstance(value, (int, float)):
                        errors.append(
                            f"Parameter '{param.name}' must be a number (float or integer), got {type(value).__name__}"
                        )
                        continue
                    # Convert int to float for consistency
                    parameters[param.name] = float(value)
                    value = float(value)
                elif not isinstance(value, param.param_type):
                    errors.append(
                        f"Parameter '{param.name}' must be of type {param.param_type.__name__}, got {type(value).__name__}"
                    )
                    continue

                # Range validation for numeric parameters
                if param.param_type in [int, float]:
                    if param.min_value is not None and value < param.min_value:
                        errors.append(
                            f"Parameter '{param.name}' must be >= {param.min_value}, got {value}"
                        )
                    if param.max_value is not None and value > param.max_value:
                        errors.append(
                            f"Parameter '{param.name}' must be <= {param.max_value}, got {value}"
                        )

        # Check for unexpected parameters
        valid_param_names = {param.name for param in metadata.parameters}
        unexpected_params = set(parameters.keys()) - valid_param_names
        if unexpected_params:
            errors.append(
                f"Unexpected parameters for strategy '{strategy_id}': {', '.join(unexpected_params)}"
            )

        # Perform strategy-specific validation (e.g., parameter relationships)
        try:
            strategy_errors = strategy.validate_parameters(parameters)
            errors.extend(strategy_errors)
        except Exception as e:
            errors.append(f"Strategy-specific validation failed: {str(e)}")

        return errors

    def discover_strategies(self) -> int:
        # Comprehensive strategy discovery from configured filesystem paths
        # Scans for Python modules implementing StrategyInterface and registers them
        # Returns count of successfully discovered and registered strategies
        discovered_count = 0
        total_files_scanned = 0

        logger.info(
            f"Starting strategy discovery across {len(self._strategy_paths)} paths"
        )

        for strategy_path in self._strategy_paths:
            if not strategy_path.exists():
                logger.debug(f"Strategy path does not exist: {strategy_path}")
                continue

            logger.debug(f"Scanning strategy path: {strategy_path}")

            # Look for Python strategy modules
            python_files = list(strategy_path.glob("*.py"))
            path_discovered = 0

            for python_file in python_files:
                # Skip Python package/init files
                if python_file.name.startswith("__"):
                    continue

                total_files_scanned += 1

                try:
                    # Dynamic module import from file path
                    module_name = python_file.stem
                    spec = importlib.util.spec_from_file_location(
                        module_name, python_file
                    )
                    if not spec or not spec.loader:
                        logger.warning(
                            f"Could not create module spec for {python_file}"
                        )
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Find strategy classes that implement StrategyInterface
                    file_strategies = 0
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Filter for strategy classes:
                        # 1. Not the abstract interface itself
                        # 2. Implements StrategyInterface
                        # 3. Defined in this module (not imported)
                        if (
                            obj != StrategyInterface
                            and issubclass(obj, StrategyInterface)
                            and obj.__module__ == module.__name__
                        ):

                            logger.debug(
                                f"Found strategy class: {name} in {python_file.name}"
                            )

                            if self.register_strategy(obj):
                                discovered_count += 1
                                path_discovered += 1
                                file_strategies += 1

                    if file_strategies == 0:
                        logger.debug(f"No strategy classes found in {python_file.name}")

                except Exception as e:
                    logger.error(f"Failed to load strategy from {python_file}: {e}")

            if path_discovered > 0:
                logger.info(
                    f"Discovered {path_discovered} strategies from path: {strategy_path}"
                )

        logger.info(
            f"Strategy discovery completed: {discovered_count} strategies discovered "
            f"from {total_files_scanned} files across {len(self._strategy_paths)} paths"
        )

        return discovered_count

    def _load_core_strategies(self):
        # Load essential core strategies to ensure basic platform functionality
        # These strategies are always available regardless of plugin discovery
        # Provides fallback if strategy discovery fails
        core_strategies_loaded = 0

        try:
            # Import and register core strategy implementations
            from strategies.ma_crossover_strategy import MACrossoverStrategy
            from strategies.rsi_strategy import RSIStrategy

            # Register core strategies
            if self.register_strategy(MACrossoverStrategy):
                core_strategies_loaded += 1
            if self.register_strategy(RSIStrategy):
                core_strategies_loaded += 1

            logger.info(f"Successfully loaded {core_strategies_loaded} core strategies")

        except ImportError as e:
            logger.warning(f"Failed to load core strategies: {e}")
            logger.info(
                "Platform will continue without core strategies - they can be loaded later via discovery"
            )
        except Exception as e:
            logger.error(f"Unexpected error loading core strategies: {e}")


# Global strategy registry instance
# Singleton pattern ensures consistent strategy state across the entire application
# Used by strategy factory, simulation engine, and strategy management endpoints
strategy_registry = StrategyRegistry()


def get_strategy_registry() -> StrategyRegistry:
    # Get the global strategy registry instance for dependency injection
    # Provides access to all strategy management and discovery capabilities
    return strategy_registry


def refresh_strategy_registry() -> int:
    # Convenience function to refresh the registry by discovering new strategies
    # Returns count of newly discovered strategies
    # Used by strategy refresh endpoints and periodic discovery tasks
    return strategy_registry.discover_strategies()
