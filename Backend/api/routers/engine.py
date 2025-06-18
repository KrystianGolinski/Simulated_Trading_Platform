from fastapi import APIRouter
import subprocess
import os
from pathlib import Path

from simulation_engine import simulation_engine

router = APIRouter(tags=["engine"])

@router.get("/engine/test")
async def test_engine():
    # Test engine directly and return raw output

    engine_path = Path("/app/cpp-engine/build/trading_engine")
    if not engine_path.exists():
        return {"error": "Engine not found"}
    
    try:
        # Run test simulation to capture output
        result = subprocess.run([str(engine_path), "--simulate", "--symbol", "AAPL", "--start", "2023-01-01", "--end", "2023-01-31", "--capital", "10000"], 
                              capture_output=True, text=True, timeout=30)
        
        return {
            "command": f"{engine_path} --simulate --symbol AAPL --start 2023-01-01 --end 2023-01-31 --capital 10000",
            "return_code": result.returncode,
            "stdout": result.stdout[:2000],  # Limit output
            "stderr": result.stderr[:1000]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/engine/status")
async def get_engine_status():
    # Get engine status and path information
    # Check engine path
    engine_path_info = {
        "cpp_engine_path": str(simulation_engine.cpp_engine_path) if simulation_engine.cpp_engine_path else None,
        "path_exists": simulation_engine.cpp_engine_path.exists() if simulation_engine.cpp_engine_path else False,
        "path_executable": os.access(simulation_engine.cpp_engine_path, os.X_OK) if simulation_engine.cpp_engine_path and simulation_engine.cpp_engine_path.exists() else False,
        "is_valid": simulation_engine._validate_cpp_engine(),
        "current_working_directory": str(Path.cwd()),
        "api_file_location": str(Path(__file__).parent),
    }
    
    # List contents of possible directories
    # Avoid creation of incorrect directories (Docker)
    possible_dirs = [
        Path("/home/krystian/Desktop/Simulated_Trading_Platform/Backend/cpp-engine"),  # Absolute development path
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
    
    return {
        "engine_info": engine_path_info,
        "directory_scan": directory_contents
    }