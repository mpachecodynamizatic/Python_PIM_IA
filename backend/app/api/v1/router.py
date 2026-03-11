from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.i18n import router as i18n_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.media import router as media_router
from app.api.v1.products import router as products_router
from app.api.v1.quality import router as quality_router
from app.api.v1.quality_rules import router as quality_rules_router
from app.api.v1.users import router as users_router
from app.api.v1.attributes import router as attributes_router
from app.api.v1.sync import router as sync_router
from app.api.v1.views import router as views_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(products_router)
api_router.include_router(categories_router)
api_router.include_router(ingest_router)
api_router.include_router(media_router)
api_router.include_router(quality_router)
api_router.include_router(i18n_router)
api_router.include_router(attributes_router)
api_router.include_router(sync_router)
api_router.include_router(quality_rules_router)
api_router.include_router(views_router)
