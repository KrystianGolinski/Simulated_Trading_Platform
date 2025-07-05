from fastapi import APIRouter
import subprocess
import os
from pathlib import Path
from typing import Dict, Any

from simulation_engine import simulation_engine
from models import StandardResponse, ApiError
from routing import get_router_service_factory

# Create router using RouterBase pattern
router_factory = get_router_service_factory()
router_base = router_factory.create_router_base("engine")
router = router_base.get_router()
router.tags = ["engine"]

@router.get("/engine/test")
async def test_engine() -> StandardResponse[Dict[str, Any]]:
    # Test engine directly and return raw output
    engine_path = Path("/app/cpp-engine/build/trading_engine")
    router_base.router_logger.log_request("/engine/test", {})
    
    if not engine_path.exists():
        response = router_base.response_formatter.create_error_response(
            f"Engine not found at {engine_path}",
            [ApiError(code="ENGINE_NOT_FOUND", message=f"Engine binary not found at {engine_path}", field="engine_path")]
        )
        router_base.router_logger.log_error("/engine/test", Exception("Engine not found"), "ENGINE_NOT_FOUND")
        return response
    
    try:
        # Run test simulation to capture output
        result = subprocess.run([str(engine_path), "--simulate", "--symbol", "AAPL", "--start", "2023-01-01", "--end", "2023-01-31", "--capital", "10000"], 
                              capture_output=True, text=True, timeout=30)
        
        test_data = {
            "command": f"{engine_path} --simulate --symbol AAPL --start 2023-01-01 --end 2023-01-31 --capital 10000",
            "return_code": result.returncode,
            "stdout": result.stdout[:2000],  # Limit output
            "stderr": result.stderr[:1000]
        }
        
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
        router_base.router_logger.log_error("/engine/test", e, "ENGINE_TEST_ERROR")
        return router_base.response_formatter.create_error_response(
            "Engine test error",
            [ApiError(code="ENGINE_TEST_ERROR", message=str(e))]
        )

@router.get("/engine/status")
async def get_engine_status() -> StandardResponse[Dict[str, Any]]:
    # Get engine status and path information
    try:
        # Check engine path
        engine_path_info = {
            "cpp_engine_path": str(simulation_engine.cpp_engine_path) if simulation_engine.cpp_engine_path else None,
            "path_exists": simulation_engine.cpp_engine_path.exists() if simulation_engine.cpp_engine_path else False,
            "path_executable": os.access(simulation_engine.cpp_engine_path, os.X_OK) if simulation_engine.cpp_engine_path and simulation_engine.cpp_engine_path.exists() else False,
            "is_valid": simulation_engine._validate_cpp_engine(),
            "current_working_directory": str(Path.cwd()),
            "api_file_location": str(Path(__file__).parent),
        }
        
        # List contents of Docker directory
        # Always assume Docker environment
        possible_dirs = [
            Path("/app/cpp-engine"),  # Docker path
        ]
        
        directory_contents = {}
        for dir_path in possible_dirs:
            if dir_path.exists():
                try:
                    contents = [str(p) for p in dir_path.rglob("*") if p.is_file()]
                    directory_contents[str(dir_path)] = contents[:10]  # Limit to first 10 files
                except Exception as e:
                    directory_contents[str(dir_path)] = f"Error: {e}"
            else:
                directory_contents[str(dir_path)] = "Directory does not exist"
        
        status_data = {
            "engine_info": engine_path_info,
            "directory_scan": directory_contents
        }
        
        router_base.router_logger.log_request("/engine/status", {})
        
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
        router_base.router_logger.log_error("/engine/status", e, "ENGINE_STATUS_ERROR")
        return router_base.response_formatter.create_error_response(
            "Failed to get engine status",
            [ApiError(code="ENGINE_STATUS_ERROR", message=str(e))]
        )