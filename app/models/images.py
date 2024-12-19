from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class ImageAnalysisResult(BaseModel):
    id: str
    timestamp: datetime
    image_url: str
    analysis: Dict[str, Any]