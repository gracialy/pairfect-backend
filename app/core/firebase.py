import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from typing import Optional
from functools import lru_cache
import os

class FirebaseManager:
    """
    Manages Firebase services including Firestore, Auth, and Storage.
    Implements a singleton pattern using lru_cache.
    """
    
    def __init__(self, credentials_path: str):
        """
        Initialize Firebase manager with credentials.
        
        Args:
            credentials_path (str): Path to Firebase service account credentials JSON
        """
        self.credentials_path = credentials_path
        self._db: Optional[firestore.Client] = None
        self._bucket: Optional[storage.bucket] = None
        self._initialize_app()
    
    def _initialize_app(self) -> None:
        """Initialize Firebase app with all required services."""
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(self.credentials_path)
                # GOOGLE FIREBASE STORAGE BUCKET USE firebasestorage.app DONT LET GCS FOOL YOU AAAAAAAAAAAAAAAAARGHHHHHHHHHH
                firebase_admin.initialize_app(cred, {
                    'storageBucket': f"{cred.project_id}.firebasestorage.app"
                })
                self._db = firestore.client()
                self._bucket = storage.bucket()

            except Exception as e:
                raise RuntimeError(f"Failed to initialize Firebase: {str(e)}")
    
    @property
    def db(self) -> firestore.Client:
        """Get Firestore client."""
        if not self._db:
            self._initialize_app()  # Try to reinitialize if db is None
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
            self._initialize_app()  # Try to reinitialize if bucket is None
        if not self._bucket:
            raise RuntimeError("Firebase Storage bucket is not initialized.")
        return self._bucket
    
    def verify_token(self, token: str) -> dict:
        """
        Verify Firebase ID token.
        
        Args:
            token (str): Firebase ID token to verify
            
        Returns:
            dict: Decoded token claims
            
        Raises:
            ValueError: If token verification fails
        """
        try:
            return auth.verify_id_token(token)
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")
    
    def check_api_key_exists(self, api_key_id: str) -> bool:
        """
        Check if an API key document exists.
        
        Args:
            api_key_id (str): The API key ID to check
            
        Returns:
            bool: True if the API key exists, False otherwise
        """
        doc_ref = self.db.collection('api_keys').document(api_key_id)
        return doc_ref.get().exists

@lru_cache()
def get_firebase_manager(credentials_path: str) -> FirebaseManager:
    """
    Get or create a cached FirebaseManager instance.
    
    Args:
        credentials_path (str): Path to Firebase service account credentials JSON
        
    Returns:
        FirebaseManager: Singleton instance of FirebaseManager
    """
    return FirebaseManager(credentials_path)