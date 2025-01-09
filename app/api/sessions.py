import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import auth
from app.core.security import get_current_user
from app.core.config import settings
from pydantic import BaseModel, EmailStr

class SessionBody(BaseModel):
    email: EmailStr
    password: str

router = APIRouter(prefix="/session", tags=["sessions"])
    
@router.post("")
async def login(user: SessionBody):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_API_KEY}"
    payload = {
        "email": user.email,
        "password": user.password,
        "returnSecureToken": True
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    result = response.json()
    return {
        "id_token": result["idToken"],
        "expires_in": result["expiresIn"]
    }

@router.delete("")
async def logout(current_user: dict = Depends(get_current_user), status_code=status.HTTP_204_NO_CONTENT):
    try:
        auth.revoke_refresh_tokens(current_user['uid'])
        return {
            "message": "Session deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )