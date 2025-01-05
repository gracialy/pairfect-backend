from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from app.core.security import get_auth
from app.services.pairing_service import PairingService, get_pairing_service
from typing import Dict

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/pair")
async def pair_images(
    image: UploadFile = File(...),
    keyword: str = Form(...),
    auth: dict = Depends(get_auth),
    pairing_service: PairingService = Depends(get_pairing_service)
):
    """
    Pair an uploaded image with a web image based on Vision AI analysis and keyword.
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read image content
        content = await image.read()
        
        # Get image labels from Vision AI
        labels = await pairing_service.analyze_image(content)

        print(labels)
        
        # Combine keyword with labels for search
        search_term = f"{keyword} {' '.join(labels)}"

        print(search_term)
        
        # Search for matching image
        result_image_url = await pairing_service.search_image(search_term)

        print(result_image_url)
        
        # Store pairing record
        result = pairing_service.store_pairing_record(
            original_image_content=content,
            keyword=keyword,
            labels=labels,
            result_image_url=result_image_url,
            auth=auth
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image pair: {str(e)}"
        )