# FastAPI PostgreSQL Project

A modern FastAPI application with PostgreSQL, SQLAlchemy, Alembic, and JWT authentication following Django-like modular structure.

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

## Authentication

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