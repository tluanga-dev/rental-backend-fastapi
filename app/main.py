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
from app.modules.master_data.item_master.models import Item
from app.modules.suppliers.models import Supplier
from app.modules.customers.models import Customer
from app.modules.inventory.models import InventoryUnit, StockLevel, SKUSequence

# Import new modular transaction models
from app.modules.transactions.base.models import TransactionHeader, TransactionLine
from app.modules.sales.models import Sale, SaleLine
from app.modules.purchases.models import Purchase, PurchaseLine
from app.modules.rentals.models import Rental, RentalLine, RentalLifecycle, RentalExtension
from app.modules.rent_returns.models import RentReturn, RentReturnLine, RentReturnInspection

# Import old transaction models for backward compatibility
# Note: Commented out to avoid table conflicts - legacy models still available via imports
# from app.modules.transactions.models import (
#     TransactionMetadata, RentalInspection, PurchaseCreditMemo,
#     RentalReturnEvent, RentalItemInspection, RentalStatusLog
# )
# from app.modules.transactions.models.events import TransactionEvent
from app.modules.analytics.models import AnalyticsReport, BusinessMetric, SystemAlert
from app.modules.system.models import SystemSetting, SystemBackup, AuditLog
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.master_data.routes import router as master_data_router
from app.modules.suppliers.routes import router as suppliers_router
from app.modules.customers.routes import router as customers_router
from app.modules.inventory.routes import router as inventory_router

# Import new modular transaction routers
from app.modules.sales.routes import router as sales_router
from app.modules.purchases.routes import router as purchases_router
from app.modules.rentals.routes import router as rentals_router
from app.modules.rent_returns.routes import router as rent_returns_router

# Import old transaction routers for backward compatibility
# Note: Temporarily commented out to avoid model conflicts with new modular system
# from app.modules.transactions.routes import router as transactions_router, returns_router
# Temporarily commented out to avoid legacy transaction model conflicts
# from app.modules.analytics.routes import router as analytics_router
from app.modules.system.routes import router as system_router

# Import centralized logging configuration
from app.core.logging_config import setup_application_logging, get_application_logger
from app.core.logging_middleware import TransactionLoggingMiddleware, RequestContextMiddleware

# Import task scheduler
from app.core.scheduler import task_scheduler

# Import performance monitoring
from app.modules.monitoring.performance_monitor import monitoring_router, PerformanceTrackingMiddleware

# Initialize centralized logging
setup_application_logging()
logger = get_application_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization operations"
        },
        {
            "name": "Users",
            "description": "User management operations"
        },
        {
            "name": "Master Data",
            "description": "Master data management operations"
        },
        {
            "name": "Items",
            "description": "Item master data operations - create, read, update, delete items with search and filtering"
        },
        {
            "name": "Suppliers",
            "description": "Supplier management operations"
        },
        {
            "name": "Customers",
            "description": "Customer management operations"
        },
        {
            "name": "Inventory",
            "description": "Inventory management operations"
        },
        {
            "name": "Sales",
            "description": "Sales transaction management operations"
        },
        {
            "name": "Purchases",
            "description": "Purchase transaction management operations"
        },
        {
            "name": "Rentals",
            "description": "Rental transaction management operations"
        },
        {
            "name": "Rent Returns",
            "description": "Rental return transaction management operations"
        },
        # Legacy transaction tags temporarily commented out to avoid model conflicts
        # {
        #     "name": "Transactions",
        #     "description": "Legacy transaction management operations (backward compatibility)"
        # },
        # {
        #     "name": "Returns", 
        #     "description": "Legacy return transaction management (backward compatibility)"
        # },
        {
            "name": "Analytics",
            "description": "Analytics and reporting operations"
        },
        {
            "name": "System",
            "description": "System administration operations"
        }
    ]
)

# Add custom whitelist middleware (before CORS)
app.add_middleware(WhitelistMiddleware, enabled=settings.USE_WHITELIST_CONFIG)
app.add_middleware(EndpointAccessMiddleware, enabled=settings.USE_WHITELIST_CONFIG)

