import os
from dotenv import load_dotenv
from typing import Optional
from pydantic_settings import BaseSettings
import firebase_admin
from firebase_admin import credentials

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Firebase Auth"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Firebase settings
    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", "app/config/serviceAccountKey.json"
    )
    FIREBASE_API_KEY: str = os.getenv("FIREBASE_API_KEY")

    if not FIREBASE_API_KEY:
        raise ValueError("FIREBASE_API_KEY environment variable is not set!")

    if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        raise ValueError(f"Firebase credentials file not found at: {FIREBASE_CREDENTIALS_PATH}")

settings = Settings()

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    except FileNotFoundError:
        print(f"Error: Firebase credentials file not found at {settings.FIREBASE_CREDENTIALS_PATH}")
        raise
    except ValueError:
        # Firebase is already initialized
        pass
    except Exception as e:
        print(f"Unexpected error initializing Firebase: {e}")
        raise
