# Simulation Router - Trading Simulation Lifecycle Management Endpoints
# This module provides comprehensive API endpoints for trading simulation management
# Key responsibilities:
# - Simulation configuration validation and parameter checking
# - Simulation lifecycle management (start, monitor, cancel, complete)
# - Real-time simulation progress tracking and status monitoring
# - Simulation result retrieval and analysis
# - Memory usage monitoring and optimization analytics
# - Parallel and sequential simulation coordination
# - Error handling and validation for simulation operations
#
# Architecture Features:
# - RouterBase pattern for consistent endpoint structure and logging
# - Integration with SimulationEngine for comprehensive simulation orchestration
# - Dependency injection for SimulationValidator and repository access
# - Real-time progress tracking for both parallel and sequential simulations
# - Comprehensive validation with detailed error reporting
# - Memory statistics tracking for optimization analysis
# - Simulation cancellation support for long-running operations
#
# Endpoints Provided:
# - /simulation/validate: Validate simulation configuration without execution
# - /simulation/start: Start new simulation with automatic optimization
# - /simulation/{simulation_id}/status: Get real-time simulation status and progress
# - /simulation/{simulation_id}/results: Get complete simulation results with metrics
# - /simulation/{simulation_id}/memory: Get memory usage statistics and optimization data
# - /simulation/{simulation_id}/cancel: Cancel running simulation
# - /simulations: List all historical simulations with status
#
# Integration Points:
# - Uses SimulationEngine for simulation orchestration and execution
# - Integrates with SimulationValidator for configuration validation
# - Supports RouterBase pattern for consistent response formatting
# - Provides real-time progress tracking for monitoring systems

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

# Create router using RouterBase pattern for consistent simulation endpoint structure
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("simulation")
router = router_base.get_router()
router.tags = ["simulation"]

logger = logging.getLogger(__name__)

async def _validate_config(config: SimulationConfig, validator: SimulationValidator) -> ValidationResult:
    # Centralized validation logic for simulation configurations
    # Provides comprehensive parameter validation and error handling
    # Used by both validation and simulation start endpoints
    try:
        return await validator.validate_simulation_config(config)
    except Exception as e:
        logger.error(f"Validation system error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

def _handle_validation_warnings(validation_result: ValidationResult) -> None:
    # Log validation warnings for monitoring and user awareness
    # Provides visibility into potential simulation configuration issues
    # Used to inform users of non-critical configuration concerns
    if validation_result.warnings:
        for warning in validation_result.warnings:
            logger.warning(f"Simulation validation warning: {warning}")

@router.post("/simulation/validate", response_model=StandardResponse[ValidationResult])
async def validate_simulation_config(config: SimulationConfig, validator: SimulationValidator = Depends(get_simulation_validator)):
    # Validate simulation configuration without starting simulation execution
    # Performs comprehensive parameter validation including symbol existence and temporal checks
    # Returns detailed validation results with errors and warnings for configuration refinement
    validation_result = await _validate_config(config, validator)
    router_base.router_logger.log_request("/simulation/validate", {"symbols": len(config.symbols)})
    
    # Format validation response based on validation outcome
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
    # Start a new trading simulation with comprehensive validation and automatic optimization
    # Validates configuration, starts simulation execution, and returns simulation ID for tracking
    # Supports both parallel and sequential execution based on optimization analysis
    try:
        # Perform comprehensive configuration validation before simulation start
        validation_result = await _validate_config(config, validator)
        
        # Handle validation failures with detailed error reporting
        if not validation_result.is_valid:
            error_messages = [f"{error.field}: {error.message}" for error in validation_result.errors]
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Validation failed",
                    "errors": error_messages,
                    "error_details": [error.model_dump() for error in validation_result.errors]
                }
            )
        
        # Log validation warnings for user awareness
        _handle_validation_warnings(validation_result)
        
        # Start simulation execution with automatic optimization
        simulation_id = await simulation_engine.start_simulation(config)
        
        # Create simulation response with warning information
        message = "Simulation started successfully"
        if validation_result.warnings:
            message += f" (with {len(validation_result.warnings)} warnings)"
        
        response_data = SimulationResponse(
            simulation_id=simulation_id,
            status="pending",
            message=message
        )
        
        # Format response with warnings if present
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
        # Re-raise HTTP exceptions for proper error handling
        raise
    except Exception as e:
        # Handle unexpected simulation start errors
        logger.error(f"Unexpected error starting simulation: {e}")
        router_base.router_logger.log_error("/simulation/start", e, "SIMULATION_START_ERROR")
        return router_base.response_formatter.create_error_response(
            "Failed to start simulation",
            [ApiError(code="SIMULATION_START_ERROR", message=str(e))]
        )

