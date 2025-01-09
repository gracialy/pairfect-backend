from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import auth
from app.core.security import get_current_user
from pydantic import BaseModel, EmailStr

class UserBody(BaseModel):
    email: EmailStr
    password: str
    display_name: str

class UserResponse(BaseModel):
    uid: str

class MeResponse(BaseModel):
    uid: str
    email: str
    display_name: str

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserResponse)
async def signup(user: UserBody):
    try:
        user_record = auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.display_name
        )
        return {
            "uid": user_record.uid
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=MeResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user_record = auth.get_user(current_user['uid'])
        return {
            "uid": user_record.uid,
            "email": user_record.email,
            "display_name": user_record.display_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )