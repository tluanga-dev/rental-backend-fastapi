import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
import os
from uuid import uuid4

from app.db.base import Base
from app.db.session import get_session
from app.core.config import settings
from app.main import app  # This will be created later

# Test database configuration
TEST_DATABASE_URL = settings.TEST_DATABASE_URL or "sqlite+aiosqlite:///:memory:"


# Fixtures for event loop
@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for the test session."""
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    # Use NullPool for SQLite to avoid connection issues
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Create and drop test database tables."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def session(test_engine: AsyncEngine, test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create session factory
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    # Create and yield session
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override."""
    
    # Override the get_session dependency
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    # Create async client
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Content-Type": "application/json"}
    ) as test_client:
        yield test_client
    
    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: AsyncClient, test_user_token: str) -> AsyncClient:
    """Create authenticated test client."""
    client.headers.update({"Authorization": f"Bearer {test_user_token}"})
    return client


# Test data fixtures
@pytest.fixture
def test_user_data() -> dict:
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "Test123!@#",
        "name": "Test User",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_superuser": False,
    }


@pytest.fixture
def test_admin_data() -> dict:
    """Test admin user data."""
    return {
        "email": "admin@example.com",
        "password": "Admin123!@#",
        "name": "Admin User",
        "first_name": "Admin",
        "last_name": "User",
        "is_active": True,
        "is_superuser": True,
    }


@pytest_asyncio.fixture
async def test_user(session: AsyncSession, test_user_data: dict):
    """Create test user in database."""
    from app.modules.auth.models import User
    
    user = User(
        username=test_user_data["first_name"].lower(),
        email=test_user_data["email"],
        password=test_user_data["password"],  # Will be hashed in __init__
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"]
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(session: AsyncSession, test_admin_data: dict):
    """Create test admin user in database."""
    from app.modules.auth.models import User
    
    admin = User(
        username=test_admin_data["first_name"].lower(),
        email=test_admin_data["email"],
        password=test_admin_data["password"],  # Will be hashed in __init__
        first_name=test_admin_data["first_name"],
        last_name=test_admin_data["last_name"]
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


@pytest.fixture
def test_user_token(test_user) -> str:
    """Create test user JWT token."""
    from app.core.security import create_access_token
    
    token_data = {
        "sub": test_user.email,
        "user_id": str(test_user.id),
        "permissions": ["customers:read", "suppliers:read", "locations:read"],
        "role": "user"
    }
    return create_access_token(token_data)


@pytest.fixture
def test_admin_token(test_admin) -> str:
    """Create test admin JWT token."""
    from app.core.security import create_access_token
    
    token_data = {
        "sub": test_admin.email,
        "user_id": str(test_admin.id),
        "permissions": ["*"],  # Admin has all permissions
        "role": "admin"
    }
    return create_access_token(token_data)


# Utility fixtures
@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for consistent testing."""
    class MockDateTime:
        @staticmethod
        def now(tz=None):
            return datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz or timezone.utc)
        
        @staticmethod
        def utcnow():
            return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    monkeypatch.setattr("app.db.base.datetime", MockDateTime)
    return MockDateTime


@pytest.fixture
def sample_uuid() -> str:
    """Generate sample UUID."""
    return str(uuid4())


# Factory fixtures (will be expanded as models are created)
@pytest.fixture
def customer_factory():
    """Factory for creating test customers."""
    def _factory(**kwargs):
        defaults = {
            "customer_code": f"CUST{uuid4().hex[:8].upper()}",
            "customer_type": "INDIVIDUAL",
            "first_name": "John",
            "last_name": "Doe",
            "email": f"customer_{uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "is_active": True,
        }
        return {**defaults, **kwargs}
    return _factory


@pytest.fixture
def item_factory():
    """Factory for creating test items."""
    def _factory(**kwargs):
        defaults = {
            "sku": f"ITEM{uuid4().hex[:8].upper()}",
            "item_name": "Test Item",
            "category_id": str(uuid4()),
            "is_rentable": True,
            "is_saleable": True,
            "rental_base_price": "10.00",
            "sale_base_price": "100.00",
            "is_active": True,
        }
        return {**defaults, **kwargs}
    return _factory


@pytest.fixture
def transaction_factory():
    """Factory for creating test transactions."""
    def _factory(**kwargs):
        defaults = {
            "transaction_number": f"TXN{uuid4().hex[:8].upper()}",
            "transaction_type": "RENTAL",
            "transaction_date": datetime.utcnow(),
            "customer_id": str(uuid4()),
            "location_id": str(uuid4()),
            "status": "DRAFT",
            "payment_status": "PENDING",
            "total_amount": "100.00",
        }
        return {**defaults, **kwargs}
    return _factory


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.auth = pytest.mark.auth


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as requiring authentication")


# Helper functions
async def create_test_data(session: AsyncSession, model_class, **kwargs):
    """Helper to create test data in database."""
    instance = model_class(**kwargs)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return instance


async def assert_db_item_exists(session: AsyncSession, model_class, **filters):
    """Assert that an item exists in database with given filters."""
    from sqlalchemy import select
    
    query = select(model_class)
    for key, value in filters.items():
        query = query.where(getattr(model_class, key) == value)
    
    result = await session.execute(query)
    item = result.scalar_one_or_none()
    assert item is not None, f"{model_class.__name__} not found with filters: {filters}"
    return item


# Export fixtures
__all__ = [
    "event_loop",
    "test_engine",
    "test_db",
    "session",
    "client",
    "authenticated_client",
    "test_user_data",
    "test_admin_data",
    "test_user",
    "test_admin",
    "test_user_token",
    "test_admin_token",
    "mock_datetime",
    "sample_uuid",
    "customer_factory",
    "item_factory",
    "transaction_factory",
    "create_test_data",
    "assert_db_item_exists",
]