# Add transaction logging middleware
app.add_middleware(TransactionLoggingMiddleware)
app.add_middleware(RequestContextMiddleware)

# Add performance tracking middleware
app.add_middleware(PerformanceTrackingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Use origins from settings
    allow_credentials=True,  # Allow credentials when using specific origins
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
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

# Detailed health check with pool status
@app.get("/health/detailed")
async def health_check_detailed():
    from app.core.database import get_pool_status
    from datetime import datetime
    
    pool_status = await get_pool_status()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database_pool": pool_status,
        "timestamp": datetime.now().isoformat()
    }

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(master_data_router, prefix="/api/master-data", tags=["Master Data"])
app.include_router(suppliers_router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(customers_router, prefix="/api/customers", tags=["Customers"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["Inventory"])

# Include new modular transaction routers
app.include_router(sales_router, prefix="/api", tags=["Sales"])
app.include_router(purchases_router, prefix="/api", tags=["Purchases"])
app.include_router(rentals_router, prefix="/api", tags=["Rentals"])
app.include_router(rent_returns_router, prefix="/api", tags=["Rent Returns"])

# Include legacy transaction routers for backward compatibility
# Note: Temporarily commented out to avoid model conflicts with new modular system
# app.include_router(transactions_router, prefix="/api/transactions", tags=["Transactions"])
# app.include_router(returns_router, prefix="/api/transactions", tags=["Returns"])

# Temporarily commented out to avoid legacy transaction model conflicts
# app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(system_router, prefix="/api/system", tags=["System"])
app.include_router(monitoring_router)  # Performance monitoring endpoints

# API v1 routes (for backward compatibility)
app.include_router(suppliers_router, prefix="/api/v1/suppliers", tags=["Suppliers V1"])

# Startup event
@app.on_event("startup")
async def startup():
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info("Comprehensive logging system initialized")
    logger.info("Transaction audit logging enabled")
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Database tables created/verified")
    
    # Initialize Redis cache
    try:
        from app.core.cache import cache, CacheWarmer
        await cache.initialize()
        logger.info("Redis cache initialized")
        
        # Warm cache with frequently accessed data
        from app.shared.dependencies import get_session
        async for session in get_session():
            try:
                warmer = CacheWarmer()
                await warmer.warm_item_cache(session)
                await warmer.warm_location_cache(session)
                logger.info("Cache warmed with frequently accessed data")
                break
            except Exception as e:
                logger.warning(f"Cache warming failed: {str(e)}")
                break
    except Exception as e:
        logger.warning(f"Redis initialization failed: {str(e)} - Cache disabled")
    
    # Initialize system settings
    try:
        from app.modules.system.service import SystemService
        from app.shared.dependencies import get_session
        
        # Get a database session for initialization
        async for session in get_session():
            try:
                system_service = SystemService(session)
                initialized_settings = await system_service.initialize_default_settings()
                if initialized_settings:
                    logger.info(f"Initialized {len(initialized_settings)} default system settings")
                else:
                    logger.info("System settings already initialized")
                break  # Exit after first successful session
            except Exception as e:
                logger.error(f"Failed to initialize system settings: {str(e)}")
                # Continue startup even if settings initialization fails
                break
    except Exception as e:
        logger.error(f"Error during system settings initialization: {str(e)}")
        # Continue startup even if there's an import or other error
    
    # Initialize and start the task scheduler
    try:
        await task_scheduler.start()
        logger.info("Task scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start task scheduler: {str(e)}")
        # Continue startup even if scheduler fails to start
    
    logger.info(f"{settings.PROJECT_NAME} startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    logger.info(f"Shutting down {settings.PROJECT_NAME}")
    
    # Stop the task scheduler
    try:
        await task_scheduler.stop()
        logger.info("Task scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping task scheduler: {str(e)}")
    
    # Close Redis cache
    try:
        from app.core.cache import cache
        await cache.close()
        logger.info("Redis cache closed")
    except Exception as e:
        logger.warning(f"Error closing Redis cache: {str(e)}")
    
    logger.info("Shutdown complete")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )