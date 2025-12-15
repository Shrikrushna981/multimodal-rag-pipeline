from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.api.v1.api import api_router
from app.observability.telemetry import setup_telemetry
from app.observability import metrics

settings = get_settings()
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} version {settings.VERSION}")
    yield
    # Shutdown
    logger.info("Shutting down application")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Telemetry
setup_telemetry(app)

# Middleware
app.add_middleware(RequestLoggingMiddleware)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(metrics.router) # /metrics endpoint

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint.
    """
    return {"status": "ok", "version": settings.VERSION}

@app.get("/readiness", tags=["Health"])
async def readiness_check():
    """
    Readiness probe for K8s. 
    Checks if the application is ready to accept traffic (e.g. DB connected).
    """
    # TODO: Add actual DB/service checks here
    return {"status": "ready"}

@app.get("/liveness", tags=["Health"])
async def liveness_check():
    """
    Liveness probe for K8s.
    Checks if the application is running.
    """
    return {"status": "alive"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
