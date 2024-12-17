from fastapi import FastAPI
from app.core.config import init_firebase
from app.api import auth, users

# Initialize FastAPI app
app = FastAPI(title="Hello World API with Auth")

# Initialize Firebase
init_firebase()

# Include routers
app.include_router(auth.router)
app.include_router(users.router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)