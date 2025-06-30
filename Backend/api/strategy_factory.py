# Enhanced Strategy Factory with Dynamic Loading Support
from typing import Dict, Any, List, Optional
import logging
from dataclasses import asdict

from strategy_registry import get_strategy_registry, StrategyInterface, StrategyMetadata
from response_models import StandardResponse, create_success_response, create_error_response, ApiError

logger = logging.getLogger(__name__)

class StrategyFactory:
    # Enhanced factory for dynamic strategy management and configuration
    
    def __init__(self):
        self.registry = get_strategy_registry()
        # Refresh registry on initialization to pick up any new strategies
        discovered = self.registry.discover_strategies()
        if discovered > 0:
            logger.info(f"Discovered {discovered} additional strategies")
    
    def get_available_strategies(self) -> StandardResponse[Dict[str, Any]]:
        # Get all available strategies with their metadata
        try:
            strategies = self.registry.get_available_strategies()
            
            # Transform metadata for API response
            strategy_list = []
            for strategy_id, metadata in strategies.items():
                strategy_info = {
                    "id": metadata.strategy_id,
                    "name": metadata.display_name,
                    "description": metadata.description,
                    "version": metadata.version,
                    "author": metadata.author,
                    "category": metadata.category,
                    "risk_level": metadata.risk_level,
                    "min_data_points": metadata.min_data_points,
                    "requires_indicators": metadata.requires_indicators,
                    "parameters": [
                        {
                            "name": param.name,
                            "type": param.param_type.__name__,
                            "default": param.default,
                            "min_value": param.min_value,
                            "max_value": param.max_value,
                            "description": param.description,
                            "required": param.required
                        }
                        for param in metadata.parameters
                    ]
                }
                strategy_list.append(strategy_info)
            
            return create_success_response(
                {
                    "strategies": strategy_list,
                    "total_count": len(strategy_list)
                },
                f"Retrieved {len(strategy_list)} available strategies"
            )
            
        except Exception as e:
            logger.error(f"Failed to get available strategies: {e}")
            return create_error_response(
                "Failed to retrieve strategies",
                [ApiError(code="STRATEGY_RETRIEVAL_ERROR", message=str(e))]
            )
    
    def get_strategy_metadata(self, strategy_id: str) -> StandardResponse[Dict[str, Any]]:
        # Get detailed metadata for a specific strategy
        try:
            strategies = self.registry.get_available_strategies()
            
            if strategy_id not in strategies:
                return create_error_response(
                    f"Strategy '{strategy_id}' not found",
                    [ApiError(code="STRATEGY_NOT_FOUND", message=f"Strategy '{strategy_id}' is not registered")]
                )
            
            metadata = strategies[strategy_id]
            strategy_info = {
                "id": metadata.strategy_id,
                "name": metadata.display_name,
                "description": metadata.description,
                "version": metadata.version,
                "author": metadata.author,
                "category": metadata.category,
                "risk_level": metadata.risk_level,
                "min_data_points": metadata.min_data_points,
                "requires_indicators": metadata.requires_indicators,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.param_type.__name__,
                        "default": param.default,
                        "min_value": param.min_value,
                        "max_value": param.max_value,
                        "description": param.description,
                        "required": param.required
                    }
                    for param in metadata.parameters
                ]
            }
            
            return create_success_response(
                strategy_info,
                f"Retrieved metadata for strategy '{strategy_id}'"
            )
            
        except Exception as e:
            logger.error(f"Failed to get strategy metadata for {strategy_id}: {e}")
            return create_error_response(
                f"Failed to retrieve strategy metadata",
                [ApiError(code="METADATA_RETRIEVAL_ERROR", message=str(e))]
            )
    
    def validate_strategy_config(self, strategy_id: str, parameters: Dict[str, Any]) -> StandardResponse[Dict[str, Any]]:
        # Validate strategy configuration with dynamic parameter validation
        try:
            # Check if strategy exists
            if strategy_id not in self.registry.get_available_strategies():
                return create_error_response(
                    f"Strategy '{strategy_id}' not found",
                    [ApiError(code="STRATEGY_NOT_FOUND", message=f"Strategy '{strategy_id}' is not registered")]
                )
            
            # Validate parameters
            validation_errors = self.registry.validate_strategy_config(strategy_id, parameters)
            
            if validation_errors:
                return create_error_response(
                    "Strategy configuration validation failed",
                    [ApiError(code="VALIDATION_FAILED", message=error) for error in validation_errors]
                )
            
            # Get strategy instance for parameter transformation
            strategy = self.registry.get_strategy(strategy_id)
            if not strategy:
                return create_error_response(
                    "Failed to instantiate strategy",
                    [ApiError(code="STRATEGY_INSTANTIATION_ERROR", message="Could not create strategy instance")]
                )
            
            # Transform parameters for C++ engine
            transformed_params = strategy.transform_parameters(parameters)
            
            return create_success_response(
                {
                    "strategy_id": strategy_id,
                    "parameters": parameters,
                    "transformed_parameters": transformed_params,
                    "validation_status": "passed"
                },
                f"Strategy configuration for '{strategy_id}' is valid"
            )
            
        except Exception as e:
            logger.error(f"Failed to validate strategy config for {strategy_id}: {e}")
            return create_error_response(
                "Strategy validation failed",
                [ApiError(code="STRATEGY_VALIDATION_ERROR", message=str(e))]
            )
    
    def create_strategy_config(self, strategy_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Create C++ engine compatible strategy configuration
        try:
            strategy = self.registry.get_strategy(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy '{strategy_id}' not found")
            
            return strategy.transform_parameters(parameters)
            
        except Exception as e:
            logger.error(f"Failed to create strategy config for {strategy_id}: {e}")
            raise
    
    def refresh_strategies(self) -> StandardResponse[Dict[str, Any]]:
        # Refresh the strategy registry by discovering new strategies
        try:
            discovered_count = self.registry.discover_strategies()
            total_strategies = len(self.registry.get_available_strategies())
            
            return create_success_response(
                {
                    "discovered_strategies": discovered_count,
                    "total_strategies": total_strategies,
                    "refresh_timestamp": __import__("time").time()
                },
                f"Strategy registry refreshed: {discovered_count} new strategies discovered"
            )
            
        except Exception as e:
            logger.error(f"Failed to refresh strategies: {e}")
            return create_error_response(
                "Failed to refresh strategy registry",
                [ApiError(code="REGISTRY_REFRESH_ERROR", message=str(e))]
            )

# Global factory instance
strategy_factory = StrategyFactory()

def get_strategy_factory() -> StrategyFactory:
    # Get the global strategy factory instance
    return strategy_factory