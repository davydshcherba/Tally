import secrets
import string
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models  # noqa: F401  register models in BaseModel.metadata
from .db import get_db, run_migrations
from .models import LinkModel, StatsModel
from .schemas import LinkCreate, LinkList, LinkOut

CODE_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 7
MAX_CODE_ATTEMPTS = 5
# codes that would collide with fixed routes if used as a custom alias
RESERVED_CODES = {"health"}


# Apply pending DB migrations on startup before the app starts serving requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations()
    yield


app = FastAPI(lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


def _generate_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


# Create a new short link for the given URL
@app.post("/", response_model=LinkOut, status_code=201)
@limiter.limit("10/minute")
async def create_link(payload: LinkCreate, request: Request, db: AsyncSession = Depends(get_db)):
    if payload.code is not None:
        if payload.code in RESERVED_CODES or await db.get(LinkModel, payload.code) is not None:
            raise HTTPException(status_code=409, detail="Code already in use")
        code = payload.code
    else:
        for _ in range(MAX_CODE_ATTEMPTS):
            code = _generate_code()
            if await db.get(LinkModel, code) is None:
                break
        else:
            raise HTTPException(status_code=500, detail="Could not generate a unique code")

    link = LinkModel(code=code, original_url=str(payload.url), expires_at=payload.expires_at)
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return LinkOut(
        code=link.code,
        short_url=str(request.base_url) + link.code,
        original_url=link.original_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )

# List existing links, newest first, as a limit/offset page
@app.get("/", response_model=LinkList)
async def list_links(
    request: Request,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    total = (await db.execute(select(func.count()).select_from(LinkModel))).scalar_one()

    links = (
        (
            await db.execute(
                select(LinkModel)
                # tie-break on code so pages stay stable when created_at collides
                .order_by(LinkModel.created_at.desc(), LinkModel.code)
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )

    return LinkList(
        items=[
            LinkOut(
                code=link.code,
                short_url=str(request.base_url) + link.code,
                original_url=link.original_url,
                created_at=link.created_at,
                expires_at=link.expires_at,
            )
            for link in links
        ],
        total=total,
        limit=limit,
        offset=offset,
    )

# Return total/unique click counts for a short link
@app.get("/{code}/stats")
async def get_stats(code: str, db: AsyncSession = Depends(get_db)):
    link = await db.get(LinkModel, code)
    if link is None:
        raise HTTPException(status_code=404)

    total, unique = (
        await db.execute(
            select(
                func.count(StatsModel.id),
                func.count(func.distinct(StatsModel.ip_address)),
            ).where(StatsModel.link_code == code)
        )
    ).one()

    return {"code": code, "total_clicks": total, "unique_clicks": unique}

# Delete a short link by its code
@app.delete("/{code}", status_code=204)
async def delete_link(code: str, db: AsyncSession = Depends(get_db)):
    link = await db.get(LinkModel, code)
    if link is None:
        raise HTTPException(status_code=404)

    await db.delete(link)
    await db.commit()

# ---- Services ----
# Liveness check for the API
@app.get("/health")
def health():
    return {"status": "ok"}

# ---- Catch-all redirect: use the latest ----
# Resolve a short code, log the click, and redirect to the original URL
@app.get("/{code}")
async def redirect(code: str, request: Request, db: AsyncSession = Depends(get_db)):
    link = await db.get(LinkModel, code)
    if link is None:
        raise HTTPException(status_code=404)

    if link.expires_at is not None and link.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Link has expired")

    db.add(
        StatsModel(
            link_code=code,
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()

    return RedirectResponse(link.original_url, status_code=302)