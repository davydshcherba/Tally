from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, HTTPException
from . import models  # noqa: F401  register models in BaseModel.metadata
from .db import init_models
from .schemas import LinkCreate, LinkOut


# Create DB tables on startup before the app starts serving requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    yield


app = FastAPI(lifespan=lifespan)


# Create a new short link for the given URL
@app.post("", response_model=LinkOut, status_code=201)
def create_link(payload: LinkCreate):
    ...  # generate code, check for collision, INSERT

# Return total/unique click counts for a short link
@app.get("/{code}/stats")
def get_stats(code: str):
    ...  # total/unique clicks + aggregations

# Delete a short link by its code
@app.delete("/{code}", status_code=204)
def delete_link(code: str):
    ...

# ---- Services ----
# Liveness check for the API
@app.get("/health")
def health():
    return {"status": "ok"}

# ---- Catch-all redirect: use the latest ----
# Resolve a short code, log the click, and redirect to the original URL
@app.get("/{code}")
def redirect(code: str):
    ...  # SELECT → write click → RedirectResponse(original, status_code=302)
    raise HTTPException(status_code=404)