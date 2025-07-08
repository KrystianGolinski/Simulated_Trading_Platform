# Engine Router - C++ Trading Engine Integration and Testing Endpoints
# This module provides API endpoints for C++ trading engine integration and testing
# Key responsibilities:
# - C++ trading engine connectivity testing and validation
# - Engine status monitoring and health checks
# - Integration testing for simulation execution capability
# - Engine path validation and accessibility verification
# - Docker container engine detection and testing
# - Engine output capture and analysis for debugging
# - System integration validation for the C++ trading engine
#
# Architecture Features:
# - RouterBase pattern for consistent endpoint structure
# - Direct subprocess integration with C++ trading engine
# - Engine path detection across multiple deployment scenarios
# - Comprehensive error handling for engine connectivity issues
# - Structured logging for engine operations and testing
# - Docker-aware engine path resolution
# - Timeout handling for engine execution safety
#
# Endpoints Provided:
# - /engine/test: Execute test simulation to validate engine functionality
# - /engine/status: Get engine status, path information, and accessibility
#
# Integration Points:
# - Integrates with simulation_engine for engine path management
# - Uses RouterBase pattern for consistent response formatting
# - Provides engine validation for simulation system health checks
# - Supports Docker-based deployment with container-aware path resolution

from fastapi import APIRouter
import subprocess
import os
from pathlib import Path
from typing import Dict, Any

from simulation_engine import simulation_engine
from models import StandardResponse, ApiError
from routing import get_router_service_factory

# Create router using RouterBase pattern for consistent endpoint structure
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("engine")
router = router_base.get_router()
router.tags = ["engine"]

@router.get("/engine/test")
async def test_engine() -> StandardResponse[Dict[str, Any]]:
    # Execute test simulation with C++ trading engine to validate functionality
    # Runs a sample AAPL simulation to verify engine connectivity and basic operation
    # Returns comprehensive test results including stdout, stderr, and return codes
    engine_path = Path("/app/cpp-engine/build/trading_engine")
    router_base.router_logger.log_request("/engine/test", {})
    
    # Validate engine binary exists and is accessible
    if not engine_path.exists():
        response = router_base.response_formatter.create_error_response(
            f"Engine not found at {engine_path}",
            [ApiError(code="ENGINE_NOT_FOUND", message=f"Engine binary not found at {engine_path}", field="engine_path")]
        )
        router_base.router_logger.log_error("/engine/test", Exception("Engine not found"), "ENGINE_NOT_FOUND")
        return response
    
    try:
        # Execute test simulation with timeout protection to prevent hanging
        result = subprocess.run([str(engine_path), "--simulate", "--symbol", "AAPL", "--start", "2023-01-01", "--end", "2023-01-31", "--capital", "10000"], 
                              capture_output=True, text=True, timeout=30)
        
        # Create comprehensive test result data for analysis
        test_data = {
            "command": f"{engine_path} --simulate --symbol AAPL --start 2023-01-01 --end 2023-01-31 --capital 10000",
            "return_code": result.returncode,
            "stdout": result.stdout[:2000],  # Limit output to prevent response bloat
            "stderr": result.stderr[:1000]   # Capture error output for debugging
        }
        
        # Analyze test execution results and format appropriate response
        if result.returncode == 0:
            response = router_base.response_formatter.create_success_response(test_data, "Engine test completed successfully")
            router_base.router_logger.log_success("/engine/test")
            return response
        else:
            response = router_base.response_formatter.create_error_response(
                "Engine test failed",
                [ApiError(code="ENGINE_TEST_FAILED", message=f"Engine returned code {result.returncode}")]
            )
            router_base.router_logger.log_error("/engine/test", Exception(f"Engine returned code {result.returncode}"), "ENGINE_TEST_FAILED")
            return response
    except Exception as e:
        # Handle execution errors including timeouts and subprocess failures
        router_base.router_logger.log_error("/engine/test", e, "ENGINE_TEST_ERROR")
        return router_base.response_formatter.create_error_response(
            "Engine test error",
            [ApiError(code="ENGINE_TEST_ERROR", message=str(e))]
        )

@router.get("/engine/status")
async def get_engine_status() -> StandardResponse[Dict[str, Any]]:
    # Get comprehensive engine status including path validation and accessibility
    # Provides detailed diagnostic information for engine troubleshooting
    # Returns engine path status, validation results, and directory scanning
    try:
        # Gather comprehensive engine path and accessibility information
        engine_path_info = {
            "cpp_engine_path": str(simulation_engine.cpp_engine_path) if simulation_engine.cpp_engine_path else None,
            "path_exists": simulation_engine.cpp_engine_path.exists() if simulation_engine.cpp_engine_path else False,
            "path_executable": os.access(simulation_engine.cpp_engine_path, os.X_OK) if simulation_engine.cpp_engine_path and simulation_engine.cpp_engine_path.exists() else False,
            "is_valid": simulation_engine._validate_cpp_engine(),
            "current_working_directory": str(Path.cwd()),
            "api_file_location": str(Path(__file__).parent),
        }
        
        # Scan Docker directories for engine files and diagnostic information
        # Docker-aware directory scanning for deployment troubleshooting
        possible_dirs = [
            Path("/app/cpp-engine"),  # Docker deployment path
        ]
        
        directory_contents = {}
        for dir_path in possible_dirs:
            if dir_path.exists():
                try:
                    # Recursively scan for files with safety limit
                    contents = [str(p) for p in dir_path.rglob("*") if p.is_file()]
                    directory_contents[str(dir_path)] = contents[:10]  # Limit to first 10 files for response size
                except Exception as e:
                    directory_contents[str(dir_path)] = f"Error: {e}"
            else:
                directory_contents[str(dir_path)] = "Directory does not exist"
        
        # Compile comprehensive status data for diagnostic analysis
        status_data = {
            "engine_info": engine_path_info,
            "directory_scan": directory_contents
        }
        
        router_base.router_logger.log_request("/engine/status", {})
        
        # Format response based on engine validation status
        if engine_path_info["is_valid"]:
            response = router_base.response_formatter.create_success_response(status_data, "Engine status retrieved successfully")
            router_base.router_logger.log_success("/engine/status")
            return response
        else:
            response = router_base.response_formatter.create_error_response(
                "Engine validation failed",
                [ApiError(code="ENGINE_INVALID", message="Engine is not valid or not accessible")]
            )
            router_base.router_logger.log_error("/engine/status", Exception("Engine invalid"), "ENGINE_INVALID")
            return response
    except Exception as e:
        # Handle status retrieval errors with comprehensive error reporting
        router_base.router_logger.log_error("/engine/status", e, "ENGINE_STATUS_ERROR")
        return router_base.response_formatter.create_error_response(
            "Failed to get engine status",
            [ApiError(code="ENGINE_STATUS_ERROR", message=str(e))]
        )