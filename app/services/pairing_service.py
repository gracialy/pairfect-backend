from datetime import datetime
import uuid
from typing import Tuple, List, Dict
import aiohttp
from fastapi import HTTPException
from app.core.config import get_settings
from app.core.firebase import get_firebase_manager
from app.core.vision import get_vision_manager
from functools import lru_cache

class PairingService:
    def __init__(self):
        self.settings = get_settings()
        self.firebase = get_firebase_manager(self.settings.FIREBASE_CREDENTIALS_PATH)
        self.vision = get_vision_manager(
            credentials_path=self.settings.VISION_CREDENTIALS_PATH,
            location=self.settings.VISION_AI_LOCATION
        )

    async def analyze_image(self, content: bytes) -> List[str]:
        """Analyze image using Vision AI and return the last 3 labels."""
        try:
            labels = await self.vision.detect_labels(
                image_content=content,
                max_results=10  # Fetch more labels to ensure we can get the last 3
            )
            return [label.description for label in labels[-3:]]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vision AI analysis failed: {str(e)}"
            )

    async def search_image(self, search_term: str) -> str:
        """Search for image using Google Custom Search."""
        async with aiohttp.ClientSession() as session:
            search_url = "https://customsearch.googleapis.com/customsearch/v1"
            params = {
                "key": self.settings.CUSTOM_SEARCH_API_KEY,
                "cx": self.settings.CUSTOM_SEARCH_CX,
                "q": search_term,
                "searchType": "image",
                "num": 1,
                "safe": "active",
                "imgType": "photo"
            }
            
            try:
                async with session.get(search_url, params=params) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Image search failed: {await response.text()}"
                        )
                    
                    data = await response.json()
                    if not data.get("items"):
                        raise HTTPException(
                            status_code=404,
                            detail=f"No images found for search term: {search_term}"
                        )
                    
                    return data["items"][0]["link"]
            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error during image search: {str(e)}"
                )

    def store_pairing_record(self, 
        original_image_content: bytes,
        keyword: str,
        labels: List[str],
        result_image_url: str,
        auth: dict
    ) -> Dict:
        """Store pairing record in Firestore."""
        try:
            pairing_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            record = {
                'id': pairing_id,
                'timestamp': timestamp,
                'keyword': keyword,
                'labels': labels,
                'result_image_url': result_image_url,
                'search_term': f"{keyword} {' '.join(labels)}"
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
                    'total_requests': 1
                })
            else:
                record.update({
                    'user_id': auth.get('uid'),
                    'user_email': auth.get('email')
                })

            # Store record
            self.firebase.db.collection('image_pairings').document(pairing_id).set(record)
            
            return {
                'id': pairing_id,
                'timestamp': timestamp,
                'labels': labels,
                'result_image_url': result_image_url,
                'search_term': record['search_term']
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store pairing record: {str(e)}"
            )

@lru_cache()
def get_pairing_service() -> PairingService:
    return PairingService()