from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, HTTPException
from . import models  # noqa: F401  register models in BaseModel.metadata
from .db import init_models
from .schemas import LinkCreate, LinkOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("", response_model=LinkOut, status_code=201)
def create_link(payload: LinkCreate):
    ...  # generate code, check for collision, INSERT

@app.get("/{code}/stats")
def get_stats(code: str):
    ...  # total/unique clicks + aggregations

@app.delete("/{code}", status_code=204)
def delete_link(code: str):
    ...

# ---- Services ----
@app.get("/health")
def health():
    return {"status": "ok"}

# ---- Catch-all redirect: use the latest ----
@app.get("/{code}")
def redirect(code: str):
    ...  # SELECT → write click → RedirectResponse(original, status_code=302)
    raise HTTPException(status_code=404)