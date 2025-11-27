"""
Main FastAPI application entry point.

"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.v1.endpoints import auth, books

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Intern Training API",
    description="Production-ready FastAPI application for intern training program",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware configuration
# TODO: Update allowed origins based on your frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "intern-training-api"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {"message": "Welcome to the Intern Training API", "version": "1.0.0", "docs": "/docs", "health": "/health"}


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(books.router, prefix="/api/v1/books", tags=["books"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
