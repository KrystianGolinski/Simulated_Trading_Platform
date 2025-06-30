from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
import logging

from database import DatabaseManager, get_database
from models import (
    SimulationConfig, 
    SimulationResponse, 
    SimulationResults, 
    SimulationStatusResponse,
    ValidationResult
)
from simulation_engine import simulation_engine
from validation import SimulationValidator
from response_models import StandardResponse, create_success_response, create_error_response, create_warning_response, ApiError
from base_router import BaseRouter

router = APIRouter(tags=["simulation"])
logger = logging.getLogger(__name__)

class SimulationRouter(BaseRouter):
    # Simulation router with standardized error handling and validation
    pass

simulation_router = SimulationRouter()

async def _validate_config(config: SimulationConfig, db: DatabaseManager) -> ValidationResult:
    # Centralized validation logic for simulation configurations
    try:
        validator = SimulationValidator(db)
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
async def validate_simulation_config(config: SimulationConfig, db: DatabaseManager = Depends(get_database)):
    # Validate simulation configuration without starting simulation
    validation_result = await _validate_config(config, db)
    return simulation_router.handle_validation_result(validation_result, "Configuration is valid")

@router.post("/simulation/start", response_model=StandardResponse[SimulationResponse])
async def start_simulation(config: SimulationConfig, db: DatabaseManager = Depends(get_database)):
    # Start a new trading simulation with validation
    try:
        # Validate configuration
        validation_result = await _validate_config(config, db)
        
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
            return create_warning_response(
                response_data,
                message,
                validation_result.warnings
            )
        else:
            return create_success_response(response_data, message)
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error starting simulation: {e}")
        return create_error_response(
            "Failed to start simulation",
            [ApiError(code="SIMULATION_START_ERROR", message=str(e))]
        )

@router.get("/simulation/{simulation_id}/status", response_model=StandardResponse[SimulationStatusResponse])
async def get_simulation_status(simulation_id: str):
    # Get the current status of a simulation
    progress = simulation_engine.get_simulation_progress(simulation_id)
    
    if "error" in progress:
        return create_error_response(
            "Simulation not found",
            [ApiError(code="SIMULATION_NOT_FOUND", message="Simulation not found", field="simulation_id")]
        )
    
    # Handle case where execution service doesn't have the simulation (completed/failed simulations)
    if progress.get("status") == "not_found":
        # Check if simulation exists in result processor
        result = simulation_engine.get_simulation_status(simulation_id)
        if not result:
            return create_error_response(
                "Simulation not found",
                [ApiError(code="SIMULATION_NOT_FOUND", message="Simulation not found", field="simulation_id")]
            )
        
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
    return create_success_response(status_response, "Simulation status retrieved successfully")

@router.get("/simulation/{simulation_id}/results", response_model=StandardResponse[SimulationResults])
async def get_simulation_results(simulation_id: str):
    # Get the complete results of a simulation
    result = simulation_engine.get_simulation_status(simulation_id)
    
    if not result:
        return create_error_response(
            "Simulation not found",
            [ApiError(code="SIMULATION_NOT_FOUND", message="Simulation not found", field="simulation_id")]
        )
    
    return create_success_response(result, "Simulation results retrieved successfully")

@router.get("/simulation/{simulation_id}/cancel")
async def cancel_simulation(simulation_id: str) -> StandardResponse[Dict[str, str]]:
    # Cancel a running simulation
    success = await simulation_engine.cancel_simulation(simulation_id)
    
    if not success:
        return create_error_response(
            "Failed to cancel simulation",
            [ApiError(code="SIMULATION_CANCEL_FAILED", message="Failed to cancel simulation or simulation not running", field="simulation_id")]
        )
    
    return create_success_response(
        {"status": "cancelled"},
        "Simulation cancelled successfully"
    )

@router.get("/simulations", response_model=StandardResponse[Dict[str, SimulationResults]])
async def list_simulations():
    # List all simulations with status
    try:
        simulations = simulation_engine.list_simulations()
        return create_success_response(
            simulations,
            f"Retrieved {len(simulations)} simulations",
            metadata={"count": len(simulations)}
        )
    except Exception as e:
        return create_error_response(
            "Failed to list simulations",
            [ApiError(code="SIMULATION_LIST_ERROR", message=str(e))]
        )