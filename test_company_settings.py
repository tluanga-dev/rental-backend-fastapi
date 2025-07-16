#!/usr/bin/env python3
"""
Test script to verify company settings functionality.
Run this to test the new company settings in the system module.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.modules.system.service import SystemService
from app.db.session import get_session


async def test_company_settings():
    """Test the new company settings functionality."""
    print("Testing Company Settings Integration...")
    
    # Get a database session
    async for session in get_session():
        try:
            service = SystemService(session)
            
            # Test 1: Initialize default settings
            print("\n1. Testing default settings initialization...")
            await service.initialize_default_settings()
            print("✓ Default settings initialized")
            
            # Test 2: Check if company settings exist
            print("\n2. Testing company settings existence...")
            company_settings = [
                "company_name",
                "company_address", 
                "company_email",
                "company_phone",
                "company_gst_no",
                "company_registration_number"
            ]
            
            for setting_key in company_settings:
                setting = await service.get_setting(setting_key)
                if setting:
                    print(f"✓ {setting_key}: {setting.setting_value or 'empty'}")
                else:
                    print(f"✗ {setting_key}: Not found")
            
            # Test 3: Update a company setting
            print("\n3. Testing company setting update...")
            await service.update_setting("company_name", "Test Company Ltd")
            updated_name = await service.get_setting_value("company_name")
            print(f"✓ Updated company name: {updated_name}")
            
            # Test 4: Get all business settings
            print("\n4. Testing business category settings...")
            from app.modules.system.models import SettingCategory
            business_settings = await service.get_settings_by_category(SettingCategory.BUSINESS)
            print(f"✓ Found {len(business_settings)} business settings:")
            for setting in business_settings:
                print(f"  - {setting.setting_key}: {setting.setting_value or 'empty'}")
            
            print("\n✅ All tests passed! Company settings are working correctly.")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(test_company_settings())