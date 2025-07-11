from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from app.core.config import settings
from app.core.database import engine
from app.core.middleware import WhitelistMiddleware, EndpointAccessMiddleware
from app.db.base import Base
from app.shared.exceptions import CustomHTTPException

# Import all models to ensure they are registered with Base.metadata
from app.modules.users.models import User, UserProfile
from app.modules.auth.models import RefreshToken, LoginAttempt, PasswordResetToken, Role, Permission
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.categories.models import Category
from app.modules.master_data.locations.models import Location
from app.modules.master_data.units.models import UnitOfMeasurement
from app.modules.suppliers.models import Supplier
from app.modules.customers.models import Customer
from app.modules.inventory.models import Item, InventoryUnit, StockLevel
from app.modules.transactions.models import TransactionHeader, TransactionLine
from app.modules.rentals.models import RentalReturn, RentalReturnLine, InspectionReport
from app.modules.analytics.models import AnalyticsReport, BusinessMetric, SystemAlert
from app.modules.system.models import SystemSetting, SystemBackup, AuditLog
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.master_data.routes import router as master_data_router
from app.modules.suppliers.routes import router as suppliers_router
from app.modules.customers.routes import router as customers_router
from app.modules.inventory.routes import router as inventory_router
from app.modules.transactions.routes import router as transactions_router
from app.modules.rentals.routes import router as rentals_router
from app.modules.analytics.routes import router as analytics_router
from app.modules.system.routes import router as system_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add custom whitelist middleware (before CORS)
app.add_middleware(WhitelistMiddleware, enabled=settings.USE_WHITELIST_CONFIG)
app.add_middleware(EndpointAccessMiddleware, enabled=settings.USE_WHITELIST_CONFIG)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Origin",
        "Content-Type", 
        "Accept",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "Cache-Control"
    ],
    expose_headers=[
        "X-Total-Count",
        "X-Page-Count", 
        "X-Has-Next",
        "X-Has-Previous"
    ],
)

# Custom exception handler
@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": exc.error_type}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(master_data_router, prefix="/api/master-data", tags=["Master Data"])
app.include_router(suppliers_router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(customers_router, prefix="/api/customers", tags=["Customers"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(rentals_router, prefix="/api/rentals", tags=["Rentals"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(system_router, prefix="/api/system", tags=["System"])

# API v1 routes (for backward compatibility)
app.include_router(suppliers_router, prefix="/api/v1/suppliers", tags=["Suppliers V1"])

# Startup event
@app.on_event("startup")
async def startup():
    logger.info(f"Starting {settings.PROJECT_NAME}")
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )