from fastapi import APIRouter

from app.api.v1.routes import auth, products, listings, platform_accounts, media

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(listings.router)
api_router.include_router(platform_accounts.router)
api_router.include_router(media.router)
