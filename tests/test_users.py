import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from tests.conftest import TestUtils


class TestUsers:
    """Test user management endpoints"""
    
    def test_get_current_user_profile(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test getting current user profile"""
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["id"] == test_user.id
        assert user_data["email"] == test_user.email
        assert user_data["full_name"] == test_user.full_name
    
    def test_update_current_user_profile(self, client: TestClient, auth_headers: dict, sample_user_update_data: dict):
        """Test updating current user profile"""
        response = client.put("/api/users/me", json=sample_user_update_data, headers=auth_headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["full_name"] == sample_user_update_data["full_name"]
        assert user_data["phone"] == sample_user_update_data["phone"]
        assert user_data["bio"] == sample_user_update_data["bio"]
    
    def test_update_current_user_profile_invalid_email(self, client: TestClient, auth_headers: dict):
        """Test updating current user profile with invalid email"""
        update_data = {"email": "invalid-email"}
        response = client.put("/api/users/me", json=update_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_change_current_user_password(self, client: TestClient, auth_headers: dict):
        """Test changing current user password"""
        password_data = {
            "current_password": "TestPassword123",
            "new_password": "NewPassword123"
        }
        
        response = client.post("/api/users/me/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Password changed successfully"
    
    def test_update_user_profile(self, client: TestClient, auth_headers: dict, sample_profile_data: dict):
        """Test updating user extended profile"""
        response = client.put("/api/users/me/profile", json=sample_profile_data, headers=auth_headers)
        assert response.status_code == 200
        
        profile_data = response.json()
        assert profile_data["first_name"] == sample_profile_data["first_name"]
        assert profile_data["last_name"] == sample_profile_data["last_name"]
        assert profile_data["city"] == sample_profile_data["city"]
        assert profile_data["country"] == sample_profile_data["country"]
    
    def test_get_user_profile(self, client: TestClient, auth_headers: dict, sample_profile_data: dict):
        """Test getting user extended profile"""
        # First create profile
        client.put("/api/users/me/profile", json=sample_profile_data, headers=auth_headers)
        
        # Then get profile
        response = client.get("/api/users/me/profile", headers=auth_headers)
        assert response.status_code == 200
        
        profile_data = response.json()
        assert profile_data["first_name"] == sample_profile_data["first_name"]
        assert profile_data["last_name"] == sample_profile_data["last_name"]
    
    def test_get_user_profile_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting user profile when it doesn't exist"""
        response = client.get("/api/users/me/profile", headers=auth_headers)
        assert response.status_code == 404
    

class TestUserAdmin:
    """Test user admin endpoints"""
    
    def test_get_users_admin(self, client: TestClient, admin_auth_headers: dict):
        """Test getting all users as admin"""
        response = client.get("/api/users/", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "page" in data
        assert "size" in data
        assert "total" in data
        assert "pages" in data
        assert isinstance(data["data"], list)
    
    def test_get_users_admin_with_search(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """Test getting users with search as admin"""
        response = client.get(f"/api/users/?search={test_user.email}", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["data"]) >= 1
        assert any(user["email"] == test_user.email for user in data["data"])
    
    def test_get_users_regular_user(self, client: TestClient, auth_headers: dict):
        """Test getting users as regular user (should fail)"""
        response = client.get("/api/users/", headers=auth_headers)
        assert response.status_code == 403
    
    def test_create_user_admin(self, client: TestClient, admin_auth_headers: dict):
        """Test creating user as admin"""
        user_data = {
            "email": "admin-created@example.com",
            "password": "AdminPassword123",
            "full_name": "Admin Created User"
        }
        
        response = client.post("/api/users/", json=user_data, headers=admin_auth_headers)
        assert response.status_code == 201
        
        user_response = response.json()
        assert user_response["email"] == user_data["email"]
        assert user_response["full_name"] == user_data["full_name"]
    
    def test_create_user_duplicate_email_admin(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """Test creating user with duplicate email as admin"""
        user_data = {
            "email": test_user.email,
            "password": "AdminPassword123",
            "full_name": "Duplicate User"
        }
        
        response = client.post("/api/users/", json=user_data, headers=admin_auth_headers)
        assert response.status_code == 409
    
    def test_get_user_admin(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """Test getting specific user as admin"""
        response = client.get(f"/api/users/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["id"] == test_user.id
        assert user_data["email"] == test_user.email
    
    def test_get_user_not_found_admin(self, client: TestClient, admin_auth_headers: dict):
        """Test getting nonexistent user as admin"""
        response = client.get("/api/users/99999", headers=admin_auth_headers)
        assert response.status_code == 404
    
    def test_update_user_admin(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """Test updating user as admin"""
        update_data = {
            "full_name": "Updated by Admin",
            "phone": "+1234567890"
        }
        
        response = client.put(f"/api/users/{test_user.id}", json=update_data, headers=admin_auth_headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["full_name"] == update_data["full_name"]
        assert user_data["phone"] == update_data["phone"]
    
    def test_update_user_status_admin(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """Test updating user status as admin"""
        status_data = {
            "is_active": False,
            "is_verified": True
        }
        
        response = client.patch(f"/api/users/{test_user.id}/status", json=status_data, headers=admin_auth_headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["is_active"] == status_data["is_active"]
        assert user_data["is_verified"] == status_data["is_verified"]
    
    def test_delete_user_admin(self, client: TestClient, admin_auth_headers: dict, db_session: AsyncSession):
        """Test deleting user as admin"""
        # Create a user to delete
        from app.modules.users.services import UserService
        user_service = UserService(db_session)
        
        user_data = {
            "email": "to-delete@example.com",
            "password": "Password123",
            "full_name": "User To Delete"
        }
        
        user = await user_service.create(user_data)
        
        response = client.delete(f"/api/users/{user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "User deleted successfully"
    
    def test_admin_actions_regular_user(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test admin actions as regular user (should fail)"""
        # Test creating user
        user_data = {
            "email": "regular-created@example.com",
            "password": "Password123",
            "full_name": "Regular Created User"
        }
        response = client.post("/api/users/", json=user_data, headers=auth_headers)
        assert response.status_code == 403
        
        # Test getting specific user
        response = client.get(f"/api/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 403
        
        # Test updating user
        update_data = {"full_name": "Updated Name"}
        response = client.put(f"/api/users/{test_user.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 403
        
        # Test deleting user
        response = client.delete(f"/api/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 403