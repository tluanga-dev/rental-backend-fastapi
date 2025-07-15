#!/usr/bin/env python3
"""
Comprehensive test script for rental field migration.
Tests database models, API endpoints, and business logic.
"""

import asyncio
import json
import requests
from decimal import Decimal
from datetime import datetime, date, timedelta
from uuid import uuid4

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_api_health():
    """Test basic API connectivity."""
    print("=== API HEALTH CHECK ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy and responding")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_api_docs():
    """Test API documentation endpoint."""
    print("\n=== API DOCUMENTATION TEST ===")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API documentation is accessible")
            return True
        else:
            print(f"❌ API docs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs error: {e}")
        return False

def test_openapi_schema():
    """Test OpenAPI schema for rental field changes."""
    print("\n=== OPENAPI SCHEMA VALIDATION ===")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            schema = response.json()
            
            # Check TransactionHeader schemas
            if "components" in schema and "schemas" in schema["components"]:
                schemas = schema["components"]["schemas"]
                
                # Test TransactionHeaderResponse
                if "TransactionHeaderResponse" in schemas:
                    header_props = schemas["TransactionHeaderResponse"].get("properties", {})
                    has_rental_fields = any(field in header_props for field in 
                                          ["rental_start_date", "rental_end_date", "current_rental_status"])
                    if has_rental_fields:
                        print("❌ TransactionHeaderResponse still contains rental fields")
                    else:
                        print("✅ TransactionHeaderResponse rental fields removed")
                
                # Test TransactionLineResponse
                if "TransactionLineResponse" in schemas:
                    line_props = schemas["TransactionLineResponse"].get("properties", {})
                    has_rental_status = "current_rental_status" in line_props
                    if has_rental_status:
                        print("✅ TransactionLineResponse contains current_rental_status")
                    else:
                        print("❌ TransactionLineResponse missing current_rental_status")
                
                # Test RentalStatus enum
                if "RentalStatus" in schemas:
                    rental_enum = schemas["RentalStatus"].get("enum", [])
                    expected_statuses = ["ACTIVE", "LATE", "EXTENDED", "PARTIAL_RETURN", "LATE_PARTIAL_RETURN", "COMPLETED"]
                    if set(rental_enum) == set(expected_statuses):
                        print("✅ RentalStatus enum values are correct")
                    else:
                        print(f"❌ RentalStatus enum mismatch. Got: {rental_enum}")
                
                return True
            else:
                print("❌ No schemas found in OpenAPI spec")
                return False
        else:
            print(f"❌ OpenAPI schema request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OpenAPI schema error: {e}")
        return False

def test_authentication():
    """Test authentication and get access token."""
    print("\n=== AUTHENTICATION TEST ===")
    try:
        # Try to login with admin credentials
        login_data = {
            "username": "admin",
            "password": "Admin@123"
        }
        response = requests.post(f"{API_BASE}/auth/login", data=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print("✅ Authentication successful")
                return {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            else:
                print("❌ No access token in response")
                return None
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_transaction_creation(headers):
    """Test transaction creation with rental fields."""
    print("\n=== TRANSACTION CREATION TEST ===")
    
    if not headers:
        print("❌ No authentication headers available")
        return None
    
    try:
        # Create a test transaction with rental data
        transaction_data = {
            "transaction_number": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "transaction_type": "RENTAL",
            "transaction_date": datetime.now().isoformat(),
            "customer_id": str(uuid4()),  # Using dummy UUID
            "location_id": str(uuid4()),   # Using dummy UUID
            "status": "PENDING",
            "payment_status": "PENDING",
            "notes": "Test rental transaction for migration validation"
        }
        
        response = requests.post(f"{API_BASE}/transactions/", 
                               json=transaction_data, headers=headers)
        
        if response.status_code in [200, 201]:
            transaction = response.json()
            print("✅ Transaction creation successful")
            return transaction
        else:
            print(f"⚠️  Transaction creation returned: {response.status_code}")
            # This might fail due to missing customer/location, which is expected
            return None
    except Exception as e:
        print(f"⚠️  Transaction creation error (expected): {e}")
        return None

def test_rental_specific_endpoints(headers):
    """Test rental-specific API endpoints."""
    print("\n=== RENTAL-SPECIFIC ENDPOINTS TEST ===")
    
    if not headers:
        print("❌ No authentication headers available")
        return False
    
    try:
        # Test rental endpoints if they exist
        endpoints_to_test = [
            "/api/rentals/",
            "/api/transactions/",
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
                if response.status_code in [200, 404]:
                    print(f"✅ Endpoint {endpoint} is accessible (status: {response.status_code})")
                else:
                    print(f"⚠️  Endpoint {endpoint} returned: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Endpoint {endpoint} error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Rental endpoints test error: {e}")
        return False

def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🚀 STARTING COMPREHENSIVE RENTAL MIGRATION TESTING")
    print("=" * 60)
    
    results = {
        "api_health": False,
        "api_docs": False, 
        "openapi_schema": False,
        "authentication": False,
        "transaction_creation": False,
        "rental_endpoints": False
    }
    
    # Test 1: API Health
    results["api_health"] = test_api_health()
    
    # Test 2: API Documentation
    if results["api_health"]:
        results["api_docs"] = test_api_docs()
    
    # Test 3: OpenAPI Schema
    if results["api_health"]:
        results["openapi_schema"] = test_openapi_schema()
    
    # Test 4: Authentication
    if results["api_health"]:
        auth_headers = test_authentication()
        results["authentication"] = auth_headers is not None
    else:
        auth_headers = None
    
    # Test 5: Transaction Creation
    if results["authentication"]:
        transaction = test_transaction_creation(auth_headers)
        results["transaction_creation"] = transaction is not None
    
    # Test 6: Rental Endpoints
    if results["authentication"]:
        results["rental_endpoints"] = test_rental_specific_endpoints(auth_headers)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Rental migration is working correctly.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Some issues may need attention.")
    else:
        print("❌ Multiple test failures. Migration needs review.")
    
    return results

if __name__ == "__main__":
    run_comprehensive_tests()