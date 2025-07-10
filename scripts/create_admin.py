#!/usr/bin/env python3
"""
Admin User Creation Script

This script creates a default admin user for the FastAPI application.
It runs during container startup to ensure an admin account exists.
"""

import asyncio
import sys
import os
import logging
from typing import Optional

# Add app directory to Python path
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, engine
from app.core.security import get_password_hash
# Import all models to ensure relationships are properly initialized
from app.modules.users.models import User, UserProfile, UserRole, UserRoleAssignment
from app.modules.auth.models import RefreshToken, LoginAttempt, PasswordResetToken
from app.modules.users.services import UserService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Admin user configuration from environment variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@admin.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin@123')
ADMIN_FULL_NAME = os.getenv('ADMIN_FULL_NAME', 'System Administrator')


async def check_database_connection() -> bool:
    """Check if database is accessible"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def admin_user_exists(session: AsyncSession) -> bool:
    """Check if admin user already exists"""
    try:
        user_service = UserService(session)
        admin_user = await user_service.get_by_username(ADMIN_USERNAME)
        return admin_user is not None
    except Exception as e:
        logger.error(f"Error checking for admin user: {e}")
        # If there's an error (like table doesn't exist), assume user doesn't exist
        return False


async def create_admin_user(session: AsyncSession) -> bool:
    """Create the admin user"""
    try:
        user_service = UserService(session)
        
        admin_data = {
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,  # UserService.create will hash this
            "full_name": ADMIN_FULL_NAME,
            "is_active": True,
            "is_superuser": True,
            "is_verified": True
        }
        
        admin_user = await user_service.create(admin_data)
        logger.info(f"Admin user created successfully with ID: {admin_user.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        return False


async def main():
    """Main function to create admin user"""
    logger.info("Starting admin user creation script...")
    
    # Check database connection
    if not await check_database_connection():
        logger.error("Cannot connect to database. Exiting.")
        sys.exit(1)
    
    try:
        async with AsyncSessionLocal() as session:
            # Check if admin user already exists
            user_exists = await admin_user_exists(session)
            if user_exists:
                logger.info(f"Admin user with username '{ADMIN_USERNAME}' already exists. Skipping creation.")
                sys.exit(0)
            
            # Create admin user
            if await create_admin_user(session):
                logger.info("Admin user creation completed successfully")
                sys.exit(0)
            else:
                logger.error("Admin user creation failed")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Unexpected error during admin user creation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())