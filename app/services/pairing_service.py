from datetime import datetime
import uuid
from typing import Tuple, List, Dict
import aiohttp
from fastapi import HTTPException
from app.core.config import get_settings
from app.core.firebase import get_firebase_manager
from app.core.vision import get_vision_manager
from functools import lru_cache
import random

class PairingService:
    def __init__(self):
        self.settings = get_settings()
        self.firebase = get_firebase_manager(self.settings.FIREBASE_CREDENTIALS_PATH)
        self.vision = get_vision_manager(
            credentials_path=self.settings.VISION_CREDENTIALS_PATH,
            location=self.settings.VISION_AI_LOCATION
        )

    async def analyze_image(self, 
        content: bytes, 
        include_faces: bool
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Analyze image using Vision AI and return labels, colors, and faces."""
        labels, colors, faces = [], [], []
        
        labels = await self.analyze_labels(content)
        colors = await self.analyze_colors(content)
        if include_faces:
            faces = await self.analyze_faces(content)
        
        return labels, colors, faces
    
    async def analyze_image_from_uri(self, 
        image_uri: str, 
        include_faces: bool
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Analyze image using Vision AI and return labels, colors, and faces from URI."""
        labels, colors, faces = [], [], []
        
        labels = await self.analyze_labels_from_uri(image_uri)
        colors = await self.analyze_colors_from_uri(image_uri)
        if include_faces:
            faces = await self.analyze_faces_from_uri(image_uri)
        
        return labels, colors, faces

    async def analyze_labels(self, content: bytes) -> List[Dict]:
        """Analyze image using Vision AI and return labels."""
        try:
            labels = await self.vision.detect_labels(image_content=content)
            return [{'description': label.description, 'score': label.score} for label in labels]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vision AI label analysis failed: {str(e)}"
            )

    async def analyze_labels_from_uri(self, image_uri: str) -> List[Dict]:
        """Analyze image using Vision AI and return labels from URI."""
        try:
            labels = await self.vision.detect_labels_from_uri(image_uri=image_uri)
            return [{'description': label.description, 'score': label.score} for label in labels]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vision AI label analysis failed: {str(e)}"
            )

    async def analyze_colors(self, content: bytes) -> List[Dict]:
        """Analyze image using Vision AI and return dominant colors."""
        try:
            properties = await self.vision.detect_image_properties(image_content=content)
            return [
                {
                    'color': {
                        'red': color.color.red,
                        'green': color.color.green,
                        'blue': color.color.blue
                    },
                    'score': color.score,
                    'percentRounded': round(color.pixel_fraction * 100)
                }
                for color in properties.dominant_colors.colors
            ]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vision AI color analysis from URI failed: {str(e)}"
            )
        
    async def analyze_colors_from_uri(self, image_uri: str) -> List[Dict]:
        """Analyze image using Vision AI and return dominant colors from URI."""
        try:
            properties = await self.vision.detect_image_properties_from_uri(image_uri=image_uri)
            return [
                {
                    'color': {
                        'red': color.color.red,
                        'green': color.color.green,
                        'blue': color.color.blue
                    },
                    'score': color.score,
                    'percentRounded': round(color.pixel_fraction * 100)
                }
                for color in properties.dominant_colors.colors
            ]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vision AI color analysis from URI failed: {str(e)}"
            )
        
    async def analyze_faces(self, content: bytes) -> List[Dict]:
        """Analyze image using Vision AI and return face annotations."""
        try:
            faces = await self.vision.detect_faces(image_content=content)
            return [
                {
                    'roll_angle': face.roll_angle,
                    'tilt_angle': face.tilt_angle,
                    'pan_angle': face.pan_angle
                }
                for face in faces
            ]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vision AI face analysis failed: {str(e)}"
            )
        
    async def analyze_faces_from_uri(self, image_uri: str) -> List[Dict]:
        """Analyze image using Vision AI and return face annotations from URI."""
        try:
            faces = await self.vision.detect_faces_from_uri(image_uri=image_uri)
            return [
                {
                    'roll_angle': face.roll_angle,
                    'tilt_angle': face.tilt_angle,
                    'pan_angle': face.pan_angle
                }
                for face in faces
            ]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vision AI face analysis from URI failed: {str(e)}"
            )
    
    def build_search_term(self, keyword: str, original_labels: List[Dict], original_colors: List[Dict]) -> str:
        """Combine keyword, labels, colors into a search term."""
        keywords = [keyword]
        keywords.extend(self.map_labels_to_keywords(original_labels))
        color_keywords = self.map_colors_to_keywords(original_colors)
        if color_keywords:
            keywords.append(random.choice(color_keywords))
        return " ".join(keywords)
    
    def map_labels_to_keywords(self, labels: List[Dict]) -> List[str]:
        """Map image labels to generalized keywords."""
        # Filter labels with score > 0.5
        high_confidence_labels = [
            label['description'].lower()
            for label in labels
            if label['score'] > 0.5
        ]
        # Get one random high confidence label
        high_confidence_labels = random.sample(high_confidence_labels, min(1, len(high_confidence_labels)))  
        
        # Get one random low confidence label (score < 0.7)
        low_confidence_labels = [
            label['description'].lower()
            for label in labels
            if 0.5 < label['score'] < 0.7
        ]
        
        # Return one random low confidence labels or high confidence labels if low not available
        return random.sample(low_confidence_labels, min(1, len(low_confidence_labels))) if low_confidence_labels else high_confidence_labels

    def map_colors_to_keywords(self, colors: List[Dict]) -> List[str]:
        """Map dominant colors to generalized keywords."""
        def rgb_to_keyword(rgb: Tuple[int, int, int]) -> str:
            red, green, blue = rgb
            if red > 100 and green > 100 and blue > 100:
                return "light"
            elif red > green and red > blue:
                return "red" if green < 100 and blue < 100 else "brown"
            elif green > red and green > blue:
                return "green"
            elif blue > red and blue > green:
                return "blue"
            elif abs(red - green) < 20 and blue < 100:
                return "yellow"
            else:
                return "gray"
        
        # Extract RGB and map to keywords
        keywords = [
            rgb_to_keyword(
                (color['color']['red'], color['color']['green'], color['color']['blue'])
            )
            for color in colors
        ]
        return list(set(keywords))  # Deduplicate keywords

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
                        # Split search term into words
                        words = search_term.split()
                        
                        # Try progressively shorter search terms
                        while len(words) > 1:
                            words.pop()  # Remove last word
                            shorter_term = " ".join(words)
                            
                            # Try search with shorter term
                            params["q"] = shorter_term
                            async with session.get(search_url, params=params) as retry_response:
                                retry_data = await retry_response.json()
                                if retry_data.get("items"):
                                    return retry_data["items"][0]["link"]
                        
                        # No images were found with any combination
                        raise HTTPException(
                            status_code=404,
                            detail=f"No images found for search term or its variations: {search_term}"
                        )
                    
                    return data["items"][0]["link"]
                    
            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error during image search: {str(e)}"
                )
            
    async def store_image_to_storage(self, 
        content: bytes, 
        result_image_url: str
    ) -> Tuple[str, str]:
        """Store original and pair image to Firebase Storage."""
        original_image_id = str(uuid.uuid4())
        result_image_id = str(uuid.uuid4())

        try:
            bucket = self.firebase.storage

            # Store original image
            original_blob = bucket.blob(f"originals/{original_image_id}.jpg")
            original_blob.upload_from_string(content, content_type='image/jpeg')
            original_blob.make_public()

            # Store result image
            async with aiohttp.ClientSession() as session:
                async with session.get(result_image_url) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to download result image: {await response.text()}"
                        )

                    result_image_content = await response.read()
                    result_blob = bucket.blob(f"results/{result_image_id}.jpg")
                    result_blob.upload_from_string(result_image_content, content_type='image/jpeg')
                    result_blob.make_public()

            return original_blob.public_url, result_blob.public_url

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store images to Firebase Storage: {str(e)}"
            )

    def store_pairing_record(self, 
        original_image_uri: str,
        original_keyword: str,
        result_image_uri: str,
        original_labels: List[Dict],
        original_colors: List[Dict],
        original_faces: List[Dict],
        result_labels: List[Dict],
        result_colors: List[Dict],
        result_faces: List[Dict],
        percentage_match: float,
        auth: dict
    ) -> Dict:
        """Store pairing record in Firestore."""
        try:
            pairing_id = str(uuid.uuid4())
            timestamp = datetime.now(datetime.timezone.utc)
            
            record = {
                'id': pairing_id,
                'timestamp': timestamp,
                'original_image_uri': original_image_uri,
                'original_keyword': original_keyword,
                'result_image_uri': result_image_uri,
                'original_labels': original_labels,
                'original_colors': original_colors,
                'original_faces': original_faces,
                'result_labels': result_labels,
                'result_colors': result_colors,
                'result_faces': result_faces,
                'percentage_match': percentage_match
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
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store pairing record: {str(e)}"
            )
        
    def calculate_percentage_match(self,
        original_labels: List[Dict],
        original_colors: List[Dict],
        original_faces: List[Dict],
        result_labels: List[Dict],
        result_colors: List[Dict],
        result_faces: List[Dict]
    ) -> float:
        """Calculate percentage match between original and result images."""
        # Calculate label match percentage
        # Early return if no labels
        if not original_labels and not result_labels:
            label_match = 1.0
        else: label_match = self.calculate_label_match(original_labels, result_labels)
        
        # Calculate color match percentage
        if not original_colors and not result_colors:
            color_match = 1.0
        else: color_match = self.calculate_color_match(original_colors, result_colors)
        
        # Calculate face match percentage
        if not original_faces and not result_faces:
            face_match = 1.0
        else: face_match = self.calculate_face_match(original_faces, result_faces)
        
        # Calculate total match percentage
        return (label_match + color_match + face_match) / 3


    def calculate_label_match(self, original_labels: List[Dict], result_labels: List[Dict]) -> float:
        """Identify common labels percentage."""
        original_set = set(label['description'] for label in original_labels)
        result_set = set(label['description'] for label in result_labels)

        # Calculate common label
        if not original_set:  # Avoid division by zero
            return 0.0
        common_labels = original_set.intersection(result_set)
        
        return len(common_labels) / len(original_set)
    
    def calculate_color_match(self, original_colors: List[Dict], result_colors: List[Dict]) -> float:
        """Identify common colors percentage."""
        original_set = set(color['color'] for color in original_colors)
        result_set = set(color['color'] for color in result_colors)
        
        # Convert RGB to color keywords for comparison
        original_keywords = set(self.map_colors_to_keywords([{'color': color} for color in original_set]))
        result_keywords = set(self.map_colors_to_keywords([{'color': color} for color in result_set]))
        
        # Handle empty case
        if not original_keywords:
            return 0.0
        common_colors = original_keywords.intersection(result_keywords)
        
        return len(common_colors) / len(original_set)
    
    def calculate_face_match(self, original_faces: List[Dict], result_faces: List[Dict]) -> float:
        """Calculate face match percentage."""
        original_set = set((face['roll_angle'], face['tilt_angle'], face['pan_angle']) for face in original_faces)
        result_set = set((face['roll_angle'], face['tilt_angle'], face['pan_angle']) for face in result_faces)
        
        # if any of them is empty
        if not original_set:
            return 0.0
        if not result_set:
            return 0.0
        
        # Calculate roll, tilt and pan similarity
        max_similarity = 0.0
        for original_face in original_set:
            face_similarities = []
            for result_face in result_set:
                roll_diff = abs(original_face[0] - result_face[0])
                tilt_diff = abs(original_face[1] - result_face[1])
                pan_diff = abs(original_face[2] - result_face[2])
                # Calculate similarity score (1 - normalized difference)
                similarity = 1.0 - (roll_diff + tilt_diff + pan_diff) / 180.0
                face_similarities.append(max(0.0, similarity))
            if face_similarities:
                max_similarity += max(face_similarities)
        
        # Return average similarity normalized by number of faces in original image
        return max_similarity / len(original_set) if original_set else 0.0

@lru_cache()
def get_pairing_service() -> PairingService:
    return PairingService()