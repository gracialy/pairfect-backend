from pydantic import BaseModel

class APIKeyRequest(BaseModel):
    client_id: str  # The ID of the client (app or organization)
