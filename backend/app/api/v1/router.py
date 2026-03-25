from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.channels import router as channels_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.export import router as export_router
from app.api.v1.external_taxonomies import router as external_taxonomies_router
from app.api.v1.i18n import router as i18n_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.logistics import router as logistics_router
from app.api.v1.media import router as media_router
from app.api.v1.products import router as products_router
from app.api.v1.quality import router as quality_router
from app.api.v1.quality_rules import router as quality_rules_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.users import router as users_router
from app.api.v1.attributes import router as attributes_router
from app.api.v1.sync import router as sync_router
from app.api.v1.views import router as views_router
from app.api.v1.brands import router as brands_router
from app.api.v1.roles import router as roles_router
from app.api.v1.database import router as database_router
from app.api.v1.pim_mapping import router as pim_mapping_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
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
api_router.include_router(export_router)
api_router.include_router(brands_router)
api_router.include_router(logistics_router)
api_router.include_router(compliance_router)
api_router.include_router(channels_router)
api_router.include_router(suppliers_router)
api_router.include_router(external_taxonomies_router)
api_router.include_router(database_router)
api_router.include_router(pim_mapping_router)
