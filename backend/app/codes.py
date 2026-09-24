import secrets
import string

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .models import LinkModel

CODE_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 7
MAX_CODE_ATTEMPTS = 5
# codes that would collide with fixed routes if used as a custom alias
RESERVED_CODES = {"health"}


def _generate_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


async def _is_taken(db: AsyncSession, code: str) -> bool:
    return await db.get(LinkModel, code) is not None


async def _claim_custom_code(db: AsyncSession, code: str) -> str:
    if code in RESERVED_CODES or await _is_taken(db, code):
        raise HTTPException(status_code=409, detail="Code already in use")
    return code


async def _generate_unique_code(db: AsyncSession) -> str:
    for _ in range(MAX_CODE_ATTEMPTS):
        code = _generate_code()
        if not await _is_taken(db, code):
            return code
    raise HTTPException(status_code=500, detail="Could not generate a unique code")


# Use the client's custom alias if given, otherwise generate a free random code
async def resolve_code(db: AsyncSession, requested: str | None) -> str:
    if requested is not None:
        return await _claim_custom_code(db, requested)
    return await _generate_unique_code(db)
