from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
import logging

from dependencies import get_simulation_validator
from models import (
    SimulationConfig, 
    SimulationResponse, 
    SimulationResults, 
    SimulationStatusResponse,
    ValidationResult
)
from simulation_engine import simulation_engine
from validation import SimulationValidator
from models import StandardResponse, ApiError
from routing import get_router_service_factory

# Create router using RouterBase pattern
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("simulation")
router = router_base.get_router()
router.tags = ["simulation"]

logger = logging.getLogger(__name__)

async def _validate_config(config: SimulationConfig, validator: SimulationValidator) -> ValidationResult:
    # Centralized validation logic for simulation configurations
    try:
        return await validator.validate_simulation_config(config)
    except Exception as e:
        logger.error(f"Validation system error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

def _handle_validation_warnings(validation_result: ValidationResult) -> None:
    # Log validation warnings if present
    if validation_result.warnings:
        for warning in validation_result.warnings:
            logger.warning(f"Simulation validation warning: {warning}")

@router.post("/simulation/validate", response_model=StandardResponse[ValidationResult])
async def validate_simulation_config(config: SimulationConfig, validator: SimulationValidator = Depends(get_simulation_validator)):
    # Validate simulation configuration without starting simulation
    validation_result = await _validate_config(config, validator)
    router_base.router_logger.log_request("/simulation/validate", {"symbols": len(config.symbols)})
    
    if validation_result.is_valid:
        response = router_base.response_formatter.create_success_response(validation_result, "Configuration is valid")
        router_base.router_logger.log_success("/simulation/validate")
        return response
    else:
        response = router_base.response_formatter.create_error_response(
            "Validation failed",
            [ApiError(code=error.error_code, message=error.message, field=error.field) for error in validation_result.errors]
        )
        router_base.router_logger.log_error("/simulation/validate", Exception("Validation failed"), "VALIDATION_FAILED")
        return response

@router.post("/simulation/start", response_model=StandardResponse[SimulationResponse])
async def start_simulation(config: SimulationConfig, validator: SimulationValidator = Depends(get_simulation_validator)):
    # Start a new trading simulation with validation
    try:
        # Validate configuration
        validation_result = await _validate_config(config, validator)
        
        if not validation_result.is_valid:
            # Return validation errors
            error_messages = [f"{error.field}: {error.message}" for error in validation_result.errors]
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Validation failed",
                    "errors": error_messages,
                    "error_details": [error.model_dump() for error in validation_result.errors]
                }
            )
        
        # Handle warnings
        _handle_validation_warnings(validation_result)
        
        # Start simulation
        simulation_id = await simulation_engine.start_simulation(config)
        
        message = "Simulation started successfully"
        if validation_result.warnings:
            message += f" (with {len(validation_result.warnings)} warnings)"
        
        response_data = SimulationResponse(
            simulation_id=simulation_id,
            status="pending",
            message=message
        )
        
        if validation_result.warnings:
            response = router_base.response_formatter.create_success_with_metadata(
                response_data,
                message,
                warnings=validation_result.warnings
            )
        else:
            response = router_base.response_formatter.create_success_response(response_data, message)
        
        router_base.router_logger.log_success("/simulation/start")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error starting simulation: {e}")
        router_base.router_logger.log_error("/simulation/start", e, "SIMULATION_START_ERROR")
        return router_base.response_formatter.create_error_response(
            "Failed to start simulation",
            [ApiError(code="SIMULATION_START_ERROR", message=str(e))]
        )

