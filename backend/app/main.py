import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

import alembic.command
import alembic.config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import health
from app.routers import auth as auth_router
from app.routers import households as households_router
from app.routers import accounts as accounts_router
from app.routers import categories as categories_router
from app.routers import transactions as tx_router
from app.routers import import_ as import_router
from app.routers import reports as reports_router
from app.routers import backup as backup_router
from app.routers import users as users_router
from app.routers import admin as admin_router
from app.routers import dashboard as dashboard_router
from app.routers import loans as loans_router
from app.routers import fixed_costs as fixed_costs_router
from app.routers import savings_goals as goals_router
from app.routers import search as search_router
from app.routers import forecast as forecast_router
from app.services import backup as backup_svc
from app.database import get_session

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _run_migrations() -> None:
    cfg = alembic.config.Config("alembic.ini")
    alembic.command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if not settings.TESTING:
            logger.info("Running database migrations")
            _run_migrations()
            asyncio.create_task(_backup_loop())
        logger.info("HELLEDGER started")
    except BaseException:
        logger.exception("Startup failed")
        sys.stderr.flush()
        raise
    yield


async def _backup_loop() -> None:
    while True:
        await asyncio.sleep(settings.BACKUP_INTERVAL_HOURS * 3600)
        if settings.DATABASE_PATH == ":memory:":
            continue
        try:
            db = get_session()
            try:
                backup_svc.create_backup(db, settings.BACKUP_PATH, settings.DATABASE_PATH)
                logger.info("Scheduled backup completed")
            finally:
                db.close()
        except Exception as exc:
            logger.error("Scheduled backup failed: %s", exc)


app = FastAPI(
    title="HELLEDGER",
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")
app.include_router(households_router.router, prefix="/api")
app.include_router(accounts_router.router, prefix="/api")
app.include_router(categories_router.router, prefix="/api")
app.include_router(tx_router.router, prefix="/api")
app.include_router(import_router.router, prefix="/api")
app.include_router(import_router.export_router, prefix="/api")
app.include_router(reports_router.router, prefix="/api")
app.include_router(backup_router.router, prefix="/api")
app.include_router(users_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")
app.include_router(dashboard_router.router, prefix="/api")
app.include_router(loans_router.router, prefix="/api")
app.include_router(fixed_costs_router.router, prefix="/api")
app.include_router(goals_router.router, prefix="/api")
app.include_router(search_router.router, prefix="/api")
app.include_router(forecast_router.router, prefix="/api")

_frontend = os.environ.get("HELLEDGER_FRONTEND") or os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "dist"
)
if os.path.isdir(_frontend):
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="static")
