"""
Comprehensive RBAC (Role-Based Access Control) Test Suite

This test suite covers all aspects of the RBAC system including:
- Permission model and operations
- Role model and permission assignments
- User-Role relationships
- Permission checking and validation
- RBAC decorators and middleware
- JWT token permission inclusion
- Edge cases and error handling
"""

import pytest
import pytest_asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.testclient import TestClient

from app.modules.auth.models import Role, Permission, role_permissions_table, user_roles_table
from app.modules.users.models import User
from app.modules.users.services import UserService, UserRoleService
from app.modules.auth.services import AuthService
from app.core.security import create_token_pair, verify_token
from app.shared.exceptions import NotFoundError, AlreadyExistsError, ValidationError
from app.core.config import settings
import jwt


def decode_token_for_test(token: str) -> dict:
    """Helper function to decode JWT token for testing"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return {}


class TestPermissionModel:
    """Test Permission model and basic operations"""
    
    @pytest_asyncio.fixture
    async def sample_permissions(self, db_session: AsyncSession) -> List[Permission]:
        """Create sample permissions for testing"""
        permissions_data = [
            {
                "name": "users:read",
                "description": "Read user information",
                "resource": "users",
                "action": "read",
                "risk_level": "LOW"
            },
            {
                "name": "users:write",
                "description": "Create and update users",
                "resource": "users", 
                "action": "write",
                "risk_level": "MEDIUM"
            },
            {
                "name": "users:delete",
                "description": "Delete users",
                "resource": "users",
                "action": "delete", 
                "risk_level": "HIGH"
            },
            {
                "name": "inventory:manage",
                "description": "Manage inventory items",
                "resource": "inventory",
                "action": "manage",
                "risk_level": "MEDIUM"
            }
        ]
        
        permissions = []
        for perm_data in permissions_data:
            permission = Permission(**perm_data)
            db_session.add(permission)
            permissions.append(permission)
        
        await db_session.commit()
        for perm in permissions:
            await db_session.refresh(perm)
        
        return permissions
    
    @pytest.mark.asyncio
    async def test_permission_creation(self, db_session: AsyncSession):
        """Test creating a permission"""
        permission_data = {
            "name": "test:permission",
            "description": "Test permission",
            "resource": "test",
            "action": "test",
            "risk_level": "LOW"
        }
        
        permission = Permission(**permission_data)
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)
        
        assert permission.id is not None
        assert permission.name == "test:permission"
        assert permission.resource == "test"
        assert permission.action == "test"
        assert permission.risk_level == "LOW"
        assert permission.is_system_permission is False
        assert permission.created_at is not None
    
    @pytest.mark.asyncio
    async def test_permission_unique_name(self, db_session: AsyncSession, sample_permissions: List[Permission]):
        """Test that permission names must be unique"""
        # Try to create permission with existing name
        duplicate_permission = Permission(
            name="users:read",  # This already exists
            description="Duplicate permission",
            resource="users",
            action="read"
        )
        
        db_session.add(duplicate_permission)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_permission_query(self, db_session: AsyncSession, sample_permissions: List[Permission]):
        """Test querying permissions"""
        # Query by name
        stmt = select(Permission).where(Permission.name == "users:read")
        result = await db_session.execute(stmt)
        permission = result.scalar_one_or_none()
        
        assert permission is not None
        assert permission.name == "users:read"
        assert permission.resource == "users"
        
        # Query by resource
        stmt = select(Permission).where(Permission.resource == "users")
        result = await db_session.execute(stmt)
        user_permissions = result.scalars().all()
        
        assert len(user_permissions) == 3  # read, write, delete
        
        # Query by risk level
        stmt = select(Permission).where(Permission.risk_level == "HIGH")
        result = await db_session.execute(stmt)
        high_risk_permissions = result.scalars().all()
        
        assert len(high_risk_permissions) == 1
        assert high_risk_permissions[0].name == "users:delete"


class TestRoleModel:
    """Test Role model and permission assignments"""
    
    @pytest_asyncio.fixture
    async def sample_roles_and_permissions(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Create sample roles and permissions for testing"""
        # Create permissions
        permissions_data = [
            {"name": "users:read", "resource": "users", "action": "read", "risk_level": "LOW"},
            {"name": "users:write", "resource": "users", "action": "write", "risk_level": "MEDIUM"},
            {"name": "users:delete", "resource": "users", "action": "delete", "risk_level": "HIGH"},
            {"name": "inventory:read", "resource": "inventory", "action": "read", "risk_level": "LOW"},
            {"name": "inventory:write", "resource": "inventory", "action": "write", "risk_level": "MEDIUM"},
            {"name": "reports:read", "resource": "reports", "action": "read", "risk_level": "LOW"},
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
        roles_data = [
            {
                "name": "VIEWER",
                "description": "Can view data",
                "is_system_role": True,
                "permissions": ["users:read", "inventory:read", "reports:read"]
            },
            {
                "name": "EDITOR", 
                "description": "Can view and edit data",
                "is_system_role": True,
                "permissions": ["users:read", "users:write", "inventory:read", "inventory:write", "reports:read"]
            },
            {
                "name": "ADMIN",
                "description": "Full access",
                "is_system_role": True,
                "permissions": ["users:read", "users:write", "users:delete", "inventory:read", "inventory:write", "reports:read"]
            }
        ]
        
        roles = []
        for role_data in roles_data:
            role_perms = role_data.pop("permissions", [])
            role = Role(**role_data)
            db_session.add(role)
            
            # Add permissions to role
            for perm_name in role_perms:
                permission = next((p for p in permissions if p.name == perm_name), None)
                if permission:
                    role.permissions.append(permission)
            
            roles.append(role)
        
        await db_session.commit()
        for role in roles:
            await db_session.refresh(role)
        
        return {"roles": roles, "permissions": permissions}
    
    @pytest.mark.asyncio
    async def test_role_creation(self, db_session: AsyncSession):
        """Test creating a role"""
        role_data = {
            "name": "TEST_ROLE",
            "description": "Test role",
            "is_system_role": False,
            "is_active": True
        }
        
        role = Role(**role_data)
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        assert role.id is not None
        assert role.name == "TEST_ROLE"
        assert role.description == "Test role"
        assert role.is_system_role is False
        assert role.is_active is True
        assert role.created_at is not None
    
    @pytest.mark.asyncio
    async def test_role_permission_assignment(self, db_session: AsyncSession, sample_roles_and_permissions: Dict[str, Any]):
        """Test assigning permissions to roles"""
        roles = sample_roles_and_permissions["roles"]
        permissions = sample_roles_and_permissions["permissions"]
        
        # Check VIEWER role permissions
        viewer_role = next((r for r in roles if r.name == "VIEWER"), None)
        assert viewer_role is not None
        
        viewer_permission_names = [p.name for p in viewer_role.permissions]
        expected_viewer_perms = ["users:read", "inventory:read", "reports:read"]
        
        assert len(viewer_permission_names) == 3
        for perm_name in expected_viewer_perms:
            assert perm_name in viewer_permission_names
        
        # Check ADMIN role permissions
        admin_role = next((r for r in roles if r.name == "ADMIN"), None)
        assert admin_role is not None
        
        admin_permission_names = [p.name for p in admin_role.permissions]
        expected_admin_perms = ["users:read", "users:write", "users:delete", "inventory:read", "inventory:write", "reports:read"]
        
        assert len(admin_permission_names) == 6
        for perm_name in expected_admin_perms:
            assert perm_name in admin_permission_names
    
    @pytest.mark.asyncio
    async def test_role_permission_removal(self, db_session: AsyncSession, sample_roles_and_permissions: Dict[str, Any]):
        """Test removing permissions from roles"""
        roles = sample_roles_and_permissions["roles"]
        
        # Get EDITOR role
        editor_role = next((r for r in roles if r.name == "EDITOR"), None)
        assert editor_role is not None
        
        # Remove a permission
        permission_to_remove = next((p for p in editor_role.permissions if p.name == "inventory:write"), None)
        assert permission_to_remove is not None
        
        editor_role.permissions.remove(permission_to_remove)
        await db_session.commit()
        await db_session.refresh(editor_role)
        
        # Verify permission was removed
        remaining_permission_names = [p.name for p in editor_role.permissions]
        assert "inventory:write" not in remaining_permission_names
        assert len(remaining_permission_names) == 4  # Was 5, now 4
    
    @pytest.mark.asyncio
    async def test_role_unique_name(self, db_session: AsyncSession, sample_roles_and_permissions: Dict[str, Any]):
        """Test that role names must be unique"""
        # Try to create role with existing name
        duplicate_role = Role(
            name="ADMIN",  # This already exists
            description="Duplicate admin role"
        )
        
        db_session.add(duplicate_role)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()


class TestUserRoleRelationships:
    """Test User-Role relationships and assignments"""
    
    @pytest_asyncio.fixture
    async def rbac_setup(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Setup complete RBAC structure for testing"""
        # Create permissions
        permissions_data = [
            {"name": "users:read", "resource": "users", "action": "read", "risk_level": "LOW"},
            {"name": "users:write", "resource": "users", "action": "write", "risk_level": "MEDIUM"},
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
        
        # Create roles with permissions
        staff_role = Role(name="STAFF", description="Staff role", is_system_role=True)
        manager_role = Role(name="MANAGER", description="Manager role", is_system_role=True)
        
        # Assign permissions to roles
        staff_perms = [p for p in permissions if p.name in ["users:read", "inventory:read"]]
        manager_perms = [p for p in permissions if p.name in ["users:read", "users:write", "inventory:read", "inventory:write"]]
        
        for perm in staff_perms:
            staff_role.permissions.append(perm)
        
        for perm in manager_perms:
            manager_role.permissions.append(perm)
        
        db_session.add(staff_role)
        db_session.add(manager_role)
        await db_session.commit()
        
        await db_session.refresh(staff_role)
        await db_session.refresh(manager_role)
        
        # Create users
        user_service = UserService(db_session)
        
        staff_user = await user_service.create({
            "username": "staff_user",
            "email": "staff@example.com", 
            "password": "StaffPassword123",
            "full_name": "Staff User",
            "user_type": "STAFF"
        })
        
        manager_user = await user_service.create({
            "username": "manager_user",
            "email": "manager@example.com",
            "password": "ManagerPassword123", 
            "full_name": "Manager User",
            "user_type": "MANAGER"
        })
        
        return {
            "permissions": permissions,
            "roles": {"staff": staff_role, "manager": manager_role},
            "users": {"staff": staff_user, "manager": manager_user}
        }
    
    @pytest.mark.asyncio
    async def test_user_role_assignment(self, db_session: AsyncSession, rbac_setup: Dict[str, Any]):
        """Test assigning roles to users"""
        role_service = UserRoleService(db_session)
        users = rbac_setup["users"]
        roles = rbac_setup["roles"]
        
        # Assign staff role to staff user
        assignment = await role_service.assign_role(users["staff"].id, roles["staff"].id)
        assert assignment["assigned"] is True
        assert assignment["user_id"] == users["staff"].id
        assert assignment["role_id"] == roles["staff"].id
        
        # Assign manager role to manager user
        assignment = await role_service.assign_role(users["manager"].id, roles["manager"].id)
        assert assignment["assigned"] is True
    
    @pytest.mark.asyncio
    async def test_user_role_removal(self, db_session: AsyncSession, rbac_setup: Dict[str, Any]):
        """Test removing roles from users"""
        role_service = UserRoleService(db_session)
        users = rbac_setup["users"] 
        roles = rbac_setup["roles"]
        
        # First assign a role
        await role_service.assign_role(users["staff"].id, roles["staff"].id)
        
        # Then remove it
        result = await role_service.remove_role(users["staff"].id, roles["staff"].id)
        assert result is True
        
        # Verify it's removed
        assignment = await role_service.get_user_role_assignment(users["staff"].id, roles["staff"].id)
        assert assignment is None
    
    @pytest.mark.asyncio
    async def test_duplicate_role_assignment(self, db_session: AsyncSession, rbac_setup: Dict[str, Any]):
        """Test that duplicate role assignments are prevented"""
        role_service = UserRoleService(db_session)
        users = rbac_setup["users"]
        roles = rbac_setup["roles"]
        
        # Assign role first time
        await role_service.assign_role(users["staff"].id, roles["staff"].id)
        
        # Try to assign same role again
        with pytest.raises(AlreadyExistsError):
            await role_service.assign_role(users["staff"].id, roles["staff"].id)
    
    @pytest.mark.asyncio
    async def test_get_user_roles(self, db_session: AsyncSession, rbac_setup: Dict[str, Any]):
        """Test getting all roles for a user"""
        role_service = UserRoleService(db_session)
        users = rbac_setup["users"]
        roles = rbac_setup["roles"]
        
        # Assign multiple roles to user
        await role_service.assign_role(users["manager"].id, roles["staff"].id)
        await role_service.assign_role(users["manager"].id, roles["manager"].id)
        
        # Get user roles
        user_roles = await role_service.get_user_roles(users["manager"].id)
        
        assert len(user_roles) == 2
        role_names = [role.name for role in user_roles]
        assert "STAFF" in role_names
        assert "MANAGER" in role_names
    
    @pytest.mark.asyncio
    async def test_get_user_permissions(self, db_session: AsyncSession, rbac_setup: Dict[str, Any]):
        """Test getting all permissions for a user through roles"""
        role_service = UserRoleService(db_session)
        users = rbac_setup["users"]
        roles = rbac_setup["roles"]
        
        # Assign manager role to user
        await role_service.assign_role(users["manager"].id, roles["manager"].id)
        
        # Get user permissions
        user_permissions = await role_service.get_user_permissions(users["manager"].id)
        
        expected_permissions = ["users:read", "users:write", "inventory:read", "inventory:write"]
        assert len(user_permissions) == 4
        for perm in expected_permissions:
            assert perm in user_permissions
    
    @pytest.mark.asyncio
    async def test_user_has_permission(self, db_session: AsyncSession, rbac_setup: Dict[str, Any]):
        """Test checking if user has specific permission"""
        role_service = UserRoleService(db_session)
        users = rbac_setup["users"]
        roles = rbac_setup["roles"]
        
        # Assign staff role (limited permissions)
        await role_service.assign_role(users["staff"].id, roles["staff"].id)
        
        # Check permissions
        assert await role_service.user_has_permission(users["staff"].id, "users:read") is True
        assert await role_service.user_has_permission(users["staff"].id, "inventory:read") is True
        assert await role_service.user_has_permission(users["staff"].id, "users:write") is False
        assert await role_service.user_has_permission(users["staff"].id, "inventory:write") is False


class TestUserRoleService:
    """Test UserRoleService operations"""
    
    @pytest.mark.asyncio
    async def test_create_role_with_permissions(self, db_session: AsyncSession):
        """Test creating a role with permissions using service"""
        # First create some permissions
        permissions_data = [
            {"name": "test:read", "resource": "test", "action": "read", "risk_level": "LOW"},
            {"name": "test:write", "resource": "test", "action": "write", "risk_level": "MEDIUM"},
        ]
        
        for perm_data in permissions_data:
            permission = Permission(**perm_data)
            db_session.add(permission)
        
        await db_session.commit()
        
        # Create role with permissions using service
        role_service = UserRoleService(db_session)
        
        role_data = {
            "name": "TEST_ROLE",
            "description": "Test role created by service",
            "permissions": ["test:read", "test:write"]
        }
        
        role = await role_service.create_role(role_data)
        
        assert role.name == "TEST_ROLE"
        assert role.description == "Test role created by service"
        assert len(role.permissions) == 2
        
        permission_names = [p.name for p in role.permissions]
        assert "test:read" in permission_names
        assert "test:write" in permission_names
    
    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(self, db_session: AsyncSession):
        """Test creating role with duplicate name fails"""
        role_service = UserRoleService(db_session)
        
        # Create first role
        role_data = {
            "name": "DUPLICATE_ROLE",
            "description": "First role"
        }
        
        await role_service.create_role(role_data)
        
        # Try to create second role with same name
        duplicate_role_data = {
            "name": "DUPLICATE_ROLE",
            "description": "Second role"
        }
        
        with pytest.raises(AlreadyExistsError):
            await role_service.create_role(duplicate_role_data)
    
    @pytest.mark.asyncio
    async def test_get_role_by_name(self, db_session: AsyncSession):
        """Test getting role by name"""
        role_service = UserRoleService(db_session)
        
        # Create a role
        role_data = {
            "name": "FINDABLE_ROLE",
            "description": "Role that can be found"
        }
        
        created_role = await role_service.create_role(role_data)
        
        # Find role by name
        found_role = await role_service.get_role_by_name("FINDABLE_ROLE")
        
        assert found_role is not None
        assert found_role.id == created_role.id
        assert found_role.name == "FINDABLE_ROLE"
        
        # Try to find non-existent role
        not_found_role = await role_service.get_role_by_name("NON_EXISTENT_ROLE")
        assert not_found_role is None


class TestRBACIntegration:
    """Test RBAC integration with authentication and authorization"""
    
    @pytest_asyncio.fixture
    async def auth_rbac_setup(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Setup authentication and RBAC for integration testing"""
        # Create permissions
        permissions = []
        permission_names = ["users:read", "users:write", "inventory:read", "inventory:write", "admin:all"]
        
        for perm_name in permission_names:
            resource, action = perm_name.split(":")
            permission = Permission(
                name=perm_name,
                resource=resource,
                action=action,
                risk_level="MEDIUM" if action == "write" else "LOW"
            )
            db_session.add(permission)
            permissions.append(permission)
        
        await db_session.commit()
        for perm in permissions:
            await db_session.refresh(perm)
        
        # Create roles
        user_role = Role(name="USER", description="Regular user")
        admin_role = Role(name="ADMIN", description="Administrator")
        
        # Assign permissions
        user_perms = [p for p in permissions if p.name in ["users:read", "inventory:read"]]
        admin_perms = permissions  # Admin gets all permissions
        
        for perm in user_perms:
            user_role.permissions.append(perm)
        
        for perm in admin_perms:
            admin_role.permissions.append(perm)
        
        db_session.add(user_role)
        db_session.add(admin_role)
        await db_session.commit()
        
        await db_session.refresh(user_role)
        await db_session.refresh(admin_role)
        
        # Create users with roles
        user_service = UserService(db_session)
        role_service = UserRoleService(db_session)
        
        regular_user = await user_service.create({
            "username": "regular_user",
            "email": "user@example.com",
            "password": "UserPassword123",
            "full_name": "Regular User"
        })
        
        admin_user = await user_service.create({
            "username": "admin_user", 
            "email": "admin@example.com",
            "password": "AdminPassword123",
            "full_name": "Admin User",
            "is_superuser": True
        })
        
        # Assign roles
        await role_service.assign_role(regular_user.id, user_role.id)
        await role_service.assign_role(admin_user.id, admin_role.id)
        
        return {
            "permissions": permissions,
            "roles": {"user": user_role, "admin": admin_role},
            "users": {"regular": regular_user, "admin": admin_user}
        }
    
    @pytest.mark.asyncio
    async def test_login_includes_permissions(self, db_session: AsyncSession, auth_rbac_setup: Dict[str, Any]):
        """Test that login response includes user permissions"""
        auth_service = AuthService(db_session)
        users = auth_rbac_setup["users"]
        
        # Test regular user login
        login_data = {
            "username": "user@example.com",
            "password": "UserPassword123"
        }
        
        auth_response = await auth_service.login(login_data, "127.0.0.1", "test-agent")
        
        assert "access_token" in auth_response
        assert "user" in auth_response
        assert "effectivePermissions" in auth_response["user"]
        
        user_permissions = auth_response["user"]["effectivePermissions"]
        expected_user_permissions = ["users:read", "inventory:read"]
        
        assert len(user_permissions) == 2
        for perm in expected_user_permissions:
            assert perm in user_permissions
        
        # Test admin user login
        admin_login_data = {
            "username": "admin@example.com", 
            "password": "AdminPassword123"
        }
        
        admin_auth_response = await auth_service.login(admin_login_data, "127.0.0.1", "test-agent")
        
        admin_permissions = admin_auth_response["user"]["effectivePermissions"]
        expected_admin_permissions = ["users:read", "users:write", "inventory:read", "inventory:write", "admin:all"]
        
        assert len(admin_permissions) == 5
        for perm in expected_admin_permissions:
            assert perm in admin_permissions
    
    @pytest.mark.asyncio
    async def test_jwt_token_contains_permissions(self, db_session: AsyncSession, auth_rbac_setup: Dict[str, Any]):
        """Test that JWT tokens contain user permissions"""
        auth_service = AuthService(db_session)
        
        # Login and get token
        login_data = {
            "username": "user@example.com",
            "password": "UserPassword123"
        }
        
        auth_response = await auth_service.login(login_data, "127.0.0.1", "test-agent")
        access_token = auth_response["access_token"]
        
        # Decode token and check permissions  
        token_data = decode_token_for_test(access_token)
        
        assert "permissions" in token_data
        token_permissions = token_data["permissions"]
        expected_permissions = ["users:read", "inventory:read"]
        
        assert len(token_permissions) == 2
        for perm in expected_permissions:
            assert perm in token_permissions


class TestRBACEdgeCases:
    """Test edge cases and error handling in RBAC system"""
    
    @pytest.mark.asyncio
    async def test_user_without_roles(self, db_session: AsyncSession):
        """Test user with no roles assigned"""
        user_service = UserService(db_session)
        role_service = UserRoleService(db_session)
        
        # Create user without any roles
        user = await user_service.create({
            "username": "no_roles_user",
            "email": "noroles@example.com",
            "password": "Password123",
            "full_name": "No Roles User"
        })
        
        # Check user permissions
        permissions = await role_service.get_user_permissions(user.id)
        assert len(permissions) == 0
        
        # Check specific permission
        has_permission = await role_service.user_has_permission(user.id, "users:read")
        assert has_permission is False
    
    @pytest.mark.asyncio
    async def test_role_without_permissions(self, db_session: AsyncSession):
        """Test role with no permissions assigned"""
        role_service = UserRoleService(db_session)
        user_service = UserService(db_session)
        
        # Create role without permissions
        role_data = {
            "name": "EMPTY_ROLE",
            "description": "Role with no permissions"
        }
        
        empty_role = await role_service.create_role(role_data)
        assert len(empty_role.permissions) == 0
        
        # Create user and assign empty role
        user = await user_service.create({
            "username": "empty_role_user",
            "email": "emptyrole@example.com", 
            "password": "Password123",
            "full_name": "Empty Role User"
        })
        
        await role_service.assign_role(user.id, empty_role.id)
        
        # Check user permissions
        permissions = await role_service.get_user_permissions(user.id)
        assert len(permissions) == 0
    
    @pytest.mark.asyncio
    async def test_inactive_role(self, db_session: AsyncSession):
        """Test behavior with inactive roles"""
        # Create permission
        permission = Permission(
            name="test:action",
            resource="test",
            action="action",
            risk_level="LOW"
        )
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)
        
        # Create inactive role
        inactive_role = Role(
            name="INACTIVE_ROLE",
            description="Inactive role",
            is_active=False
        )
        inactive_role.permissions.append(permission)
        db_session.add(inactive_role)
        await db_session.commit()
        await db_session.refresh(inactive_role)
        
        # Create user and assign inactive role
        user_service = UserService(db_session)
        role_service = UserRoleService(db_session)
        
        user = await user_service.create({
            "username": "inactive_role_user",
            "email": "inactive@example.com",
            "password": "Password123", 
            "full_name": "Inactive Role User"
        })
        
        await role_service.assign_role(user.id, inactive_role.id)
        
        # Check that inactive roles are filtered out
        user_roles = await role_service.get_user_roles(user.id)
        assert len(user_roles) == 0  # Should not include inactive roles
    
    @pytest.mark.asyncio
    async def test_nonexistent_user_role_assignment(self, db_session: AsyncSession):
        """Test assigning role to non-existent user"""
        role_service = UserRoleService(db_session)
        
        # Create a role
        role_data = {
            "name": "TEST_ROLE",
            "description": "Test role"
        }
        
        role = await role_service.create_role(role_data)
        
        # Try to assign role to non-existent user
        with pytest.raises(NotFoundError):
            await role_service.assign_role(99999, role.id)  # Non-existent user ID
    
    @pytest.mark.asyncio
    async def test_nonexistent_role_assignment(self, db_session: AsyncSession):
        """Test assigning non-existent role to user"""
        role_service = UserRoleService(db_session)
        user_service = UserService(db_session)
        
        # Create a user
        user = await user_service.create({
            "username": "test_user",
            "email": "test@example.com",
            "password": "Password123",
            "full_name": "Test User"
        })
        
        # Try to assign non-existent role
        with pytest.raises(NotFoundError):
            await role_service.assign_role(user.id, 99999)  # Non-existent role ID
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_role_assignment(self, db_session: AsyncSession):
        """Test removing role assignment that doesn't exist"""
        role_service = UserRoleService(db_session) 
        user_service = UserService(db_session)
        
        # Create user and role
        user = await user_service.create({
            "username": "test_user",
            "email": "test@example.com",
            "password": "Password123",
            "full_name": "Test User"
        })
        
        role_data = {
            "name": "TEST_ROLE",
            "description": "Test role"
        }
        
        role = await role_service.create_role(role_data)
        
        # Try to remove assignment that was never made
        with pytest.raises(NotFoundError):
            await role_service.remove_role(user.id, role.id)


class TestRBACPerformance:
    """Test RBAC system performance and optimization"""
    
    @pytest.mark.asyncio
    async def test_bulk_permission_checking(self, db_session: AsyncSession):
        """Test performance of checking multiple permissions"""
        # Create many permissions
        permissions = []
        for i in range(50):
            permission = Permission(
                name=f"test:action{i}",
                resource="test",
                action=f"action{i}",
                risk_level="LOW"
            )
            db_session.add(permission)
            permissions.append(permission)
        
        await db_session.commit()
        
        # Create role with all permissions
        role = Role(name="BULK_ROLE", description="Role with many permissions")
        for permission in permissions:
            role.permissions.append(permission)
        
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        # Create user and assign role
        user_service = UserService(db_session)
        role_service = UserRoleService(db_session)
        
        user = await user_service.create({
            "username": "bulk_user",
            "email": "bulk@example.com",
            "password": "Password123",
            "full_name": "Bulk User"
        })
        
        await role_service.assign_role(user.id, role.id)
        
        # Test getting all permissions (should be efficient)
        user_permissions = await role_service.get_user_permissions(user.id)
        assert len(user_permissions) == 50
        
        # Test checking multiple specific permissions
        for i in range(0, 10):  # Check first 10
            has_permission = await role_service.user_has_permission(user.id, f"test:action{i}")
            assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_user_with_multiple_roles(self, db_session: AsyncSession):
        """Test user with multiple roles and combined permissions"""
        # Create permissions
        permissions_data = [
            {"name": "read:docs", "resource": "docs", "action": "read"},
            {"name": "write:docs", "resource": "docs", "action": "write"},
            {"name": "read:files", "resource": "files", "action": "read"},
            {"name": "write:files", "resource": "files", "action": "write"},
            {"name": "admin:system", "resource": "system", "action": "admin"},
        ]
        
        permissions = []
        for perm_data in permissions_data:
            permission = Permission(**perm_data, risk_level="LOW")
            db_session.add(permission)
            permissions.append(permission)
        
        await db_session.commit()
        
        # Create multiple roles
        reader_role = Role(name="READER", description="Can read documents")
        writer_role = Role(name="WRITER", description="Can write documents")
        file_role = Role(name="FILE_MANAGER", description="Can manage files")
        
        # Assign permissions to roles
        reader_role.permissions.append(permissions[0])  # read:docs
        writer_role.permissions.extend([permissions[0], permissions[1]])  # read:docs, write:docs
        file_role.permissions.extend([permissions[2], permissions[3]])  # read:files, write:files
        
        db_session.add_all([reader_role, writer_role, file_role])
        await db_session.commit()
        
        for role in [reader_role, writer_role, file_role]:
            await db_session.refresh(role)
        
        # Create user and assign multiple roles
        user_service = UserService(db_session)
        role_service = UserRoleService(db_session)
        
        user = await user_service.create({
            "username": "multi_role_user",
            "email": "multirole@example.com",
            "password": "Password123",
            "full_name": "Multi Role User"
        })
        
        # Assign all three roles
        await role_service.assign_role(user.id, reader_role.id)
        await role_service.assign_role(user.id, writer_role.id)
        await role_service.assign_role(user.id, file_role.id)
        
        # Check combined permissions
        user_permissions = await role_service.get_user_permissions(user.id)
        
        # Should have unique permissions from all roles
        expected_permissions = {"read:docs", "write:docs", "read:files", "write:files"}
        assert len(user_permissions) == 4  # Should deduplicate read:docs
        assert set(user_permissions) == expected_permissions
        
        # Check specific permissions
        assert await role_service.user_has_permission(user.id, "read:docs") is True
        assert await role_service.user_has_permission(user.id, "write:docs") is True
        assert await role_service.user_has_permission(user.id, "read:files") is True
        assert await role_service.user_has_permission(user.id, "write:files") is True
        assert await role_service.user_has_permission(user.id, "admin:system") is False


# Test utilities and fixtures
@pytest.fixture
def rbac_test_data():
    """Sample RBAC test data"""
    return {
        "permissions": [
            {"name": "users:read", "resource": "users", "action": "read", "risk_level": "LOW"},
            {"name": "users:write", "resource": "users", "action": "write", "risk_level": "MEDIUM"},
            {"name": "users:delete", "resource": "users", "action": "delete", "risk_level": "HIGH"},
            {"name": "inventory:read", "resource": "inventory", "action": "read", "risk_level": "LOW"},
            {"name": "inventory:write", "resource": "inventory", "action": "write", "risk_level": "MEDIUM"},
            {"name": "reports:read", "resource": "reports", "action": "read", "risk_level": "LOW"},
            {"name": "admin:all", "resource": "admin", "action": "all", "risk_level": "CRITICAL"},
        ],
        "roles": [
            {
                "name": "VIEWER",
                "description": "Read-only access",
                "permissions": ["users:read", "inventory:read", "reports:read"]
            },
            {
                "name": "STAFF", 
                "description": "Staff level access",
                "permissions": ["users:read", "inventory:read", "inventory:write", "reports:read"]
            },
            {
                "name": "MANAGER",
                "description": "Manager level access", 
                "permissions": ["users:read", "users:write", "inventory:read", "inventory:write", "reports:read"]
            },
            {
                "name": "ADMIN",
                "description": "Full administrative access",
                "permissions": ["users:read", "users:write", "users:delete", "inventory:read", "inventory:write", "reports:read", "admin:all"]
            }
        ],
        "users": [
            {
                "username": "viewer_user",
                "email": "viewer@example.com", 
                "password": "ViewerPassword123",
                "full_name": "Viewer User",
                "roles": ["VIEWER"]
            },
            {
                "username": "staff_user", 
                "email": "staff@example.com",
                "password": "StaffPassword123", 
                "full_name": "Staff User",
                "roles": ["STAFF"]
            },
            {
                "username": "manager_user",
                "email": "manager@example.com",
                "password": "ManagerPassword123",
                "full_name": "Manager User", 
                "roles": ["MANAGER"]
            },
            {
                "username": "admin_user",
                "email": "admin@example.com",
                "password": "AdminPassword123",
                "full_name": "Admin User",
                "roles": ["ADMIN"]
            }
        ]
    }


class TestRBACUtils:
    """Utility functions for RBAC testing"""
    
    @staticmethod
    async def create_test_rbac_structure(db_session: AsyncSession, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete RBAC structure for testing"""
        # Create permissions
        permissions = {}
        for perm_data in test_data["permissions"]:
            permission = Permission(**perm_data)
            db_session.add(permission)
            permissions[perm_data["name"]] = permission
        
        await db_session.commit()
        for perm in permissions.values():
            await db_session.refresh(perm)
        
        # Create roles
        roles = {}
        for role_data in test_data["roles"]:
            role_perms = role_data.pop("permissions", [])
            role = Role(**role_data)
            
            # Add permissions to role
            for perm_name in role_perms:
                if perm_name in permissions:
                    role.permissions.append(permissions[perm_name])
            
            db_session.add(role)
            roles[role_data["name"]] = role
        
        await db_session.commit()
        for role in roles.values():
            await db_session.refresh(role)
        
        # Create users
        user_service = UserService(db_session)
        role_service = UserRoleService(db_session)
        users = {}
        
        for user_data in test_data["users"]:
            user_roles = user_data.pop("roles", [])
            user = await user_service.create(user_data)
            users[user_data["username"]] = user
            
            # Assign roles to user
            for role_name in user_roles:
                if role_name in roles:
                    await role_service.assign_role(user.id, roles[role_name].id)
        
        return {
            "permissions": permissions,
            "roles": roles, 
            "users": users
        }
    
    @staticmethod
    def assert_permissions_match(actual_permissions: List[str], expected_permissions: List[str]):
        """Assert that permission lists match"""
        assert len(actual_permissions) == len(expected_permissions)
        assert set(actual_permissions) == set(expected_permissions)
    
    @staticmethod
    def assert_user_has_permissions(user_permissions: List[str], required_permissions: List[str]):
        """Assert that user has all required permissions"""
        for permission in required_permissions:
            assert permission in user_permissions, f"User missing required permission: {permission}"
    
    @staticmethod 
    def assert_user_lacks_permissions(user_permissions: List[str], forbidden_permissions: List[str]):
        """Assert that user does not have forbidden permissions"""
        for permission in forbidden_permissions:
            assert permission not in user_permissions, f"User has forbidden permission: {permission}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])