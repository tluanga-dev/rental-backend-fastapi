#!/usr/bin/env python3
"""
Comprehensive test runner for all API endpoints
Run this script to execute all tests and generate a detailed report
"""

import pytest
import sys
import subprocess
import json
import time
from pathlib import Path


def run_test_suite():
    """Run the complete test suite with detailed reporting"""
    
    print("🚀 Starting Comprehensive API Endpoint Test Suite")
    print("=" * 60)
    
    # Test configuration
    test_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable pytest warnings for cleaner output
        "-x",  # Stop on first failure for debugging
    ]
    
    # Run different test categories
    test_categories = [
        {
            "name": "Health & Core Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestHealthEndpoints",
            "description": "Basic health check and core functionality"
        },
        {
            "name": "Authentication Endpoints", 
            "pattern": "tests/test_all_endpoints.py::TestAuthenticationEndpoints",
            "description": "User registration, login, token management"
        },
        {
            "name": "User Management Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestUserManagementEndpoints", 
            "description": "User CRUD operations and admin functions"
        },
        {
            "name": "Role Management Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestRoleManagementEndpoints",
            "description": "RBAC role creation and assignment"
        },
        {
            "name": "Customer Management Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestCustomerManagementEndpoints",
            "description": "Customer CRUD operations and search"
        },
        {
            "name": "Supplier Management Endpoints", 
            "pattern": "tests/test_all_endpoints.py::TestSupplierManagementEndpoints",
            "description": "Supplier CRUD operations"
        },
        {
            "name": "Master Data Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestMasterDataEndpoints",
            "description": "Brands, categories, and locations management"
        },
        {
            "name": "Inventory Management Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestInventoryManagementEndpoints", 
            "description": "Items and inventory units management"
        },
        {
            "name": "Transaction Management Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestTransactionManagementEndpoints",
            "description": "Transaction headers and lines processing"
        },
        {
            "name": "Analytics Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestAnalyticsEndpoints",
            "description": "Business intelligence and reporting"
        },
        {
            "name": "System Endpoints",
            "pattern": "tests/test_all_endpoints.py::TestSystemEndpoints", 
            "description": "System settings and administration"
        },
        {
            "name": "End-to-End Workflows",
            "pattern": "tests/test_all_endpoints.py::TestEndToEndWorkflows",
            "description": "Complete business process testing"
        },
        {
            "name": "Error Scenarios - Authentication",
            "pattern": "tests/test_error_scenarios.py::TestAuthenticationErrors",
            "description": "Authentication error handling"
        },
        {
            "name": "Error Scenarios - Validation",
            "pattern": "tests/test_error_scenarios.py::TestValidationErrors", 
            "description": "Input validation error handling"
        },
        {
            "name": "Error Scenarios - Not Found",
            "pattern": "tests/test_error_scenarios.py::TestNotFoundErrors",
            "description": "Resource not found error handling" 
        },
        {
            "name": "Error Scenarios - Conflicts",
            "pattern": "tests/test_error_scenarios.py::TestConflictErrors",
            "description": "Resource conflict error handling"
        },
        {
            "name": "Error Scenarios - Permissions", 
            "pattern": "tests/test_error_scenarios.py::TestPermissionErrors",
            "description": "Authorization error handling"
        },
        {
            "name": "Error Scenarios - Malformed Requests",
            "pattern": "tests/test_error_scenarios.py::TestMalformedRequestErrors",
            "description": "Malformed request error handling"
        },
        {
            "name": "Performance Tests",
            "pattern": "tests/test_all_endpoints.py::TestPerformanceEndpoints",
            "description": "API performance and load testing"
        }
    ]
    
    # Results tracking
    results = []
    total_start_time = time.time()
    
    for category in test_categories:
        print(f"\n📋 Running: {category['name']}")
        print(f"   Description: {category['description']}")
        print("-" * 50)
        
        start_time = time.time()
        
        # Run the specific test category
        cmd = ["python", "-m", "pytest"] + test_args + [category["pattern"]]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per category
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            output_lines = result.stdout.split('\n')
            error_lines = result.stderr.split('\n')
            
            # Extract test results from output
            passed = failed = errors = 0
            for line in output_lines:
                if "passed" in line and "failed" in line:
                    # Parse line like "5 passed, 2 failed in 10.5s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed," or part == "passed":
                            try:
                                passed = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                        elif part == "failed," or part == "failed":
                            try:
                                failed = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                        elif part == "error," or part == "error":
                            try:
                                errors = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                elif line.strip().endswith(" passed"):
                    # Parse line like "15 passed in 5.2s"
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[1] == "passed":
                        try:
                            passed = int(parts[0])
                        except ValueError:
                            pass
            
            success = result.returncode == 0
            
            result_data = {
                "category": category["name"],
                "success": success,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "duration": duration,
                "output": result.stdout,
                "errors_output": result.stderr
            }
            
            results.append(result_data)
            
            # Print immediate results
            if success:
                print(f"   ✅ PASSED: {passed} tests in {duration:.2f}s")
            else:
                print(f"   ❌ FAILED: {passed} passed, {failed} failed, {errors} errors in {duration:.2f}s")
                if failed > 0 or errors > 0:
                    print(f"   Error details: {result.stderr[:200]}...")
        
        except subprocess.TimeoutExpired:
            print(f"   ⏰ TIMEOUT: Category exceeded 5 minute limit")
            results.append({
                "category": category["name"],
                "success": False,
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "duration": 300,
                "output": "Timeout expired",
                "errors_output": "Test category exceeded timeout limit"
            })
        
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")
            results.append({
                "category": category["name"], 
                "success": False,
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "duration": 0,
                "output": "",
                "errors_output": str(e)
            })
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    successful_categories = sum(1 for r in results if r["success"])
    total_categories = len(results)
    
    print(f"📈 Overall Statistics:")
    print(f"   Total Test Categories: {total_categories}")
    print(f"   Successful Categories: {successful_categories}")
    print(f"   Failed Categories: {total_categories - successful_categories}")
    print(f"   Total Tests Passed: {total_passed}")
    print(f"   Total Tests Failed: {total_failed}")
    print(f"   Total Errors: {total_errors}")
    print(f"   Total Duration: {total_duration:.2f}s")
    print(f"   Success Rate: {(successful_categories/total_categories)*100:.1f}%")
    
    print(f"\n📋 Detailed Results by Category:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {status} {result['category']}")
        print(f"        Tests: {result['passed']} passed, {result['failed']} failed, {result['errors']} errors")
        print(f"        Duration: {result['duration']:.2f}s")
        if not result["success"] and result["errors_output"]:
            error_preview = result["errors_output"][:100].replace('\n', ' ')
            print(f"        Error: {error_preview}...")
    
    # Performance summary
    print(f"\n⚡ Performance Summary:")
    fastest_category = min(results, key=lambda x: x["duration"])
    slowest_category = max(results, key=lambda x: x["duration"])
    avg_duration = sum(r["duration"] for r in results) / len(results)
    
    print(f"   Fastest Category: {fastest_category['category']} ({fastest_category['duration']:.2f}s)")
    print(f"   Slowest Category: {slowest_category['category']} ({slowest_category['duration']:.2f}s)")
    print(f"   Average Duration: {avg_duration:.2f}s")
    
    # Final assessment
    print(f"\n🎯 Final Assessment:")
    if successful_categories == total_categories:
        print("   🟢 EXCELLENT: All test categories passed!")
        print("   🚀 API is production-ready with comprehensive coverage")
    elif successful_categories >= total_categories * 0.8:
        print("   🟡 GOOD: Most test categories passed")
        print("   🔧 Minor issues detected, review failed categories")
    else:
        print("   🔴 NEEDS ATTENTION: Multiple test categories failed")
        print("   🛠️  Significant issues detected, requires debugging")
    
    # Save detailed results to file
    results_file = Path("test_results.json")
    with open(results_file, "w") as f:
        json.dump({
            "summary": {
                "total_categories": total_categories,
                "successful_categories": successful_categories,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_errors": total_errors,
                "total_duration": total_duration,
                "success_rate": (successful_categories/total_categories)*100
            },
            "detailed_results": results,
            "timestamp": time.time()
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    print("\n✅ Test suite execution completed!")
    
    # Return exit code based on overall success
    return 0 if successful_categories == total_categories else 1


if __name__ == "__main__":
    exit_code = run_test_suite()
    sys.exit(exit_code)