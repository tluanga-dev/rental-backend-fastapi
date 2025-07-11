"""
RBAC Test Runner

Comprehensive test runner for all RBAC-related tests.
This script runs all RBAC tests and provides a summary report.
"""

import pytest
import sys
import os
from pathlib import Path


def run_rbac_tests():
    """Run all RBAC tests and return results"""
    
    # Add the app directory to Python path
    app_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(app_dir))
    
    # Test files to run
    test_files = [
        "test_rbac.py",
        "test_rbac_api.py", 
        "test_rbac_auth.py"
    ]
    
    print("=" * 80)
    print("RBAC COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    
    # Check if test files exist
    missing_files = []
    for test_file in test_files:
        if not os.path.exists(test_file):
            missing_files.append(test_file)
    
    if missing_files:
        print("❌ Missing test files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("📋 Test Files:")
    for test_file in test_files:
        print(f"   ✓ {test_file}")
    print()
    
    # Run tests with detailed output
    pytest_args = [
        "-v",  # Verbose output
        "-s",  # Don't capture stdout
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Treat unknown markers as errors
        "-p", "no:warnings",  # Disable warnings
        "--maxfail=5",  # Stop after 5 failures
    ]
    
    # Add test files
    pytest_args.extend(test_files)
    
    print("🚀 Running RBAC Tests...")
    print("-" * 40)
    
    # Run the tests
    exit_code = pytest.main(pytest_args)
    
    print()
    print("-" * 40)
    
    if exit_code == 0:
        print("✅ ALL RBAC TESTS PASSED!")
        print()
        print("🔐 RBAC System Verification Complete:")
        print("   ✓ Permission model and operations")
        print("   ✓ Role model and permission assignments")
        print("   ✓ User-Role relationships")
        print("   ✓ Permission checking and validation")
        print("   ✓ API endpoint protection")
        print("   ✓ Authentication integration")
        print("   ✓ JWT token permission inclusion")
        print("   ✓ Edge cases and error handling")
        print("   ✓ Security scenarios")
        print("   ✓ Performance considerations")
    else:
        print("❌ SOME RBAC TESTS FAILED")
        print()
        print("Please review the test output above and fix any issues.")
        print("Common issues:")
        print("   - Database connection problems")
        print("   - Missing dependencies")
        print("   - Configuration errors")
        print("   - Model relationship issues")
    
    print()
    print("=" * 80)
    
    return exit_code == 0


def run_specific_test_class(test_class: str):
    """Run a specific test class"""
    
    test_class_map = {
        "permission": "test_rbac.py::TestPermissionModel",
        "role": "test_rbac.py::TestRoleModel", 
        "user_role": "test_rbac.py::TestUserRoleRelationships",
        "service": "test_rbac.py::TestUserRoleService",
        "integration": "test_rbac.py::TestRBACIntegration",
        "edge_cases": "test_rbac.py::TestRBACEdgeCases",
        "performance": "test_rbac.py::TestRBACPerformance",
        "api": "test_rbac_api.py::TestRBACAPIIntegration",
        "middleware": "test_rbac_api.py::TestRBACMiddleware",
        "api_errors": "test_rbac_api.py::TestRBACErrorHandling",
        "api_performance": "test_rbac_api.py::TestRBACPerformanceAPI",
        "auth": "test_rbac_auth.py::TestAuthRBACIntegration",
        "session": "test_rbac_auth.py::TestRBACSessionManagement",
        "security": "test_rbac_auth.py::TestRBACSecurityScenarios",
    }
    
    if test_class not in test_class_map:
        print(f"❌ Unknown test class: {test_class}")
        print("Available test classes:")
        for key in sorted(test_class_map.keys()):
            print(f"   - {key}")
        return False
    
    test_path = test_class_map[test_class]
    
    print(f"🎯 Running specific test class: {test_class}")
    print(f"📂 Test path: {test_path}")
    print()
    
    pytest_args = [
        "-v",
        "-s", 
        "--tb=short",
        test_path
    ]
    
    exit_code = pytest.main(pytest_args)
    return exit_code == 0


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        # Run specific test class
        test_class = sys.argv[1]
        success = run_specific_test_class(test_class)
    else:
        # Run all RBAC tests
        success = run_rbac_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()