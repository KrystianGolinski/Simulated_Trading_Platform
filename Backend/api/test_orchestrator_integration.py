#!/usr/bin/env python3
"""
Simple test script to verify orchestrator integration with the API.
This tests the new Phase 3 functionality.
"""

import asyncio
import sys
from pathlib import Path
from datetime import date

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from models import SimulationConfig
from simulation_engine import SimulationEngine

async def test_orchestrator_integration():
    """Test the new orchestrator integration."""
    print("Testing Phase 3 Orchestrator Integration")
    print("=" * 50)
    
    # Create test configuration
    config = SimulationConfig(
        symbols=["AAPL", "MSFT"],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        starting_capital=10000.0,
        strategy="ma_crossover",
        strategy_parameters={"short_window": "10", "long_window": "50"}
    )
    
    print(f"Test Configuration:")
    print(f"   Symbols: {config.symbols}")
    print(f"   Strategy: {config.strategy}")
    print(f"   Date Range: {config.start_date} to {config.end_date}")
    print(f"   Capital: ${config.starting_capital:,.2f}")
    print()
    
    # Create simulation engine
    engine = SimulationEngine()
    
    # Test orchestrator path detection
    print(f"Orchestrator Path: {engine.execution_service.orchestrator_path}")
    print(f"Trading Engine Path: {engine.execution_service.cpp_engine_path}")
    print()
    
    try:
        # Test validation
        print("Testing engine validation...")
        validation = engine._validate_cpp_engine()
        if not validation["is_valid"]:
            print(f"Engine validation failed: {validation['error']}")
            return False
        print("Engine validation passed")
        
        # Test orchestrator execution (this will fail gracefully outside Docker)
        print("\nTesting orchestrator execution...")
        simulation_id = await engine.start_simulation_via_orchestrator(config)
        print(f"Simulation started with ID: {simulation_id}")
        
        # Wait a moment for execution to complete
        await asyncio.sleep(2)
        
        # Check results
        result = engine.result_processor.get_simulation_result(simulation_id)
        print(f"Simulation Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting Phase 3 Orchestrator Integration Test...")
    success = asyncio.run(test_orchestrator_integration())
    
    if success:
        print("\nIntegration test completed successfully!")
        print("The API can now use the C++ orchestrator instead of performance_optimizer.py")
    else:
        print("\nIntegration test failed!")
        print("Check the error messages above for troubleshooting.")