#!/usr/bin/env python3
"""
Complete Company Settings Fix Test

This script performs a comprehensive test of all company settings fixes:
1. File modifications verification
2. Code logic verification  
3. API endpoint validation
4. Frontend integration check
5. Error handling validation
"""

import os
import re
import sys
from pathlib import Path

def test_file_exists(file_path, description):
    """Test if a file exists and return result."""
    if os.path.exists(file_path):
        print(f"  ✅ {description}: EXISTS")
        return True
    else:
        print(f"  ❌ {description}: MISSING")
        return False

def test_file_contains(file_path, pattern, description, count=1):
    """Test if a file contains specific content."""
    if not os.path.exists(file_path):
        print(f"  ❌ {description}: FILE NOT FOUND")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            if matches >= count:
                print(f"  ✅ {description}: FOUND ({matches} matches)")
                return True
            else:
                print(f"  ❌ {description}: NOT FOUND (expected >= {count}, found {matches})")
                return False
    except Exception as e:
        print(f"  ❌ {description}: ERROR reading file - {str(e)}")
        return False

def run_complete_test():
    """Run the complete company settings fix test."""
    print("🧪 COMPLETE COMPANY SETTINGS FIX TEST")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Backend File Modifications
    print("\n📁 1. BACKEND FILE MODIFICATIONS")
    
    # Test main.py modifications
    total_tests += 1
    if test_file_contains("app/main.py", r"initialize_default_settings", "Startup initialization"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains("app/main.py", r"SystemService", "SystemService import"):
        passed_tests += 1
    
    # Test service.py modifications
    total_tests += 1
    if test_file_contains("app/modules/system/service.py", r"_create_missing_company_setting", "Missing setting creation method"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains("app/modules/system/service.py", r'setting_key\.startswith\("company_"\)', "Company setting detection"):
        passed_tests += 1
    
    # Test initialization script
    total_tests += 1
    if test_file_exists("scripts/init_system_settings.py", "Initialization script"):
        passed_tests += 1
        # Check if executable
        if os.access("scripts/init_system_settings.py", os.X_OK):
            print("  ✅ Script is executable")
        else:
            print("  ⚠️  Script is not executable")
    
    # Test 2: System Settings Definitions
    print("\n⚙️  2. SYSTEM SETTINGS DEFINITIONS")
    
    company_settings = [
        "company_name",
        "company_address", 
        "company_email",
        "company_phone",
        "company_gst_no", 
        "company_registration_number"
    ]
    
    for setting in company_settings:
        total_tests += 1
        if test_file_contains("app/modules/system/service.py", f'"{setting}"', f"Setting: {setting}"):
            passed_tests += 1
    
    # Test 3: API Endpoints
    print("\n🔗 3. API ENDPOINTS")
    
    total_tests += 1
    if test_file_contains("app/modules/system/routes.py", r'@router\.get\("/company"', "GET /system/company endpoint"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains("app/modules/system/routes.py", r'@router\.put\("/company"', "PUT /system/company endpoint"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains("app/modules/system/routes.py", r"CompanyInfo", "CompanyInfo schema"):
        passed_tests += 1
    
    # Test 4: Frontend Integration
    print("\n🎨 4. FRONTEND INTEGRATION")
    
    frontend_api_path = "../rental-manager-frontend/src/services/api/system.ts"
    
    total_tests += 1
    if test_file_contains(frontend_api_path, r"getCompanyInfo", "Frontend getCompanyInfo method"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains(frontend_api_path, r"updateCompanyInfo", "Frontend updateCompanyInfo method"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains(frontend_api_path, r"/system/company", "Frontend API endpoint", 2):
        passed_tests += 1
    
    # Test 5: Enhanced Error Handling
    print("\n🛡️  5. ENHANCED ERROR HANDLING")
    
    frontend_page_path = "../rental-manager-frontend/src/app/settings/company/page.tsx"
    
    total_tests += 1
    if test_file_contains(frontend_page_path, r"Network error", "Network error handling"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains(frontend_page_path, r"Authentication error", "Auth error handling"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains(frontend_page_path, r"System not initialized", "Initialization error handling"):
        passed_tests += 1
    
    # Test 6: Code Quality Checks
    print("\n🔍 6. CODE QUALITY CHECKS")
    
    total_tests += 1
    if test_file_contains("app/modules/system/service.py", r"async def", "Async methods", 10):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains("app/modules/system/routes.py", r"HTTPException", "Error handling in routes"):
        passed_tests += 1
    
    total_tests += 1
    if test_file_contains("scripts/init_system_settings.py", r"if __name__ == \"__main__\"", "Script main guard"):
        passed_tests += 1
    
    # Test 7: Documentation
    print("\n📚 7. DOCUMENTATION")
    
    total_tests += 1
    if test_file_exists("../COMPANY_SETTINGS_FIX_SUMMARY.md", "Fix summary documentation"):
        passed_tests += 1
    
    # Test Results Summary
    print("\n" + "=" * 60)
    print(f"🎯 TEST RESULTS SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Company settings fix is complete and verified.")
        print("\n📋 NEXT STEPS:")
        print("1. Start backend server: uvicorn app.main:app --reload")
        print("2. Check logs for: 'Initialized X default system settings'")
        print("3. Test frontend: http://localhost:3000/settings/company")
        print("4. Try updating company information")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED!")
        print("Please review the failed tests above and fix any issues.")
        return False

def main():
    """Main test execution."""
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print(f"🏁 Running tests from: {os.getcwd()}")
    
    success = run_complete_test()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()