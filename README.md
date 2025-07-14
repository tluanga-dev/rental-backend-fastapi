# Rental Management System - Backend API

A comprehensive FastAPI-based rental management system with PostgreSQL, featuring integrated inventory tracking, purchase management, and automated stock level updates.

## Features

- **FastAPI**: Modern, fast (high-performance) web framework
- **PostgreSQL**: Powerful, open-source relational database
- **SQLAlchemy 2.0**: Modern async ORM with type safety
- **Alembic**: Database migration tool
- **JWT Authentication**: Secure token-based authentication
- **Docker Support**: Containerized development and deployment
- **Testing**: Comprehensive test suite with pytest
- **Modular Architecture**: Django-like app structure
- **RBAC**: Role-based access control
- **Type Safety**: Full type hints with Pydantic v2
- **🆕 Purchase-Inventory Integration**: Automatic stock level updates on purchases
- **🆕 Real-time Stock Tracking**: Live inventory management across locations
- **🆕 Transaction Management**: Complete purchase and rental transaction system

## Project Structure

```
app/
├── core/                   # Core configuration and utilities
│   ├── config.py          # Settings and configuration
│   ├── database.py        # Database connection and base model
│   ├── security.py        # JWT and password utilities
│   └── dependencies.py    # Common dependencies
├── modules/               # Domain modules
│   ├── auth/             # Authentication module
│   │   ├── models.py     # Auth-related models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── services.py   # Business logic
│   │   ├── routes.py     # API endpoints
│   │   └── dependencies.py
│   └── users/            # User management module
│       ├── models.py
│       ├── schemas.py
│       ├── services.py
│       └── routes.py
├── shared/               # Shared utilities
│   ├── exceptions.py    # Custom exceptions
│   ├── models.py        # Base response models
│   └── utils.py         # Utility functions
└── main.py              # FastAPI application entry point
```

## Quick Start

### 1. Environment Setup

```bash
# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### 3. Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb fastapi_db
createdb fastapi_test_db

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Core API Endpoints

#### 🔐 Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | User login |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `POST` | `/api/auth/logout` | User logout |
| `GET` | `/api/auth/me` | Get current user |

#### 🛒 Purchase Transaction Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/transactions/purchases` | List purchase transactions |
| `GET` | `/api/transactions/purchases/{id}` | Get specific purchase |
| `POST` | `/api/transactions/new-purchase` | **Create new purchase (with automatic stock updates)** |

#### 📦 Stock Level Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/inventory/stock` | Get all stock levels |
| `GET` | `/api/inventory/stock/{id}` | Get specific stock level |
| `GET` | `/api/inventory/stock/low` | Get low stock items |
| `GET` | `/api/inventory/items/{item_id}/stock` | Get stock levels for item |
| `GET` | `/api/inventory/items/{item_id}/stock-summary` | **Comprehensive item stock summary** |
| `GET` | `/api/inventory/locations/{location_id}/stock` | Get stock levels by location |
| `POST` | `/api/inventory/stock/{id}/adjust` | Adjust stock quantity |
| `POST` | `/api/inventory/stock/{id}/reserve` | Reserve stock |
| `POST` | `/api/inventory/stock/{id}/release` | Release stock reservation |

#### 📋 Master Data Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/master/items` | List items |
| `POST` | `/api/master/items` | Create new item |
| `GET` | `/api/master/categories` | List categories |
| `GET` | `/api/master/suppliers` | List suppliers |
| `GET` | `/api/master/locations` | List locations |

### 🆕 Purchase Transaction Integration

#### Create Purchase with Automatic Stock Updates

**Endpoint**: `POST /api/transactions/new-purchase`

**Features**:
- ✅ Creates purchase transaction
- ✅ **Automatically updates stock levels**
- ✅ **Creates new stock records if needed**
- ✅ **Increments existing stock quantities**
- ✅ Atomic database transactions
- ✅ Complete rollback on failures

**Request Example**:
```json
{
  "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
  "location_id": "987fcdeb-51a2-43d1-9f4e-123456789abc",
  "purchase_date": "2024-01-15",
  "notes": "Monthly inventory purchase",
  "items": [
    {
      "item_id": "456e7890-e89b-12d3-a456-426614174000",
      "quantity": 10,
      "unit_cost": 99.99,
      "condition": "NEW",
      "tax_rate": 8.5,
      "discount_amount": 0,
      "notes": "Premium quality items"
    }
  ]
}
```

**Response Example**:
```json
{
  "success": true,
  "message": "Purchase transaction created successfully",
  "transaction_id": "789e1234-e89b-12d3-a456-426614174000",
  "transaction_number": "PUR-20240115-1234",
  "data": {
    "id": "789e1234-e89b-12d3-a456-426614174000",
    "transaction_type": "PURCHASE",
    "status": "COMPLETED",
    "total_amount": 1089.89,
    "transaction_lines": [...]
  }
}
```

### 📊 Stock Information Queries

#### Get All Stock Information

**Endpoint**: `GET /api/inventory/stock`

**Query Parameters**:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Records per page (default: 100)
- `item_id` (UUID): Filter by item
- `location_id` (UUID): Filter by location
- `active_only` (bool): Show only active stock (default: true)

