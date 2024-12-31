from google.cloud import vision
from typing import List, Optional
from functools import lru_cache
import os

class VisionAIManager:
    def __init__(self, credentials_path: str, location: str = "us-central1"):
        self.credentials_path = credentials_path
        self.location = location
        self._client: Optional[vision.ImageAnnotatorClient] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Vision AI client with specific credentials."""
        try:
            self._client = vision.ImageAnnotatorClient.from_service_account_json(
                self.credentials_path
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vision AI client: {e}")
    
    @property
    def client(self) -> vision.ImageAnnotatorClient:
        """Get Vision AI client."""
        if not self._client:
            raise RuntimeError("Vision AI client is not initialized.")
        return self._client
    
    async def detect_labels(
        self, 
        image_content: bytes, 
        max_results: int = 3
    ) -> List[vision.EntityAnnotation]:
        """
        Detect labels in an image using Vision AI.
        
        Args:
            image_content: Bytes of the image content
            max_results: Maximum number of labels to return
            
        Returns:
            List of detected labels with their scores
        """
        try:
            image = vision.Image(content=image_content)
            response = self.client.label_detection(
                image=image,
                max_results=max_results
            )
            
            if response.error.message:
                raise Exception(
                    f"Error detecting labels: {response.error.message}"
                )
                
            return response.label_annotations
            
        except Exception as e:
            raise RuntimeError(f"Label detection failed: {e}")

@lru_cache()
def get_vision_manager(
    credentials_path: str,
    location: str = "us-central1"
) -> VisionAIManager:
    """Get or create a cached VisionAIManager instance."""
    return VisionAIManager(credentials_path, location)