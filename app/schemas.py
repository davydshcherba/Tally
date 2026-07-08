from pydantic import BaseModel, HttpUrl
from datetime import datetime

# Request body for POST /: the URL the client wants shortened
class LinkCreate(BaseModel):
    url: HttpUrl

# Response body returned after creating (or looking up) a link
class LinkOut(BaseModel):
    code: str
    short_url: str
    original_url: HttpUrl
    created_at: datetime
