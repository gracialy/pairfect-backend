from fastapi import APIRouter, HTTPException, Depends, status
import uuid
from datetime import datetime
from app.core.security import get_current_user, get_api_key
from app.core.config import get_settings
from app.core.firebase import get_firebase_manager

router = APIRouter(prefix="/developers", tags=["developers"])
settings = get_settings()

def get_db():
    """Get Firestore database instance"""
    firebase = get_firebase_manager(settings.FIREBASE_CREDENTIALS_PATH)
    return firebase.db


@router.post("/key-generation")
async def create_api_key(current_user: dict = Depends(get_current_user)):
    """Create a new API key for a developer."""
    db = get_db()
    api_key = str(uuid.uuid4())
    
    try:
        # Store API key in Firestore
        doc_ref = db.collection('api_keys').document(api_key)
        doc_ref.set({
            'user_id': current_user['uid'],
            'created_at': datetime.utcnow(),
            'last_used': None,
            'is_active': True,
            'metadata': {
                'created_by': current_user.get('email'),
                'ip_address': None  # Optional: Add request.client.host if needed
            }
        })

        return {
            "api_key": api_key,
            "message": "Store this API key safely - it won't be shown again"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )

@router.get("/api-keys")
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """List all API keys for the current developer"""
    db = get_db()
    
    try:
        keys = db.collection('api_keys')\
            .where('user_id', '==', current_user['uid'])\
            .where('is_active', '==', True)\
            .stream()
        
        return [{
            'id': key.id,
            'created_at': key.to_dict()['created_at'],
            'last_used': key.to_dict()['last_used'],
            'metadata': key.to_dict().get('metadata', {})
        } for key in keys]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )

@router.delete("/api-key/{api_key}")
async def revoke_api_key(api_key: str, current_user: dict = Depends(get_current_user)):
    """Revoke an API key"""
    db = get_db()
    
    try:
        key_doc = db.collection('api_keys').document(api_key).get()
        
        if not key_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        key_data = key_doc.to_dict()
        if key_data['user_id'] != current_user['uid']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revoke this API key"
            )
        
        db.collection('api_keys').document(api_key).update({
            'is_active': False,
            'revoked_at': datetime.utcnow(),
            'revoked_by': current_user.get('email')
        })
        
        return {"message": "API key revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )