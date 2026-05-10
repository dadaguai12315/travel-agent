from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, sessions
from app.core.config import settings
from app.core.exceptions import (
    AppError,
    HTTPException,
    app_error_handler,
    general_exception_handler,
    http_exception_handler,
)
from app.core.redis import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    yield
    # Shutdown
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Routers
prefix = settings.api_v1_prefix
app.include_router(auth.router, prefix=prefix)
app.include_router(sessions.router, prefix=prefix)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
