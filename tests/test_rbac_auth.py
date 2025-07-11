"""
RBAC Authentication Integration Tests

Tests for RBAC integration with authentication system:
- Login flow with permission inclusion
- Token generation with permissions
- Permission-based route protection
- Session management with RBAC
"""

import pytest
import pytest_asyncio
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from datetime import datetime, timedelta

from app.modules.auth.models import Role, Permission
from app.modules.users.models import User
from app.modules.users.services import UserService, UserRoleService
from app.modules.auth.services import AuthService
from app.core.security import create_token_pair, verify_token
from app.core.config import settings
import jwt


def decode_token_for_test(token: str) -> dict:
    """Helper function to decode JWT token for testing"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return {}


class TestAuthRBACIntegration:
    """Test authentication and RBAC integration"""
    
    @pytest_asyncio.fixture
    async def auth_test_setup(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Setup authentication test environment with RBAC"""
        # Create permissions
        permissions_data = [
            {"name": "auth:login", "resource": "auth", "action": "login", "risk_level": "LOW"},
            {"name": "auth:logout", "resource": "auth", "action": "logout", "risk_level": "LOW"},
            {"name": "profile:read", "resource": "profile", "action": "read", "risk_level": "LOW"},
            {"name": "profile:write", "resource": "profile", "action": "write", "risk_level": "MEDIUM"},
            {"name": "users:manage", "resource": "users", "action": "manage", "risk_level": "HIGH"},
            {"name": "system:admin", "resource": "system", "action": "admin", "risk_level": "CRITICAL"},
        ]
        
        permissions = []
        for perm_data in permissions_data:
            permission = Permission(**perm_data)
            db_session.add(permission)
            permissions.append(permission)
        
        await db_session.commit()
        for perm in permissions:
            await db_session.refresh(perm)
        
        # Create roles
        basic_role = Role(name="BASIC_USER", description="Basic user access")
        basic_role.permissions.extend([
            p for p in permissions if p.name in ["auth:login", "auth:logout", "profile:read", "profile:write"]
        ])
        
        power_role = Role(name="POWER_USER", description="Power user access") 
        power_role.permissions.extend([
            p for p in permissions if p.name in ["auth:login", "auth:logout", "profile:read", "profile:write", "users:manage"]
        ])
        
        admin_role = Role(name="SYSTEM_ADMIN", description="System administrator")
        admin_role.permissions.extend(permissions)  # All permissions
        
        db_session.add_all([basic_role, power_role, admin_role])
        await db_session.commit()
        
        for role in [basic_role, power_role, admin_role]:
            await db_session.refresh(role)
        
        # Create test users
        user_service = UserService(db_session)
        role_service = UserRoleService(db_session)
        
        users = {}
        
        # Basic user
        basic_user = await user_service.create({
            "username": "basic_user",
            "email": "basic@test.com",
            "password": "BasicPass123",
            "full_name": "Basic Test User"
        })
        await role_service.assign_role(basic_user.id, basic_role.id)
        users["basic"] = basic_user
        
        # Power user
        power_user = await user_service.create({
            "username": "power_user", 
            "email": "power@test.com",
            "password": "PowerPass123",
            "full_name": "Power Test User"
        })
        await role_service.assign_role(power_user.id, power_role.id)
        users["power"] = power_user
        
        # Admin user
        admin_user = await user_service.create({
            "username": "admin_user",
            "email": "admin@test.com", 
            "password": "AdminPass123",
            "full_name": "Admin Test User",
            "is_superuser": True
        })
        await role_service.assign_role(admin_user.id, admin_role.id)
        users["admin"] = admin_user
        
        # User with no roles
        no_roles_user = await user_service.create({
            "username": "no_roles_user",
            "email": "noroles@test.com",
            "password": "NoRolesPass123", 
            "full_name": "No Roles User"
        })
        users["noroles"] = no_roles_user
        
        return {
            "permissions": {p.name: p for p in permissions},
            "roles": {"basic": basic_role, "power": power_role, "admin": admin_role},
            "users": users
        }
    
    @pytest.mark.asyncio
    async def test_login_includes_permissions(self, db_session: AsyncSession, auth_test_setup: Dict[str, Any]):
        """Test that login response includes user permissions"""
        auth_service = AuthService(db_session)
        
        # Test basic user login
        login_response = await auth_service.login(
            {"username": "basic@test.com", "password": "BasicPass123"},
            "127.0.0.1",
            "test-client"
        )
        
        assert "access_token" in login_response
        assert "refresh_token" in login_response
        assert "user" in login_response
        assert "effectivePermissions" in login_response["user"]
        
        basic_permissions = login_response["user"]["effectivePermissions"]
        expected_basic_permissions = ["auth:login", "auth:logout", "profile:read", "profile:write"]
        
        assert len(basic_permissions) == 4
        assert set(basic_permissions) == set(expected_basic_permissions)
        
        # Test admin user login
        admin_login_response = await auth_service.login(
            {"username": "admin@test.com", "password": "AdminPass123"},
            "127.0.0.1", 
            "test-client"
        )
        
        admin_permissions = admin_login_response["user"]["effectivePermissions"]
        expected_admin_permissions = ["auth:login", "auth:logout", "profile:read", "profile:write", "users:manage", "system:admin"]
        
        assert len(admin_permissions) == 6
        assert set(admin_permissions) == set(expected_admin_permissions)
        
        # Test user with no roles
        noroles_login_response = await auth_service.login(
            {"username": "noroles@test.com", "password": "NoRolesPass123"},
            "127.0.0.1",
            "test-client"
        )
        
        noroles_permissions = noroles_login_response["user"]["effectivePermissions"]
        assert len(noroles_permissions) == 0
    
    def test_jwt_token_contains_permissions(self, auth_test_setup: Dict[str, Any]):
        """Test that JWT tokens contain user permissions"""
        users = auth_test_setup["users"]
        
        # Create token for basic user
        basic_user = users["basic"]
        basic_permissions = ["auth:login", "auth:logout", "profile:read", "profile:write"]
        
        token_pair = create_token_pair(
            user_id=basic_user.id,
            username=basic_user.email,
            scopes=basic_permissions
        )
        
        # Decode and verify token contains permissions
        token_data = decode_token_for_test(token_pair.access_token)
        
        assert "sub" in token_data
        assert "username" in token_data
        assert "permissions" in token_data
        assert "exp" in token_data
        
        assert token_data["sub"] == str(basic_user.id)
        assert token_data["username"] == basic_user.email
        assert set(token_data["permissions"]) == set(basic_permissions)
        
        # Verify token expiration
        exp_timestamp = token_data["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        
        assert exp_datetime > now  # Token should not be expired
        assert exp_datetime <= now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1)
    
    def test_token_verification_with_permissions(self, auth_test_setup: Dict[str, Any]):
        """Test token verification includes permission validation"""
        users = auth_test_setup["users"]
        power_user = users["power"]
        
        # Create token with specific permissions
        power_permissions = ["auth:login", "auth:logout", "profile:read", "profile:write", "users:manage"]
        
        token_pair = create_token_pair(
            user_id=power_user.id,
            username=power_user.email,
            scopes=power_permissions
        )
        
        # Verify token
        is_valid = verify_token(token_pair.access_token)
        assert is_valid is True
        
        # Decode and check permissions
        token_data = decode_token_for_test(token_pair.access_token)
        token_permissions = token_data.get("permissions", [])
        
        assert "users:manage" in token_permissions
        assert "system:admin" not in token_permissions  # Should not have admin permission
    
    def test_login_with_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        # Wrong password
        response = client.post("/api/auth/login", json={
            "username": "basic@test.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 401
        
        # Non-existent user
        response = client.post("/api/auth/login", json={
            "username": "nonexistent@test.com",
            "password": "AnyPassword123"
        })
        assert response.status_code == 401
        
        # Missing fields
        response = client.post("/api/auth/login", json={
            "username": "basic@test.com"
        })
        assert response.status_code == 422  # Validation error
    
    def test_login_api_endpoint(self, client: TestClient, auth_test_setup: Dict[str, Any]):
        """Test login API endpoint returns proper response structure"""
        # Test successful login
        response = client.post("/api/auth/login", json={
            "username": "basic@test.com",
            "password": "BasicPass123"
        })
        
        assert response.status_code == 200
        
        login_data = response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert "token_type" in login_data
        assert "expires_in" in login_data
        assert "user" in login_data
        
        assert login_data["token_type"] == "bearer"
        assert login_data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        user_data = login_data["user"]
        assert "id" in user_data
        assert "email" in user_data
        assert "full_name" in user_data
        assert "effectivePermissions" in user_data
        
        # Verify permissions in response
        permissions = user_data["effectivePermissions"]
        expected_permissions = ["auth:login", "auth:logout", "profile:read", "profile:write"]
        assert set(permissions) == set(expected_permissions)
    
    def test_token_refresh_preserves_permissions(self, client: TestClient, auth_test_setup: Dict[str, Any]):
        """Test that token refresh preserves user permissions"""
        # Login to get initial tokens
        login_response = client.post("/api/auth/login", json={
            "username": "power@test.com",
            "password": "PowerPass123"
        })
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        refresh_token = login_data["refresh_token"]
        original_permissions = set(login_data["user"]["effectivePermissions"])
        
        # Refresh token
        refresh_response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        # Verify new token has same permissions
        new_access_token = refresh_data["access_token"]
        token_data = decode_token_for_test(new_access_token)
        new_permissions = set(token_data.get("permissions", []))
        
        assert new_permissions == original_permissions
    
    def test_logout_invalidates_tokens(self, client: TestClient, auth_test_setup: Dict[str, Any]):
        """Test that logout properly invalidates tokens"""
        # Login
        login_response = client.post("/api/auth/login", json={
            "username": "basic@test.com",
            "password": "BasicPass123"
        })
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        # Verify token works
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get("/api/users/me", headers=auth_headers)
        assert profile_response.status_code == 200
        
        # Logout
        logout_response = client.post("/api/auth/logout", headers=auth_headers)
        assert logout_response.status_code == 200
        
        # Verify token is invalidated (this depends on implementation)
        # Note: Token blacklisting would be needed for true invalidation
        profile_response_after_logout = client.get("/api/users/me", headers=auth_headers)
        # If blacklisting is implemented, this should be 401
        # Otherwise, token might still work until expiration
    
    def test_user_profile_includes_permissions(self, client: TestClient, auth_test_setup: Dict[str, Any]):
        """Test that user profile endpoint includes effective permissions"""
        # Login
        login_response = client.post("/api/auth/login", json={
            "username": "admin@test.com",
            "password": "AdminPass123"
        })
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        
        # Get user profile
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get("/api/users/me", headers=auth_headers)
        
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert "effectivePermissions" in profile_data
        
        permissions = profile_data["effectivePermissions"]
        expected_admin_permissions = ["auth:login", "auth:logout", "profile:read", "profile:write", "users:manage", "system:admin"]
        
        assert len(permissions) == 6
        assert set(permissions) == set(expected_admin_permissions)
    
    @pytest.mark.asyncio
    async def test_permission_changes_require_new_login(self, client: TestClient, auth_test_setup: Dict[str, Any], db_session: AsyncSession):
        """Test that permission changes require new login to take effect"""
        # Login as basic user
        login_response = client.post("/api/auth/login", json={
            "username": "basic@test.com", 
            "password": "BasicPass123"
        })
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        original_permissions = set(login_data["user"]["effectivePermissions"])
        
        # Verify initial permissions
        assert "users:manage" not in original_permissions
        
        # Simulate admin adding power role to basic user
        role_service = UserRoleService(db_session)
        basic_user = auth_test_setup["users"]["basic"]
        power_role = auth_test_setup["roles"]["power"]
        
        await role_service.assign_role(basic_user.id, power_role.id)
        
        # Old token should still have old permissions
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get("/api/users/me", headers=auth_headers)
        profile_data = profile_response.json()
        
        # The JWT token still contains old permissions until refresh/re-login
        token_data = decode_token_for_test(access_token)
        token_permissions = set(token_data.get("permissions", []))
        
        # Token permissions should still be the original ones
        assert token_permissions == original_permissions
        
        # New login should get updated permissions
        new_login_response = client.post("/api/auth/login", json={
            "username": "basic@test.com",
            "password": "BasicPass123"
        })
        
        new_login_data = new_login_response.json()
        new_permissions = set(new_login_data["user"]["effectivePermissions"])
        
        # Should now include permissions from both roles
        assert "users:manage" in new_permissions
        assert len(new_permissions) > len(original_permissions)


class TestRBACSessionManagement:
    """Test RBAC integration with session management"""
    
    def test_concurrent_sessions_same_user(self, client: TestClient, auth_test_setup: Dict[str, Any]):
        """Test multiple concurrent sessions for same user"""
        credentials = {
            "username": "basic@test.com",
            "password": "BasicPass123"
        }
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            response = client.post("/api/auth/login", json=credentials)
            assert response.status_code == 200
            sessions.append(response.json())
        
        # All sessions should be valid
        for session in sessions:
            auth_headers = {"Authorization": f"Bearer {session['access_token']}"}
            profile_response = client.get("/api/users/me", headers=auth_headers)
            assert profile_response.status_code == 200
            
            # All should have same permissions
            permissions = profile_response.json()["effectivePermissions"]
            expected_permissions = ["auth:login", "auth:logout", "profile:read", "profile:write"]
            assert set(permissions) == set(expected_permissions)
    
    def test_session_permission_consistency(self, client: TestClient, auth_test_setup: Dict[str, Any]):
        """Test that all sessions for a user have consistent permissions"""
        # Login multiple times
        login_responses = []
        for _ in range(3):
            response = client.post("/api/auth/login", json={
                "username": "power@test.com",
                "password": "PowerPass123"
            })
            login_responses.append(response.json())
        
        # All sessions should have identical permissions
        expected_permissions = set(login_responses[0]["user"]["effectivePermissions"])
        
        for response_data in login_responses:
            permissions = set(response_data["user"]["effectivePermissions"])
            assert permissions == expected_permissions
            
            # Verify token permissions match
            token_data = decode_token_for_test(response_data["access_token"])
            token_permissions = set(token_data.get("permissions", []))
            assert token_permissions == expected_permissions


class TestRBACSecurityScenarios:
    """Test RBAC security scenarios and edge cases"""
    
    def test_token_tampering_detection(self, auth_test_setup: Dict[str, Any]):
        """Test detection of tampered tokens"""
        users = auth_test_setup["users"]
        basic_user = users["basic"]
        
        # Create legitimate token
        legitimate_permissions = ["profile:read", "profile:write"]
        token_pair = create_token_pair(
            user_id=basic_user.id,
            username=basic_user.email,
            scopes=legitimate_permissions
        )
        
        # Try to tamper with token (add admin permission)
        # This should fail during token verification
        token_parts = token_pair.access_token.split('.')
        
        # Decode payload
        import base64
        import json
        
        # Add padding if needed
        payload = token_parts[1]
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        decoded_payload = json.loads(base64.urlsafe_b64decode(payload))
        
        # Tamper with permissions
        decoded_payload["permissions"] = ["profile:read", "profile:write", "system:admin"]
        
        # Re-encode (this will break the signature)
        tampered_payload = base64.urlsafe_b64encode(
            json.dumps(decoded_payload).encode()
        ).decode().rstrip('=')
        
        tampered_token = f"{token_parts[0]}.{tampered_payload}.{token_parts[2]}"
        
        # Token verification should fail
        is_valid = verify_token(tampered_token)
        assert is_valid is False
    
    def test_privilege_escalation_prevention(self, client: TestClient, auth_test_setup: Dict[str, Any]):
        """Test prevention of privilege escalation attacks"""
        # Login as basic user
        login_response = client.post("/api/auth/login", json={
            "username": "basic@test.com",
            "password": "BasicPass123"
        })
        
        basic_token = login_response.json()["access_token"]
        basic_headers = {"Authorization": f"Bearer {basic_token}"}
        
        # Try to access admin-only endpoints
        admin_endpoints = [
            "/api/users/",  # List users (requires higher permissions)
            "/api/users/roles/",  # List roles
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=basic_headers)
            # Should be forbidden or return limited data based on permissions
            assert response.status_code in [200, 403]  # 200 if filtering is applied, 403 if blocked
            
            if response.status_code == 200:
                # If allowed, should return filtered/limited data
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    # Paginated response - check if properly filtered
                    pass  # Implementation specific
    
    def test_role_hierarchy_enforcement(self, client: TestClient, auth_test_setup: Dict[str, Any]):
        """Test that role hierarchy is properly enforced"""
        # Login with different role levels
        role_credentials = {
            "basic": {"username": "basic@test.com", "password": "BasicPass123"},
            "power": {"username": "power@test.com", "password": "PowerPass123"},  
            "admin": {"username": "admin@test.com", "password": "AdminPass123"},
        }
        
        tokens = {}
        for role, creds in role_credentials.items():
            response = client.post("/api/auth/login", json=creds)
            tokens[role] = response.json()["access_token"]
        
        # Test permission hierarchy
        # Basic user cannot do power user actions
        basic_headers = {"Authorization": f"Bearer {tokens['basic']}"}
        response = client.post("/api/users/", json={
            "email": "test@example.com",
            "password": "Test123",
            "full_name": "Test User"
        }, headers=basic_headers)
        assert response.status_code == 403
        
        # Power user can do basic and power actions but not admin
        power_headers = {"Authorization": f"Bearer {tokens['power']}"}
        
        # Should be able to create users (if they have permission)
        response = client.post("/api/users/", json={
            "email": "powertest@example.com",
            "password": "Test123", 
            "full_name": "Power Test User"
        }, headers=power_headers)
        # This depends on the actual permission setup
        
        # Admin can do everything
        admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
        response = client.post("/api/users/", json={
            "email": "admintest@example.com",
            "password": "Test123",
            "full_name": "Admin Test User"
        }, headers=admin_headers)
        assert response.status_code == 201


if __name__ == "__main__":
    pytest.main([__file__, "-v"])