@router.get("/simulation/{simulation_id}/status", response_model=StandardResponse[SimulationStatusResponse])
async def get_simulation_status(simulation_id: str):
    # Get real-time simulation status and progress for both parallel and sequential simulations
    # Returns comprehensive progress information including completion percentage and timing
    # Supports progress aggregation for parallel execution with multiple symbol groups
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
    # Get comprehensive simulation results including performance metrics and optimization data
    # Returns complete simulation analysis with trading statistics and execution metadata
    # Includes optimization information for parallel execution analysis
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

@router.get("/simulation/{simulation_id}/memory", response_model=StandardResponse[Dict])
async def get_simulation_memory_statistics(simulation_id: str):
    # Get comprehensive memory usage statistics and optimization analytics for simulation
    # Returns memory timeline data, optimization correlation, and efficiency analysis
    # Used for performance monitoring and memory optimization insights
    result = simulation_engine.get_simulation_status(simulation_id)
    
    router_base.router_logger.log_request(f"/simulation/{simulation_id}/memory", {"simulation_id": simulation_id})
    
    if not result:
        response = router_base.response_formatter.create_not_found_response(
            "Simulation", simulation_id, "simulation_id"
        )
        router_base.router_logger.log_error(f"/simulation/{simulation_id}/memory", 
                                          Exception("Simulation not found"), "SIMULATION_NOT_FOUND")
        return response
    
    # Extract and process memory statistics from simulation results
    memory_stats = result.memory_statistics if hasattr(result, 'memory_statistics') and result.memory_statistics else None
    
    if not memory_stats:
        # Return structured response when no memory data is available
        memory_response = {
            "simulation_id": simulation_id,
            "status": "no_memory_data",
            "message": "No memory statistics available for this simulation",
            "simulation_status": result.status.value if hasattr(result, 'status') else "unknown"
        }
    else:
        # Return comprehensive memory statistics with analysis metadata
        memory_response = {
            "simulation_id": simulation_id,
            "status": "success", 
            "simulation_status": result.status.value if hasattr(result, 'status') else "unknown",
            "memory_statistics": memory_stats,
            "summary": {
                "has_timeline": "timeline" in memory_stats if isinstance(memory_stats, dict) else False,
                "has_analysis": "analysis" in memory_stats if isinstance(memory_stats, dict) else False,
                "tracking_status": memory_stats.get("status") if isinstance(memory_stats, dict) else "unknown"
            }
        }
    
    response = router_base.response_formatter.create_success_response(
        memory_response, 
        "Memory statistics retrieved successfully" if memory_stats else "No memory data available"
    )
    router_base.router_logger.log_success(f"/simulation/{simulation_id}/memory")
    return response

@router.get("/simulation/{simulation_id}/cancel")
async def cancel_simulation(simulation_id: str) -> StandardResponse[Dict[str, str]]:
    # Cancel a running simulation with support for both parallel and sequential execution
    # Performs graceful shutdown and cleanup of simulation resources
    # Returns cancellation status and cleanup confirmation
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
    # List all historical simulations with comprehensive status and performance information
    # Returns simulation history with execution metadata, performance metrics, and optimization data
    # Used for simulation monitoring, analysis, and historical performance tracking
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
        # Handle simulation listing errors with comprehensive error reporting
        router_base.router_logger.log_error("/simulations", e, "SIMULATION_LIST_ERROR")
        return router_base.response_formatter.create_error_response(
            "Failed to list simulations",
            [ApiError(code="SIMULATION_LIST_ERROR", message=str(e))]
        )