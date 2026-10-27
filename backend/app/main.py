from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.database.connection import init_db
from app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing Engineering Intelligence Hub database...")
    await init_db()
    logger.info("Engineering Intelligence Hub backend started successfully.")
    yield
    logger.info("Shutting down Engineering Intelligence Hub backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="An Autonomous Agentic Software Engineering Platform for Repository Understanding, Code Generation, Testing & Documentation",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "vector_store": settings.VECTOR_STORE
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to Engineering Intelligence Hub API",
        "docs_url": "/docs",
        "health_check": "/api/v1/health"
    }
