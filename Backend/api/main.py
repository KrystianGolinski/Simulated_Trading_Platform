# FastAPI Backend for Simulated Trading Platform
# This file serves as the main entry point for the API server, providing:
# - FastAPI application setup and configuration
# - Global exception handlers with standardised error responses
# - CORS middleware for frontend communication
# - Request correlation tracking middleware
# - Router registration for all API endpoints
# - Database connection lifecycle management

import logging
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Core application components
from database import get_database
from routers import health, stocks, simulation, performance, engine, strategies
from models import ApiError
from routing import get_router_service_factory

# Custom exception classes for API error handling
# These exceptions are caught by global exception handlers and converted to standardised API responses

class ValidationError(Exception):
    # Raised when input validation fails (e.g., invalid simulation configuration)
    # Automatically converted to HTTP 400 Bad Request with detailed error list
    def __init__(self, message: str, errors: list = None):
        self.message = message
        self.errors = errors or []  # List of ApiError objects for detailed validation feedback
        super().__init__(self.message)

class OperationError(Exception):
    # Raised when business logic operations fail (e.g., simulation execution errors)
    # Automatically converted to HTTP 500 Internal Server Error
    def __init__(self, message: str, code: str = "OPERATION_ERROR"):
        self.message = message
        self.code = code  # Error code for client-side error handling
        super().__init__(self.message)

# Configure structured logging with correlation ID support
# Each request gets a unique correlation ID for tracking requests across the system
# This enables distributed tracing and debugging of complex simulation workflows

class CorrelationFormatter(logging.Formatter):
    # Custom formatter that includes correlation ID in log messages
    # The correlation ID is set by the middleware for each request
    def format(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'N/A'  # Default for logs outside request context
        return super().format(record)

# Set up logging with correlation ID support
# All log messages include timestamp, logger name, level, correlation ID, and message
handler = logging.StreamHandler()
handler.setFormatter(CorrelationFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
# This is the main ASGI application that handles all HTTP requests
app = FastAPI(
    title="Trading Platform API",
    description="FastAPI backend for the simulated trading platform with parallel simulation support",
    version="1.0.0"
)

# Get global response formatter for exception handling
# Uses the same response formatting infrastructure as the RouterBase pattern
# Ensures consistent error response format across all endpoints
_global_factory = get_router_service_factory()
_global_response_formatter = _global_factory.get_response_formatter()

# Global exception handlers
# These handlers catch exceptions from all endpoints and convert them to standardised API responses
# All responses follow the standard format: {status, message, data, errors, warnings, metadata}

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    # Handle validation errors (HTTP 400) - typically from simulation config validation
    # or stock symbol validation in routers
    logger.warning(f"Validation error: {exc.message}")
    response = _global_response_formatter.create_error_response(
        "Validation failed",
        exc.errors or [ApiError(code="VALIDATION_FAILED", message=exc.message)]
    )
    return JSONResponse(status_code=400, content=response.dict())

@app.exception_handler(OperationError)
async def operation_exception_handler(request: Request, exc: OperationError):
    # Handle business logic errors (HTTP 500) - typically from simulation execution
    # or C++ engine communication failures
    logger.error(f"Operation error: {exc.message}")
    response = _global_response_formatter.create_error_response(
        "Operation failed",
        [ApiError(code=exc.code, message=exc.message)]
    )
    return JSONResponse(status_code=500, content=response.dict())

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    # Handle Python ValueError exceptions (HTTP 400) - typically from invalid parameters
    # or data type conversion failures
    logger.warning(f"Value error: {str(exc)}")
    response = _global_response_formatter.create_error_response(
        "Invalid input provided",
        [ApiError(code="INVALID_INPUT", message=str(exc))]
    )
    return JSONResponse(status_code=400, content=response.dict())

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Catch-all handler for unexpected exceptions (HTTP 500)
    # Logs the full exception but returns a generic message to avoid exposing internal details
    logger.error(f"Unhandled exception: {str(exc)}")
    response = _global_response_formatter.create_error_response(
        "Internal server error",
        [ApiError(code="INTERNAL_ERROR", message="An unexpected error occurred")]
    )
    return JSONResponse(status_code=500, content=response.dict())

# Add CORS middleware for frontend communication
# Allows the React frontend to make requests to the API from different ports/domains
# Currently configured for local development with React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server in Docker
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],     # Allow all headers including custom ones
)

# Add correlation ID middleware for request tracing
# This middleware enables distributed tracing across the entire system
# Essential for debugging complex parallel simulation workflows
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # Extract correlation ID from request header or generate a new one
    # Clients can provide their own correlation ID for end-to-end tracing
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Add correlation ID to logging context for all log messages during this request
    # This allows tracking of all operations related to a single request
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.correlation_id = correlation_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    # Process the request and ensure correlation ID is included in response
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    # Restore original factory to avoid affecting other requests
    logging.setLogRecordFactory(old_factory)
    
    return response

# Include routers for all API endpoints
# Each router handles a specific domain of functionality using the RouterBase pattern
# All routers use dependency injection for services and follow standardised response formats
app.include_router(health.router)      # Health checks and system status (/health/*)
app.include_router(stocks.router)      # Stock data and temporal validation (/stocks/*)
app.include_router(simulation.router)  # Simulation lifecycle and parallel execution (/simulation/*)
app.include_router(performance.router) # Performance analytics and optimization metrics (/performance/*)
app.include_router(engine.router)      # C++ engine interface and testing (/engine/*)
app.include_router(strategies.router)  # Strategy management and discovery (/strategies/*)

# Startup and shutdown events for application lifecycle management
# These events handle database connection lifecycle and resource cleanup

@app.on_event("startup")
async def startup_event():
    # Initialize database connection on startup
    # If database is not available, the application will still start but log a warning
    # This allows for graceful handling of database connectivity issues
    try:
        await get_database()
        logger.info("Database connection established at startup")
    except Exception as e:
        logger.warning(f"Database not available at startup: {e}")
        logger.info("Will retry connections on first request")

@app.on_event("shutdown")
async def shutdown_event():
    # Clean shutdown: close database connections and release resources
    # This ensures proper cleanup when the application terminates
    from database import db_manager
    await db_manager.disconnect()

# Development server entry point
# In production, this application is typically run via Docker with gunicorn/uvicorn
# This allows for local development and testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)