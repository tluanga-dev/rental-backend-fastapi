"""
Seed RBAC data - roles, permissions, and demo users
"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.core.security import get_password_hash
from app.modules.auth.models import Role, Permission, UserType
from app.modules.users.models import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload


# Define core permissions
CORE_PERMISSIONS = [
    # User Management
    {"name": "USER_VIEW", "resource": "users", "action": "view", "description": "View users"},
    {"name": "USER_CREATE", "resource": "users", "action": "create", "description": "Create users"},
    {"name": "USER_UPDATE", "resource": "users", "action": "update", "description": "Update users"},
    {"name": "USER_DELETE", "resource": "users", "action": "delete", "description": "Delete users"},
    
    # Role Management
    {"name": "ROLE_VIEW", "resource": "roles", "action": "view", "description": "View roles"},
    {"name": "ROLE_CREATE", "resource": "roles", "action": "create", "description": "Create roles"},
    {"name": "ROLE_UPDATE", "resource": "roles", "action": "update", "description": "Update roles"},
    {"name": "ROLE_DELETE", "resource": "roles", "action": "delete", "description": "Delete roles"},
    
    # Customer Management
    {"name": "CUSTOMER_VIEW", "resource": "customers", "action": "view", "description": "View customers"},
    {"name": "CUSTOMER_CREATE", "resource": "customers", "action": "create", "description": "Create customers"},
    {"name": "CUSTOMER_UPDATE", "resource": "customers", "action": "update", "description": "Update customers"},
    {"name": "CUSTOMER_DELETE", "resource": "customers", "action": "delete", "description": "Delete customers"},
    
    # Supplier Management
    {"name": "SUPPLIER_VIEW", "resource": "suppliers", "action": "view", "description": "View suppliers"},
    {"name": "SUPPLIER_CREATE", "resource": "suppliers", "action": "create", "description": "Create suppliers"},
    {"name": "SUPPLIER_UPDATE", "resource": "suppliers", "action": "update", "description": "Update suppliers"},
    {"name": "SUPPLIER_DELETE", "resource": "suppliers", "action": "delete", "description": "Delete suppliers"},
    
    # Inventory Management
    {"name": "INVENTORY_VIEW", "resource": "inventory", "action": "view", "description": "View inventory"},
    {"name": "INVENTORY_CREATE", "resource": "inventory", "action": "create", "description": "Create inventory items"},
    {"name": "INVENTORY_UPDATE", "resource": "inventory", "action": "update", "description": "Update inventory"},
    {"name": "INVENTORY_DELETE", "resource": "inventory", "action": "delete", "description": "Delete inventory"},
    
    # Rental Management
    {"name": "RENTAL_VIEW", "resource": "rentals", "action": "view", "description": "View rentals"},
    {"name": "RENTAL_CREATE", "resource": "rentals", "action": "create", "description": "Create rentals"},
    {"name": "RENTAL_UPDATE", "resource": "rentals", "action": "update", "description": "Update rentals"},
    {"name": "RENTAL_DELETE", "resource": "rentals", "action": "delete", "description": "Delete rentals"},
    
    # Transaction Management
    {"name": "TRANSACTION_VIEW", "resource": "transactions", "action": "view", "description": "View transactions"},
    {"name": "TRANSACTION_CREATE", "resource": "transactions", "action": "create", "description": "Create transactions"},
    {"name": "TRANSACTION_UPDATE", "resource": "transactions", "action": "update", "description": "Update transactions"},
    {"name": "TRANSACTION_DELETE", "resource": "transactions", "action": "delete", "description": "Delete transactions"},
    
    # Master Data Management
    {"name": "MASTER_DATA_VIEW", "resource": "master_data", "action": "view", "description": "View master data"},
    {"name": "MASTER_DATA_CREATE", "resource": "master_data", "action": "create", "description": "Create master data"},
    {"name": "MASTER_DATA_UPDATE", "resource": "master_data", "action": "update", "description": "Update master data"},
    {"name": "MASTER_DATA_DELETE", "resource": "master_data", "action": "delete", "description": "Delete master data"},
    
    # Analytics & Reporting
    {"name": "ANALYTICS_VIEW", "resource": "analytics", "action": "view", "description": "View analytics"},
    {"name": "REPORT_VIEW", "resource": "reports", "action": "view", "description": "View reports"},
    {"name": "REPORT_CREATE", "resource": "reports", "action": "create", "description": "Create reports"},
    
    # System Administration
    {"name": "SYSTEM_CONFIG", "resource": "system", "action": "config", "description": "Configure system settings"},
    {"name": "AUDIT_VIEW", "resource": "audit", "action": "view", "description": "View audit logs"},
    {"name": "BACKUP_MANAGE", "resource": "backup", "action": "manage", "description": "Manage backups"},
]

# Define roles with their permissions
ROLES_CONFIG = {
    "ADMIN": {
        "description": "Full system administrator",
        "permissions": [p["name"] for p in CORE_PERMISSIONS],  # All permissions
        "is_system_role": True
    },
    "MANAGER": {
        "description": "Operations manager",
        "permissions": [
            "USER_VIEW", "USER_CREATE", "USER_UPDATE",
            "CUSTOMER_VIEW", "CUSTOMER_CREATE", "CUSTOMER_UPDATE", "CUSTOMER_DELETE",
            "SUPPLIER_VIEW", "SUPPLIER_CREATE", "SUPPLIER_UPDATE", "SUPPLIER_DELETE",
            "INVENTORY_VIEW", "INVENTORY_CREATE", "INVENTORY_UPDATE", "INVENTORY_DELETE",
            "RENTAL_VIEW", "RENTAL_CREATE", "RENTAL_UPDATE", "RENTAL_DELETE",
            "TRANSACTION_VIEW", "TRANSACTION_CREATE", "TRANSACTION_UPDATE",
            "MASTER_DATA_VIEW", "MASTER_DATA_CREATE", "MASTER_DATA_UPDATE",
            "ANALYTICS_VIEW", "REPORT_VIEW", "REPORT_CREATE",
        ],
        "is_system_role": True
    },
    "STAFF": {
        "description": "Regular staff member",
        "permissions": [
            "CUSTOMER_VIEW", "CUSTOMER_CREATE", "CUSTOMER_UPDATE",
            "SUPPLIER_VIEW",
            "INVENTORY_VIEW", "INVENTORY_UPDATE",
            "RENTAL_VIEW", "RENTAL_CREATE", "RENTAL_UPDATE",
            "TRANSACTION_VIEW", "TRANSACTION_CREATE",
            "MASTER_DATA_VIEW",
            "ANALYTICS_VIEW", "REPORT_VIEW",
        ],
        "is_system_role": True
    },
    "CUSTOMER": {
        "description": "Customer role",
        "permissions": [
            "RENTAL_VIEW",  # Can view their own rentals
            "CUSTOMER_VIEW"  # Can view their own profile
        ],
        "is_system_role": True
    }
}

# Demo users configuration
DEMO_USERS = [
    {
        "username": "admin",
        "email": "admin@admin.com",
        "password": "Admin@123",
        "full_name": "System Administrator",
        "first_name": "System",
        "last_name": "Administrator",
        "user_type": UserType.ADMIN,
        "is_superuser": True,
        "roles": ["ADMIN"]
    },
    {
        "username": "manager",
        "email": "manager@manager.com",
        "password": "Manager@123",
        "full_name": "Operations Manager",
        "first_name": "Operations",
        "last_name": "Manager",
        "user_type": UserType.MANAGER,
        "is_superuser": False,
        "roles": ["MANAGER"]
    },
    {
        "username": "staff",
        "email": "staff@staff.com",
        "password": "Staff@123",
        "full_name": "Staff Member",
        "first_name": "Staff",
        "last_name": "Member",
        "user_type": UserType.USER,
        "is_superuser": False,
        "roles": ["STAFF"]
    }
]


async def seed_permissions(db):
    """Seed permissions into the database"""
    print("Seeding permissions...")
    
    permissions_created = 0
    for perm_data in CORE_PERMISSIONS:
        # Check if permission already exists
        stmt = select(Permission).where(Permission.name == perm_data["name"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            permission = Permission(
                name=perm_data["name"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                description=perm_data["description"],
                is_system_permission=True
            )
            db.add(permission)
            permissions_created += 1
    
    await db.commit()
    print(f"Created {permissions_created} permissions")


async def seed_roles(db):
    """Seed roles into the database"""
    print("Seeding roles...")
    
    # Get all permissions for mapping
    stmt = select(Permission)
    result = await db.execute(stmt)
    permissions = {p.name: p for p in result.scalars().all()}
    
    roles_created = 0
    for role_name, role_config in ROLES_CONFIG.items():
        # Check if role already exists
        stmt = select(Role).where(Role.name == role_name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            role = Role(
                name=role_name,
                description=role_config["description"],
                is_system_role=role_config["is_system_role"]
            )
            
            # Add permissions to role
            for perm_name in role_config["permissions"]:
                if perm_name in permissions:
                    role.permissions.append(permissions[perm_name])
            
            db.add(role)
            roles_created += 1
    
    await db.commit()
    print(f"Created {roles_created} roles")


async def seed_demo_users(db):
    """Seed demo users into the database"""
    print("Seeding demo users...")
    
    # Get all roles for mapping
    stmt = select(Role).options(selectinload(Role.permissions))
    result = await db.execute(stmt)
    roles = {r.name: r for r in result.scalars().all()}
    
    users_created = 0
    for user_data in DEMO_USERS:
        # Check if user already exists
        stmt = select(User).where(User.username == user_data["username"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                user_type=user_data["user_type"].value,
                is_superuser=user_data["is_superuser"],
                is_active=True,
                is_verified=True
            )
            
            # Add roles to user
            for role_name in user_data["roles"]:
                if role_name in roles:
                    user.roles.append(roles[role_name])
            
            db.add(user)
            users_created += 1
    
    await db.commit()
    print(f"Created {users_created} demo users")


async def main():
    """Main seeding function"""
    print("Starting RBAC seeding...")
    
    # Get database session
    async for db in get_db():
        try:
            # Seed in order: permissions -> roles -> users
            await seed_permissions(db)
            await seed_roles(db)
            await seed_demo_users(db)
            
            print("\n✅ RBAC seeding completed successfully!")
            print("\nDemo users created:")
            for user in DEMO_USERS:
                print(f"  - {user['username']}: {user['password']}")
            
        except Exception as e:
            print(f"❌ Error seeding RBAC data: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(main())