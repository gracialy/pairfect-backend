from pydantic import BaseModel

class APIKeyRequest(BaseModel):
    client_id: str 