#!/usr/bin/env python3
"""
API endpoint tests for the new inventory endpoints using HTTP requests.
Tests the actual API endpoints without requiring database setup.
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any
from datetime import datetime
import uuid


class InventoryAPITester:
    """Test the inventory API endpoints via HTTP requests."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        
    def log_result(self, test_name: str, message: str, passed: bool, details: Dict = None):
        """Log test result."""
        self.test_results.append({
            'test_name': test_name,
            'message': message,
            'passed': passed,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
    
    def test_server_health(self):
        """Test if the server is running."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_result("Server Health", "Server is running", True)
                return True
            else:
                self.log_result("Server Health", f"Server responded with status {response.status_code}", False)
                return False
        except requests.exceptions.ConnectionError:
            self.log_result("Server Health", "Cannot connect to server", False)
            return False
        except Exception as e:
            self.log_result("Server Health", f"Error: {str(e)}", False)
            return False
    
    def test_swagger_docs(self):
        """Test if API documentation is accessible."""
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=10)
            if response.status_code == 200:
                self.log_result("Swagger Docs", "API documentation accessible", True)
                return True
            else:
                self.log_result("Swagger Docs", f"Docs responded with status {response.status_code}", False)
                return False
        except Exception as e:
            self.log_result("Swagger Docs", f"Error: {str(e)}", False)
            return False
    
    def test_openapi_spec(self):
        """Test if OpenAPI spec includes new endpoints."""
        try:
            response = self.session.get(f"{self.base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                spec = response.json()
                paths = spec.get('paths', {})
                
                # Check if new endpoints are in the spec
                overview_endpoint = '/api/inventory/items/overview'
                detailed_endpoint = '/api/inventory/items/{item_id}/detailed'
                
                has_overview = any(overview_endpoint in path for path in paths.keys())
                has_detailed = any('{item_id}/detailed' in path for path in paths.keys())
                
                if has_overview and has_detailed:
                    self.log_result("OpenAPI Spec", "New endpoints found in API specification", True)
                    return True
                else:
                    missing = []
                    if not has_overview:
                        missing.append("overview")
                    if not has_detailed:
                        missing.append("detailed")
                    self.log_result("OpenAPI Spec", f"Missing endpoints: {missing}", False)
                    return False
            else:
                self.log_result("OpenAPI Spec", f"OpenAPI spec responded with status {response.status_code}", False)
                return False
        except Exception as e:
            self.log_result("OpenAPI Spec", f"Error: {str(e)}", False)
            return False
    
    def test_overview_endpoint_unauthenticated(self):
        """Test overview endpoint without authentication."""
        try:
            response = self.session.get(f"{self.base_url}/api/inventory/items/overview", timeout=10)
            
            # Should return 401 Unauthorized
            if response.status_code == 401:
                self.log_result("Overview Unauthenticated", "Correctly returns 401 Unauthorized", True)
                return True
            elif response.status_code == 422:
                self.log_result("Overview Unauthenticated", "Returns 422 (validation error)", True)
                return True
            else:
                self.log_result("Overview Unauthenticated", f"Unexpected status: {response.status_code}", False)
                return False
        except Exception as e:
            self.log_result("Overview Unauthenticated", f"Error: {str(e)}", False)
            return False
    
    def test_detailed_endpoint_unauthenticated(self):
        """Test detailed endpoint without authentication."""
        try:
            fake_id = str(uuid.uuid4())
            response = self.session.get(f"{self.base_url}/api/inventory/items/{fake_id}/detailed", timeout=10)
            
            # Should return 401 Unauthorized
            if response.status_code == 401:
                self.log_result("Detailed Unauthenticated", "Correctly returns 401 Unauthorized", True)
                return True
            elif response.status_code == 422:
                self.log_result("Detailed Unauthenticated", "Returns 422 (validation error)", True)
                return True
            else:
                self.log_result("Detailed Unauthenticated", f"Unexpected status: {response.status_code}", False)
                return False
        except Exception as e:
            self.log_result("Detailed Unauthenticated", f"Error: {str(e)}", False)
            return False
    
    def test_overview_endpoint_invalid_params(self):
        """Test overview endpoint with invalid parameters."""
        test_cases = [
            {
                'name': 'Invalid Limit (Too High)',
                'params': {'limit': 2000},
                'expected_status': 422
            },
            {
                'name': 'Invalid Limit (Negative)',
                'params': {'limit': -1},
                'expected_status': 422
            },
            {
                'name': 'Invalid Skip (Negative)',
                'params': {'skip': -1},
                'expected_status': 422
            },
            {
                'name': 'Invalid Sort Order',
                'params': {'sort_order': 'invalid'},
                'expected_status': 422
            },
            {
                'name': 'Invalid Sort Field',
                'params': {'sort_by': 'invalid_field'},
                'expected_status': 422
            },
            {
                'name': 'Invalid Stock Status',
                'params': {'stock_status': 'INVALID_STATUS'},
                'expected_status': 422
            },
            {
                'name': 'Invalid UUID Format',
                'params': {'brand_id': 'invalid-uuid'},
                'expected_status': 422
            }
        ]
        
        passed = 0
        total = len(test_cases)
        
        for test_case in test_cases:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/inventory/items/overview",
                    params=test_case['params'],
                    timeout=10
                )
                
                if response.status_code == test_case['expected_status']:
                    passed += 1
                    self.log_result(
                        f"Invalid Params - {test_case['name']}", 
                        f"Correctly returned {response.status_code}", 
                        True
                    )
                else:
                    self.log_result(
                        f"Invalid Params - {test_case['name']}", 
                        f"Expected {test_case['expected_status']}, got {response.status_code}", 
                        False
                    )
            except Exception as e:
                self.log_result(
                    f"Invalid Params - {test_case['name']}", 
                    f"Error: {str(e)}", 
                    False
                )
        
        success = passed == total
        self.log_result(
            "Overview Invalid Parameters", 
            f"Passed {passed}/{total} parameter validation tests", 
            success
        )
        return success
    
    def test_detailed_endpoint_invalid_uuid(self):
        """Test detailed endpoint with invalid UUID."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/inventory/items/invalid-uuid/detailed",
                timeout=10
            )
            
            # Should return 422 for invalid UUID format
            if response.status_code == 422:
                self.log_result("Detailed Invalid UUID", "Correctly returns 422 for invalid UUID", True)
                return True
            else:
                self.log_result("Detailed Invalid UUID", f"Expected 422, got {response.status_code}", False)
                return False
        except Exception as e:
            self.log_result("Detailed Invalid UUID", f"Error: {str(e)}", False)
            return False
    
    def test_response_time_overview(self):
        """Test response time for overview endpoint."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/inventory/items/overview", timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Check if response time is reasonable (less than 5 seconds without auth)
            if response_time < 5.0:
                self.log_result(
                    "Overview Response Time", 
                    f"Response time: {response_time:.3f}s", 
                    True
                )
                return True
            else:
                self.log_result(
                    "Overview Response Time", 
                    f"Slow response: {response_time:.3f}s", 
                    False
                )
                return False
        except Exception as e:
            self.log_result("Overview Response Time", f"Error: {str(e)}", False)
            return False
    
    def test_response_time_detailed(self):
        """Test response time for detailed endpoint."""
        try:
            fake_id = str(uuid.uuid4())
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/inventory/items/{fake_id}/detailed", timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Check if response time is reasonable (less than 5 seconds without auth)
            if response_time < 5.0:
                self.log_result(
                    "Detailed Response Time", 
                    f"Response time: {response_time:.3f}s", 
                    True
                )
                return True
            else:
                self.log_result(
                    "Detailed Response Time", 
                    f"Slow response: {response_time:.3f}s", 
                    False
                )
                return False
        except Exception as e:
            self.log_result("Detailed Response Time", f"Error: {str(e)}", False)
            return False
    
    def test_cors_headers(self):
        """Test CORS headers."""
        try:
            response = self.session.options(f"{self.base_url}/api/inventory/items/overview", timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            has_cors = any(header for header in cors_headers.values())
            
            if has_cors:
                self.log_result("CORS Headers", "CORS headers present", True, cors_headers)
                return True
            else:
                self.log_result("CORS Headers", "No CORS headers found", False, cors_headers)
                return False
        except Exception as e:
            self.log_result("CORS Headers", f"Error: {str(e)}", False)
            return False
    
    def test_content_type_headers(self):
        """Test content type headers."""
        try:
            response = self.session.get(f"{self.base_url}/api/inventory/items/overview", timeout=10)
            
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                self.log_result("Content Type", f"Correct content type: {content_type}", True)
                return True
            else:
                self.log_result("Content Type", f"Unexpected content type: {content_type}", False)
                return False
        except Exception as e:
            self.log_result("Content Type", f"Error: {str(e)}", False)
            return False
    
    def test_endpoint_availability(self):
        """Test if endpoints are available (even if they return auth errors)."""
        endpoints = [
            ('/api/inventory/items/overview', 'GET'),
            (f'/api/inventory/items/{uuid.uuid4()}/detailed', 'GET')
        ]
        
        passed = 0
        total = len(endpoints)
        
        for endpoint, method in endpoints:
            try:
                response = self.session.request(method, f"{self.base_url}{endpoint}", timeout=10)
                
                # Any response other than 404 means the endpoint exists
                if response.status_code != 404:
                    passed += 1
                    self.log_result(
                        f"Endpoint Available - {method} {endpoint}", 
                        f"Endpoint exists (status: {response.status_code})", 
                        True
                    )
                else:
                    self.log_result(
                        f"Endpoint Available - {method} {endpoint}", 
                        "Endpoint not found (404)", 
                        False
                    )
            except Exception as e:
                self.log_result(
                    f"Endpoint Available - {method} {endpoint}", 
                    f"Error: {str(e)}", 
                    False
                )
        
        success = passed == total
        self.log_result(
            "Endpoint Availability", 
            f"Available endpoints: {passed}/{total}", 
            success
        )
        return success
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("INVENTORY API ENDPOINTS TEST SUMMARY")
        print("="*70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if total_tests > 0:
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  ❌ {result['test_name']}: {result['message']}")
        
        print("\nALL TESTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} - {result['test_name']}")
        
        print("="*70)
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """Run all API tests."""
        print("Starting Inventory API Endpoints Testing...")
        print("="*70)
        print(f"Testing against: {self.base_url}")
        print("="*70)
        
        # Test methods to run
        test_methods = [
            self.test_server_health,
            self.test_swagger_docs,
            self.test_openapi_spec,
            self.test_endpoint_availability,
            self.test_overview_endpoint_unauthenticated,
            self.test_detailed_endpoint_unauthenticated,
            self.test_overview_endpoint_invalid_params,
            self.test_detailed_endpoint_invalid_uuid,
            self.test_response_time_overview,
            self.test_response_time_detailed,
            self.test_cors_headers,
            self.test_content_type_headers
        ]
        
        # Run tests
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_result(
                    f"Test Method: {test_method.__name__}", 
                    f"Unexpected error: {str(e)}", 
                    False
                )
        
        return self.print_summary()


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Inventory API Endpoints')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL of the API')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    tester = InventoryAPITester(base_url=args.url)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! The new inventory endpoints are working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the issues above.")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test runner failed: {str(e)}")
        sys.exit(1)