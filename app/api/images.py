from fastapi import APIRouter, Form, HTTPException, Depends, File, UploadFile
from app.core.security import get_auth
from app.models.images import ImageAnalysisResult, ImagePairingResult
from app.services.image_service import ImageService, get_image_service
from datetime import datetime

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/analyze", response_model=ImageAnalysisResult)
async def hybrid_analyze_image(
    image: UploadFile = File(...),
    auth: dict = Depends(get_auth),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Analyze an uploaded image using Google Cloud Vision AI and store results
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read image content
        content = await image.read()
        
        # Store image
        blob_path = "dummy"
        analysis_id = "dummy"
        # blob_path, analysis_id = await image_service.store_image(
        #     content, 
        #     image.filename, 
        #     image.content_type
        # )
        
        # Analyze image
        analysis_result = await image_service.analyze_image(content)
        # analysis_result = {
        #     'labels': [
        #         {
        #             'description': 'dummy',
        #             'score': 0.0,
        #             'confidence': 0.0,
        #             'topicality': 0.0
        #         }
        #     ]
        # }
        
        # Store analysis record
        timestamp = datetime.utcnow()
        # timestamp = await image_service.store_analysis_record(
        #     analysis_id=analysis_id,
        #     blob_path=blob_path,
        #     filename=image.filename,
        #     content_type=image.content_type,
        #     analysis_result=analysis_result,
        #     auth=auth
        # )
        
        return ImageAnalysisResult(
            id=analysis_id,
            timestamp=timestamp,
            image_url=f"/storage/{blob_path}",
            analysis=analysis_result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
    
@router.post("/pair", response_model=ImagePairingResult)
async def pair_image(
    image: UploadFile = File(...),
    keyword: str = Form(...),
    auth: dict = Depends(get_auth),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Find and analyze a matching image from the web based on the uploaded image and keyword
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read image content
        content = await image.read()
        
        # Store original image
        blob_path = "dummy"
        analysis_id = "dummy"
        # blob_path, analysis_id = await image_service.store_image(
        #     content, 
        #     image.filename, 
        #     image.content_type
        # )
        
        # Perform pairing analysis
        analysis_result = await image_service.pair_images(content, keyword)
        
        # Store analysis record
        timestamp = await image_service.store_analysis_record(
            analysis_id=analysis_id,
            blob_path=blob_path,
            filename=image.filename,
            content_type=image.content_type,
            analysis_result=analysis_result,
            auth=auth
        )
        
        return ImagePairingResult(
            id=analysis_id,
            timestamp=timestamp,
            image_url=f"/storage/{blob_path}",
            analysis=analysis_result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image pair: {str(e)}"
        )