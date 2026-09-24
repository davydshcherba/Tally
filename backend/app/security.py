import os
import secrets

from fastapi import Header, HTTPException


# Guard for admin endpoints (list/delete): requires the X-API-Key header to
# match the API_KEY env var. Fails closed with 503 when no key is configured.
def require_api_key(x_api_key: str | None = Header(None)) -> None:
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="API_KEY is not configured")
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode(), expected.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
