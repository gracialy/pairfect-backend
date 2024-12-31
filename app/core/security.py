from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from firebase_admin import auth
from app.core.firebase import get_firebase_manager
from app.core.config import get_settings
from typing import Optional

settings = get_settings()
firebase_manager = get_firebase_manager(settings.FIREBASE_CREDENTIALS_PATH)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
api_key_header_optional = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify Firebase ID token and return user data."""
    try:
        return firebase_manager.verify_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key from Firestore."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header not found"
        )
    try:
        doc = firebase_manager.db.collection('api_keys').document(api_key).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key"
            )
        key_data = doc.to_dict()
        if not key_data.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API Key is inactive"
            )
        return key_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating API Key: {e}"
        )

# Optional versions for the combined auth
async def get_optional_user(token: str = Depends(oauth2_scheme_optional)):
    if not token:
        return None
    try:
        # Dummy
        return {
            "uid": "dummy_uid",
            "email": "dummy@example.com",
            "name": "Dummy User"
        }
        # return firebase_manager.verify_token(token)
    except ValueError:
        return None

async def get_optional_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[dict]:
    if not api_key:
        return None
    try:
        # Dummy
        return {
            "api_key_id": "",
            "client_id": None 
        }
        # doc = firebase_manager.db.collection('api_keys').document(api_key).get()
        # if not doc.exists:
        #     raise HTTPException(status_code=401, detail="Invalid API Key")
        # key_data = doc.to_dict()
        # if not key_data.get("is_active"):
        #     raise HTTPException(status_code=403, detail="API Key is inactive")
        # return {
        #     "api_key_id": api_key,
        #     "client_id": key_data.get("client_id") 
        # }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating API Key: {e}")


async def get_auth(
    user: Optional[dict] = Depends(get_optional_user),
    api_key: Optional[dict] = Depends(get_optional_api_key)
) -> dict:
    """Authenticate user via Firebase or API key."""
    if user:
        return user
    if api_key:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Either user authentication or a valid API key is required",
        headers={"WWW-Authenticate": "Bearer"}
    )
