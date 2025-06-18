from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import get_database
from routers import health, stocks, simulation, performance, engine

# Create FastAPI app
app = FastAPI(
    title="Trading Platform API",
    description="FastAPI backend for the simulated trading platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(simulation.router)
app.include_router(performance.router)
app.include_router(engine.router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    # Initialize database connection on startup
    try:
        await get_database()
        print("Database connection established at startup")
    except Exception as e:
        print(f"Warning: Database not available at startup: {e}")
        print("Will retry connections on first request")

@app.on_event("shutdown")
async def shutdown_event():
    # Close database connection on shutdown
    from database import db_manager
    await db_manager.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)