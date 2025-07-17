#!/usr/bin/env python3
"""
System Settings Initialization Script

This script initializes default system settings for the rental management system.
It can be run manually to ensure all required system settings exist.

Usage:
    python scripts/init_system_settings.py

Requirements:
    - PostgreSQL database must be running
    - Environment variables must be configured
    - Database must be initialized (tables created)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.modules.system.service import SystemService


async def init_system_settings():
    """Initialize system settings."""
    print("Starting system settings initialization...")
    
    try:
        # Create database engine
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,  # Set to True for SQL debugging
            future=True
        )
        
        # Create session maker
        async_session = sessionmaker(
            engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Initialize settings
        async with async_session() as session:
            system_service = SystemService(session)
            
            print("Initializing default system settings...")
            initialized_settings = await system_service.initialize_default_settings()
            
            if initialized_settings:
                print(f"✓ Successfully initialized {len(initialized_settings)} system settings:")
                for setting in initialized_settings:
                    print(f"  - {setting.setting_key}: {setting.setting_name}")
            else:
                print("✓ All system settings already exist - no initialization needed")
            
            # Verify company settings specifically
            print("\nVerifying company settings...")
            company_settings = [
                "company_name",
                "company_address", 
                "company_email",
                "company_phone",
                "company_gst_no",
                "company_registration_number"
            ]
            
            missing_settings = []
            for setting_key in company_settings:
                setting = await system_service.get_setting(setting_key)
                if setting:
                    print(f"  ✓ {setting_key}: {setting.setting_value or '[empty]'}")
                else:
                    missing_settings.append(setting_key)
                    print(f"  ✗ {setting_key}: MISSING")
            
            if missing_settings:
                print(f"\n⚠️  WARNING: {len(missing_settings)} company settings are missing!")
                print("This may cause issues with the company settings page.")
                print("Missing settings:", ", ".join(missing_settings))
                return False
            else:
                print("\n✓ All company settings are properly initialized")
                return True
                
    except Exception as e:
        print(f"❌ Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            await engine.dispose()
        except:
            pass


def main():
    """Main entry point."""
    print("System Settings Initialization Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("❌ Error: This script must be run from the project root directory")
        print("Usage: python scripts/init_system_settings.py")
        sys.exit(1)
    
    # Check environment
    try:
        database_url = settings.DATABASE_URL
        if not database_url:
            print("❌ Error: DATABASE_URL not configured")
            sys.exit(1)
        print(f"Database URL: {database_url.split('@')[-1]}")  # Hide credentials
    except Exception as e:
        print(f"❌ Error: Failed to load configuration: {str(e)}")
        sys.exit(1)
    
    # Run initialization
    success = asyncio.run(init_system_settings())
    
    if success:
        print("\n🎉 System settings initialization completed successfully!")
        print("The company settings page should now work properly.")
    else:
        print("\n❌ System settings initialization failed!")
        print("Please check the errors above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()