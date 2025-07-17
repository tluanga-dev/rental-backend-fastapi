#!/usr/bin/env python3
"""
API Endpoint Test for Company Settings

Tests the API functionality directly without browser automation.
"""

import asyncio
import aiohttp
import json
import uuid

async def test_company_api():
    """Test company API endpoints."""
    print("🔗 Testing Company API Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Health check
            print("1. 🏥 Testing backend health...")
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"   ✅ Backend healthy: {health_data}")
                else:
                    print(f"   ❌ Backend unhealthy: {response.status}")
                    return False

            # Test 2: Initialize settings
            print("2. ⚙️  Initializing system settings...")
            async with session.post(f"{base_url}/api/system/settings/initialize") as response:
                if response.status in [200, 201]:
                    settings_data = await response.json()
                    print(f"   ✅ Settings initialized: {len(settings_data)} settings created")
                else:
                    print(f"   ⚠️  Settings initialization: {response.status}")
                    # Continue anyway, settings might already exist

            # Test 3: Get company info
            print("3. 📋 Getting company information...")
            async with session.get(f"{base_url}/api/system/company") as response:
                if response.status == 200:
                    company_data = await response.json()
                    print(f"   ✅ Company info retrieved:")
                    for key, value in company_data.items():
                        print(f"      {key}: {value or '[empty]'}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed to get company info: {response.status}")
                    print(f"      Error: {error_text}")
                    return False

            # Test 4: Update company info
            print("4. 💾 Updating company information...")
            test_data = {
                "company_name": "Puppeteer Test Company",
                "company_address": "123 Automation Street\nTest City, TC 12345",
                "company_email": "test@automation.com",
                "company_phone": "+1-555-TEST-001",
                "company_gst_no": "GST999888777",
                "company_registration_number": "REG555444333"
            }
            
            test_user_id = str(uuid.uuid4())
            async with session.put(
                f"{base_url}/api/system/company?updated_by={test_user_id}",
                json=test_data
            ) as response:
                if response.status == 200:
                    updated_data = await response.json()
                    print(f"   ✅ Company info updated successfully:")
                    for key, value in updated_data.items():
                        print(f"      {key}: {value}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed to update company info: {response.status}")
                    print(f"      Error: {error_text}")
                    return False

            # Test 5: Verify persistence
            print("5. 🔄 Verifying data persistence...")
            async with session.get(f"{base_url}/api/system/company") as response:
                if response.status == 200:
                    persisted_data = await response.json()
                    
                    # Check if the data was actually saved
                    success = True
                    for key, expected_value in test_data.items():
                        actual_value = persisted_data.get(key, '')
                        if actual_value == expected_value:
                            print(f"   ✅ {key}: Persisted correctly")
                        else:
                            print(f"   ❌ {key}: Expected '{expected_value}', got '{actual_value}'")
                            success = False
                    
                    if success:
                        print("   🎉 All data persisted correctly!")
                        return True
                    else:
                        print("   ⚠️  Some data was not persisted correctly")
                        return False
                else:
                    print(f"   ❌ Failed to verify persistence: {response.status}")
                    return False

        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}")
            print("Make sure the backend server is running on http://localhost:8000")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

async def main():
    """Main test function."""
    print("🧪 COMPANY SETTINGS API TEST")
    print("=" * 50)
    
    success = await test_company_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL API TESTS PASSED!")
        print("✅ Company settings API is working correctly")
        print("\n📋 Next Steps:")
        print("1. The backend API is confirmed working")
        print("2. You can now test the frontend at:")
        print("   http://localhost:3000/settings/company")
        print("3. The form should load and save data successfully")
    else:
        print("❌ API TESTS FAILED!")
        print("Please check the backend server and try again")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)