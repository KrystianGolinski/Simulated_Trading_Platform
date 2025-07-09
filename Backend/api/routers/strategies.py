# Strategies Router - Trading Strategy Management and Discovery Endpoints
# This module provides API endpoints for trading strategy management and configuration
# Key responsibilities:
# - Trading strategy discovery and metadata retrieval
# - Strategy configuration validation and parameter management
# - Strategy registry refresh and plugin discovery
# - Strategy categorization and filtering support
# - Strategy factory integration for dynamic strategy loading
# - Configuration validation with detailed error reporting
# - Strategy metadata exposure for client applications
#
# Architecture Features:
# - RouterBase pattern for consistent endpoint structure and logging
# - Integration with StrategyFactory for strategy management operations
# - Dynamic strategy discovery and plugin support
# - Comprehensive parameter validation with detailed error messages
# - Strategy categorization for organized strategy selection
# - Real-time strategy registry refresh capability
# - Structured response formatting for strategy metadata
#
# Endpoints Provided:
# - /strategies: Get all available strategies with metadata
# - /strategies/{strategy_id}: Get detailed metadata for specific strategy
# - /strategies/{strategy_id}/validate: Validate strategy configuration parameters
# - /strategies/refresh: Refresh strategy registry for new plugin discovery
# - /strategies/categories: Get strategy categories for filtering and organization
#
# Integration Points:
# - Uses StrategyFactory for strategy management and validation operations
# - Integrates with strategy registry for plugin discovery
# - Supports RouterBase pattern for consistent response formatting
# - Provides validation integration for simulation configuration

from typing import Any, Dict, List

from fastapi import APIRouter

from models import ApiError, StandardResponse
from routing import get_router_service_factory
from strategy_factory import get_strategy_factory

# Create router using RouterBase pattern for consistent strategy endpoint structure
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("strategies")
router = router_base.get_router()
router.tags = ["strategies"]


@router.get("/strategies")
async def get_available_strategies() -> StandardResponse[Dict[str, Any]]:
    # Get comprehensive list of all available trading strategies with detailed metadata
    # Returns strategy information including parameters, categories, and requirements
    # Used by client applications for strategy selection and configuration
    router_base.log_request("/strategies")

    factory = get_strategy_factory()
    result = factory.get_available_strategies()

    if result.success:
        router_base.router_logger.log_success("/strategies")
    else:
        router_base.router_logger.log_error(
            "/strategies", Exception("Failed to get strategies"), "STRATEGY_ERROR"
        )

    return result


@router.get("/strategies/{strategy_id}")
async def get_strategy_metadata(strategy_id: str) -> StandardResponse[Dict[str, Any]]:
    # Get comprehensive metadata for a specific trading strategy
    # Returns detailed information including parameters, validation rules, and requirements
    # Used for strategy configuration UI and parameter validation
    router_base.log_request(f"/strategies/{strategy_id}", {"strategy_id": strategy_id})

    factory = get_strategy_factory()
    result = factory.get_strategy_metadata(strategy_id)

    if result.success:
        router_base.router_logger.log_success(f"/strategies/{strategy_id}")
    else:
        router_base.router_logger.log_error(
            f"/strategies/{strategy_id}",
            Exception(f"Strategy {strategy_id} not found"),
            "STRATEGY_NOT_FOUND",
        )

    return result


@router.post("/strategies/{strategy_id}/validate")
async def validate_strategy_configuration(
    strategy_id: str, parameters: Dict[str, Any]
) -> StandardResponse[Dict[str, Any]]:
    # Validate strategy configuration parameters against strategy requirements
    # Performs comprehensive parameter validation including type checking and business rules
    # Returns validation results with detailed error messages for invalid configurations
    router_base.log_request(
        f"/strategies/{strategy_id}/validate",
        {"strategy_id": strategy_id, "param_count": len(parameters)},
    )

    factory = get_strategy_factory()
    result = factory.validate_strategy_config(strategy_id, parameters)

    if result.success:
        router_base.router_logger.log_success(f"/strategies/{strategy_id}/validate")
    else:
        router_base.router_logger.log_error(
            f"/strategies/{strategy_id}/validate",
            Exception("Strategy validation failed"),
            "VALIDATION_FAILED",
        )

    return result


@router.post("/strategies/refresh")
async def refresh_strategy_registry() -> StandardResponse[Dict[str, Any]]:
    # Refresh strategy registry to discover newly added strategies and plugins
    # Scans strategy directories and plugin locations for new strategy implementations
    # Used for dynamic strategy loading without system restart
    router_base.log_request("/strategies/refresh")

    factory = get_strategy_factory()
    result = factory.refresh_strategies()

    if result.success:
        router_base.router_logger.log_success("/strategies/refresh")
    else:
        router_base.router_logger.log_error(
            "/strategies/refresh",
            Exception("Strategy refresh failed"),
            "REFRESH_FAILED",
        )

    return result


@router.get("/strategies/categories")
async def get_strategy_categories() -> StandardResponse[Dict[str, Any]]:
    # Get strategy categories with organized strategy groupings for filtering and selection
    # Returns categorized strategies with counts and metadata for UI organization
    # Enables strategy filtering by category (trend_following, momentum, mean_reversion, etc.)
    factory = get_strategy_factory()
    strategies_result = factory.get_available_strategies()

    # Validate strategy data retrieval and format
    if not strategies_result.success or not strategies_result.data:
        return strategies_result

    # Validate response structure for proper category processing
    if "strategies" not in strategies_result.data:
        response = router_base.response_formatter.create_error_response(
            "Missing 'strategies' key in response data",
            [
                ApiError(
                    code="INVALID_RESPONSE_FORMAT",
                    message="Missing 'strategies' key in response data",
                )
            ],
        )
        router_base.router_logger.log_error(
            "/strategies/categories",
            Exception("Invalid response format"),
            "INVALID_RESPONSE_FORMAT",
        )
        return response

    # Process strategies into organized category structure
    categories = {}
    for strategy in strategies_result.data["strategies"]:
        category = strategy["category"]
        if category not in categories:
            categories[category] = {"name": category, "strategies": [], "count": 0}

        # Add strategy summary to category with essential information
        categories[category]["strategies"].append(
            {
                "id": strategy["id"],
                "name": strategy["name"],
                "risk_level": strategy["risk_level"],
            }
        )
        categories[category]["count"] += 1

    # Format and return categorized strategy response with metadata
    router_base.log_request("/strategies/categories")
    response = router_base.response_formatter.create_success_with_metadata(
        {"categories": list(categories.values())},
        f"Retrieved {len(categories)} strategy categories",
        total_categories=len(categories),
    )
    router_base.router_logger.log_success("/strategies/categories", len(categories))
    return response
