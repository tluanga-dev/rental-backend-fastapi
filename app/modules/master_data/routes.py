from fastapi import APIRouter

from app.modules.master_data.brands.routes import router as brands_router
from app.modules.master_data.categories.routes import router as categories_router
from app.modules.master_data.locations.routes import router as locations_router
from app.modules.master_data.units.routes import router as units_router

router = APIRouter()

# Include all master data sub-module routers
router.include_router(brands_router, prefix="/brands")
router.include_router(categories_router, prefix="/categories")
router.include_router(locations_router, prefix="/locations")
router.include_router(units_router, prefix="/units-of-measurement")