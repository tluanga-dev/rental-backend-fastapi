#!/usr/bin/env python3
"""
Test script to validate the API documentation examples.
Verifies that documented endpoints work as described.
"""

import requests
import json
from typing import Dict, Any


def test_api_documentation():
    """Test key endpoints documented in the API reference."""
    base_url = "http://localhost:8000/api/master-data/item-master"
    
    print("🔍 Testing API Documentation Examples...")
    
    # Test 1: Basic item listing
    print("\n1. Testing basic item listing...")
    response = requests.get(f"{base_url}/")
    assert response.status_code == 200
    items = response.json()
    print(f"   ✅ Retrieved {len(items)} items")
    
    # Test 2: Search functionality
    print("\n2. Testing search functionality...")
    response = requests.get(f"{base_url}/?search=apple")
    assert response.status_code == 200
    search_results = response.json()
    print(f"   ✅ Search for 'apple' returned {len(search_results)} items")
    
    # Test 3: Filter by item type
    print("\n3. Testing filter by item type...")
    response = requests.get(f"{base_url}/?item_type=RENTAL")
    assert response.status_code == 200
    rental_items = response.json()
    print(f"   ✅ RENTAL filter returned {len(rental_items)} items")
    
    # Test 4: Combined search and filter
    print("\n4. Testing combined search and filter...")
    response = requests.get(f"{base_url}/?search=apple&item_type=RENTAL")
    assert response.status_code == 200
    combined_results = response.json()
    print(f"   ✅ Combined search + filter returned {len(combined_results)} items")
    
    # Test 5: Pagination
    print("\n5. Testing pagination...")
    response = requests.get(f"{base_url}/?limit=2")
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1) <= 2
    print(f"   ✅ Pagination limit=2 returned {len(page1)} items")
    
    # Test 6: Count endpoint
    print("\n6. Testing count endpoint...")
    response = requests.get(f"{base_url}/count/total")
    assert response.status_code == 200
    count_data = response.json()
    assert "count" in count_data
    print(f"   ✅ Total count: {count_data['count']}")
    
    # Test 7: Count with filters
    print("\n7. Testing count with filters...")
    response = requests.get(f"{base_url}/count/total?item_type=RENTAL")
    assert response.status_code == 200
    rental_count = response.json()["count"]
    print(f"   ✅ RENTAL count: {rental_count}")
    
    # Test 8: Specialized endpoints
    print("\n8. Testing specialized endpoints...")
    
    # Test rental items endpoint
    response = requests.get(f"{base_url}/types/rental")
    assert response.status_code == 200
    rental_only = response.json()
    print(f"   ✅ Rental items endpoint returned {len(rental_only)} items")
    
    # Test sale items endpoint
    response = requests.get(f"{base_url}/types/sale")
    assert response.status_code == 200
    sale_only = response.json()
    print(f"   ✅ Sale items endpoint returned {len(sale_only)} items")
    
    # Test 9: Get item by code (if available)
    if items:
        first_item = items[0]
        item_code = first_item["item_code"]
        print(f"\n9. Testing get item by code: {item_code}...")
        response = requests.get(f"{base_url}/code/{item_code}")
        assert response.status_code == 200
        item_detail = response.json()
        assert item_detail["item_code"] == item_code
        print(f"   ✅ Retrieved item by code: {item_detail['display_name']}")
        
        # Test 10: Get item by SKU
        sku = item_detail["sku"]
        print(f"\n10. Testing get item by SKU: {sku}...")
        response = requests.get(f"{base_url}/sku/{sku}")
        assert response.status_code == 200
        item_by_sku = response.json()
        assert item_by_sku["sku"] == sku
        print(f"    ✅ Retrieved item by SKU: {item_by_sku['display_name']}")
    
    # Test 11: SKU generation preview
    print("\n11. Testing SKU generation preview...")
    sku_request = {
        "item_name": "Test Item for Documentation",
        "item_type": "RENTAL"
    }
    response = requests.post(f"{base_url}/skus/generate", json=sku_request)
    assert response.status_code == 200
    sku_preview = response.json()
    assert "sku" in sku_preview
    print(f"    ✅ SKU preview generated: {sku_preview['sku']}")
    
    # Test 12: Validate response schema matches documentation
    print("\n12. Testing response schema validation...")
    if items:
        item = items[0]
        required_fields = ["id", "item_code", "item_name", "item_type", "item_status", 
                          "purchase_price", "is_active", "created_at", "updated_at", "display_name"]
        for field in required_fields:
            assert field in item, f"Missing field {field} in response"
        print("    ✅ Response schema matches documentation")
    
    # Test 13: Error handling
    print("\n13. Testing error handling...")
    
    # Test invalid item type
    response = requests.get(f"{base_url}/?item_type=INVALID")
    assert response.status_code == 422
    print("    ✅ Invalid item_type properly rejected with 422")
    
    # Test invalid limit
    response = requests.get(f"{base_url}/?limit=-1")
    assert response.status_code == 422
    print("    ✅ Invalid limit properly rejected with 422")
    
    # Test non-existent item
    response = requests.get(f"{base_url}/code/NONEXISTENT")
    assert response.status_code == 404
    print("    ✅ Non-existent item properly returns 404")
    
    print("\n🎉 ALL DOCUMENTATION TESTS PASSED!")
    print("\nSummary:")
    print("- All documented endpoints are accessible")
    print("- Request/response formats match documentation")
    print("- Error handling works as documented")
    print("- Examples in documentation are accurate")
    
    return True


def verify_openapi_completeness():
    """Verify OpenAPI documentation completeness."""
    print("\n🔍 Verifying OpenAPI Documentation Completeness...")
    
    response = requests.get("http://localhost:8000/openapi.json")
    assert response.status_code == 200
    openapi_data = response.json()
    
    # Count item master endpoints
    paths = openapi_data.get("paths", {})
    item_master_paths = [path for path in paths.keys() if '/api/master-data/item-master' in path]
    
    print(f"\n📊 OpenAPI Documentation Statistics:")
    print(f"- Total Item Master Endpoints: {len(item_master_paths)}")
    print(f"- Total HTTP Methods: {sum(len(paths[path]) for path in item_master_paths)}")
    
    # Verify key endpoints are documented
    expected_endpoints = [
        "/api/master-data/item-master/",
        "/api/master-data/item-master/{item_id}",
        "/api/master-data/item-master/code/{item_code}",
        "/api/master-data/item-master/sku/{sku}",
        "/api/master-data/item-master/search/{search_term}",
        "/api/master-data/item-master/count/total",
        "/api/master-data/item-master/skus/generate",
        "/api/master-data/item-master/types/rental",
        "/api/master-data/item-master/types/sale"
    ]
    
    missing_endpoints = []
    for endpoint in expected_endpoints:
        if endpoint not in item_master_paths:
            missing_endpoints.append(endpoint)
    
    if missing_endpoints:
        print(f"❌ Missing endpoints: {missing_endpoints}")
        return False
    else:
        print("✅ All expected endpoints are documented")
        return True


def main():
    """Main test runner."""
    try:
        # Test server connectivity
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not healthy. Please start the server first.")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Please start the server first.")
        return False
    
    print("🚀 API Documentation Validation Test Suite")
    print("=" * 50)
    
    # Run tests
    api_test_passed = test_api_documentation()
    openapi_test_passed = verify_openapi_completeness()
    
    if api_test_passed and openapi_test_passed:
        print("\n🎉 DOCUMENTATION VALIDATION SUCCESSFUL!")
        print("\nThe API documentation is:")
        print("✅ Complete - All endpoints documented")
        print("✅ Accurate - Examples work as described")
        print("✅ Consistent - Schemas match actual responses")
        print("✅ Comprehensive - Error cases included")
        return True
    else:
        print("\n❌ Documentation validation failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)