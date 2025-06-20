import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from database import get_database
from routers import health, stocks, simulation, performance, engine

# Configure structured logging with correlation ID support
class CorrelationFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'N/A'
        return super().format(record)

# Set up logging with correlation ID support
handler = logging.StreamHandler()
handler.setFormatter(CorrelationFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trading Platform API",
    description="FastAPI backend for the simulated trading platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server in Docker
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware for request tracing
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Add correlation ID to logging context
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.correlation_id = correlation_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    # Restore original factory
    logging.setLogRecordFactory(old_factory)
    
    return response

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
        logger.info("Database connection established at startup")
    except Exception as e:
        logger.warning(f"Database not available at startup: {e}")
        logger.info("Will retry connections on first request")

@app.on_event("shutdown")
async def shutdown_event():
    # Close database connection on shutdown
    from database import db_manager
    await db_manager.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)