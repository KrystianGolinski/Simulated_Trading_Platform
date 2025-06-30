from fastapi import APIRouter
import subprocess
import os
from pathlib import Path
from typing import Dict, Any

from simulation_engine import simulation_engine
from response_models import StandardResponse, create_success_response, create_error_response, ApiError
from base_router import BaseRouter

router = APIRouter(tags=["engine"])

class EngineRouter(BaseRouter):
    # C++ engine testing router with standardized patterns
    pass

engine_router = EngineRouter()

@router.get("/engine/test")
async def test_engine() -> StandardResponse[Dict[str, Any]]:
    # Test engine directly and return raw output
    engine_path = Path("/app/cpp-engine/build/trading_engine")
    if not engine_path.exists():
        return engine_router.create_not_found_response("Engine", str(engine_path), "engine_path")
    
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
            return create_success_response(test_data, "Engine test completed successfully")
        else:
            return create_error_response(
                "Engine test failed",
                [ApiError(code="ENGINE_TEST_FAILED", message=f"Engine returned code {result.returncode}")]
            )
    except Exception as e:
        return create_error_response(
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
        
        if engine_path_info["is_valid"]:
            return create_success_response(status_data, "Engine status retrieved successfully")
        else:
            return create_error_response(
                "Engine validation failed",
                [ApiError(code="ENGINE_INVALID", message="Engine is not valid or not accessible")]
            )
    except Exception as e:
        return create_error_response(
            "Failed to get engine status",
            [ApiError(code="ENGINE_STATUS_ERROR", message=str(e))]
        )