from datetime import datetime
from functools import lru_cache
import uuid
from firebase_admin import firestore
from app.core.firebase import get_firebase_manager
from app.core.vision import get_vision_manager
from app.core.config import get_settings
from fastapi import HTTPException

class ImageService:
    def __init__(self):
        self.firebase = get_firebase_manager(get_settings().FIREBASE_CREDENTIALS_PATH)
        self.settings = get_settings()
        self.vision = get_vision_manager(
            credentials_path=self.settings.VISION_CREDENTIALS_PATH,
            location=self.settings.VISION_AI_LOCATION
        )

    async def store_image(self, content: bytes, filename: str, content_type: str) -> str:
        """Store image in Firebase Storage."""
        analysis_id = str(uuid.uuid4())
        blob_path = f"analysis_images/{analysis_id}/{filename}"
        
        blob = self.firebase.storage.blob(blob_path)
        blob.upload_from_string(content, content_type=content_type)
        
        return blob_path, analysis_id
    
    async def store_analysis_record(self, 
        analysis_id: str,
        blob_path: str,
        filename: str,
        content_type: str,
        analysis_result: dict,
        auth: dict
    ):
        """Store analysis record in Firestore."""
        timestamp = datetime.utcnow()
        record = {
            'id': analysis_id,
            'timestamp': timestamp,
            'image_path': blob_path,
            'analysis_result': analysis_result,
            'file_name': filename,
            'content_type': content_type
        }

        # Add auth-specific data
        if 'api_key_id' in auth:
            record.update({
                'api_key_id': auth['api_key_id'],
                'client_id': auth.get('client_id'),
            })
            # Update API usage statistics
            api_key_ref = self.firebase.db.collection('api_keys').document(auth['api_key_id'])
            api_key_ref.update({
                'last_used': timestamp,
                'total_requests': firestore.Increment(1)
            })
        else:
            record.update({
                'user_id': auth.get('uid'),
                'user_email': auth.get('email')
            })

        self.firebase.db.collection('image_analysis').document(analysis_id).set(record)
        return timestamp
    
    async def analyze_image(self, content: bytes) -> dict:
        """Analyze image using Vision AI label detection."""
        try:
            labels = await self.vision.detect_labels(
                image_content=content,
                max_results=self.settings.MAX_RESULTS
            )
            
            # Convert Vision AI response to structured dict
            return {
                'labels': [
                    {
                        'description': label.description,
                        'score': float(label.score),  # Convert to float for JSON serialization
                        'confidence': float(label.score * 100),  # Add percentage for convenience
                        'topicality': float(label.topicality)
                    }
                    for label in labels
                ]
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vision AI analysis failed: {str(e)}"
            )

@lru_cache()
def get_image_service() -> ImageService:
    return ImageService()