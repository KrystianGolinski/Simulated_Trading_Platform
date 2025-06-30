# Dynamic Strategy Management API Router
from fastapi import APIRouter
from typing import Dict, Any, List
from strategy_factory import get_strategy_factory
from response_models import StandardResponse
from base_router import BaseRouter

router = APIRouter(tags=["strategies"])

class StrategiesRouter(BaseRouter):
    # Inherits from BaseRouter - no additional functionality needed
    pass

strategies_router = StrategiesRouter()

@router.get("/strategies")
async def get_available_strategies() -> StandardResponse[Dict[str, Any]]:
    # Get all available trading strategies with metadata
    factory = get_strategy_factory()
    return factory.get_available_strategies()

@router.get("/strategies/{strategy_id}")
async def get_strategy_metadata(strategy_id: str) -> StandardResponse[Dict[str, Any]]:
    # Get detailed metadata for a specific strategy
    factory = get_strategy_factory()
    return factory.get_strategy_metadata(strategy_id)

@router.post("/strategies/{strategy_id}/validate")
async def validate_strategy_configuration(
    strategy_id: str, 
    parameters: Dict[str, Any]
) -> StandardResponse[Dict[str, Any]]:
    # Validate strategy configuration parameters
    factory = get_strategy_factory()
    return factory.validate_strategy_config(strategy_id, parameters)

@router.post("/strategies/refresh")
async def refresh_strategy_registry() -> StandardResponse[Dict[str, Any]]:
    # Refresh strategy registry to discover new strategies
    factory = get_strategy_factory()
    return factory.refresh_strategies()

@router.get("/strategies/categories")
async def get_strategy_categories() -> StandardResponse[Dict[str, Any]]:
    # Get strategy categories for filtering and organization
    factory = get_strategy_factory()
    strategies_result = factory.get_available_strategies()
    
    if not strategies_result.success or not strategies_result.data:
        return strategies_result
    
    # Check if strategies key exists in the response data
    if "strategies" not in strategies_result.data:
        return strategies_router.create_error(
            "INVALID_RESPONSE_FORMAT",
            "Missing 'strategies' key in response data"
        )
    
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
    
    return strategies_router.create_success_with_metadata(
        {"categories": list(categories.values())},
        f"Retrieved {len(categories)} strategy categories"
    )