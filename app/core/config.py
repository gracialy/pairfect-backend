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
    STORAGE_BUCKET: str
    GOOGLE_CLOUD_PROJECT: str

    # Vision AI settings
    VISION_CREDENTIALS_PATH: str = os.getenv(
        "VISION_CREDENTIALS_PATH",
        "app/config/SAKeyVision.json"
    )
    VISION_AI_LOCATION: str = os.getenv("VISION_AI_LOCATION", "us-central1")
    MAX_RESULTS: int = int(os.getenv("VISION_MAX_RESULTS", "3"))
    
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
