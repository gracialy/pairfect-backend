from pydantic import BaseModel
from typing import Optional

class PairImagesRequest(BaseModel):
    keyword: str
    include_faces: Optional[bool] = False  

class EncryptImageRequest(BaseModel):
    text: str
    sensitivity: Optional[str] = "medium"  

class DecryptImageRequest(BaseModel):
    key_id: str
    cipher_text: str
    iv: str