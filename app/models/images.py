from pydantic import BaseModel
from typing import Optional

class PairImagesBody(BaseModel):
    keyword: str
    include_faces: Optional[bool] = False  

class EncryptImageBody(BaseModel):
    sensitivity: Optional[str] = "medium"  

class DecryptImageBody(BaseModel):
    key_id: str
    cipher_text: str
    iv: str