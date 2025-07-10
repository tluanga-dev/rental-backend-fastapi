from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.core.middleware import setup_middleware
from app.db.session import engine
from app.db.base import Base

# Import modules to ensure they are registered with SQLAlchemy
from app.modules.master_data.brands import models as brand_models
from app.modules.master_data.categories import models as category_models
from app.modules.master_data.locations import models as location_models
from app.modules.customers import models as customer_models
from app.modules.inventory import models as inventory_models
from app.modules.transactions import models as transaction_models
from app.modules.rentals import models as rental_models
from app.modules.analytics import models as analytics_models
from app.modules.system import models as system_models

# Import routes
from app.modules.customers import routes as customer_routes
from app.modules.suppliers import routes as supplier_routes
from app.modules.master_data.brands import routes as brand_routes
from app.modules.master_data.categories import routes as category_routes
from app.modules.master_data.locations import routes as location_routes
from app.modules.inventory import routes as inventory_routes
from app.modules.transactions import routes as transaction_routes
from app.modules.rentals import routes as rental_routes
from app.modules.analytics import routes as analytics_routes
from app.modules.system import routes as system_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    
    # Initialize database optimizations
    try:
        from app.core.database_optimization import initialize_database_optimizations
        await initialize_database_optimizations()
        print("✅ Database optimizations initialized")
    except Exception as e:
        print(f"⚠️  Database optimization failed: {e}")
    
    yield
    
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Rental Management System API",
    description="""
# Rental Management System API

A comprehensive rental management system built with Domain-Driven Design (DDD) principles.

## Features

- **No Authentication**: Open access for all endpoints
- **Customer Management**: Complete customer lifecycle management with credit scoring
- **Supplier Management**: Supplier relationship management with performance tracking
- **Master Data Management**: Brands, categories, and location management
- **Inventory Management**: Real-time inventory tracking with stock levels
- **Transaction Processing**: Complete transaction workflow with payment processing
- **Rental Operations**: Rental booking, tracking, and return management
- **Analytics & Reporting**: Business intelligence and performance metrics
- **System Management**: Configuration, monitoring, and maintenance tools

## Architecture

The system follows Domain-Driven Design (DDD) principles with clean architecture:

- **Domain Layer**: Business entities, value objects, and repository interfaces
- **Application Layer**: Use cases and business logic orchestration
- **Infrastructure Layer**: Database models, repository implementations
- **API Layer**: FastAPI endpoints, schemas, and dependencies

## Security

- Input validation and sanitization
- SQL injection protection
- No authentication required

## Database

- SQLite with async SQLAlchemy
- Alembic for database migrations
- Optimized queries with proper indexing
- Foreign key constraints and data integrity

## API Standards

- RESTful API design
- OpenAPI 3.0 specification
- Consistent error handling
- Comprehensive input validation
- Standardized response formats
    """,
    version="2.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "Rental Management System Support",
        "url": "https://example.com/contact/",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Customer Management",
            "description": "Customer lifecycle management, profiles, and relationship tracking",
        },
        {
            "name": "Supplier Management", 
            "description": "Supplier relationship management, performance tracking, and contracts",
        },
        {
            "name": "Master Data - Brands",
            "description": "Brand management for inventory categorization",
        },
        {
            "name": "Master Data - Categories",
            "description": "Hierarchical category management for items and services",
        },
        {
            "name": "Master Data - Locations",
            "description": "Location and warehouse management for inventory tracking",
        },
        {
            "name": "Inventory Management",
            "description": "Real-time inventory tracking, stock levels, and item management",
        },
        {
            "name": "Transaction Processing",
            "description": "Complete transaction workflow with payment processing and receipts",
        },
        {
            "name": "Rental Operations",
            "description": "Rental booking, tracking, returns, and availability management",
        },
        {
            "name": "Analytics & Reporting",
            "description": "Business intelligence, performance metrics, and data analytics",
        },
        {
            "name": "System Management",
            "description": "Configuration, monitoring, maintenance, and administrative tools",
        },
    ],
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up performance and caching middleware
setup_middleware(app)

# Set up exception handlers
setup_exception_handlers(app)

# Include API routes

# Customer Management
app.include_router(customer_routes.router, prefix="/api/v1", tags=["Customer Management"])

# Supplier Management
app.include_router(supplier_routes.router, prefix="/api/v1", tags=["Supplier Management"])

# Master Data Management
app.include_router(brand_routes.router, prefix="/api/v1", tags=["Master Data - Brands"])
app.include_router(category_routes.router, prefix="/api/v1", tags=["Master Data - Categories"])
app.include_router(location_routes.router, prefix="/api/v1", tags=["Master Data - Locations"])

# Inventory Management
app.include_router(inventory_routes.router, prefix="/api/v1", tags=["Inventory Management"])

# Transaction Processing
app.include_router(transaction_routes.router, prefix="/api/v1", tags=["Transaction Processing"])

# Rental Operations
app.include_router(rental_routes.router, prefix="/api/v1", tags=["Rental Operations"])

# Analytics & Reporting
app.include_router(analytics_routes.router, prefix="/api/v1", tags=["Analytics & Reporting"])

# System Management
app.include_router(system_routes.router, prefix="/api/v1", tags=["System Management"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "2.0.0",
        "description": "Complete Rental Management System with Domain-Driven Design",
        "features": [
            "Customer & Supplier Management", 
            "Master Data Management",
            "Inventory Management",
            "Transaction Processing",
            "Rental Operations",
            "Analytics & Reporting",
            "System Management"
        ],
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "2.0.0",
        "architecture": "Domain-Driven Design",
        "modules": [
            "customers", "suppliers", "inventory", 
            "master_data", "transactions", "rentals", 
            "analytics", "system"
        ],
        "endpoints": 200,
        "database": "SQLite with async SQLAlchemy"
    }


