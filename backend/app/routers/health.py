from fastapi import APIRouter

router = APIRouter()


# Liveness check for the API
@router.get("/health")
def health():
    return {"status": "ok"}
