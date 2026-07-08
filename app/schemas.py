from pydantic import BaseModel, HttpUrl
from datetime import datetime

class LinkCreate(BaseModel):
    url: HttpUrl                     

class LinkOut(BaseModel):
    code: str
    short_url: str
    original_url: HttpUrl
    created_at: datetime
