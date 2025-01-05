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
    
    async def detect_labels(self, image_content: bytes) -> List[vision.EntityAnnotation]:
        """Detect labels in an image"""
        try:
            image = vision.Image(content=image_content)
            response = self.client.label_detection(image=image)
            
            if response.error.message:
                raise Exception(
                    f"Error detecting labels: {response.error.message}"
                )
                
            return response.label_annotations
            
        except Exception as e:
            raise RuntimeError(f"Label detection failed: {e}")
        
    async def detect_image_properties(self, image_content: bytes) -> vision.ImageProperties:
        """Detect image properties, including dominant colors."""
        try:
            image = vision.Image(content=image_content)
            response = self.client.image_properties(image=image)

            if response.error.message:
                raise Exception(f"Vision AI image properties detection failed: {response.error.message}")
        
            return response.image_properties_annotation
        
        except Exception as e:
            raise RuntimeError(f"Image properties detection failed: {e}")
        
    async def detect_faces(self, image_content: bytes) -> List[vision.FaceAnnotation]:
        """Detect faces in an image."""
        try:
            image = vision.Image(content=image_content)
            response = self.client.face_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Face detection failed: {response.error.message}")
            
            return response.face_annotations
        
        except Exception as e:
            raise RuntimeError(f"Face detection failed: {e}")
        
    async def detect_labels_from_uri(self, image_uri: str) -> List[vision.EntityAnnotation]:
        """Detect labels in an image from a URI."""
        try:
            image = vision.Image()
            image.source.image_uri = image_uri
            response = self.client.label_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Error detecting labels: {response.error.message}")
            
            return response.label_annotations
        
        except Exception as e:
            raise RuntimeError(f"Label detection failed: {e}")
        
    async def detect_image_properties_from_uri(self, image_uri: str) -> vision.ImageProperties:
        """Detect image properties from a URI."""
        try:
            image = vision.Image()
            image.source.image_uri = image_uri
            response = self.client.image_properties(image=image)
            
            if response.error.message:
                raise Exception(f"Image properties detection failed: {response.error.message}")
            
            return response.image_properties_annotation
        
        except Exception as e:
            raise RuntimeError(f"Image properties detection failed: {e}")
        
    async def detect_faces_from_uri(self, image_uri: str) -> List[vision.FaceAnnotation]:
        """Detect faces in an image from a URI."""
        try:
            image = vision.Image()
            image.source.image_uri = image_uri
            response = self.client.face_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Face detection failed: {response.error.message}")
            
            return response.face_annotations
        
        except Exception as e:
            raise RuntimeError(f"Face detection failed: {e}")

@lru_cache()
def get_vision_manager(
    credentials_path: str,
    location: str = "us-central1"
) -> VisionAIManager:
    """Get or create a cached VisionAIManager instance."""
    return VisionAIManager(credentials_path, location)