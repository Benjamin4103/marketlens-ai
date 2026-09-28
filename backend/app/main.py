import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("marketlens")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Market Research & Competitive Intelligence Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def on_startup():
    logger.info(
        "MarketLens AI starting | environment=%s | demo_mode=%s",
        settings.ENVIRONMENT,
        settings.effective_demo_mode,
    )


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} API — see /docs for OpenAPI schema"}
