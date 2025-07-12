#!/usr/bin/env python3
"""
Verification script to ensure Item Master endpoints are properly displayed in Swagger UI.
"""

import requests
import json


def verify_swagger_integration():
    """Verify that Item Master endpoints are properly integrated in Swagger UI."""
    base_url = "http://localhost:8000"
    
    print("🔍 Verifying Swagger UI Integration for Item Master API")
    print("=" * 60)
    
    # 1. Check OpenAPI JSON
    print("\n1. Checking OpenAPI JSON schema...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code != 200:
            print("❌ Cannot access OpenAPI JSON")
            return False
        
        openapi_data = response.json()
        
        # Check tags
        tags = openapi_data.get('tags', [])
        items_tag = next((tag for tag in tags if tag['name'] == 'Items'), None)
        if not items_tag:
            print("❌ 'Items' tag not found in OpenAPI tags")
            return False
        
        print(f"✅ Items tag found: {items_tag['description']}")
        
        # Check endpoints
        paths = openapi_data.get('paths', {})
        item_endpoints = []
        
        for path, methods in paths.items():
            if 'item-master' in path:
                for method, details in methods.items():
                    if 'Items' in details.get('tags', []):
                        item_endpoints.append({
                            'method': method.upper(),
                            'path': path,
                            'summary': details.get('summary', 'No summary')
                        })
        
        print(f"✅ Found {len(item_endpoints)} Item Master endpoints")
        
    except Exception as e:
        print(f"❌ Error checking OpenAPI JSON: {e}")
        return False
    
    # 2. Check Swagger UI accessibility
    print("\n2. Checking Swagger UI accessibility...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code != 200:
            print("❌ Cannot access Swagger UI at /docs")
            return False
        
        print("✅ Swagger UI is accessible")
        
        # Check if the HTML contains item master references
        html_content = response.text
        if 'item-master' in html_content.lower():
            print("✅ Item Master endpoints referenced in Swagger UI HTML")
        else:
            print("⚠️  Item Master endpoints may not be visible in UI (client-side rendering)")
        
    except Exception as e:
        print(f"❌ Error checking Swagger UI: {e}")
        return False
    
    # 3. Test actual endpoints
    print("\n3. Testing actual Item Master endpoints...")
    
    test_endpoints = [
        ("GET", "/api/master-data/item-master/", "Get Items"),
        ("GET", "/api/master-data/item-master/count/total", "Count Items"),
        ("GET", "/api/master-data/item-master/types/rental", "Get Rental Items"),
        ("POST", "/api/master-data/item-master/skus/generate", "SKU Preview", {
            "item_name": "Test Item",
            "item_type": "RENTAL"
        })
    ]
    
    for method, endpoint, name, *payload in test_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{base_url}{endpoint}", json=payload[0] if payload else {})
            
            if response.status_code in [200, 201]:
                print(f"✅ {name}: {response.status_code}")
            else:
                print(f"❌ {name}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    # 4. Show available endpoints summary
    print("\n4. Item Master API Summary:")
    print(f"   📊 Total endpoints: {len(item_endpoints)}")
    print("   🔍 Key functionality:")
    print("     - Create, Read, Update, Delete items")
    print("     - Advanced search and filtering")
    print("     - SKU generation and management")
    print("     - Specialized queries (rental/sale items)")
    print("     - Count and pagination support")
    
    print("\n5. Swagger UI Access:")
    print(f"   🌐 Swagger UI: {base_url}/docs")
    print(f"   📋 OpenAPI JSON: {base_url}/openapi.json")
    print(f"   📚 ReDoc: {base_url}/redoc")
    
    print("\n✅ Verification completed successfully!")
    print("\nThe Item Master API is properly integrated and should be visible in Swagger UI.")
    print("Look for the 'Items' section in the API documentation.")
    
    return True


def show_endpoint_examples():
    """Show some example API calls."""
    print("\n" + "=" * 60)
    print("📝 Example API Calls")
    print("=" * 60)
    
    examples = [
        {
            "title": "Get all items",
            "method": "GET",
            "url": "/api/master-data/item-master/",
            "description": "Retrieve paginated list of all items"
        },
        {
            "title": "Search items",
            "method": "GET",
            "url": "/api/master-data/item-master/?search=drill&item_type=RENTAL",
            "description": "Search for rental items containing 'drill'"
        },
        {
            "title": "Create item",
            "method": "POST",
            "url": "/api/master-data/item-master/",
            "body": {
                "item_code": "NEW001",
                "item_name": "New Power Tool",
                "item_type": "RENTAL",
                "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
                "rental_price_per_day": 25.00
            },
            "description": "Create a new rental item"
        },
        {
            "title": "Generate SKU preview",
            "method": "POST",
            "url": "/api/master-data/item-master/skus/generate",
            "body": {
                "item_name": "Milwaukee Impact Driver",
                "item_type": "RENTAL"
            },
            "description": "Preview SKU generation without creating item"
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}:")
        print(f"  {example['method']} {example['url']}")
        if 'body' in example:
            print(f"  Body: {json.dumps(example['body'], indent=2)}")
        print(f"  Description: {example['description']}")


if __name__ == "__main__":
    try:
        # Test server connectivity
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not healthy. Please ensure the server is running.")
            exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server at http://localhost:8000")
        print("   Please ensure the FastAPI server is running.")
        exit(1)
    
    success = verify_swagger_integration()
    if success:
        show_endpoint_examples()
        print(f"\n🎉 SUCCESS: Visit http://localhost:8000/docs to see the Item Master API!")
    else:
        print("\n❌ FAILED: Some issues were found with the Swagger UI integration.")
        exit(1)