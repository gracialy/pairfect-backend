from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import auth
from app.core.security import get_current_user
from app.models.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user_record = auth.get_user(current_user['uid'])
        return {
            "uid": user_record.uid,
            "email": user_record.email,
            "display_name": user_record.display_name,
            "email_verified": user_record.email_verified
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/me/display-name")
async def update_display_name(
    display_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Update user's display name"""
    try:
        auth.update_user(
            current_user['uid'],
            display_name=display_name
        )
        return {"message": "Display name updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/me/email")
async def update_email(
    new_email: str,
    current_user: dict = Depends(get_current_user)
):
    """Update user's email"""
    try:
        auth.update_user(
            current_user['uid'],
            email=new_email
        )
        return {"message": "Email updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )