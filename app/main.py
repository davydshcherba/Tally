from fastapi import FastAPI, APIRouter, HTTPException
from .schemas import LinkCreate, LinkOut


app = FastAPI()


@app.post("", response_model=LinkOut, status_code=201)
def create_link(payload: LinkCreate):
    ...  # генеруєш код, перевіряєш колізію, INSERT

@app.get("/{code}/stats")
def get_stats(code: str):
    ...  # total/unique кліки + агрегації

@app.delete("/{code}", status_code=204)
def delete_link(code: str):
    ...

# ---- Службові ----
@app.get("/health")
def health():
    return {"status": "ok"}

# ---- Catch-all редірект: вмикаємо ОСТАННІМ ----
@app.get("/{code}")
def redirect(code: str):
    ...  # SELECT → пишеш клік → RedirectResponse(original, status_code=302)
    raise HTTPException(status_code=404)