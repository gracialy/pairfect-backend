import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import auth
from app.models.users import UserSignup, UserLogin
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
async def signup(user: UserSignup):
    try:
        user_record = auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.display_name
        )
        return {"message": "User created successfully", "uid": user_record.uid}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.post("/login")
async def login(user: UserLogin):
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
        "message": "Login successful",
        "id_token": result["idToken"],
        "refresh_token": result["refreshToken"],
        "expires_in": result["expiresIn"]
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    try:
        auth.revoke_refresh_tokens(current_user['uid'])
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )