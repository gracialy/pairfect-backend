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

class PairedImageAnalysis(BaseModel):
    url: str
    analysis: Analysis

class Compatibility(BaseModel):
    score: float
    common_elements: List[str]
    unique_elements1: List[str]
    unique_elements2: List[str]
    confidence: float

class ImagePairingResult(BaseModel):
    id: str
    timestamp: datetime
    image_url: str
    analysis: dict