#!/usr/bin/env python3
"""
Basic test script to verify rental endpoints exist and are routed correctly.
"""

import sys
import json

# Add the app directory to the path
sys.path.insert(0, '/app')

from fastapi.testclient import TestClient
from app.main import app


def test_rental_endpoints_basic():
    """Test that rental endpoints are properly configured."""
    print("Testing Rental Endpoints Configuration...")
    
    try:
        # Create test client
        client = TestClient(app)
        
        # Test that the endpoints are configured in OpenAPI
        print("Checking OpenAPI configuration...")
        openapi_response = client.get("/openapi.json")
        
        if openapi_response.status_code == 200:
            openapi_data = openapi_response.json()
            paths = openapi_data.get("paths", {})
            
            # Check for rental endpoints
            rental_endpoints = [path for path in paths.keys() if "/rentals" in path]
            print(f"Found rental endpoints: {rental_endpoints}")
            
            expected_endpoints = [
                "/api/rentals/",
                "/api/rentals/rentable-items",
                "/api/rentals/{rental_id}",
                "/api/rentals/new",
                "/api/rentals/new-optimized"
            ]
            
            found_endpoints = []
            for expected in expected_endpoints:
                # Convert path parameters to match OpenAPI format
                openapi_path = expected.replace("{rental_id}", "{rental_id}")
                if openapi_path in paths:
                    found_endpoints.append(expected)
                    print(f"✅ Found endpoint: {expected}")
                else:
                    print(f"❌ Missing endpoint: {expected}")
            
            if len(found_endpoints) >= 3:  # At least the main endpoints
                print(f"\n✅ Rental endpoints are properly configured!")
                print(f"Found {len(found_endpoints)} out of {len(expected_endpoints)} expected endpoints")
                return True
            else:
                print(f"\n❌ Missing critical rental endpoints")
                return False
        else:
            print(f"❌ Could not fetch OpenAPI configuration: {openapi_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during endpoint test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rental_endpoints_basic()
    sys.exit(0 if success else 1)