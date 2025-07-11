"""
RBAC Test Configuration and Fixtures

Specialized fixtures and configuration for RBAC testing.
This file provides comprehensive test fixtures for RBAC scenarios.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Role, Permission, user_roles_table, role_permissions_table
from app.modules.users.models import User
from app.modules.users.services import UserService, UserRoleService
from app.modules.auth.services import AuthService
from app.core.security import create_token_pair


@pytest_asyncio.fixture
async def rbac_permissions(db_session: AsyncSession) -> Dict[str, Permission]:
    """Create standard set of permissions for RBAC testing"""
    
    permissions_data = [
        # User management
        {"name": "users:create", "resource": "users", "action": "create", "risk_level": "MEDIUM"},
        {"name": "users:read", "resource": "users", "action": "read", "risk_level": "LOW"},
        {"name": "users:update", "resource": "users", "action": "update", "risk_level": "MEDIUM"},
        {"name": "users:delete", "resource": "users", "action": "delete", "risk_level": "HIGH"},
        {"name": "users:list", "resource": "users", "action": "list", "risk_level": "LOW"},
        
        # Role management
        {"name": "roles:create", "resource": "roles", "action": "create", "risk_level": "HIGH"},
        {"name": "roles:read", "resource": "roles", "action": "read", "risk_level": "LOW"},
        {"name": "roles:update", "resource": "roles", "action": "update", "risk_level": "HIGH"},
        {"name": "roles:delete", "resource": "roles", "action": "delete", "risk_level": "CRITICAL"},
        {"name": "roles:assign", "resource": "roles", "action": "assign", "risk_level": "HIGH"},
        
        # Profile management
        {"name": "profile:read", "resource": "profile", "action": "read", "risk_level": "LOW"},
        {"name": "profile:update", "resource": "profile", "action": "update", "risk_level": "LOW"},
        
        # Inventory management
        {"name": "inventory:create", "resource": "inventory", "action": "create", "risk_level": "MEDIUM"},
        {"name": "inventory:read", "resource": "inventory", "action": "read", "risk_level": "LOW"},
        {"name": "inventory:update", "resource": "inventory", "action": "update", "risk_level": "MEDIUM"},
        {"name": "inventory:delete", "resource": "inventory", "action": "delete", "risk_level": "HIGH"},
        
        # Reports
        {"name": "reports:read", "resource": "reports", "action": "read", "risk_level": "LOW"},
        {"name": "reports:create", "resource": "reports", "action": "create", "risk_level": "MEDIUM"},
        {"name": "reports:export", "resource": "reports", "action": "export", "risk_level": "MEDIUM"},
        
        # System administration
        {"name": "system:backup", "resource": "system", "action": "backup", "risk_level": "HIGH"},
        {"name": "system:restore", "resource": "system", "action": "restore", "risk_level": "CRITICAL"},
        {"name": "system:config", "resource": "system", "action": "config", "risk_level": "CRITICAL"},
        {"name": "system:logs", "resource": "system", "action": "logs", "risk_level": "MEDIUM"},
        
        # Authentication
        {"name": "auth:login", "resource": "auth", "action": "login", "risk_level": "LOW"},
        {"name": "auth:logout", "resource": "auth", "action": "logout", "risk_level": "LOW"},
        {"name": "auth:reset_password", "resource": "auth", "action": "reset_password", "risk_level": "MEDIUM"},
    ]
    
    permissions = {}
    for perm_data in permissions_data:
        permission = Permission(**perm_data)
        db_session.add(permission)
        permissions[perm_data["name"]] = permission
    
    await db_session.commit()
    for permission in permissions.values():
        await db_session.refresh(permission)
    
    return permissions


@pytest_asyncio.fixture
async def rbac_roles(db_session: AsyncSession, rbac_permissions: Dict[str, Permission]) -> Dict[str, Role]:
    """Create standard set of roles for RBAC testing"""
    
    roles_config = {
        "GUEST": {
            "description": "Guest user with minimal access",
            "permissions": ["auth:login", "auth:logout"]
        },
        "USER": {
            "description": "Regular user with basic access",
            "permissions": [
                "auth:login", "auth:logout", "profile:read", "profile:update",
                "inventory:read", "reports:read"
            ]
        },
        "STAFF": {
            "description": "Staff member with extended access",
            "permissions": [
                "auth:login", "auth:logout", "profile:read", "profile:update",
                "users:read", "users:list", "inventory:create", "inventory:read", 
                "inventory:update", "reports:read", "reports:create"
            ]
        },
        "SUPERVISOR": {
            "description": "Supervisor with management capabilities",
            "permissions": [
                "auth:login", "auth:logout", "profile:read", "profile:update",
                "users:create", "users:read", "users:update", "users:list",
                "inventory:create", "inventory:read", "inventory:update", "inventory:delete",
                "reports:read", "reports:create", "reports:export", "roles:read"
            ]
        },
        "MANAGER": {
            "description": "Manager with user management capabilities",
            "permissions": [
                "auth:login", "auth:logout", "profile:read", "profile:update",
                "users:create", "users:read", "users:update", "users:delete", "users:list",
                "inventory:create", "inventory:read", "inventory:update", "inventory:delete",
                "reports:read", "reports:create", "reports:export",
                "roles:read", "roles:assign", "system:logs"
            ]
        },
        "ADMIN": {
            "description": "System administrator with full access",
            "permissions": list(rbac_permissions.keys())  # All permissions
        }
    }
    
    roles = {}
    for role_name, role_config in roles_config.items():
        role = Role(
            name=role_name,
            description=role_config["description"],
            is_system_role=True,
            is_active=True
        )
        
        # Add permissions to role
        for perm_name in role_config["permissions"]:
            if perm_name in rbac_permissions:
                role.permissions.append(rbac_permissions[perm_name])
        
        db_session.add(role)
        roles[role_name] = role
    
    await db_session.commit()
    for role in roles.values():
        await db_session.refresh(role)
    
    return roles


@pytest_asyncio.fixture
async def rbac_users(db_session: AsyncSession, rbac_roles: Dict[str, Role]) -> Dict[str, User]:
    """Create standard set of users for RBAC testing"""
    
    user_service = UserService(db_session)
    role_service = UserRoleService(db_session)
    
    users_config = [
        {
            "username": "guest_user",
            "email": "guest@rbactest.com",
            "password": "GuestPass123",
            "full_name": "Guest User",
            "user_type": "USER",
            "roles": ["GUEST"]
        },
        {
            "username": "regular_user",
            "email": "user@rbactest.com",
            "password": "UserPass123",
            "full_name": "Regular User",
            "user_type": "USER",
            "roles": ["USER"]
        },
        {
            "username": "staff_user",
            "email": "staff@rbactest.com",
            "password": "StaffPass123",
            "full_name": "Staff User",
            "user_type": "STAFF",
            "roles": ["STAFF"]
        },
        {
            "username": "supervisor_user",
            "email": "supervisor@rbactest.com",
            "password": "SupervisorPass123",
            "full_name": "Supervisor User",
            "user_type": "MANAGER",
            "roles": ["SUPERVISOR"]
        },
        {
            "username": "manager_user",
            "email": "manager@rbactest.com",
            "password": "ManagerPass123",
            "full_name": "Manager User",
            "user_type": "MANAGER",
            "roles": ["MANAGER"]
        },
        {
            "username": "admin_user",
            "email": "admin@rbactest.com",
            "password": "AdminPass123",
            "full_name": "Admin User",
            "user_type": "ADMIN",
            "is_superuser": True,
            "roles": ["ADMIN"]
        },
        {
            "username": "multi_role_user",
            "email": "multirole@rbactest.com",
            "password": "MultiPass123",
            "full_name": "Multi Role User",
            "user_type": "STAFF",
            "roles": ["USER", "STAFF"]  # Multiple roles
        },
        {
            "username": "no_roles_user",
            "email": "noroles@rbactest.com",
            "password": "NoRolesPass123",
            "full_name": "No Roles User",
            "user_type": "USER",
            "roles": []  # No roles assigned
        }
    ]
    
    users = {}
    for user_config in users_config:
        user_roles = user_config.pop("roles", [])
        user = await user_service.create(user_config)
        users[user_config["username"]] = user
        
        # Assign roles to user
        for role_name in user_roles:
            if role_name in rbac_roles:
                await role_service.assign_role(user.id, rbac_roles[role_name].id)
    
    return users


@pytest_asyncio.fixture 
async def rbac_tokens(db_session: AsyncSession, rbac_users: Dict[str, User]) -> Dict[str, str]:
    """Create authentication tokens for RBAC test users"""
    
    auth_service = AuthService(db_session)
    tokens = {}
    
    user_credentials = {
        "guest_user": {"email": "guest@rbactest.com", "password": "GuestPass123"},
        "regular_user": {"email": "user@rbactest.com", "password": "UserPass123"},
        "staff_user": {"email": "staff@rbactest.com", "password": "StaffPass123"},
        "supervisor_user": {"email": "supervisor@rbactest.com", "password": "SupervisorPass123"},
        "manager_user": {"email": "manager@rbactest.com", "password": "ManagerPass123"},
        "admin_user": {"email": "admin@rbactest.com", "password": "AdminPass123"},
        "multi_role_user": {"email": "multirole@rbactest.com", "password": "MultiPass123"},
        "no_roles_user": {"email": "noroles@rbactest.com", "password": "NoRolesPass123"},
    }
    
    for username, credentials in user_credentials.items():
        try:
            login_response = await auth_service.login(
                {"username": credentials["email"], "password": credentials["password"]},
                "127.0.0.1",
                "rbac-test-client"
            )
            tokens[username] = login_response["access_token"]
        except Exception as e:
            # If login fails, skip this user
            print(f"Warning: Could not create token for {username}: {e}")
            continue
    
    return tokens


@pytest.fixture
def rbac_auth_headers(rbac_tokens: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """Create authorization headers for RBAC test users"""
    
    headers = {}
    for username, token in rbac_tokens.items():
        headers[username] = {"Authorization": f"Bearer {token}"}
    
    return headers


@pytest_asyncio.fixture
async def rbac_complete_setup(
    db_session: AsyncSession,
    rbac_permissions: Dict[str, Permission],
    rbac_roles: Dict[str, Role],
    rbac_users: Dict[str, User],
    rbac_tokens: Dict[str, str]
) -> Dict[str, Any]:
    """Complete RBAC setup with all components"""
    
    return {
        "db_session": db_session,
        "permissions": rbac_permissions,
        "roles": rbac_roles,
        "users": rbac_users,
        "tokens": rbac_tokens,
        "auth_headers": {username: {"Authorization": f"Bearer {token}"} 
                        for username, token in rbac_tokens.items()}
    }


class RBACTestHelper:
    """Helper class for RBAC testing"""
    
    @staticmethod
    def assert_has_permissions(user_permissions: List[str], required_permissions: List[str]):
        """Assert that user has all required permissions"""
        missing_permissions = set(required_permissions) - set(user_permissions)
        assert not missing_permissions, f"User missing permissions: {missing_permissions}"
    
    @staticmethod
    def assert_lacks_permissions(user_permissions: List[str], forbidden_permissions: List[str]):
        """Assert that user does not have forbidden permissions"""
        forbidden_found = set(user_permissions) & set(forbidden_permissions)
        assert not forbidden_found, f"User has forbidden permissions: {forbidden_found}"
    
    @staticmethod
    def assert_permission_hierarchy(lower_perms: List[str], higher_perms: List[str]):
        """Assert that higher role includes all permissions of lower role"""
        missing_perms = set(lower_perms) - set(higher_perms)
        assert not missing_perms, f"Higher role missing lower role permissions: {missing_perms}"
    
    @staticmethod
    async def verify_user_permissions(
        role_service: UserRoleService, 
        user_id: int, 
        expected_permissions: List[str]
    ):
        """Verify user has exactly the expected permissions"""
        actual_permissions = await role_service.get_user_permissions(user_id)
        assert set(actual_permissions) == set(expected_permissions)
    
    @staticmethod
    def get_permissions_by_risk_level(permissions: Dict[str, Permission], risk_level: str) -> List[str]:
        """Get all permissions of a specific risk level"""
        return [name for name, perm in permissions.items() if perm.risk_level == risk_level]
    
    @staticmethod
    def get_permissions_by_resource(permissions: Dict[str, Permission], resource: str) -> List[str]:
        """Get all permissions for a specific resource"""
        return [name for name, perm in permissions.items() if perm.resource == resource]


@pytest.fixture
def rbac_helper():
    """RBAC test helper fixture"""
    return RBACTestHelper


# Permission test data sets
@pytest.fixture
def permission_test_data():
    """Test data for permission testing"""
    return {
        "valid_permissions": [
            {"name": "test:read", "resource": "test", "action": "read", "risk_level": "LOW"},
            {"name": "test:write", "resource": "test", "action": "write", "risk_level": "MEDIUM"},
            {"name": "test:delete", "resource": "test", "action": "delete", "risk_level": "HIGH"},
        ],
        "invalid_permissions": [
            {"name": "", "resource": "test", "action": "read"},  # Empty name
            {"name": "test:read", "resource": "", "action": "read"},  # Empty resource
            {"name": "test:read", "resource": "test", "action": ""},  # Empty action
        ],
        "risk_levels": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "resources": ["users", "roles", "inventory", "reports", "system", "auth"],
        "actions": ["create", "read", "update", "delete", "list", "assign", "export"]
    }


# Role test data sets
@pytest.fixture
def role_test_data():
    """Test data for role testing"""
    return {
        "valid_roles": [
            {"name": "TEST_ROLE_1", "description": "Test role 1", "is_system_role": False},
            {"name": "TEST_ROLE_2", "description": "Test role 2", "is_system_role": True},
            {"name": "CUSTOM_ROLE", "description": "Custom role", "is_active": True},
        ],
        "invalid_roles": [
            {"name": "", "description": "Empty name"},  # Empty name
            {"name": "DUPLICATE", "description": "First"},  # Will be duplicated
        ],
        "permission_sets": {
            "basic": ["profile:read", "profile:update"],
            "extended": ["users:read", "users:list", "inventory:read"],
            "advanced": ["users:create", "users:update", "users:delete", "roles:read"],
            "admin": ["system:config", "system:backup", "system:restore"]
        }
    }


# User test data sets  
@pytest.fixture
def user_test_data():
    """Test data for user testing"""
    return {
        "valid_users": [
            {
                "username": "test_user_1",
                "email": "test1@rbactest.com",
                "password": "TestPass123",
                "full_name": "Test User 1"
            },
            {
                "username": "test_user_2", 
                "email": "test2@rbactest.com",
                "password": "TestPass123",
                "full_name": "Test User 2",
                "is_superuser": True
            }
        ],
        "invalid_users": [
            {"username": "", "email": "invalid@test.com", "password": "Test123"},  # Empty username
            {"username": "test", "email": "", "password": "Test123"},  # Empty email
            {"username": "test", "email": "test@test.com", "password": ""},  # Empty password
            {"username": "test", "email": "invalid-email", "password": "Test123"},  # Invalid email
        ],
        "role_assignments": {
            "single_role": ["USER"],
            "multiple_roles": ["USER", "STAFF"],
            "high_privilege": ["MANAGER"],
            "admin_role": ["ADMIN"],
            "no_roles": []
        }
    }


# API test scenarios
@pytest.fixture 
def api_test_scenarios():
    """Test scenarios for API RBAC testing"""
    return {
        "endpoints": {
            "users": {
                "list": {"method": "GET", "path": "/api/users/", "required_permission": "users:list"},
                "create": {"method": "POST", "path": "/api/users/", "required_permission": "users:create"},
                "read": {"method": "GET", "path": "/api/users/{id}", "required_permission": "users:read"},
                "update": {"method": "PUT", "path": "/api/users/{id}", "required_permission": "users:update"},
                "delete": {"method": "DELETE", "path": "/api/users/{id}", "required_permission": "users:delete"},
            },
            "roles": {
                "list": {"method": "GET", "path": "/api/users/roles/", "required_permission": "roles:read"},
                "create": {"method": "POST", "path": "/api/users/roles/", "required_permission": "roles:create"},
                "assign": {"method": "POST", "path": "/api/users/{user_id}/roles/{role_id}", "required_permission": "roles:assign"},
            },
            "profile": {
                "read": {"method": "GET", "path": "/api/users/me", "required_permission": "profile:read"},
                "update": {"method": "PUT", "path": "/api/users/me", "required_permission": "profile:update"},
            }
        },
        "expected_status_codes": {
            "success": [200, 201, 204],
            "unauthorized": [401],
            "forbidden": [403],
            "not_found": [404],
            "validation_error": [422]
        }
    }