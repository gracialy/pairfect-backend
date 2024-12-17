from fastapi import FastAPI
import os

app = FastAPI(title="Hello World API")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}