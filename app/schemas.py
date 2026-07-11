from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

# Request body for POST /: the URL the client wants shortened
class LinkCreate(BaseModel):
    url: HttpUrl
    # optional expiration timestamp; once past, the link stops redirecting
    expires_at: datetime | None = None
    # optional custom alias; if omitted, a random code is generated
    code: str | None = Field(default=None, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")

# Response body returned after creating (or looking up) a link
class LinkOut(BaseModel):
    code: str
    short_url: str
    original_url: HttpUrl
    created_at: datetime
    expires_at: datetime | None = None

# Paginated response for GET /: one page of links plus paging metadata
class LinkList(BaseModel):
    items: list[LinkOut]
    total: int
    limit: int
    offset: int
