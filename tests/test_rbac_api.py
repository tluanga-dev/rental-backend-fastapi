"""
RBAC API Integration Tests

Tests for RBAC integration with API endpoints, including:
- Permission decorators and middleware
- Route-level permission checking
- HTTP status codes for authorization failures
- Token-based permission validation
"""

import pytest
import pytest_asyncio
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Role, Permission
from app.modules.users.models import User
from app.modules.users.services import UserService, UserRoleService
from app.modules.auth.services import AuthService
from app.core.security import create_token_pair


class TestRBACAPIIntegration:
    """Test RBAC integration with API endpoints"""
    
    @pytest_asyncio.fixture
    async def api_rbac_setup(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Setup RBAC structure for API testing"""
        # Create permissions for different endpoints
        permissions_data = [
            # User management permissions
            {"name": "users:read", "resource": "users", "action": "read", "risk_level": "LOW"},
            {"name": "users:write", "resource": "users", "action": "write", "risk_level": "MEDIUM"},
            {"name": "users:delete", "resource": "users", "action": "delete", "risk_level": "HIGH"},
            
            # Role management permissions
            {"name": "roles:read", "resource": "roles", "action": "read", "risk_level": "LOW"},
            {"name": "roles:write", "resource": "roles", "action": "write", "risk_level": "MEDIUM"},
            {"name": "roles:assign", "resource": "roles", "action": "assign", "risk_level": "HIGH"},
            
            # Admin permissions
            {"name": "admin:all", "resource": "admin", "action": "all", "risk_level": "CRITICAL"},
            
            # Inventory permissions (for testing other modules)
            {"name": "inventory:read", "resource": "inventory", "action": "read", "risk_level": "LOW"},
            {"name": "inventory:write", "resource": "inventory", "action": "write", "risk_level": "MEDIUM"},
        ]
        
        permissions = []
        for perm_data in permissions_data:
            permission = Permission(**perm_data)
            db_session.add(permission)
            permissions.append(permission)
        
        await db_session.commit()
        for perm in permissions:
            await db_session.refresh(perm)
        
        # Create roles with different permission levels
        roles_config = [
            {
                "name": "VIEWER",
                "description": "Can only view data",
                "permissions": ["users:read", "roles:read", "inventory:read"]
            },
            {
                "name": "EDITOR", 
                "description": "Can view and edit data",
                "permissions": ["users:read", "users:write", "roles:read", "inventory:read", "inventory:write"]
            },
            {
                "name": "MANAGER",
                "description": "Can manage users and roles",
                "permissions": ["users:read", "users:write", "users:delete", "roles:read", "roles:write", "roles:assign", "inventory:read", "inventory:write"]
            },
            {
                "name": "ADMIN",
                "description": "Full system access",
                "permissions": [p.name for p in permissions]  # All permissions
            }
        ]
        
        roles = {}
        for role_config in roles_config:
            role = Role(
                name=role_config["name"],
                description=role_config["description"],
                is_system_role=True
            )
            
            # Add permissions to role
            for perm_name in role_config["permissions"]:
                permission = next((p for p in permissions if p.name == perm_name), None)
                if permission:
                    role.permissions.append(permission)
            
            db_session.add(role)
            roles[role_config["name"]] = role
        
        await db_session.commit()
        for role in roles.values():
            await db_session.refresh(role)
        
        # Create test users with different roles
        user_service = UserService(db_session)
        role_service = UserRoleService(db_session)
        
        users_config = [
            {
                "username": "viewer",
                "email": "viewer@test.com",
                "password": "ViewerPass123",
                "full_name": "Viewer User",
                "roles": ["VIEWER"]
            },
            {
                "username": "editor",
                "email": "editor@test.com", 
                "password": "EditorPass123",
                "full_name": "Editor User",
                "roles": ["EDITOR"]
            },
            {
                "username": "manager",
                "email": "manager@test.com",
                "password": "ManagerPass123",
                "full_name": "Manager User",
                "roles": ["MANAGER"]
            },
            {
                "username": "admin",
                "email": "admin@test.com",
                "password": "AdminPass123",
                "full_name": "Admin User",
                "is_superuser": True,
                "roles": ["ADMIN"]
            },
            {
                "username": "noroles",
                "email": "noroles@test.com",
                "password": "NoRolesPass123",
                "full_name": "No Roles User",
                "roles": []  # User with no roles
            }
        ]
        
        users = {}
        for user_config in users_config:
            user_roles = user_config.pop("roles", [])
            user = await user_service.create(user_config)
            users[user_config["username"]] = user
            
            # Assign roles to user
            for role_name in user_roles:
                if role_name in roles:
                    await role_service.assign_role(user.id, roles[role_name].id)
        
        return {
            "permissions": permissions,
            "roles": roles,
            "users": users
        }
    
    @pytest_asyncio.fixture
    async def auth_tokens(self, db_session: AsyncSession, api_rbac_setup: Dict[str, Any]) -> Dict[str, str]:
        """Create authentication tokens for test users"""
        auth_service = AuthService(db_session)
        users = api_rbac_setup["users"]
        tokens = {}
        
        user_credentials = {
            "viewer": {"email": "viewer@test.com", "password": "ViewerPass123"},
            "editor": {"email": "editor@test.com", "password": "EditorPass123"},
            "manager": {"email": "manager@test.com", "password": "ManagerPass123"},
            "admin": {"email": "admin@test.com", "password": "AdminPass123"},
            "noroles": {"email": "noroles@test.com", "password": "NoRolesPass123"},
        }
        
        for username, credentials in user_credentials.items():
            login_response = await auth_service.login(
                {"username": credentials["email"], "password": credentials["password"]},
                "127.0.0.1",
                "test-client"
            )
            tokens[username] = login_response["access_token"]
        
        return tokens
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        return {"Authorization": f"Bearer {token}"}
    
    def test_user_list_endpoint_permissions(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test user list endpoint with different permission levels"""
        # Viewer should be able to read users
        response = client.get("/api/users/", headers=self.get_auth_headers(auth_tokens["viewer"]))
        assert response.status_code == 200
        
        # Editor should be able to read users
        response = client.get("/api/users/", headers=self.get_auth_headers(auth_tokens["editor"]))
        assert response.status_code == 200
        
        # Manager should be able to read users
        response = client.get("/api/users/", headers=self.get_auth_headers(auth_tokens["manager"]))
        assert response.status_code == 200
        
        # Admin should be able to read users
        response = client.get("/api/users/", headers=self.get_auth_headers(auth_tokens["admin"]))
        assert response.status_code == 200
        
        # User with no roles should be forbidden
        response = client.get("/api/users/", headers=self.get_auth_headers(auth_tokens["noroles"]))
        assert response.status_code == 403
        
        # Unauthenticated request should be unauthorized
        response = client.get("/api/users/")
        assert response.status_code == 401
    
    def test_user_creation_endpoint_permissions(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test user creation endpoint with different permission levels"""
        new_user_data = {
            "email": "newuser@test.com",
            "password": "NewUserPass123",
            "full_name": "New Test User"
        }
        
        # Viewer should NOT be able to create users (only read permission)
        response = client.post("/api/users/", json=new_user_data, headers=self.get_auth_headers(auth_tokens["viewer"]))
        assert response.status_code == 403
        
        # Editor should be able to create users (has write permission)
        response = client.post("/api/users/", json=new_user_data, headers=self.get_auth_headers(auth_tokens["editor"]))
        assert response.status_code == 201
        
        # Update email for next test
        new_user_data["email"] = "newuser2@test.com"
        
        # Manager should be able to create users
        response = client.post("/api/users/", json=new_user_data, headers=self.get_auth_headers(auth_tokens["manager"]))
        assert response.status_code == 201
        
        # Update email for next test
        new_user_data["email"] = "newuser3@test.com"
        
        # Admin should be able to create users
        response = client.post("/api/users/", json=new_user_data, headers=self.get_auth_headers(auth_tokens["admin"]))
        assert response.status_code == 201
        
        # User with no roles should be forbidden
        new_user_data["email"] = "newuser4@test.com"
        response = client.post("/api/users/", json=new_user_data, headers=self.get_auth_headers(auth_tokens["noroles"]))
        assert response.status_code == 403
    
    def test_user_deletion_endpoint_permissions(self, client: TestClient, auth_tokens: Dict[str, str], api_rbac_setup: Dict[str, Any]):
        """Test user deletion endpoint with different permission levels"""
        # Get a user ID to delete (use the noroles user)
        user_id = api_rbac_setup["users"]["noroles"].id
        
        # Viewer should NOT be able to delete users
        response = client.delete(f"/api/users/{user_id}", headers=self.get_auth_headers(auth_tokens["viewer"]))
        assert response.status_code == 403
        
        # Editor should NOT be able to delete users (no delete permission)
        response = client.delete(f"/api/users/{user_id}", headers=self.get_auth_headers(auth_tokens["editor"]))
        assert response.status_code == 403
        
        # Manager should be able to delete users (has delete permission)
        response = client.delete(f"/api/users/{user_id}", headers=self.get_auth_headers(auth_tokens["manager"]))
        assert response.status_code == 200
        
        # Verify user was deleted
        response = client.get(f"/api/users/{user_id}", headers=self.get_auth_headers(auth_tokens["admin"]))
        assert response.status_code == 404
    
    def test_role_management_endpoint_permissions(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test role management endpoints with different permission levels"""
        # Test getting roles list
        response = client.get("/api/users/roles/", headers=self.get_auth_headers(auth_tokens["viewer"]))
        assert response.status_code == 200  # Viewer can read roles
        
        response = client.get("/api/users/roles/", headers=self.get_auth_headers(auth_tokens["editor"]))
        assert response.status_code == 200  # Editor can read roles
        
        response = client.get("/api/users/roles/", headers=self.get_auth_headers(auth_tokens["noroles"]))
        assert response.status_code == 403  # No roles user cannot read roles
        
        # Test creating roles
        new_role_data = {
            "name": "TEST_ROLE",
            "description": "Test role for API testing",
            "permissions": []
        }
        
        # Viewer should NOT be able to create roles
        response = client.post("/api/users/roles/", json=new_role_data, headers=self.get_auth_headers(auth_tokens["viewer"]))
        assert response.status_code == 403
        
        # Editor should NOT be able to create roles (no write permission for roles)
        response = client.post("/api/users/roles/", json=new_role_data, headers=self.get_auth_headers(auth_tokens["editor"]))
        assert response.status_code == 403
        
        # Manager should be able to create roles
        response = client.post("/api/users/roles/", json=new_role_data, headers=self.get_auth_headers(auth_tokens["manager"]))
        assert response.status_code == 201
        
        # Admin should be able to create roles
        new_role_data["name"] = "ANOTHER_TEST_ROLE"
        response = client.post("/api/users/roles/", json=new_role_data, headers=self.get_auth_headers(auth_tokens["admin"]))
        assert response.status_code == 201
    
    def test_role_assignment_endpoint_permissions(self, client: TestClient, auth_tokens: Dict[str, str], api_rbac_setup: Dict[str, Any]):
        """Test role assignment endpoints with different permission levels"""
        user_id = api_rbac_setup["users"]["editor"].id
        role_id = api_rbac_setup["roles"]["VIEWER"].id
        
        # Viewer should NOT be able to assign roles
        response = client.post(f"/api/users/{user_id}/roles/{role_id}", headers=self.get_auth_headers(auth_tokens["viewer"]))
        assert response.status_code == 403
        
        # Editor should NOT be able to assign roles (no assign permission)
        response = client.post(f"/api/users/{user_id}/roles/{role_id}", headers=self.get_auth_headers(auth_tokens["editor"]))
        assert response.status_code == 403
        
        # Manager should be able to assign roles
        response = client.post(f"/api/users/{user_id}/roles/{role_id}", headers=self.get_auth_headers(auth_tokens["manager"]))
        assert response.status_code == 200
        
        # Test removing role assignment
        response = client.delete(f"/api/users/{user_id}/roles/{role_id}", headers=self.get_auth_headers(auth_tokens["manager"]))
        assert response.status_code == 200
    
    def test_current_user_endpoints_permissions(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test current user endpoints (should work for all authenticated users)"""
        # All authenticated users should be able to access their own profile
        for username, token in auth_tokens.items():
            response = client.get("/api/users/me", headers=self.get_auth_headers(token))
            assert response.status_code == 200
            
            user_data = response.json()
            assert "email" in user_data
            assert "full_name" in user_data
            
            # Check that permissions are included in response
            if username != "noroles":
                assert "effectivePermissions" in user_data
                assert isinstance(user_data["effectivePermissions"], list)
            else:
                # User with no roles should have empty permissions
                assert user_data.get("effectivePermissions", []) == []
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints properly reject unauthorized requests"""
        endpoints_to_test = [
            ("GET", "/api/users/"),
            ("POST", "/api/users/"),
            ("GET", "/api/users/1"),
            ("PUT", "/api/users/1"),
            ("DELETE", "/api/users/1"),
            ("GET", "/api/users/roles/"),
            ("POST", "/api/users/roles/"),
            ("POST", "/api/users/1/roles/1"),
            ("DELETE", "/api/users/1/roles/1"),
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should return 401 for unauthorized requests"
    
    def test_invalid_token_access(self, client: TestClient):
        """Test that endpoints properly reject invalid tokens"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/users/", headers=invalid_headers)
        assert response.status_code == 401
        
        response = client.get("/api/users/me", headers=invalid_headers)
        assert response.status_code == 401
    
    def test_token_permission_validation(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test that tokens contain correct permissions for API access"""
        # Get user profile to check permissions in token
        response = client.get("/api/users/me", headers=self.get_auth_headers(auth_tokens["viewer"]))
        assert response.status_code == 200
        
        user_data = response.json()
        permissions = user_data.get("effectivePermissions", [])
        
        # Viewer should have read permissions
        expected_viewer_permissions = ["users:read", "roles:read", "inventory:read"]
        for perm in expected_viewer_permissions:
            assert perm in permissions
        
        # Viewer should NOT have write/delete permissions
        forbidden_permissions = ["users:write", "users:delete", "roles:write", "roles:assign"]
        for perm in forbidden_permissions:
            assert perm not in permissions
        
        # Test manager permissions
        response = client.get("/api/users/me", headers=self.get_auth_headers(auth_tokens["manager"]))
        user_data = response.json()
        permissions = user_data.get("effectivePermissions", [])
        
        # Manager should have extensive permissions
        expected_manager_permissions = ["users:read", "users:write", "users:delete", "roles:read", "roles:write", "roles:assign"]
        for perm in expected_manager_permissions:
            assert perm in permissions
    
    def test_permission_inheritance_in_api(self, client: TestClient, auth_tokens: Dict[str, str], api_rbac_setup: Dict[str, Any]):
        """Test that users with multiple roles get combined permissions"""
        # Create a user and assign multiple roles
        user_id = api_rbac_setup["users"]["editor"].id
        viewer_role_id = api_rbac_setup["roles"]["VIEWER"].id
        
        # Assign additional role (VIEWER) to editor user
        response = client.post(
            f"/api/users/{user_id}/roles/{viewer_role_id}",
            headers=self.get_auth_headers(auth_tokens["manager"])  # Manager can assign roles
        )
        assert response.status_code == 200
        
        # Get updated user permissions by getting their roles
        response = client.get(f"/api/users/{user_id}/roles", headers=self.get_auth_headers(auth_tokens["manager"]))
        assert response.status_code == 200
        
        user_roles = response.json()
        assert len(user_roles) >= 2  # Should have at least EDITOR and VIEWER roles
        
        # Get all permissions from all roles
        all_permissions = set()
        for role in user_roles:
            all_permissions.update(role.get("permissions", []))
        
        # Should have combined permissions from both roles
        expected_combined_permissions = ["users:read", "users:write", "roles:read", "inventory:read", "inventory:write"]
        for perm in expected_combined_permissions:
            assert perm in all_permissions


class TestRBACMiddleware:
    """Test RBAC middleware functionality"""
    
    def test_permission_middleware_bypass_for_public_endpoints(self, client: TestClient):
        """Test that public endpoints bypass permission checks"""
        # Health endpoint should be accessible without authentication
        response = client.get("/health")
        assert response.status_code == 200
        
        # Login endpoint should be accessible without authentication
        response = client.post("/api/auth/login", json={
            "username": "test@example.com",
            "password": "wrongpassword"
        })
        # Should return 401 for wrong credentials, not 403 for permissions
        assert response.status_code in [400, 401, 422]  # Not 403
    
    def test_permission_middleware_enforcement(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test that permission middleware properly enforces access control"""
        # Test that viewer can access GET endpoints but not POST/PUT/DELETE
        viewer_headers = {"Authorization": f"Bearer {auth_tokens['viewer']}"}
        
        # Should be able to GET
        response = client.get("/api/users/", headers=viewer_headers)
        assert response.status_code == 200
        
        # Should NOT be able to POST (create)
        response = client.post("/api/users/", json={
            "email": "test@example.com",
            "password": "Test123",
            "full_name": "Test User"
        }, headers=viewer_headers)
        assert response.status_code == 403
    
    def test_superuser_bypass(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test that superusers can bypass permission checks"""
        admin_headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        # Admin should be able to access all endpoints
        response = client.get("/api/users/", headers=admin_headers)
        assert response.status_code == 200
        
        response = client.post("/api/users/", json={
            "email": "superuser_test@example.com",
            "password": "Test123",
            "full_name": "Superuser Test"
        }, headers=admin_headers)
        assert response.status_code == 201


class TestRBACErrorHandling:
    """Test RBAC error handling and edge cases in API"""
    
    def test_missing_permission_error_response(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test that missing permission errors return proper error responses"""
        # Viewer trying to delete user should get proper error
        response = client.delete("/api/users/999", headers={"Authorization": f"Bearer {auth_tokens['viewer']}"})
        assert response.status_code == 403
        
        error_data = response.json()
        assert "detail" in error_data
        # Should contain information about missing permission
        assert "permission" in error_data["detail"].lower() or "forbidden" in error_data["detail"].lower()
    
    def test_expired_token_handling(self, client: TestClient):
        """Test handling of expired tokens"""
        # Create an expired token (this would normally be handled by token validation)
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        
        response = client.get("/api/users/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401
    
    def test_malformed_token_handling(self, client: TestClient):
        """Test handling of malformed tokens"""
        malformed_tokens = [
            "not_a_token",
            "Bearer",
            "Bearer ",
            "Bearer invalid.token.format",
            "InvalidScheme token_here"
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": token} if not token.startswith("Bearer") else {"Authorization": token}
            response = client.get("/api/users/me", headers=headers)
            assert response.status_code == 401


class TestRBACPerformanceAPI:
    """Test RBAC performance in API context"""
    
    def test_permission_check_performance(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test that permission checks don't significantly impact API performance"""
        import time
        
        # Make multiple requests and measure average response time
        headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
        
        times = []
        for _ in range(10):
            start_time = time.time()
            response = client.get("/api/users/me", headers=headers)
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        # Permission checks should not add significant overhead (< 100ms)
        assert avg_time < 0.1, f"Average response time {avg_time:.3f}s is too slow"
    
    def test_bulk_permission_validation(self, client: TestClient, auth_tokens: Dict[str, str]):
        """Test permission validation with multiple rapid requests"""
        headers = {"Authorization": f"Bearer {auth_tokens['manager']}"}
        
        # Make multiple concurrent-style requests
        responses = []
        for i in range(20):
            response = client.get("/api/users/", headers=headers)
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Test mixed permission scenarios
        forbidden_responses = []
        for i in range(10):
            response = client.delete(f"/api/users/{i+1000}", headers={"Authorization": f"Bearer {auth_tokens['viewer']}"})
            forbidden_responses.append(response)
        
        # All should be forbidden
        for response in forbidden_responses:
            assert response.status_code in [403, 404]  # 404 for non-existent users, 403 for permission


if __name__ == "__main__":
    pytest.main([__file__, "-v"])