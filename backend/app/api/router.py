from fastapi import APIRouter

from app.api.routes import auth, research, companies, compare, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(research.router)
api_router.include_router(companies.router)
api_router.include_router(compare.router)
