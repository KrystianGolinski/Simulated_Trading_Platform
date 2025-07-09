# Strategy Factory - Dynamic Strategy Management and Configuration
# This module provides comprehensive strategy management capabilities for the Trading Platform
# Key responsibilities:
# - Dynamic strategy discovery and registration management
# - Strategy metadata extraction and API formatting
# - Strategy parameter validation and configuration
# - C++ engine compatible parameter transformation
# - Strategy registry integration and coordination
# - Standardised API response formatting for strategy operations
#
# Architecture Integration:
# - Integrates with StrategyRegistry for dynamic strategy discovery
# - Provides API-friendly interfaces for strategy management endpoints
# - Transforms strategy metadata for frontend consumption
# - Validates strategy configurations before simulation execution
# - Ensures compatibility between Python API and C++ trading engine

import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from models import (
    ApiError,
    StandardResponse,
    create_error_response,
    create_success_response,
)
from strategy_registry import StrategyInterface, StrategyMetadata, get_strategy_registry

logger = logging.getLogger(__name__)


class StrategyFactory:
    # Central factory for dynamic strategy management and configuration
    # Provides high-level API interfaces for strategy discovery, validation, and configuration
    # Acts as a bridge between the strategy registry and API endpoints

    def __init__(self):
        # Initialize strategy registry connection
        self.registry = get_strategy_registry()

        # Perform initial strategy discovery to ensure all available strategies are loaded
        # This includes both core strategies and dynamically discovered plugin strategies
        discovered = self.registry.discover_strategies()
        if discovered > 0:
            logger.info(
                f"Discovered {discovered} additional strategies during factory initialization"
            )

        # Log total available strategies for monitoring
        total_strategies = len(self.registry.get_available_strategies())
        logger.info(
            f"Strategy factory initialized with {total_strategies} total strategies available"
        )

    def get_available_strategies(self) -> StandardResponse[Dict[str, Any]]:
        # Retrieve all available strategies with comprehensive metadata for API consumption
        # Transforms internal strategy metadata into API-friendly format with detailed parameter information
        # Used by strategy listing endpoints and strategy selection interfaces
        try:
            # Get all registered strategies from the registry
            strategies = self.registry.get_available_strategies()

            # Transform internal metadata structure to API-friendly format
            strategy_list = []
            for strategy_id, metadata in strategies.items():
                # Create comprehensive strategy information for API response
                strategy_info = {
                    "id": metadata.strategy_id,  # Unique strategy identifier
                    "name": metadata.display_name,  # Human-readable strategy name
                    "description": metadata.description,  # Strategy description and purpose
                    "version": metadata.version,  # Strategy version for compatibility
                    "author": metadata.author,  # Strategy author information
                    "category": metadata.category,  # Strategy category for filtering
                    "risk_level": metadata.risk_level,  # Risk assessment (low/medium/high)
                    "min_data_points": metadata.min_data_points,  # Minimum data requirements
                    "requires_indicators": metadata.requires_indicators,  # Required technical indicators
                    # Transform parameter metadata for frontend parameter forms
                    "parameters": [
                        {
                            "name": param.name,  # Parameter identifier
                            "type": param.param_type.__name__,  # Data type for validation
                            "default": param.default,  # Default value
                            "min_value": param.min_value,  # Minimum allowed value
                            "max_value": param.max_value,  # Maximum allowed value
                            "description": param.description,  # Parameter description
                            "required": param.required,  # Whether parameter is mandatory
                        }
                        for param in metadata.parameters
                    ],
                }
                strategy_list.append(strategy_info)

            # Return standardised success response with strategy data
            return create_success_response(
                {
                    "strategies": strategy_list,
                    "total_count": len(strategy_list),
                    "categories": list(
                        set(s["category"] for s in strategy_list)
                    ),  # Available categories
                    "registry_status": "active",  # Registry health indicator
                },
                f"Retrieved {len(strategy_list)} available strategies from registry",
            )

        except Exception as e:
            logger.error(f"Failed to get available strategies: {e}")
            return create_error_response(
                "Failed to retrieve strategies from registry",
                [
                    ApiError(
                        code="STRATEGY_RETRIEVAL_ERROR",
                        message=str(e),
                        details={"operation": "get_available_strategies"},
                    )
                ],
            )

    def get_strategy_metadata(
        self, strategy_id: str
    ) -> StandardResponse[Dict[str, Any]]:
        # Retrieve detailed metadata for a specific strategy with comprehensive parameter information
        # Used by strategy detail endpoints and strategy configuration interfaces
        # Provides all information needed for strategy parameter form generation
        try:
            strategies = self.registry.get_available_strategies()

            # Validate strategy existence in registry
            if strategy_id not in strategies:
                available_strategies = list(strategies.keys())
                logger.warning(
                    f"Strategy '{strategy_id}' not found. Available strategies: {available_strategies}"
                )

                return create_error_response(
                    f"Strategy '{strategy_id}' not found in registry",
                    [
                        ApiError(
                            code="STRATEGY_NOT_FOUND",
                            message=f"Strategy '{strategy_id}' is not registered",
                            details={
                                "available_strategies": available_strategies,
                                "requested_strategy": strategy_id,
                            },
                        )
                    ],
                )

            # Extract and transform metadata for API response
            metadata = strategies[strategy_id]
            strategy_info = {
                "id": metadata.strategy_id,  # Strategy identifier
                "name": metadata.display_name,  # Display name for UI
                "description": metadata.description,  # Detailed strategy description
                "version": metadata.version,  # Version for compatibility tracking
                "author": metadata.author,  # Author information
                "category": metadata.category,  # Strategy category
                "risk_level": metadata.risk_level,  # Risk assessment
                "min_data_points": metadata.min_data_points,  # Data requirements
                "requires_indicators": metadata.requires_indicators,  # Technical indicator dependencies
                # Detailed parameter specifications for form generation
                "parameters": [
                    {
                        "name": param.name,  # Parameter name/key
                        "type": param.param_type.__name__,  # Data type for validation
                        "default": param.default,  # Default value
                        "min_value": param.min_value,  # Validation bounds
                        "max_value": param.max_value,
                        "description": param.description,  # Parameter explanation
                        "required": param.required,  # Validation requirement
                        "validation_rules": {  # Additional validation info
                            "type_validation": param.param_type.__name__,
                            "range_validation": param.min_value is not None
                            or param.max_value is not None,
                        },
                    }
                    for param in metadata.parameters
                ],
                # Additional metadata for strategy usage
                "usage_info": {
                    "complexity": "medium",  # Could be derived from parameters count
                    "execution_time": "standard",  # Could be estimated
                    "data_intensive": metadata.min_data_points > 100,
                },
            }

            return create_success_response(
                strategy_info,
                f"Retrieved detailed metadata for strategy '{strategy_id}'",
            )

        except Exception as e:
            logger.error(f"Failed to get strategy metadata for {strategy_id}: {e}")
            return create_error_response(
                f"Failed to retrieve metadata for strategy '{strategy_id}'",
                [
                    ApiError(
                        code="METADATA_RETRIEVAL_ERROR",
                        message=str(e),
                        details={
                            "strategy_id": strategy_id,
                            "operation": "get_strategy_metadata",
                        },
                    )
                ],
            )

    def validate_strategy_config(
        self, strategy_id: str, parameters: Dict[str, Any]
    ) -> StandardResponse[Dict[str, Any]]:
        # Comprehensive strategy configuration validation with parameter transformation
        # Validates both parameter structure and values, then transforms for C++ engine compatibility
        # Used by simulation validation endpoints and strategy testing interfaces
        try:
            # Verify strategy exists in registry
            available_strategies = self.registry.get_available_strategies()
            if strategy_id not in available_strategies:
                available_ids = list(available_strategies.keys())
                logger.warning(
                    f"Validation requested for unknown strategy '{strategy_id}'. Available: {available_ids}"
                )

                return create_error_response(
                    f"Strategy '{strategy_id}' not found for validation",
                    [
                        ApiError(
                            code="STRATEGY_NOT_FOUND",
                            message=f"Strategy '{strategy_id}' is not registered",
                            details={
                                "available_strategies": available_ids,
                                "validation_context": "strategy_config_validation",
                            },
                        )
                    ],
                )

            # Perform comprehensive parameter validation using registry
            validation_errors = self.registry.validate_strategy_config(
                strategy_id, parameters
            )

            if validation_errors:
                logger.info(
                    f"Strategy configuration validation failed for '{strategy_id}': {len(validation_errors)} errors"
                )

                # Create detailed error responses for each validation failure
                error_details = []
                for error in validation_errors:
                    error_details.append(
                        ApiError(
                            code="VALIDATION_FAILED",
                            message=error,
                            details={
                                "strategy_id": strategy_id,
                                "parameter_context": "validation",
                            },
                        )
                    )

                return create_error_response(
                    f"Strategy configuration validation failed for '{strategy_id}'",
                    error_details,
                )

            # Get strategy instance for parameter transformation
            strategy = self.registry.get_strategy(strategy_id)
            if not strategy:
                logger.error(
                    f"Failed to instantiate strategy '{strategy_id}' after successful validation"
                )
                return create_error_response(
                    f"Failed to instantiate strategy '{strategy_id}'",
                    [
                        ApiError(
                            code="STRATEGY_INSTANTIATION_ERROR",
                            message="Could not create strategy instance for parameter transformation",
                            details={
                                "strategy_id": strategy_id,
                                "validation_stage": "post_validation",
                            },
                        )
                    ],
                )

            # Transform parameters for C++ engine compatibility
            try:
                transformed_params = strategy.transform_parameters(parameters)
                logger.debug(
                    f"Successfully transformed parameters for strategy '{strategy_id}'"
                )
            except Exception as transform_error:
                logger.error(
                    f"Parameter transformation failed for '{strategy_id}': {transform_error}"
                )
                return create_error_response(
                    f"Parameter transformation failed for strategy '{strategy_id}'",
                    [
                        ApiError(
                            code="PARAMETER_TRANSFORMATION_ERROR",
                            message=str(transform_error),
                            details={
                                "strategy_id": strategy_id,
                                "original_parameters": parameters,
                            },
                        )
                    ],
                )

            # Return comprehensive validation success response
            return create_success_response(
                {
                    "strategy_id": strategy_id,
                    "original_parameters": parameters,
                    "transformed_parameters": transformed_params,
                    "validation_status": "passed",
                    "parameter_count": len(parameters),
                    "transformation_applied": True,
                    "engine_compatibility": "verified",
                },
                f"Strategy configuration for '{strategy_id}' validated and transformed successfully",
            )

        except Exception as e:
            logger.error(
                f"Unexpected error during strategy validation for '{strategy_id}': {e}"
            )
            return create_error_response(
                f"Strategy validation failed due to unexpected error",
                [
                    ApiError(
                        code="STRATEGY_VALIDATION_ERROR",
                        message=str(e),
                        details={
                            "strategy_id": strategy_id,
                            "error_type": type(e).__name__,
                            "validation_stage": "general",
                        },
                    )
                ],
            )

    def create_strategy_config(
        self, strategy_id: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Create C++ engine compatible strategy configuration from validated parameters
        # This method assumes parameters have already been validated and focuses on transformation
        # Used by simulation execution pipeline after successful validation
        try:
            # Get strategy instance from registry
            strategy = self.registry.get_strategy(strategy_id)
            if not strategy:
                logger.error(
                    f"Strategy '{strategy_id}' not found during configuration creation"
                )
                raise ValueError(f"Strategy '{strategy_id}' not found in registry")

            # Transform parameters to C++ engine format
            logger.debug(
                f"Creating C++ compatible configuration for strategy '{strategy_id}'"
            )
            transformed_config = strategy.transform_parameters(parameters)

            # Validate transformation result
            if not isinstance(transformed_config, dict):
                raise ValueError(
                    f"Strategy '{strategy_id}' transformation returned invalid format: {type(transformed_config)}"
                )

            logger.debug(
                f"Successfully created strategy configuration for '{strategy_id}': {list(transformed_config.keys())}"
            )
            return transformed_config

        except Exception as e:
            logger.error(f"Failed to create strategy config for '{strategy_id}': {e}")
            raise ValueError(
                f"Strategy configuration creation failed for '{strategy_id}': {str(e)}"
            )

    def refresh_strategies(self) -> StandardResponse[Dict[str, Any]]:
        # Refresh the strategy registry by discovering new strategies from configured paths
        # Scans for new plugin strategies and updates the registry with discovered strategies
        # Used by strategy refresh endpoints and periodic strategy discovery tasks
        try:
            # Capture initial state for comparison
            initial_strategies = self.registry.get_available_strategies()
            initial_count = len(initial_strategies)

            logger.info(
                f"Starting strategy registry refresh from {initial_count} strategies"
            )

            # Perform strategy discovery
            discovered_count = self.registry.discover_strategies()

            # Capture final state
            final_strategies = self.registry.get_available_strategies()
            final_count = len(final_strategies)

            # Calculate refresh statistics
            net_change = final_count - initial_count
            refresh_timestamp = __import__("time").time()

            # Identify newly discovered strategies
            new_strategy_ids = [
                sid for sid in final_strategies.keys() if sid not in initial_strategies
            ]

            logger.info(
                f"Strategy registry refresh completed: {discovered_count} scanned, "
                f"{net_change} net change, {final_count} total strategies"
            )

            return create_success_response(
                {
                    "discovered_strategies": discovered_count,  # Strategies processed during scan
                    "new_strategies": new_strategy_ids,  # Actually new strategy IDs
                    "total_strategies": final_count,  # Total strategies after refresh
                    "net_change": net_change,  # Change in total count
                    "refresh_timestamp": refresh_timestamp,  # Refresh completion time
                    "registry_status": "refreshed",  # Registry status
                    "scan_paths": len(
                        self.registry._strategy_paths
                    ),  # Number of paths scanned
                },
                f"Strategy registry refreshed successfully: {discovered_count} strategies scanned, "
                f"{len(new_strategy_ids)} new strategies discovered",
            )

        except Exception as e:
            logger.error(f"Failed to refresh strategy registry: {e}")
            return create_error_response(
                "Failed to refresh strategy registry",
                [
                    ApiError(
                        code="REGISTRY_REFRESH_ERROR",
                        message=str(e),
                        details={
                            "operation": "strategy_discovery",
                            "error_type": type(e).__name__,
                        },
                    )
                ],
            )


# Global strategy factory instance
# Singleton pattern ensures consistent strategy management state across the application
# Used by strategy routers, validation services, and simulation configuration
strategy_factory = StrategyFactory()


def get_strategy_factory() -> StrategyFactory:
    # Get the global strategy factory instance for dependency injection
    # Provides access to comprehensive strategy management capabilities
    return strategy_factory
