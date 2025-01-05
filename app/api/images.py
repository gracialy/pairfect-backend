import uuid
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from app.core.security import get_auth
from app.services.pairing_service import PairingService, get_pairing_service
from typing import Dict
from app.core.firebase import get_firebase_manager
from app.core.config import get_settings

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/pair")
async def pair_images(
    image: UploadFile = File(...),
    keyword: str = Form(...),
    include_faces: bool = Form(...),
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

        print(f"Percentage match: {percentage_match}")
                 
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