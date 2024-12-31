from datetime import datetime
from functools import lru_cache
import uuid
from firebase_admin import firestore
from app.core.firebase import get_firebase_manager
from app.core.vision import get_vision_manager
from app.core.config import get_settings
from fastapi import HTTPException
import aiohttp
from typing import Tuple, List
import random

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
            # labels = await self.vision.detect_labels(
            #     image_content=content,
            #     max_results=self.settings.MAX_RESULTS
            # )
            labels = [
                {
                    'description': 'dog',
                    'score': 0.95,
                    'topicality': 0.90
                },
                {
                    'description': 'pet',
                    'score': 0.93,
                    'topicality': 0.88
                }
            ]
            
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
        
    async def fetch_image_url_from_web(self, keyword: str) -> str:
        """Fetch an image URL from the web using Google Custom Search API."""
        async with aiohttp.ClientSession() as session:
            search_url = "https://customsearch.googleapis.com/customsearch/v1"
            params = {
                "key": self.settings.CUSTOM_SEARCH_API_KEY,
                "cx": self.settings.CUSTOM_SEARCH_CX,
                "q": keyword,
                "searchType": "image",
                "safe": "active",
                "imgSize": "large",
                "imgType": "photo",
                "num": 5
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
                            detail=f"No images found for keyword: {keyword}"
                        )
                    
                    # Randomly select one of the top results
                    image_item = random.choice(data["items"][:5])
                    return image_item["link"]

            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error during image search: {str(e)}"
                )

    async def analyze_image_from_url(self, image_url: str) -> dict:
        """Analyze image using Vision AI directly from URL."""
        try:
            # image = vision.Image()
            # image.source.image_uri = image_url
            
            # labels = await self.vision.detect_labels(
            #     image=image,
            #     max_results=self.settings.MAX_RESULTS
            # )
            labels = [
                {
                    'description': 'cat',
                    'score': 0.98,
                    'topicality': 0.95
                },
                {
                    'description': 'animal',
                    'score': 0.97,
                    'topicality': 0.94
                }
            ]
            
            return {
                'labels': [
                    {
                        'description': label.description,
                        'score': float(label.score),
                        'confidence': float(label.score * 100),
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

    async def pair_images(self, content: bytes, keyword: str) -> dict:
        """Analyze and pair an uploaded image with a web image."""
        # Analyze uploaded image
        # uploaded_analysis = await self.analyze_image(content)
        uploaded_analysis = {
            'labels': [
                {
                    'description': 'flower',
                    'score': 0.92,
                    'confidence': 92.0,
                    'topicality': 0.89
                },
                {
                    'description': 'nature',
                    'score': 0.90,
                    'confidence': 90.0,
                    'topicality': 0.87
                }
            ]
        }
        
        # Get and analyze web image
        web_image_url = await self.fetch_image_url_from_web(keyword)
        # web_analysis = await self.analyze_image_from_url(web_image_url)
        web_analysis = {
            'labels': [
                {
                    'description': 'tree',
                    'score': 0.88,
                    'confidence': 88.0,
                    'topicality': 0.85
                },
                {
                    'description': 'forest',
                    'score': 0.86,
                    'confidence': 86.0,
                    'topicality': 0.83
                }
            ]
        }
        
        # Calculate compatibility
        # compatibility = await self.calculate_compatibility_score(
        #     uploaded_analysis["labels"],
        #     web_analysis["labels"]
        # )
        compatibility = {
            "score": random.uniform(0, 1),
            "description": "Dummy compatibility score"
        }
        
        return {
            "uploaded_image": uploaded_analysis,
            "paired_image": {
                "url": web_image_url,
                "analysis": web_analysis
            },
            "compatibility": compatibility
        }

@lru_cache()
def get_image_service() -> ImageService:
    return ImageService()