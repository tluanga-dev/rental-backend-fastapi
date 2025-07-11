import pytest
import pytest_asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.modules.users.models import User
from app.modules.users.services import UserService
from app.core.security import get_password_hash, create_token_pair


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://fastapi_user:fastapi_password@localhost:5432/fastapi_test_db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_size=1,
    max_overflow=0,
    pool_pre_ping=False,
    poolclass=None,
    connect_args={}
)

# Create test session factory
TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def setup_test_db():
    """Setup test database"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async with TestingSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
def client(db_session):
    """Create test client"""
    
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user"""
    user_service = UserService(db_session)
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
        "is_active": True
    }
    
    user = await user_service.create(user_data)
    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Create test superuser"""
    user_service = UserService(db_session)
    
    user_data = {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "AdminPassword123",
        "full_name": "Admin User",
        "is_active": True,
        "is_superuser": True
    }
    
    user = await user_service.create(user_data)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Create test user token"""
    tokens = create_token_pair(
        user_id=test_user.id,
        username=test_user.email,
        scopes=["read", "write"]
    )
    return tokens.access_token


@pytest.fixture
def test_superuser_token(test_superuser: User) -> str:
    """Create test superuser token"""
    tokens = create_token_pair(
        user_id=test_superuser.id,
        username=test_superuser.email,
        scopes=["read", "write", "admin"]
    )
    return tokens.access_token


@pytest.fixture
def auth_headers(test_user_token: str):
    """Create auth headers for test user"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_auth_headers(test_superuser_token: str):
    """Create auth headers for test superuser"""
    return {"Authorization": f"Bearer {test_superuser_token}"}


# Sample data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "newuser@example.com",
        "password": "NewPassword123",
        "full_name": "New User"
    }


@pytest.fixture
def sample_login_data():
    """Sample login data for testing"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123"
    }


@pytest.fixture
def sample_user_update_data():
    """Sample user update data for testing"""
    return {
        "full_name": "Updated User Name",
        "phone": "+1234567890",
        "bio": "Updated bio"
    }


@pytest.fixture
def sample_profile_data():
    """Sample user profile data for testing"""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "city": "New York",
        "country": "USA",
        "timezone": "America/New_York",
        "language": "en",
        "email_notifications": True,
        "sms_notifications": False
    }


# Test utilities
class TestUtils:
    """Test utility functions"""
    
    @staticmethod
    def assert_user_response(user_data: dict, expected_email: str):
        """Assert user response structure"""
        assert "id" in user_data
        assert "email" in user_data
        assert "full_name" in user_data
        assert "is_active" in user_data
        assert "created_at" in user_data
        assert user_data["email"] == expected_email
    
    @staticmethod
    def assert_token_response(token_data: dict):
        """Assert token response structure"""
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert "token_type" in token_data
        assert "expires_in" in token_data
        assert "user" in token_data
        assert token_data["token_type"] == "bearer"
    
    @staticmethod
    def assert_error_response(error_data: dict, expected_detail: str = None):
        """Assert error response structure"""
        assert "detail" in error_data
        if expected_detail:
            assert error_data["detail"] == expected_detail


@pytest.fixture
def test_utils():
    """Test utilities fixture"""
    return TestUtils