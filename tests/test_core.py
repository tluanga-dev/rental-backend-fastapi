import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_token_pair
)
from app.shared.utils import (
    validate_email,
    validate_phone,
    clean_phone,
    sanitize_string,
    snake_to_camel,
    camel_to_snake,
    calculate_pagination_info
)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == settings.PROJECT_NAME


class TestSecurity:
    """Test security utilities"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123"
        
        # Hash password
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_access_token(self):
        """Test access token verification"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        
        token_data = verify_token(token, "access")
        assert token_data.username == "test@example.com"
        assert token_data.user_id == 1
    
    def test_verify_refresh_token(self):
        """Test refresh token verification"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_refresh_token(data)
        
        token_data = verify_token(token, "refresh")
        assert token_data.username == "test@example.com"
        assert token_data.user_id == 1
    
    def test_create_token_pair(self):
        """Test token pair creation"""
        tokens = create_token_pair(1, "test@example.com", ["read", "write"])
        
        assert hasattr(tokens, 'access_token')
        assert hasattr(tokens, 'refresh_token')
        assert hasattr(tokens, 'token_type')
        assert tokens.token_type == "bearer"
        assert len(tokens.access_token) > 0
        assert len(tokens.refresh_token) > 0
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        with pytest.raises(Exception):
            verify_token("invalid_token", "access")
    
    def test_verify_wrong_token_type(self):
        """Test verification with wrong token type"""
        data = {"sub": "test@example.com", "user_id": 1}
        access_token = create_access_token(data)
        
        with pytest.raises(Exception):
            verify_token(access_token, "refresh")


class TestUtils:
    """Test utility functions"""
    
    def test_validate_email(self):
        """Test email validation"""
        # Valid emails
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True
        assert validate_email("user+tag@example.org") is True
        
        # Invalid emails
        assert validate_email("invalid-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("test@") is False
        assert validate_email("test.example.com") is False
    
    def test_validate_phone(self):
        """Test phone validation"""
        # Valid phones
        assert validate_phone("+1234567890") is True
        assert validate_phone("1234567890") is True
        assert validate_phone("+44 20 7946 0958") is True
        assert validate_phone("123-456-7890") is True
        
        # Invalid phones
        assert validate_phone("123") is False
        assert validate_phone("abc123") is False
        assert validate_phone("") is False
    
    def test_clean_phone(self):
        """Test phone cleaning"""
        assert clean_phone("+1 234-567-8900") == "+12345678900"
        assert clean_phone("123 456 7890") == "1234567890"
        assert clean_phone("123-456-7890") == "1234567890"
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        assert sanitize_string("  hello world  ") == "hello world"
        assert sanitize_string("long text", 4) == "long"
        assert sanitize_string("") == ""
    
    def test_snake_to_camel(self):
        """Test snake_case to camelCase conversion"""
        assert snake_to_camel("snake_case") == "snakeCase"
        assert snake_to_camel("user_name") == "userName"
        assert snake_to_camel("first_name_last_name") == "firstNameLastName"
        assert snake_to_camel("single") == "single"
    
    def test_camel_to_snake(self):
        """Test camelCase to snake_case conversion"""
        assert camel_to_snake("camelCase") == "camel_case"
        assert camel_to_snake("userName") == "user_name"
        assert camel_to_snake("firstNameLastName") == "first_name_last_name"
        assert camel_to_snake("single") == "single"
    
    def test_calculate_pagination_info(self):
        """Test pagination calculation"""
        info = calculate_pagination_info(total=100, page=1, size=10)
        
        assert info["total"] == 100
        assert info["page"] == 1
        assert info["size"] == 10
        assert info["pages"] == 10
        assert info["has_next"] is True
        assert info["has_prev"] is False
        
        # Test last page
        info = calculate_pagination_info(total=100, page=10, size=10)
        assert info["has_next"] is False
        assert info["has_prev"] is True
        
        # Test middle page
        info = calculate_pagination_info(total=100, page=5, size=10)
        assert info["has_next"] is True
        assert info["has_prev"] is True


class TestConfig:
    """Test configuration"""
    
    def test_settings_loaded(self):
        """Test that settings are loaded correctly"""
        assert settings.PROJECT_NAME is not None
        assert settings.PROJECT_VERSION is not None
        assert settings.DATABASE_URL is not None
        assert settings.SECRET_KEY is not None
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0
    
    def test_password_settings(self):
        """Test password-related settings"""
        assert settings.PASSWORD_MIN_LENGTH >= 8
        assert settings.PASSWORD_BCRYPT_ROUNDS >= 10
    
    def test_pagination_settings(self):
        """Test pagination settings"""
        assert settings.DEFAULT_PAGE_SIZE > 0
        assert settings.MAX_PAGE_SIZE > settings.DEFAULT_PAGE_SIZE
    
    def test_cors_settings(self):
        """Test CORS settings"""
        assert isinstance(settings.ALLOWED_ORIGINS, list)
        assert len(settings.ALLOWED_ORIGINS) > 0