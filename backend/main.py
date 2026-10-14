from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import settings
from .logging_config import setup_logging
from .database import connect_to_mongo, close_mongo_connection, is_mongo_connected
from .seed import seed_admin
from .repositories.user_repository import UserRepository
from .routers import (
    auth_router,
    users_router,
    admin_router,
    projects_router,
    test_runs_router,
    dashboard_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing AgentQA Backend...")

    # Phase 8.1: Production environment security safeguard
    if settings.ENVIRONMENT.lower() == "production":
        if settings.JWT_SECRET == "agentqa_super_secure_jwt_secret_dev_key_2026":
            raise RuntimeError(
                "Production security violation: Insecure default JWT_SECRET detected. "
                "A strong, unique JWT_SECRET must be configured via environment variables."
            )
        if settings.DEFAULT_ADMIN_PASSWORD == "Admin@123":
            raise RuntimeError(
                "Production security violation: Insecure default DEFAULT_ADMIN_PASSWORD detected. "
                "Set a secure DEFAULT_ADMIN_PASSWORD before deploying to production."
            )

    await connect_to_mongo()
    await seed_admin(UserRepository())

    # Phase 7.2: Reconcile runs left interrupted from prior backend instance
    from .services.test_run_service import reconcile_interrupted_runs
    from .repositories.test_run_repository import TestRunRepository
    from .repositories.project_repository import ProjectRepository
    try:
        reconciled = await reconcile_interrupted_runs(TestRunRepository(), ProjectRepository())
        if reconciled > 0:
            logger.warning(f"Safely reconciled {reconciled} interrupted test run(s) from previous server execution.")
    except Exception as rec_err:
        logger.warning(f"Could not reconcile interrupted runs: {rec_err}")

    yield
    await close_mongo_connection()
    logger.info("AgentQA Backend shut down.")


app = FastAPI(
    title="AgentQA Multi-Agent Testing Platform API",
    description="Backend API for the Multi-Agent Software Testing and Bug Analysis Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
origins = [
    settings.CLIENT_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers matching frontend expectations
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    err_messages = []
    for err in exc.errors():
        msg = err.get("msg", "Invalid value")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        err_messages.append(msg)
    primary_msg = err_messages[0] if err_messages else "Validation error."
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": primary_msg, "errors": err_messages},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Something went wrong on the server."},
    )


# Health check endpoint
@app.get("/api/health")
async def health_check():
    db_status = "connected" if is_mongo_connected() else "disconnected"
    return {
        "status": "ok",
        "service": "AgentQA Multi-Agent Testing Platform",
        "database": db_status,
    }


# Mount Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(projects_router)
app.include_router(test_runs_router)
app.include_router(dashboard_router)


# 404 fallback for unknown /api routes
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_404_fallback(path: str):
    return JSONResponse(status_code=404, content={"error": "Not found."})
