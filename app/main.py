from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.logging import logger
from app.core.rate_limiter import limiter
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="High-performance Multi-User Conversational RAG with LangChain LCEL, PostgreSQL PGVector, and SSE streaming.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    logger.debug(f"Incoming -> {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Outgoing <- {request.method} {request.url.path} [{response.status_code}]")
    return response


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }
