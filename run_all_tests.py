#!/usr/bin/env python3
"""
Run all comprehensive tests for the rental delivery and pickup fields implementation.
"""

import subprocess
import sys
import time
from datetime import datetime

def run_test(test_name, test_file):
    """Run a single test and return results."""
    print(f"\n{'='*60}")
    print(f"Running {test_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=30)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"\n✅ {test_name} PASSED (Duration: {duration:.2f}s)")
            return True, duration
        else:
            print(result.stdout)
            print(result.stderr)
            print(f"\n❌ {test_name} FAILED (Duration: {duration:.2f}s)")
            return False, duration
            
    except subprocess.TimeoutExpired:
        print(f"\n⏰ {test_name} TIMED OUT (>30s)")
        return False, 30.0
    except Exception as e:
        print(f"\n💥 {test_name} ERROR: {e}")
        return False, 0.0

def main():
    """Run all tests and generate summary."""
    print("🚀 COMPREHENSIVE TEST SUITE")
    print("Rental Delivery and Pickup Fields Implementation")
    print(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Define all tests
    tests = [
        ("Database Migration Tests", "test_new_fields.py"),
        ("Schema Validation Tests", "test_schemas.py"),
        ("Service Logic Tests", "test_service.py"),
        ("API Endpoint Tests", "test_api.py"),
        ("Edge Cases & Error Handling", "test_edge_cases.py"),
        ("Backward Compatibility Tests", "test_backward_compatibility.py"),
    ]
    
    # Run all tests
    results = []
    total_duration = 0
    
    for test_name, test_file in tests:
        passed, duration = run_test(test_name, test_file)
        results.append((test_name, passed, duration))
        total_duration += duration
        
        if not passed:
            print(f"\n⚠️  {test_name} failed - continuing with remaining tests...")
    
    # Generate summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    print(f"Total Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Success Rate: {(passed_count/total_count)*100:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")
    
    print(f"\n{'Test Results:':<40} {'Status':<10} {'Duration':<10}")
    print("-" * 60)
    
    for test_name, passed, duration in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<40} {status:<10} {duration:.2f}s")
    
    # Overall result
    print(f"\n{'='*60}")
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Implementation is ready for production deployment")
        print("\nNext steps:")
        print("1. Run database migration: alembic upgrade head")
        print("2. Deploy application to production")
        print("3. Update API documentation")
        print("4. Notify frontend team of new fields")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please review failed tests before deployment")
        print("\nFailed tests need attention:")
        for test_name, passed, _ in results:
            if not passed:
                print(f"  - {test_name}")
    
    print(f"\n{'='*60}")
    print("Test suite completed!")
    
    # Return appropriate exit code
    return 0 if passed_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())