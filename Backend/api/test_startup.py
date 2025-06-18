#!/usr/bin/env python3

print("Testing imports...")

try:
    import fastapi
    print("FastAPI import OK")
except Exception as e:
    print(f"FastAPI import failed: {e}")

try:
    from models import SimulationConfig
    print("Models import OK")
except Exception as e:
    print(f"Models import failed: {e}")

try:
    from simulation_engine import simulation_engine
    print("Simulation engine import OK")
except Exception as e:
    print(f"Simulation engine import failed: {e}")

try:
    from database import get_database
    print("Database import OK")
except Exception as e:
    print(f"Database import failed: {e}")

try:
    import main
    print("Main import OK")
except Exception as e:
    print(f"Main import failed: {e}")

print("All imports completed")