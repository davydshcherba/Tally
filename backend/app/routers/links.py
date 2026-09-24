from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..codes import resolve_code
from ..db import get_db
from ..limiter import limiter
from ..models import LinkModel, StatsModel
from ..schemas import LinkCreate, LinkList, LinkOut
from ..security import require_api_key

router = APIRouter()


def _to_link_out(link: LinkModel, request: Request) -> LinkOut:
    return LinkOut(
        code=link.code,
        short_url=str(request.base_url) + link.code,
        original_url=link.original_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )


async def _get_link_or_404(db: AsyncSession, code: str) -> LinkModel:
    link = await db.get(LinkModel, code)
    if link is None:
        raise HTTPException(status_code=404)
    return link


# Create a new short link for the given URL
@router.post("/", response_model=LinkOut, status_code=201)
@limiter.limit("10/minute")
async def create_link(payload: LinkCreate, request: Request, db: AsyncSession = Depends(get_db)):
    code = await resolve_code(db, payload.code)

    link = LinkModel(code=code, original_url=str(payload.url), expires_at=payload.expires_at)
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return _to_link_out(link, request)


# List existing links, newest first, as a limit/offset page
@router.get("/", response_model=LinkList, dependencies=[Depends(require_api_key)])
async def list_links(
    request: Request,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    total = (await db.execute(select(func.count()).select_from(LinkModel))).scalar_one()

    page = select(LinkModel).offset(offset).limit(limit)
    # tie-break on code so pages stay stable when created_at collides
    page = page.order_by(LinkModel.created_at.desc(), LinkModel.code)
    links = (await db.execute(page)).scalars().all()

    return LinkList(
        items=[_to_link_out(link, request) for link in links],
        total=total,
        limit=limit,
        offset=offset,
    )


# Return total/unique click counts for a short link
@router.get("/{code}/stats")
async def get_stats(code: str, db: AsyncSession = Depends(get_db)):
    await _get_link_or_404(db, code)

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
@router.delete("/{code}", status_code=204, dependencies=[Depends(require_api_key)])
async def delete_link(code: str, db: AsyncSession = Depends(get_db)):
    link = await _get_link_or_404(db, code)

    await db.delete(link)
    await db.commit()
