import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from typing import Optional
from functools import lru_cache
import os

class FirebaseManager:
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self._db: Optional[firestore.Client] = None
        self._bucket: Optional[storage.bucket] = None
        self._initialize_app()
    
    def _initialize_app(self) -> None:
        """Initialize Firebase app with all required services."""
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': f"{cred.project_id}.appspot.com"
                })
                self._db = firestore.client()
                self._bucket = storage.bucket()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Firebase: {e}")
    
    @property
    def db(self) -> firestore.Client:
        """Get Firestore client."""
        if not self._db:
            raise RuntimeError("Firestore client is not initialized.")
        return self._db
    
    @property
    def auth(self) -> auth:
        """Get Firebase Auth."""
        return auth
    
    @property
    def storage(self) -> storage.bucket:
        """Get Firebase Storage bucket."""
        if not self._bucket:
            raise RuntimeError("Firebase Storage bucket is not initialized.")
        return self._bucket
    
    def verify_token(self, token: str) -> dict:
        """Verify Firebase ID token."""
        try:
            return auth.verify_id_token(token)
        except Exception as e:
            raise ValueError(f"Token verification failed: {e}")

@lru_cache()
def get_firebase_manager(credentials_path: str) -> FirebaseManager:
    """Get or create a cached FirebaseManager instance."""
    return FirebaseManager(credentials_path)
