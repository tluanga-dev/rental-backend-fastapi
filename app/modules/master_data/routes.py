from fastapi import APIRouter

from app.modules.master_data.brands.routes import router as brands_router
from app.modules.master_data.categories.routes import router as categories_router
from app.modules.master_data.locations.routes import router as locations_router

router = APIRouter()

# Include all master data sub-module routers
router.include_router(brands_router, prefix="/brands", tags=["Brands"])
router.include_router(categories_router, prefix="/categories", tags=["Categories"])
router.include_router(locations_router, prefix="/locations", tags=["Locations"])