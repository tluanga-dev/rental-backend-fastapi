#!/usr/bin/env python3
"""
Test runner script for purchase CRUD tests.

This script sets up the environment and runs the purchase CRUD tests.
It can be used to run all tests or specific test cases.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_tests():
    """Run purchase CRUD tests."""
    print("Running Purchase CRUD Tests...")
    print("=" * 50)
    
    # Set test environment variables
    os.environ["TEST_DATABASE_URL"] = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql+asyncpg://fastapi_user:fastapi_password@localhost:5432/fastapi_test_db"
    )
    
    # Test commands to run
    test_commands = [
        # Run all purchase CRUD tests
        ["python", "-m", "pytest", "tests/test_purchase_crud.py", "-v"],
        
        # Run specific test categories
        ["python", "-m", "pytest", "tests/test_purchase_crud.py::TestPurchaseCRUD::test_create_purchase_success", "-v"],
        ["python", "-m", "pytest", "tests/test_purchase_crud.py::TestPurchaseCRUD::test_get_purchase_by_id_success", "-v"],
        ["python", "-m", "pytest", "tests/test_purchase_crud.py::TestPurchaseCRUD::test_get_purchases_list", "-v"],
        ["python", "-m", "pytest", "tests/test_purchase_crud.py::TestPurchaseCRUD::test_purchase_data_integrity", "-v"],
    ]
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n{i}. Running: {' '.join(cmd)}")
        print("-" * 40)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            if result.returncode == 0:
                print("✓ PASSED")
                if result.stdout:
                    print(result.stdout)
            else:
                print("✗ FAILED")
                if result.stderr:
                    print("STDERR:", result.stderr)
                if result.stdout:
                    print("STDOUT:", result.stdout)
                    
        except Exception as e:
            print(f"✗ ERROR: {e}")
        
        print("-" * 40)

def run_specific_test(test_name):
    """Run a specific test."""
    cmd = ["python", "-m", "pytest", f"tests/test_purchase_crud.py::TestPurchaseCRUD::{test_name}", "-v", "-s"]
    print(f"Running specific test: {test_name}")
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running test: {e}")
        return False

def show_usage():
    """Show usage information."""
    print("Purchase CRUD Test Runner")
    print("=" * 30)
    print("\nUsage:")
    print("  python run_purchase_crud_tests.py                    # Run all tests")
    print("  python run_purchase_crud_tests.py <test_name>        # Run specific test")
    print("\nAvailable tests:")
    print("  - test_create_purchase_success")
    print("  - test_create_purchase_invalid_supplier")
    print("  - test_create_purchase_invalid_item")
    print("  - test_create_purchase_invalid_data")
    print("  - test_get_purchase_by_id_success")
    print("  - test_get_purchase_by_id_not_found")
    print("  - test_get_purchases_list")
    print("  - test_get_purchases_with_date_filter")
    print("  - test_purchase_data_integrity")
    print("  - test_concurrent_purchase_creation")
    print("  - test_purchase_validation_edge_cases")
    print("  - test_purchase_search_functionality")
    print("\nExamples:")
    print("  python run_purchase_crud_tests.py test_create_purchase_success")
    print("  python run_purchase_crud_tests.py test_get_purchases_list")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help", "help"]:
            show_usage()
        else:
            test_name = sys.argv[1]
            success = run_specific_test(test_name)
            sys.exit(0 if success else 1)
    else:
        run_tests()