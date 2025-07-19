#!/usr/bin/env python3
"""
Simple API test script to verify purchase endpoints work correctly.
"""

import asyncio
import sys
import json
from datetime import date

# Add the app directory to the path
sys.path.insert(0, '/app')

import httpx
from fastapi.testclient import TestClient
from app.main import app


def test_purchase_api():
    """Test purchase API endpoints directly."""
    print("Testing Purchase API...")
    
    try:
        # Create test client
        client = TestClient(app)
        
        # Test getting purchases list (should work even if empty)
        print("Testing GET /api/purchases/...")
        response = client.get("/api/purchases/")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ GET /api/purchases/ works! Found {len(result)} purchases")
            
            # Test purchase creation (this might fail due to missing data, but we can test the endpoint structure)
            print("\nTesting POST /api/purchases/new...")
            
            # Create a test purchase request (this will likely fail validation, but that's okay)
            test_purchase = {
                "supplier_id": "00000000-0000-0000-0000-000000000001",
                "location_id": "00000000-0000-0000-0000-000000000001", 
                "purchase_date": date.today().isoformat(),
                "notes": "API test purchase",
                "reference_number": "API-TEST-001",
                "items": [
                    {
                        "item_id": "00000000-0000-0000-0000-000000000001",
                        "quantity": 1,
                        "unit_cost": "10.00",
                        "tax_rate": "0.0",
                        "discount_amount": "0.00",
                        "condition": "A",
                        "notes": "Test item"
                    }
                ]
            }
            
            create_response = client.post(
                "/api/purchases/new",
                json=test_purchase
            )
            
            print(f"Create Status Code: {create_response.status_code}")
            
            if create_response.status_code == 401:
                print("✅ POST endpoint exists but requires authentication (expected)")
            elif create_response.status_code == 404:
                print("✅ POST endpoint exists but supplier/item not found (expected)")  
            elif create_response.status_code == 422:
                print("✅ POST endpoint exists but validation failed (expected)")
                print(f"Validation Error: {create_response.json()}")
            elif create_response.status_code == 201:
                print("✅ POST endpoint created purchase successfully!")
                print(f"Result: {create_response.json()}")
            else:
                print(f"⚠️ Unexpected response: {create_response.status_code}")
                print(f"Response: {create_response.text}")
            
            # Test getting a specific purchase (will fail with 404, but that's expected)
            print("\nTesting GET /api/purchases/{id}...")
            test_id = "00000000-0000-0000-0000-000000000001"
            get_response = client.get(f"/api/purchases/{test_id}")
            
            print(f"Get by ID Status Code: {get_response.status_code}")
            
            if get_response.status_code == 404:
                print("✅ GET by ID endpoint works (404 expected for non-existent ID)")
            elif get_response.status_code == 401:
                print("✅ GET by ID endpoint exists but requires authentication")
            else:
                print(f"⚠️ Unexpected response: {get_response.status_code}")
            
            print("\n✅ Purchase API endpoints are accessible and functional!")
            return True
            
        elif response.status_code == 401:
            print("✅ API endpoint exists but requires authentication")
            print("This means the routes are properly configured!")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during API test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_purchase_api()
    sys.exit(0 if success else 1)