@router.get("/simulation/{simulation_id}/status", response_model=StandardResponse[SimulationStatusResponse])
async def get_simulation_status(simulation_id: str):
    # Get the current status of a simulation
    progress = simulation_engine.get_simulation_progress(simulation_id)
    
    router_base.router_logger.log_request(f"/simulation/{simulation_id}/status", {"simulation_id": simulation_id})
    
    if "error" in progress:
        response = router_base.response_formatter.create_not_found_response(
            "Simulation", simulation_id, "simulation_id"
        )
        router_base.router_logger.log_error(f"/simulation/{simulation_id}/status", 
                                          Exception("Simulation not found"), "SIMULATION_NOT_FOUND")
        return response
    
    # Handle case where execution service doesn't have the simulation (completed/failed simulations)
    if progress.get("status") == "not_found":
        # Check if simulation exists in result processor
        result = simulation_engine.get_simulation_status(simulation_id)
        if not result:
            response = router_base.response_formatter.create_not_found_response(
                "Simulation", simulation_id, "simulation_id"
            )
            router_base.router_logger.log_error(f"/simulation/{simulation_id}/status", 
                                              Exception("Simulation not found"), "SIMULATION_NOT_FOUND")
            return response
        
        # Convert result to progress format
        progress = {
            "simulation_id": simulation_id,
            "status": result.status.value,
            "progress_pct": 100.0 if result.status.value == "completed" else 0.0,
            "current_date": None,
            "elapsed_time": (result.completed_at - result.started_at).total_seconds() if result.completed_at and result.started_at else None,
            "estimated_remaining": None
        }
    else:
        # Add simulation_id to the progress data
        progress["simulation_id"] = simulation_id
    
    status_response = SimulationStatusResponse(**progress)
    response = router_base.response_formatter.create_success_response(status_response, "Simulation status retrieved successfully")
    router_base.router_logger.log_success(f"/simulation/{simulation_id}/status")
    return response

@router.get("/simulation/{simulation_id}/results", response_model=StandardResponse[SimulationResults])
async def get_simulation_results(simulation_id: str):
    # Get the complete results of a simulation
    result = simulation_engine.get_simulation_status(simulation_id)
    
    router_base.router_logger.log_request(f"/simulation/{simulation_id}/results", {"simulation_id": simulation_id})
    
    if not result:
        response = router_base.response_formatter.create_not_found_response(
            "Simulation", simulation_id, "simulation_id"
        )
        router_base.router_logger.log_error(f"/simulation/{simulation_id}/results", 
                                          Exception("Simulation not found"), "SIMULATION_NOT_FOUND")
        return response
    
    response = router_base.response_formatter.create_success_response(result, "Simulation results retrieved successfully")
    router_base.router_logger.log_success(f"/simulation/{simulation_id}/results")
    return response

@router.get("/simulation/{simulation_id}/cancel")
async def cancel_simulation(simulation_id: str) -> StandardResponse[Dict[str, str]]:
    # Cancel a running simulation
    success = await simulation_engine.cancel_simulation(simulation_id)
    
    router_base.router_logger.log_request(f"/simulation/{simulation_id}/cancel", {"simulation_id": simulation_id})
    
    if not success:
        response = router_base.response_formatter.create_error_response(
            "Failed to cancel simulation",
            [ApiError(code="SIMULATION_CANCEL_FAILED", message="Failed to cancel simulation or simulation not running", field="simulation_id")]
        )
        router_base.router_logger.log_error(f"/simulation/{simulation_id}/cancel", 
                                          Exception("Cancel failed"), "SIMULATION_CANCEL_FAILED")
        return response
    
    response = router_base.response_formatter.create_success_response(
        {"status": "cancelled"},
        "Simulation cancelled successfully"
    )
    router_base.router_logger.log_success(f"/simulation/{simulation_id}/cancel")
    return response

@router.get("/simulations", response_model=StandardResponse[Dict[str, SimulationResults]])
async def list_simulations():
    # List all simulations with status
    try:
        simulations = simulation_engine.list_simulations()
        response = router_base.response_formatter.create_success_with_metadata(
            simulations,
            f"Retrieved {len(simulations)} simulations",
            count=len(simulations)
        )
        router_base.router_logger.log_success("/simulations", len(simulations))
        return response
    except Exception as e:
        router_base.router_logger.log_error("/simulations", e, "SIMULATION_LIST_ERROR")
        return router_base.response_formatter.create_error_response(
            "Failed to list simulations",
            [ApiError(code="SIMULATION_LIST_ERROR", message=str(e))]
        )