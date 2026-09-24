from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import LinkModel, StatsModel

router = APIRouter()


def _is_expired(link: LinkModel) -> bool:
    return link.expires_at is not None and link.expires_at <= datetime.now(timezone.utc)


# Catch-all: must be included after every other router so its `/{code}`
# path doesn't shadow fixed routes like /health.
# Resolve a short code, log the click, and redirect to the original URL
@router.get("/{code}")
async def redirect(code: str, request: Request, db: AsyncSession = Depends(get_db)):
    link = await db.get(LinkModel, code)
    if link is None:
        raise HTTPException(status_code=404)

    if _is_expired(link):
        raise HTTPException(status_code=410, detail="Link has expired")

    db.add(
        StatsModel(
            link_code=code,
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()

    return RedirectResponse(link.original_url, status_code=302)
