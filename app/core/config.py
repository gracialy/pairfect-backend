from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Firebase Auth"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Firebase settings
    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", 
        "app/config/serviceAccountKey.json"
    )
    FIREBASE_API_KEY: str = os.getenv("FIREBASE_API_KEY")
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET")
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT")

    # Vision AI settings
    VISION_CREDENTIALS_PATH: str = os.getenv(
        "VISION_CREDENTIALS_PATH",
        "app/config/SAKeyVision.json"
    )
    VISION_AI_LOCATION: str = os.getenv("VISION_AI_LOCATION", "us-central1")
    MAX_RESULTS: int = int(os.getenv("VISION_MAX_RESULTS", "3"))

    # Custom Search settings
    CUSTOM_SEARCH_API_KEY: str = os.getenv("CUSTOM_SEARCH_API_KEY")
    CUSTOM_SEARCH_CX: str = os.getenv("CUSTOM_SEARCH_CX") 

    # Peers API Integration
    FURINA_API_KEY: str = os.getenv("FURINA_API_KEY")
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Validate environment variables during startup
settings = get_settings()

if not settings.FIREBASE_API_KEY:
    raise ValueError("FIREBASE_API_KEY environment variable is not set!")

if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Firebase credentials file not found at: {settings.FIREBASE_CREDENTIALS_PATH}")

if not os.path.exists(settings.VISION_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Vision AI credentials file not found at: {settings.VISION_CREDENTIALS_PATH}")

if not settings.CUSTOM_SEARCH_API_KEY:
    raise ValueError("CUSTOM_SEARCH_API_KEY environment variable is not set!")
if not settings.CUSTOM_SEARCH_CX:
    raise ValueError("CUSTOM_SEARCH_CX environment variable is not set!")

if not settings.STORAGE_BUCKET:
    raise ValueError("STORAGE_BUCKET environment variable is not set!")
if not settings.GOOGLE_CLOUD_PROJECT:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set!")

if not settings.FURINA_API_KEY:
    raise ValueError("FURINA_API_KEY environment variable is not set!")


# print(f"DEBUG: FIREBASE_API_KEY = {settings.FIREBASE_API_KEY}")
# print(f"DEBUG: FIREBASE_CREDENTIALS_PATH = {settings.FIREBASE_CREDENTIALS_PATH}")
# print(f"DEBUG: VISION_CREDENTIALS_PATH = {settings.VISION_CREDENTIALS_PATH}")
# print(f"DEBUG: CUSTOM_SEARCH_API_KEY = {settings.CUSTOM_SEARCH_API_KEY}")
# print(f"DEBUG: CUSTOM_SEARCH_CX = {settings.CUSTOM_SEARCH_CX}")
# print(f"DEBUG: STORAGE_BUCKET = {settings.STORAGE_BUCKET}")
# print(f"DEBUG: GOOGLE_CLOUD_PROJECT = {settings.GOOGLE_CLOUD_PROJECT}")