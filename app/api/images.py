import uuid
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from app.core.security import get_auth
from app.services.pairing_service import PairingService, get_pairing_service
from app.models.images import PairImagesBody, EncryptImageBody, DecryptImageBody
from typing import Dict, Optional
import base64
import json
import requests
from app.core.config import get_settings
from fastapi.responses import FileResponse

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/pair")
async def pair_images(
    image: UploadFile = File(...),
    keyword: str = Form(...),    
    include_faces: bool = Form(False),
    auth: dict = Depends(get_auth),
    pairing_service: PairingService = Depends(get_pairing_service)
):
    """
    Pair an uploaded image with a web image based on Vision AI analysis and keyword.
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read the uploaded image
        content = await image.read()

        # Initialize lists for labels, colors, and faces
        original_labels, original_colors, original_faces = [], [], []

        # Analyze the original image 
        original_labels, original_colors, original_faces = await pairing_service.analyze_image(content, include_faces)
        
        # Combine keyword with labels, colors, and faces for search
        search_term = pairing_service.build_search_term(keyword, original_labels, original_colors)
        
        # Search for matching image
        result_image_url = await pairing_service.search_image(search_term)

        # Store the image to Firebase Storage
        original_uri, result_uri = await pairing_service.store_image_to_storage(content, result_image_url)

        # Get result's labels, colors, and faces
        result_labels, result_colors, result_faces = await pairing_service.analyze_image_from_uri(result_uri, include_faces)

        # Calculate percentage match
        percentage_match = pairing_service.calculate_percentage_match(
            original_labels=original_labels,
            original_colors=original_colors,
            original_faces=original_faces,
            result_labels=result_labels,
            result_colors=result_colors,
            result_faces=result_faces
        )
                 
        # Store pairing record
        result = pairing_service.store_pairing_record(
            original_image_uri=original_uri,
            original_keyword=keyword,
            result_image_uri=result_uri,
            original_labels=original_labels,
            original_colors=original_colors,
            original_faces=original_faces,
            result_labels=result_labels,
            result_colors=result_colors,
            result_faces=result_faces,
            percentage_match=percentage_match,
            auth=auth
        )
        
        # return result
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image pair: {str(e)}"
        )
    
# Integration with External API
ENCRYPT_API_URL = "https://furina-encryption-service.codebloop.my.id/api/encrypt"
DECRYPT_API_URL = "https://furina-encryption-service.codebloop.my.id/api/decrypt"

# Convert Image to Base64
def image_to_base64(file: UploadFile):
    return base64.b64encode(file.file.read()).decode("utf-8")

@router.post("/encrypt")
async def encrypt_image_api(
    image: UploadFile, 
    sensitivity: str = Form("medium"),
    auth: dict = Depends(get_auth),
):
    """
    Encrypt an image with post-quantum safe encryption.
    """
    body = EncryptImageBody(sensitivity=sensitivity)
    try:
        settings = get_settings()
        FURINA_API_KEY = settings.FURINA_API_KEY
        print(FURINA_API_KEY)

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

@router.post("/decrypt")
async def decrypt_image_api(
    body: DecryptImageBody,
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