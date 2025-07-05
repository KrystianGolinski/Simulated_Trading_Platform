# Dynamic Strategy Management API Router
from fastapi import APIRouter
from typing import Dict, Any, List
from strategy_factory import get_strategy_factory
from models import StandardResponse, ApiError
from routing import get_router_service_factory

# Create router using RouterBase pattern
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("strategies")
router = router_base.get_router()
router.tags = ["strategies"]

@router.get("/strategies")
async def get_available_strategies() -> StandardResponse[Dict[str, Any]]:
    # Get all available trading strategies with metadata
    router_base.router_logger.log_request("/strategies", {})
    
    factory = get_strategy_factory()
    result = factory.get_available_strategies()
    
    if result.success:
        router_base.router_logger.log_success("/strategies")
    else:
        router_base.router_logger.log_error("/strategies", Exception("Failed to get strategies"), "STRATEGY_ERROR")
    
    return result

@router.get("/strategies/{strategy_id}")
async def get_strategy_metadata(strategy_id: str) -> StandardResponse[Dict[str, Any]]:
    # Get detailed metadata for a specific strategy
    router_base.router_logger.log_request(f"/strategies/{strategy_id}", {"strategy_id": strategy_id})
    
    factory = get_strategy_factory()
    result = factory.get_strategy_metadata(strategy_id)
    
    if result.success:
        router_base.router_logger.log_success(f"/strategies/{strategy_id}")
    else:
        router_base.router_logger.log_error(f"/strategies/{strategy_id}", 
                                          Exception(f"Strategy {strategy_id} not found"), "STRATEGY_NOT_FOUND")
    
    return result

@router.post("/strategies/{strategy_id}/validate")
async def validate_strategy_configuration(
    strategy_id: str, 
    parameters: Dict[str, Any]
) -> StandardResponse[Dict[str, Any]]:
    # Validate strategy configuration parameters
    router_base.router_logger.log_request(f"/strategies/{strategy_id}/validate", 
                                        {"strategy_id": strategy_id, "param_count": len(parameters)})
    
    factory = get_strategy_factory()
    result = factory.validate_strategy_config(strategy_id, parameters)
    
    if result.success:
        router_base.router_logger.log_success(f"/strategies/{strategy_id}/validate")
    else:
        router_base.router_logger.log_error(f"/strategies/{strategy_id}/validate", 
                                          Exception("Strategy validation failed"), "VALIDATION_FAILED")
    
    return result

@router.post("/strategies/refresh")
async def refresh_strategy_registry() -> StandardResponse[Dict[str, Any]]:
    # Refresh strategy registry to discover new strategies
    router_base.router_logger.log_request("/strategies/refresh", {})
    
    factory = get_strategy_factory()
    result = factory.refresh_strategies()
    
    if result.success:
        router_base.router_logger.log_success("/strategies/refresh")
    else:
        router_base.router_logger.log_error("/strategies/refresh", 
                                          Exception("Strategy refresh failed"), "REFRESH_FAILED")
    
    return result

@router.get("/strategies/categories")
async def get_strategy_categories() -> StandardResponse[Dict[str, Any]]:
    # Get strategy categories for filtering and organization
    factory = get_strategy_factory()
    strategies_result = factory.get_available_strategies()
    
    if not strategies_result.success or not strategies_result.data:
        return strategies_result
    
    # Check if strategies key exists in the response data
    if "strategies" not in strategies_result.data:
        response = router_base.response_formatter.create_error_response(
            "Missing 'strategies' key in response data",
            [ApiError(code="INVALID_RESPONSE_FORMAT", message="Missing 'strategies' key in response data")]
        )
        router_base.router_logger.log_error("/strategies/categories", 
                                          Exception("Invalid response format"), "INVALID_RESPONSE_FORMAT")
        return response
    
    categories = {}
    for strategy in strategies_result.data["strategies"]:
        category = strategy["category"]
        if category not in categories:
            categories[category] = {
                "name": category,
                "strategies": [],
                "count": 0
            }
        
        categories[category]["strategies"].append({
            "id": strategy["id"],
            "name": strategy["name"],
            "risk_level": strategy["risk_level"]
        })
        categories[category]["count"] += 1
    
    router_base.router_logger.log_request("/strategies/categories", {})
    response = router_base.response_formatter.create_success_with_metadata(
        {"categories": list(categories.values())},
        f"Retrieved {len(categories)} strategy categories",
        total_categories=len(categories)
    )
    router_base.router_logger.log_success("/strategies/categories", len(categories))
    return response