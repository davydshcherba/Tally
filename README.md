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

By default the app connects to `postgresql+asyncpg://postgres:postgres@localhost:5432/postgres`. Override this with the `DATABASE_URL` environment variable.

### Run tests

Requires a running PostgreSQL instance (`docker compose up -d postgres`). Tests run against a separate `tally_test` database, created automatically on first run.

```bash
uv run ruff check .   # lint
uv run pytest         # tests
```

Both run on every pull request via [GitHub Actions](.github/workflows/ci.yml).

## API reference

| Method   | Path           | Description                                    |
|----------|----------------|-------------------------------------------------|
| `POST`   | `/`            | Create a short link for a given URL             |
| `GET`    | `/{code}`      | Redirect to the original URL and log the click  |
| `GET`    | `/{code}/stats`| Get total and unique click counts for a link    |
| `DELETE` | `/{code}`      | Delete a short link                             |
| `GET`    | `/health`      | Liveness check                                  |

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