**Examples**:
```bash
# Get all stock levels
GET /api/inventory/stock

# Get stock with pagination
GET /api/inventory/stock?skip=0&limit=50

# Get stock for specific item
GET /api/inventory/stock?item_id=123e4567-e89b-12d3-a456-426614174000

# Get stock at specific location
GET /api/inventory/stock?location_id=987fcdeb-51a2-43d1-9f4e-123456789abc
```

#### Get Stock for Specific Item

**Endpoint**: `GET /api/inventory/items/{item_id}/stock-summary`

**Response**:
```json
{
  "item_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_stock_levels": 3,
  "total_inventory_units": 25,
  "aggregate_quantities": {
    "on_hand": "50",
    "available": "45",
    "reserved": "5"
  },
  "units_by_status": {
    "AVAILABLE": 20,
    "RENTED": 3,
    "MAINTENANCE": 2
  },
  "units_by_location": {
    "Warehouse A": 30,
    "Warehouse B": 15,
    "Store Front": 5
  },
  "stock_levels": [...],
  "has_initial_stock": true
}
```

### 🔄 Business Workflow Integration

#### Purchase → Stock Update Flow

1. **Create Purchase**: POST `/api/transactions/new-purchase`
2. **Automatic Stock Updates**: System automatically:
   - Validates supplier, location, and items
   - Creates transaction header and lines
   - **Updates stock levels for each item**:
     - If stock exists: increments `quantity_on_hand` and `quantity_available`
     - If no stock: creates new stock level record
   - Commits all changes atomically
3. **Real-time Inventory**: Stock levels immediately reflect purchase

#### Stock Tracking Capabilities

- **Multi-location tracking**: Separate stock levels per item per location
- **Quantity types**: On-hand, available, reserved, on-order
- **Reorder management**: Minimum/maximum levels, reorder points
- **Low stock alerts**: Automatic identification of items needing reorder
- **Stock adjustments**: Manual quantity adjustments with audit trail
- **Reservations**: Ability to reserve and release stock for orders

## 🎯 Integration Benefits

### Purchase-Inventory Integration Advantages

- **🔄 Automatic Updates**: Purchase transactions automatically update inventory levels
- **📊 Real-time Tracking**: Live stock visibility across all locations
- **🛡️ Data Consistency**: Atomic transactions ensure purchase and stock data stay synchronized
- **🚫 Manual Elimination**: No manual stock adjustments needed after purchases
- **⚡ Performance**: Single-transaction commits optimize database performance
- **🔒 Error Resilience**: Complete rollback if any operation fails
- **📍 Multi-location**: Independent stock tracking per item per location
- **📈 Business Intelligence**: Comprehensive stock reports and analytics

### Data Flow Visualization

```
Purchase Request → Validate Data → Create Transaction → Update Stock → Commit All
     ↓               ↓                 ↓                 ↓              ↓
   Supplier      Transaction      Transaction         Stock          Success
   Location      Header           Lines               Levels         Response
   Items         Created          Created             Updated/       
                                                     Created        
```

## Authentication Examples

### Register User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123",
    "full_name": "John Doe"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

### Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Purchase with Stock Updates

```bash
curl -X POST "http://localhost:8000/api/transactions/new-purchase" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
    "location_id": "987fcdeb-51a2-43d1-9f4e-123456789abc",
    "purchase_date": "2024-01-15",
    "notes": "Monthly inventory purchase",
    "items": [
      {
        "item_id": "456e7890-e89b-12d3-a456-426614174000",
        "quantity": 10,
        "unit_cost": 99.99,
        "condition": "NEW",
        "tax_rate": 8.5,
        "discount_amount": 0,
        "notes": "Premium quality items"
      }
    ]
  }'
```

### Get Stock Information

```bash
# Get all stock levels
curl -X GET "http://localhost:8000/api/inventory/stock" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get stock for specific item
curl -X GET "http://localhost:8000/api/inventory/items/456e7890-e89b-12d3-a456-426614174000/stock-summary" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get low stock items
curl -X GET "http://localhost:8000/api/inventory/stock/low" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Development

### Code Formatting

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

### Adding a New Module

1. Create module directory in `app/modules/`
2. Add `models.py`, `schemas.py`, `services.py`, `routes.py`
3. Import models in `alembic/env.py`
4. Include router in `app/main.py`
5. Create migrations: `alembic revision --autogenerate -m "Add module"`

## Configuration

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `7` |
| `DEBUG` | Debug mode | `false` |

## Production Deployment

### Using Docker

```bash
# Build production image
docker build -t fastapi-app .

# Run with production compose
docker-compose -f docker-compose.prod.yml up -d
```

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Security Features

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: BCrypt with configurable rounds
- **Rate Limiting**: Login attempt tracking
- **CORS**: Configurable origins
- **Input Validation**: Pydantic schemas
- **SQL Injection Protection**: SQLAlchemy ORM

## Performance Features

- **Async/Await**: Full async support
- **Connection Pooling**: SQLAlchemy async pool
- **Redis Caching**: Optional Redis integration
- **Pagination**: Efficient data loading
- **Query Optimization**: Eager loading support

## Monitoring

- **Health Check**: `/health` endpoint
- **Metrics**: Prometheus-compatible metrics
- **Logging**: Structured logging support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linting
6. Submit a pull request

## License

This project is licensed under the MIT License.