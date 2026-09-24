# =====================================================================
#                                     _
#                             _      | |
#                     _      | | _.-'| |
#              _     | |_.-'`| |     | |
#             | |.-'`| |     | |     | |
#          _.-| |    | |     | |     | |
#       .-'   |_|    |_|     |_|     |_|
#
#        _____     _ _
#       |_   _|_ _| | |_   _
#         | |/ _` | | | | | |
#         | | (_| | | | |_| |
#         |_|\__,_|_|_|\__, |
#                       |___/
#
#                                        by: Davyd
# =====================================================================

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from . import models  # noqa: F401  register models in BaseModel.metadata
from .limiter import limiter
from .routers import health, links, redirect

# Migrations are applied as a separate deploy step (`alembic upgrade head`),
# not on app startup — see docker-compose.yml's `migrate` service.
app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Order matters: the catch-all redirect router must come last
app.include_router(links.router)
app.include_router(health.router)
app.include_router(redirect.router)
