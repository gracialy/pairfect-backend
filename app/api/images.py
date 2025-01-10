import asyncio
import uuid
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from app.core.security import get_auth
from app.services.pairing_service import PairingService, get_pairing_service
import base64
import json
import requests
from app.core.config import get_settings
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi import status
from datetime import datetime

class DecryptionsBody(BaseModel):
    key_id: str
    cipher_text: str
    iv: str

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/pairs")
async def pair_images(
    image: UploadFile = File(...),
    keyword: str = Form(...),    
    include_faces: bool = Form(False),
    auth: dict = Depends(get_auth),
    pairing_service: PairingService = Depends(get_pairing_service),
):
    """
    Pair an uploaded image with a web image based on Vision AI analysis and keyword.
    """

    def log_timestamp(step):
        print(f"[{datetime.now()}] Completed: {step}")

    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")

    try:
        # Read the uploaded image
        content = await image.read()
        log_timestamp("Reading uploaded image")

        # Initialize lists for labels, colors, and faces
        original_labels, original_colors, original_faces = [], [], []

        # Analyze the original image 
        original_labels, original_colors, original_faces = await pairing_service.analyze_image(content, include_faces)
        log_timestamp("Analyzing original image")
        
        # Combine keyword with labels, colors, and faces for search
        search_term = pairing_service.build_search_term(keyword, original_labels, original_colors)
        log_timestamp("Building search term")
        
        # Search for matching image
        result_image_url = await pairing_service.search_image(search_term)
        log_timestamp("Searching matching image")
        print(result_image_url)

        # Run storage and analysis tasks concurrently
        store_task = pairing_service.store_image_to_storage(content)
        analyze_task = pairing_service.analyze_image_from_uri(result_image_url, include_faces)
        
        # Wait for both tasks to complete
        (original_uri), (result_labels, result_colors, result_faces) = await asyncio.gather(
            store_task,
            analyze_task
        )
        log_timestamp("Storage and analysis tasks")

        # Calculate percentage match
        label_match, color_match, face_match, overall_match = pairing_service.calculate_percentage_match(
            original_labels=original_labels,
            original_colors=original_colors,
            original_faces=original_faces,
            result_labels=result_labels,
            result_colors=result_colors,
            result_faces=result_faces
        )
        log_timestamp("Calculating percentage match")
                 
        # Store pairing record
        result = pairing_service.store_pairing_record(
            original_image_uri=original_uri,
            original_keyword=keyword,
            result_image_uri=result_image_url,
            original_labels=original_labels,
            original_colors=original_colors,
            original_faces=original_faces,
            result_labels=result_labels,
            result_colors=result_colors,
            result_faces=result_faces,
            label_match=label_match,
            color_match=color_match,
            face_match=face_match,
            overall_match=overall_match,
            auth=auth
        )
        log_timestamp("Storing pairing record")
        
        return {
            'id': result['id'],
            'original_image_uri': result['original_image_uri'],
            'original_keyword': result['original_keyword'],
            'result_image_uri': result['result_image_uri'],
            'label_match': result['label_match'],
            'color_match': result['color_match'],
            'face_match': result['face_match'],
            'overall_match': result['overall_match']
        }
        
    except Exception as e:
        print(f"[{datetime.now()}] Error occurred: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image pair: {str(e)}"
        )
    
@router.get("/pairs")
async def get_pairing_records(
    auth: dict = Depends(get_auth),
    pairing_service: PairingService = Depends(get_pairing_service),
):
    """
    Get all pairing records.
    """
    try:
        return pairing_service.get_pairing_records(auth)
    except Exception as e:
        return {"error": str(e)}
    
# Integration with External API
ENCRYPT_API_URL = "https://furina-encryption-service.codebloop.my.id/api/encrypt"
DECRYPT_API_URL = "https://furina-encryption-service.codebloop.my.id/api/decrypt"

# Convert Image to Base64
def image_to_base64(file: UploadFile):
    return base64.b64encode(file.file.read()).decode("utf-8")

@router.post("/encryptions")
async def encrypt_image_api(
    image: UploadFile, 
    sensitivity: str = Form("medium"),
    auth: dict = Depends(get_auth),
):
    """
    Encrypt an image with post-quantum safe encryption.
    """
    try:
        settings = get_settings()
        FURINA_API_KEY = settings.FURINA_API_KEY

        # Convert image to Base64
        image_base64 = image_to_base64(image)

        # Call external encryption API
        payload = {
            "text": image_base64,
            "sensitivity": sensitivity
        }
        headers = {
            "accept": "application/json",
            "furina-encryption-service": FURINA_API_KEY,
            "Content-Type": "application/json"
        }
        response = requests.post(ENCRYPT_API_URL, headers=headers, data=json.dumps(payload))

        if response.status_code != 200:
            return {"error": "Failed to encrypt the image", "details": response.text}

        # Return encrypted data
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@router.post("/decryptions")
async def decrypt_image_api(
    body: DecryptionsBody,
    auth: dict = Depends(get_auth),
):
    """
    Decrypt an image encrypted with post-quantum safe encryption.
    """
    try:
        settings = get_settings()
        FURINA_API_KEY = settings.FURINA_API_KEY

        # Call external decryption API
        payload = {
            "key_id": body.key_id,
            "cipher_text": body.cipher_text,
            "iv": body.iv
        }
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "furina-encryption-service": FURINA_API_KEY
        }
        response = requests.post(DECRYPT_API_URL, headers=headers, data=json.dumps(payload))

        if response.status_code != 200:
            return {"error": "Failed to decrypt the image", "details": response.text}

        # Extract Base64 string from response
        decrypted_data = response.json().get("text", "")
        if not decrypted_data:
            return {"error": "No decrypted data found"}

        # Save decrypted Base64 as image
        output_path = "decrypted_image.jpg"
        with open(output_path, "wb") as img_file:
            img_file.write(base64.b64decode(decrypted_data))

        # Return the image as a downloadable file
        return FileResponse(output_path, media_type="image/jpeg", filename="decrypted_image.jpg")
    except Exception as e:
        return {"error": str(e)}