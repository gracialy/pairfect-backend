from pydantic import BaseModel
from datetime import datetime
from typing import List

class Label(BaseModel):
    description: str
    score: float
    confidence: float
    topicality: float

class Analysis(BaseModel):
    labels: List[Label]

class ImageAnalysisResult(BaseModel):
    id: str
    timestamp: datetime
    image_url: str
    analysis: Analysis