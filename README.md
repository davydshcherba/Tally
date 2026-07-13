<p align="center">
  <img src="images/icon.png" alt="Tally logo" width="200">
</p>

# Tally

[![CI](https://github.com/davydshcherba/Tally/actions/workflows/ci.yml/badge.svg)](https://github.com/davydshcherba/Tally/actions/workflows/ci.yml)

A fast, self-hosted URL shortener with built-in click analytics.

## Features

- Shorten any URL to a compact, random 7-character code
- Redirect visitors from the short code to the original URL
- Track total and unique (per-IP) clicks for every link
- Delete links on demand
- Async FastAPI + PostgreSQL, ready to run with a single `docker compose up`

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) — async web framework
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async) + [asyncpg](https://github.com/MagicStack/asyncpg) — ORM and PostgreSQL driver
- [PostgreSQL 16](https://www.postgresql.org/) — database
- [uv](https://docs.astral.sh/uv/) — Python packaging and dependency management

## Getting started

### Configure credentials

Database credentials are read from a `.env` file (used by both Docker Compose and the app):

```bash
cp .env.example .env
# edit .env — at minimum set a real POSTGRES_PASSWORD for anything beyond local dev
```

Without a `.env`, everything falls back to the local-dev defaults (`postgres`/`postgres`).

The admin endpoints (listing and deleting links) are protected by an API key: set `API_KEY` in `.env` and pass it in the `X-API-Key` header. While `API_KEY` is unset, those endpoints are disabled and respond with `503`.

### Run with Docker Compose (recommended)

```bash
docker compose up -d --build
```

This starts PostgreSQL and the API together. The API is available at `http://localhost:8000`.

### Run locally

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and a running PostgreSQL instance.

```bash
# start just the database
docker compose up -d postgres

# install dependencies
uv sync

# run the API with auto-reload
uv run uvicorn app.main:app --reload
```

The app builds its connection string from the `POSTGRES_*` variables in `.env` (falling back to `postgres`/`postgres` on `localhost:5432`). Setting `DATABASE_URL` directly overrides all of them.

### Run tests

Requires a running PostgreSQL instance (`docker compose up -d postgres`). Tests run against a separate `tally_test` database, created automatically on first run.

```bash
uv run ruff check .   # lint
uv run pytest         # tests
```

Both run on every pull request via [GitHub Actions](.github/workflows/ci.yml).

## API reference

| Method   | Path           | Auth        | Description                                    |
|----------|----------------|-------------|-------------------------------------------------|
| `POST`   | `/`            | —           | Create a short link for a given URL             |
| `GET`    | `/`            | `X-API-Key` | List existing links (paginated)                 |
| `GET`    | `/{code}`      | —           | Redirect to the original URL and log the click  |
| `GET`    | `/{code}/stats`| —           | Get total and unique click counts for a link    |
| `DELETE` | `/{code}`      | `X-API-Key` | Delete a short link                             |
| `GET`    | `/health`      | —           | Liveness check                                  |

Authenticated endpoints require the `X-API-Key` header matching the `API_KEY` env var:

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/
```

### Create a link

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/some/page"}'
```

```json
{
  "code": "mFEIt3m",
  "short_url": "http://localhost:8000/mFEIt3m",
  "original_url": "https://example.com/some/page",
  "created_at": "2026-07-09T07:29:17.476624"
}
```

### Get click stats

```bash
curl http://localhost:8000/mFEIt3m/stats
```

```json
{
  "code": "mFEIt3m",
  "total_clicks": 2,
  "unique_clicks": 1
}
```

Interactive API docs (Swagger UI) are available at `http://localhost:8000/docs` while the app is running.
