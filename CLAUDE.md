# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern FastAPI rental management backend following Domain-Driven Design (DDD) architecture with Django-like modular structure. The project uses PostgreSQL exclusively (no SQLite support) with full async/await patterns throughout.

## Architecture

### Module Structure
Each domain module follows a consistent pattern:
```
app/modules/{domain}/
├── models.py      # SQLAlchemy ORM models
├── schemas.py     # Pydantic validation schemas
├── services.py    # Business logic layer
├── routes.py      # API endpoints
├── repository.py  # Data access layer
└── dependencies.py # Module-specific dependencies
```

### Core Components
- **app/core/**: Configuration, database, security, shared dependencies
- **app/modules/**: Domain modules (auth, users, master_data)
- **app/shared/**: Shared utilities, exceptions, base models
- **app/main.py**: FastAPI application entry point

### Data Flow Pattern
Controller (routes.py) → Service (services.py) → Repository (repository.py) → Model (models.py)

## Essential Commands

### Environment Setup
```bash
# Copy and configure environment
cp .env.example .env

# Virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database setup (PostgreSQL required)
createdb fastapi_db
createdb fastapi_test_db
```

### Development Server
```bash
# FastAPI development server
uvicorn app.main:app --reload

# Docker development (recommended)
docker-compose up -d
docker-compose logs -f app
docker-compose down
```

### Database Operations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run by markers
pytest -m "unit"           # Unit tests only
pytest -m "integration"    # Integration tests only
pytest -m "not slow"       # Skip slow tests
```

### Code Quality
```bash
# Format code (100-char line length)
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

## Database Configuration

### Connection
- **Primary**: PostgreSQL with asyncpg driver
- **Test**: Separate PostgreSQL database (fastapi_test_db)
- **Redis**: Optional caching layer
- **Connection String**: `postgresql+asyncpg://user:password@host:port/database`

### Important Notes
- **PostgreSQL Only**: No SQLite support
- **Async Operations**: All database operations use async/await
- **Connection Pool**: SQLAlchemy async pool configured
- **Migrations**: Alembic manages schema changes

## Testing Architecture

### Test Configuration
- **Separate Database**: Uses `fastapi_test_db` for isolation
- **Async Support**: Full async test patterns with pytest-asyncio
- **Fixtures**: Pre-configured user, admin, and database fixtures
- **Test Markers**: `unit`, `integration`, `slow` for selective testing

### Test Database Setup
The test suite automatically handles database setup/teardown, but ensure `fastapi_test_db` exists:
```bash
createdb fastapi_test_db
```

## Authentication System

### JWT Implementation
- **Access Tokens**: 30-minute expiry (configurable)
- **Refresh Tokens**: 7-day expiry (configurable)
- **Login Tracking**: Failed attempt monitoring
- **Password Reset**: Secure token-based reset

### RBAC Support
- Role-based access control framework
- User permissions and role assignments
- Decorator-based route protection

## Environment Variables

### Required Configuration
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
TEST_DATABASE_URL=postgresql+asyncpg://user:password@host:port/test_database

# Security
SECRET_KEY=your-long-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin User (for Docker initialization)
ADMIN_EMAIL=admin@admin.com
ADMIN_PASSWORD=Admin@123
ADMIN_FULL_NAME=System Administrator

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Docker Development

### Service Configuration
```bash
# Start all services (PostgreSQL, Redis, FastAPI)
docker-compose up -d

# View application logs
docker-compose logs -f app

# Initialize admin user (automatic in Docker)
docker-compose exec app python scripts/init_admin.py
```

### Health Checks
- **Database**: Automatic health check in docker-compose
- **Application**: `/health` endpoint available
- **Admin Setup**: Automatic admin user creation on startup

## Module Creation Guidelines

### Adding New Domain Module
1. Create module directory: `app/modules/new_module/`
2. Implement required files: `models.py`, `schemas.py`, `services.py`, `routes.py`
3. Add models to `alembic/env.py` imports
4. Include router in `app/main.py`
5. Create migration: `alembic revision --autogenerate -m "Add new_module"`
6. Write tests in `tests/modules/new_module/`

### Repository Pattern Implementation
```python
# services.py
class NewModuleService:
    def __init__(self, repository: NewModuleRepository):
        self.repository = repository

# routes.py
@router.get("/")
async def get_items(service: NewModuleService = Depends(get_new_module_service)):
    return await service.get_all()
```

## API Documentation

### Endpoints
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

## Performance Considerations

### Optimization Features
- **Async/Await**: Full async support throughout
- **Connection Pooling**: SQLAlchemy async pool
- **Redis Caching**: Optional caching layer
- **Pagination**: Efficient data loading with configurable page sizes
- **Query Optimization**: Eager loading and query optimization patterns

### Monitoring
- **Health Endpoint**: `/health` for service monitoring
- **Metrics**: Prometheus-compatible metrics support
- **Logging**: Structured logging configuration

## Security Features

### Built-in Security
- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: BCrypt with configurable rounds
- **CORS**: Configurable allowed origins
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM protection
- **Rate Limiting**: Login attempt tracking

### Security Configuration
- **Password Policy**: Minimum 8 characters (configurable)
- **BCrypt Rounds**: 12 rounds (configurable)
- **Token Security**: Configurable expiration times
- **CORS Origins**: Explicit allowed origins list

## Code Quality Configuration

### Tool Configuration (pyproject.toml)
- **Black**: 100-character line length, Python 3.11 target
- **isort**: Black-compatible profile
- **mypy**: Strict type checking with untyped defs disallowed
- **pytest**: Unit/integration/slow test markers
- **Coverage**: Source coverage with exclusions for migrations

### Type Safety
- **Full Type Hints**: Comprehensive type annotations required
- **Pydantic v2**: Modern validation with type safety
- **SQLAlchemy 2.0**: Async ORM with type support
- **mypy Strict**: Strict type checking enforced