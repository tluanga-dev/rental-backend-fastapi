#!/usr/bin/env python3
"""
Test runner for company module tests.

Run all company tests:
    python tests/modules/company/test_company_runner.py

Run specific test file:
    python tests/modules/company/test_company_runner.py model
    python tests/modules/company/test_company_runner.py service
    python tests/modules/company/test_company_runner.py api
"""

import subprocess
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)


def run_tests(test_type=None):
    """Run company module tests."""
    
    # Base pytest command
    cmd = ["pytest", "-v", "-s"]
    
    # Determine which tests to run
    if test_type == "model":
        cmd.append("tests/modules/company/test_company_model.py")
        print("Running Company Model Tests...")
    elif test_type == "service":
        cmd.append("tests/modules/company/test_company_service.py")
        print("Running Company Service Tests...")
    elif test_type == "api":
        cmd.append("tests/modules/company/test_company_api.py")
        print("Running Company API Tests...")
    else:
        cmd.append("tests/modules/company/")
        print("Running All Company Module Tests...")
    
    # Add coverage if requested
    if "--cov" in sys.argv:
        cmd.extend(["--cov=app.modules.company", "--cov-report=term-missing"])
    
    # Run tests
    result = subprocess.run(cmd, cwd=project_root)
    
    return result.returncode


def main():
    """Main function."""
    # Parse command line arguments
    test_type = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["model", "service", "api"]:
            test_type = arg
    
    # Run tests
    exit_code = run_tests(test_type)
    
    # Exit with test result
    sys.exit(exit_code)


if __name__ == "__main__":
    main()