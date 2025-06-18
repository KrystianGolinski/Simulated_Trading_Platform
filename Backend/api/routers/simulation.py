from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

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

router = APIRouter(tags=["simulation"])

@router.post("/simulation/validate", response_model=ValidationResult)
async def validate_simulation_config(config: SimulationConfig, db: DatabaseManager = Depends(get_database)):
    """Validate simulation configuration without starting simulation"""
    try:
        validator = SimulationValidator(db)
        validation_result = await validator.validate_simulation_config(config)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/simulation/start", response_model=SimulationResponse)
async def start_simulation(config: SimulationConfig, db: DatabaseManager = Depends(get_database)):
    """Start a new trading simulation with comprehensive validation"""
    try:
        # Phase 3: Comprehensive validation
        validator = SimulationValidator(db)
        validation_result = await validator.validate_simulation_config(config)
        
        if not validation_result.is_valid:
            # Return detailed validation errors
            error_messages = [f"{error.field}: {error.message}" for error in validation_result.errors]
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Validation failed",
                    "errors": error_messages,
                    "error_details": [error.dict() for error in validation_result.errors]
                }
            )
        
        # Log warnings if any
        if validation_result.warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in validation_result.warnings:
                logger.warning(f"Simulation validation warning: {warning}")
        
        # Start simulation if validation passes
        simulation_id = await simulation_engine.start_simulation(config)
        
        message = "Simulation started successfully"
        if validation_result.warnings:
            message += f" (with {len(validation_result.warnings)} warnings)"
        
        return SimulationResponse(
            simulation_id=simulation_id,
            status="pending",
            message=message
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Handle unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error starting simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")

@router.get("/simulation/{simulation_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(simulation_id: str):
    """Get the current status of a simulation"""
    progress = simulation_engine.get_simulation_progress(simulation_id)
    
    if "error" in progress:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return SimulationStatusResponse(**progress)

@router.get("/simulation/{simulation_id}/results", response_model=SimulationResults)
async def get_simulation_results(simulation_id: str):
    """Get the complete results of a simulation"""
    result = simulation_engine.get_simulation_status(simulation_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return result

@router.get("/simulation/{simulation_id}/cancel")
async def cancel_simulation(simulation_id: str):
    """Cancel a running simulation"""
    success = await simulation_engine.cancel_simulation(simulation_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel simulation or simulation not running")
    
    return {"message": "Simulation cancelled successfully"}

@router.get("/simulations", response_model=Dict[str, SimulationResults])
async def list_simulations():
    """List all simulations and their status"""
    return simulation_engine.list_simulations()