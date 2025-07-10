import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from tests.conftest import TestUtils


class TestAuth:
    """Test authentication endpoints"""
    
    def test_register_user(self, client: TestClient, sample_user_data: dict, test_utils: TestUtils):
        """Test user registration"""
        response = client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        user_data = response.json()
        test_utils.assert_user_response(user_data, sample_user_data["email"])
        assert user_data["is_active"] is True
    
    def test_register_user_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "password": "TestPassword123",
            "full_name": "Another User"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 409
        
        error_data = response.json()
        assert "already exists" in error_data["detail"]
    
    def test_register_user_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        user_data = {
            "email": "weak@example.com",
            "password": "weak",
            "full_name": "Weak User"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_login_user(self, client: TestClient, sample_login_data: dict, test_utils: TestUtils):
        """Test user login"""
        response = client.post("/api/auth/login", json=sample_login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        test_utils.assert_token_response(token_data)
    
    def test_login_user_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        login_data = {
            "email": "invalid@example.com",
            "password": "InvalidPassword123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        
        error_data = response.json()
        assert "Invalid email or password" in error_data["detail"]
    
    def test_login_user_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password"""
        login_data = {
            "email": test_user.email,
            "password": "WrongPassword123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        
        error_data = response.json()
        assert "Invalid email or password" in error_data["detail"]
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test getting current user info"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["id"] == test_user.id
        assert user_data["email"] == test_user.email
        assert user_data["full_name"] == test_user.full_name
    
    def test_get_current_user_no_auth(self, client: TestClient):
        """Test getting current user without authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 403
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_change_password(self, client: TestClient, auth_headers: dict):
        """Test changing password"""
        password_data = {
            "current_password": "TestPassword123",
            "new_password": "NewPassword123"
        }
        
        response = client.post("/api/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Password changed successfully"
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """Test changing password with wrong current password"""
        password_data = {
            "current_password": "WrongPassword123",
            "new_password": "NewPassword123"
        }
        
        response = client.post("/api/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 401
        
        error_data = response.json()
        assert "Current password is incorrect" in error_data["detail"]
    
    def test_refresh_token(self, client: TestClient, sample_login_data: dict):
        """Test refreshing token"""
        # First login to get refresh token
        login_response = client.post("/api/auth/login", json=sample_login_data)
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/api/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200
        
        token_data = refresh_response.json()
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert "expires_in" in token_data
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test refreshing with invalid token"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        response = client.post("/api/auth/refresh", json=refresh_data)
        assert response.status_code == 401
        
        error_data = response.json()
        assert "Invalid refresh token" in error_data["detail"]
    
    def test_logout(self, client: TestClient, sample_login_data: dict):
        """Test logout"""
        # First login to get refresh token
        login_response = client.post("/api/auth/login", json=sample_login_data)
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Logout
        logout_data = {"refresh_token": refresh_token}
        logout_response = client.post("/api/auth/logout", json=logout_data)
        assert logout_response.status_code == 200
        
        result = logout_response.json()
        assert result["message"] == "Successfully logged out"
    
    def test_logout_all(self, client: TestClient, auth_headers: dict):
        """Test logout from all devices"""
        response = client.post("/api/auth/logout-all", headers=auth_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert "Successfully logged out from all devices" in result["message"]
    
    def test_forgot_password(self, client: TestClient, test_user: User):
        """Test forgot password"""
        forgot_data = {"email": test_user.email}
        response = client.post("/api/auth/forgot-password", json=forgot_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "reset link will be sent" in result["message"]
    
    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test forgot password with nonexistent email"""
        forgot_data = {"email": "nonexistent@example.com"}
        response = client.post("/api/auth/forgot-password", json=forgot_data)
        assert response.status_code == 200
        
        # Should return same message for security
        result = response.json()
        assert "reset link will be sent" in result["message"]