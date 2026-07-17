from datetime import datetime, timezone

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, field_validator

# Request body for POST /: the URL the client wants shortened
class LinkCreate(BaseModel):
    url: HttpUrl
    # optional expiration timestamp; once past, the link stops redirecting.
    # AwareDatetime rejects naive input, so clients can't accidentally submit
    # local time that would be silently stored as UTC.
    expires_at: AwareDatetime | None = None
    # optional custom alias; if omitted, a random code is generated
    code: str | None = Field(default=None, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")

    # A minimal working example so Swagger UI's "Try it out" doesn't prefill
    # expires_at with the current time (creating an already-expired link) or
    # code with pattern-generated noise.
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://example.com/some/very/long/url",
                    "expires_at": None,
                    "code": None,
                }
            ]
        }
    )

    @field_validator("expires_at")
    @classmethod
    def expires_at_must_be_in_future(cls, value: datetime | None) -> datetime | None:
        if value is not None and value <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        return value

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
