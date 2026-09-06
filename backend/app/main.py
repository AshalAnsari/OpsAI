import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.fulfillment_service import FulfillmentService
from app.utils.exceptions import AppError, app_error_handler

settings = get_settings()
logger = logging.getLogger("opspilot.fulfillment")


async def _fulfillment_cron_loop() -> None:
    """Poll periodically; advance orders when the configured interval has elapsed.

    Development: every 10 minutes. Production: every 60 minutes.
    """
    interval_minutes = settings.fulfillment_interval_minutes
    # Check often enough to fire soon after the interval, without busy-looping.
    poll_seconds = min(60, max(15, interval_minutes * 60 // 4))
    while True:
        try:
            db = SessionLocal()
            try:
                result = FulfillmentService(db).advance_day(triggered_by="cron", force=False)
                if not result.skipped:
                    logger.info(
                        "Fulfillment cron advanced %s order(s) (interval=%sm)",
                        result.advanced_count,
                        interval_minutes,
                    )
            except Exception:
                logger.exception("Fulfillment cron failed")
            finally:
                db.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Fulfillment cron loop error")
        await asyncio.sleep(poll_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task: asyncio.Task | None = None
    if settings.fulfillment_cron_enabled:
        task = asyncio.create_task(_fulfillment_cron_loop())
        logger.info(
            "Fulfillment cron enabled (interval_minutes=%s, app_env=%s)",
            settings.fulfillment_interval_minutes,
            settings.app_env,
        )
    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title=settings.app_name,
    description=(
        "OpsPilot is a fictional operational SaaS demo platform. "
        "These REST APIs are designed to later become controlled tools for an AI assistant. "
        "All business rules, RBAC, and audit logging live on the server."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {"success": True, "data": {"status": "ok", "service": "opspilot-api"}}
