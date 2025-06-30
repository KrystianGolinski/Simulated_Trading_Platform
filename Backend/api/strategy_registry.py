# Strategy Registry for Dynamic Strategy Loading and Management
from typing import Dict, List, Type, Any, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import importlib
import importlib.util
import inspect
from pathlib import Path
import json
import logging

from models import StrategyType
from response_models import StandardResponse, create_error_response, ApiError

logger = logging.getLogger(__name__)

@dataclass
class StrategyParameter:
    # Defines a strategy parameter with validation rules
    name: str
    param_type: Type
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    required: bool = True

@dataclass
class StrategyMetadata:
    # Comprehensive strategy metadata for dynamic registration
    strategy_id: str
    display_name: str
    description: str
    version: str
    author: str = ""
    parameters: List[StrategyParameter] = field(default_factory=list)
    category: str = "technical"
    risk_level: str = "medium"  # low, medium, high
    requires_indicators: List[str] = field(default_factory=list)
    min_data_points: int = 50

class StrategyInterface(ABC):
    # Abstract interface that all dynamic strategies must implement
    
    @abstractmethod
    def get_metadata(self) -> StrategyMetadata:
        # Return strategy metadata for registration
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        # Validate strategy-specific parameters, return list of error messages
        pass
    
    @abstractmethod
    def get_cpp_strategy_name(self) -> str:
        # Return the corresponding C++ strategy identifier
        pass
    
    @abstractmethod
    def transform_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Transform API parameters to C++ engine format
        pass

class StrategyRegistry:
    # Central registry for managing dynamic strategy loading and discovery
    
    def __init__(self):
        self._strategies: Dict[str, Type[StrategyInterface]] = {}
        self._metadata_cache: Dict[str, StrategyMetadata] = {}
        self._strategy_paths: List[Path] = [
            Path(__file__).parent / "strategies",  # Default strategies directory
            Path(__file__).parent / "plugins" / "strategies"  # Plugin strategies directory
        ]
        self._load_core_strategies()
    
    def register_strategy(self, strategy_class: Type[StrategyInterface]) -> bool:
        # Register a strategy class dynamically
        try:
            # Validate strategy class
            if not issubclass(strategy_class, StrategyInterface):
                logger.error(f"Strategy {strategy_class.__name__} does not implement StrategyInterface")
                return False
            
            # Get metadata
            instance = strategy_class()
            metadata = instance.get_metadata()
            
            # Validate metadata
            if not metadata.strategy_id or not metadata.display_name:
                logger.error(f"Strategy {strategy_class.__name__} has invalid metadata")
                return False
            
            # Check for duplicates
            if metadata.strategy_id in self._strategies:
                logger.warning(f"Strategy {metadata.strategy_id} already registered, overwriting")
            
            # Register strategy
            self._strategies[metadata.strategy_id] = strategy_class
            self._metadata_cache[metadata.strategy_id] = metadata
            
            logger.info(f"Successfully registered strategy: {metadata.strategy_id} ({metadata.display_name})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register strategy {strategy_class.__name__}: {e}")
            return False
    
    def get_strategy(self, strategy_id: str) -> Optional[StrategyInterface]:
        # Get strategy instance by ID
        if strategy_id not in self._strategies:
            return None
        
        try:
            return self._strategies[strategy_id]()
        except Exception as e:
            logger.error(f"Failed to instantiate strategy {strategy_id}: {e}")
            return None
    
    def get_available_strategies(self) -> Dict[str, StrategyMetadata]:
        # Get all available strategies with metadata
        return self._metadata_cache.copy()
    
    def get_strategy_parameters(self, strategy_id: str) -> List[StrategyParameter]:
        # Get parameters for a specific strategy
        if strategy_id not in self._metadata_cache:
            return []
        return self._metadata_cache[strategy_id].parameters
    
    def validate_strategy_config(self, strategy_id: str, parameters: Dict[str, Any]) -> List[str]:
        # Validate strategy configuration
        errors = []
        
        # Check if strategy exists
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            errors.append(f"Unknown strategy: {strategy_id}")
            return errors
        
        # Get strategy metadata
        metadata = self._metadata_cache[strategy_id]
        
        # Validate required parameters
        for param in metadata.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"Missing required parameter: {param.name}")
                continue
            
            if param.name in parameters:
                value = parameters[param.name]
                
                # Type validation
                if not isinstance(value, param.param_type):
                    errors.append(f"Parameter {param.name} must be of type {param.param_type.__name__}")
                    continue
                
                # Range validation for numeric types
                if param.param_type in [int, float]:
                    if param.min_value is not None and value < param.min_value:
                        errors.append(f"Parameter {param.name} must be >= {param.min_value}")
                    if param.max_value is not None and value > param.max_value:
                        errors.append(f"Parameter {param.name} must be <= {param.max_value}")
        
        # Strategy-specific validation
        strategy_errors = strategy.validate_parameters(parameters)
        errors.extend(strategy_errors)
        
        return errors
    
    def discover_strategies(self) -> int:
        # Discover and load strategies from configured paths
        discovered_count = 0
        
        for strategy_path in self._strategy_paths:
            if not strategy_path.exists():
                continue
            
            # Look for Python strategy modules
            for python_file in strategy_path.glob("*.py"):
                if python_file.name.startswith("__"):
                    continue
                
                try:
                    # Import module
                    module_name = python_file.stem
                    spec = importlib.util.spec_from_file_location(module_name, python_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find strategy classes
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (obj != StrategyInterface and 
                            issubclass(obj, StrategyInterface) and 
                            obj.__module__ == module.__name__):
                            
                            if self.register_strategy(obj):
                                discovered_count += 1
                                
                except Exception as e:
                    logger.error(f"Failed to load strategy from {python_file}: {e}")
        
        return discovered_count
    
    def _load_core_strategies(self):
        # Load core strategies (MA Crossover and RSI)
        try:
            from strategies.ma_crossover_strategy import MACrossoverStrategy
            from strategies.rsi_strategy import RSIStrategy
            
            self.register_strategy(MACrossoverStrategy)
            self.register_strategy(RSIStrategy)
        except ImportError as e:
            logger.warning(f"Failed to load core strategies: {e}")
            # Continue without core strategies - they can be loaded later via discovery

# Global registry instance
strategy_registry = StrategyRegistry()

def get_strategy_registry() -> StrategyRegistry:
    # Get the global strategy registry instance
    return strategy_registry

def refresh_strategy_registry() -> int:
    # Refresh the registry by discovering new strategies
    return strategy_registry.discover_strategies()