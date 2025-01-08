from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.firebase import get_firebase_manager
from app.api import auth, users, developers, images
import time
from typing import Dict

# Load settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase during startup
@app.on_event("startup")
async def startup_event():
    """Initialize Firebase and other services on startup."""
    try:
        get_firebase_manager(settings.FIREBASE_CREDENTIALS_PATH)
    except Exception as e:
        raise RuntimeError(f"Error initializing Firebase: {e}")

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Add response time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(developers.router, prefix=settings.API_V1_STR)
app.include_router(images.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to FastAPI Firebase Auth API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    try:
        # Fetch FirebaseManager instance
        firebase_manager = get_firebase_manager(settings.FIREBASE_CREDENTIALS_PATH)
        # Test Firestore connection
        firebase_manager.db.collection('health_check').limit(1).stream()
        return {
            "status": "healthy",
            "firebase": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  
        workers=1     # Single worker for development
    )
