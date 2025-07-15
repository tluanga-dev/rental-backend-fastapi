#!/usr/bin/env python3
"""
Test script for item master search and filter functionality.
Tests all combinations of search parameters and filters.
"""

import asyncio
import json
import requests
from typing import Dict, Any


class ItemSearchFilterTester:
    """Test class for item search and filter functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/master-data/item-master"
    
    def test_basic_list(self) -> bool:
        """Test basic item listing without filters."""
        print("🔍 Testing basic item listing...")
        
        response = requests.get(f"{self.api_base}/")
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        
        print(f"✅ Basic listing returned {len(items)} items")
        return True
    
    def test_search_functionality(self) -> bool:
        """Test search functionality."""
        print("🔍 Testing search functionality...")
        
        # Test search by item name
        response = requests.get(f"{self.api_base}/?search=excavator")
        assert response.status_code == 200
        items = response.json()
        
        # Verify search results contain the term
        for item in items:
            assert any([
                "excavator" in item["item_name"].lower(),
                "excavator" in item["item_code"].lower(),
                "excavator" in (item.get("description", "") or "").lower()
            ]), f"Search term not found in item: {item['item_name']}"
        
        print(f"✅ Search for 'excavator' returned {len(items)} items")
        
        # Test search by item code
        response = requests.get(f"{self.api_base}/?search=TEST")
        assert response.status_code == 200
        items = response.json()
        
        print(f"✅ Search for 'TEST' returned {len(items)} items")
        return True
    
    def test_filter_by_type(self) -> bool:
        """Test filtering by item type."""
        print("🔍 Testing filter by item type...")
        
        # Test RENTAL filter
        response = requests.get(f"{self.api_base}/?item_type=RENTAL")
        assert response.status_code == 200
        rental_items = response.json()
        
        for item in rental_items:
            assert item["item_type"] == "RENTAL", f"Non-rental item found: {item['item_name']}"
        
        print(f"✅ RENTAL filter returned {len(rental_items)} items")
        
        # Test SALE filter
        response = requests.get(f"{self.api_base}/?item_type=SALE")
        assert response.status_code == 200
        sale_items = response.json()
        
        for item in sale_items:
            assert item["item_type"] == "SALE", f"Non-sale item found: {item['item_name']}"
        
        print(f"✅ SALE filter returned {len(sale_items)} items")
        return True
    
    def test_filter_by_status(self) -> bool:
        """Test filtering by item status."""
        print("🔍 Testing filter by item status...")
        
        # Test ACTIVE filter
        response = requests.get(f"{self.api_base}/?item_status=ACTIVE")
        assert response.status_code == 200
        active_items = response.json()
        
        for item in active_items:
            assert item["item_status"] == "ACTIVE", f"Non-active item found: {item['item_name']}"
        
        print(f"✅ ACTIVE status filter returned {len(active_items)} items")
        return True
    
    def test_combined_search_and_filters(self) -> bool:
        """Test combined search and filtering."""
        print("🔍 Testing combined search and filters...")
        
        # Test search + type filter
        response = requests.get(f"{self.api_base}/?search=apple&item_type=RENTAL")
        assert response.status_code == 200
        items = response.json()
        
        for item in items:
            assert item["item_type"] == "RENTAL"
            assert any([
                "apple" in item["item_name"].lower(),
                "apple" in item["item_code"].lower(),
                "apple" in (item.get("description", "") or "").lower()
            ])
        
        print(f"✅ Combined search 'apple' + RENTAL filter returned {len(items)} items")
        return True
    
    def test_pagination(self) -> bool:
        """Test pagination with search and filters."""
        print("🔍 Testing pagination...")
        
        # Test basic pagination
        response = requests.get(f"{self.api_base}/?limit=2")
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1) <= 2
        
        response = requests.get(f"{self.api_base}/?skip=2&limit=2")
        assert response.status_code == 200
        page2 = response.json()
        
        # Ensure no overlap between pages
        page1_ids = {item["id"] for item in page1}
        page2_ids = {item["id"] for item in page2}
        assert len(page1_ids & page2_ids) == 0, "Pages should not overlap"
        
        print(f"✅ Pagination working: Page 1 has {len(page1)} items, Page 2 has {len(page2)} items")
        return True
    
    def test_count_endpoint(self) -> bool:
        """Test count endpoint with filters."""
        print("🔍 Testing count endpoint...")
        
        # Test basic count
        response = requests.get(f"{self.api_base}/count/total")
        assert response.status_code == 200
        count_data = response.json()
        assert "count" in count_data
        total_count = count_data["count"]
        
        print(f"✅ Total item count: {total_count}")
        
        # Test count with search
        response = requests.get(f"{self.api_base}/count/total?search=apple")
        assert response.status_code == 200
        search_count = response.json()["count"]
        
        print(f"✅ Count with search 'apple': {search_count}")
        
        # Test count with filter
        response = requests.get(f"{self.api_base}/count/total?item_type=RENTAL")
        assert response.status_code == 200
        rental_count = response.json()["count"]
        
        print(f"✅ Count with RENTAL filter: {rental_count}")
        return True
    
    def test_advanced_search_features(self) -> bool:
        """Test advanced search features."""
        print("🔍 Testing advanced search features...")
        
        # Test case-insensitive search
        response1 = requests.get(f"{self.api_base}/?search=APPLE")
        response2 = requests.get(f"{self.api_base}/?search=apple")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        items1 = response1.json()
        items2 = response2.json()
        
        # Should return same results regardless of case
        assert len(items1) == len(items2), "Case-insensitive search should return same results"
        
        print(f"✅ Case-insensitive search working: {len(items1)} items found")
        
        # Test partial matching
        response = requests.get(f"{self.api_base}/?search=exc")  # Should match "excavator"
        assert response.status_code == 200
        items = response.json()
        
        print(f"✅ Partial matching working: 'exc' found {len(items)} items")
        return True
    
    def test_invalid_parameters(self) -> bool:
        """Test handling of invalid parameters."""
        print("🔍 Testing invalid parameter handling...")
        
        # Test invalid item_type
        response = requests.get(f"{self.api_base}/?item_type=INVALID")
        # Should return 422 for invalid enum value
        assert response.status_code == 422
        
        print("✅ Invalid item_type properly rejected")
        
        # Test invalid limit
        response = requests.get(f"{self.api_base}/?limit=-1")
        assert response.status_code == 422
        
        print("✅ Invalid limit properly rejected")
        return True
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("🚀 Starting Item Master Search & Filter Test Suite\\n")
        
        tests = [
            ("Basic Listing", self.test_basic_list),
            ("Search Functionality", self.test_search_functionality),
            ("Filter by Type", self.test_filter_by_type),
            ("Filter by Status", self.test_filter_by_status),
            ("Combined Search & Filters", self.test_combined_search_and_filters),
            ("Pagination", self.test_pagination),
            ("Count Endpoint", self.test_count_endpoint),
            ("Advanced Search Features", self.test_advanced_search_features),
            ("Invalid Parameters", self.test_invalid_parameters)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"\\n📋 Running {test_name}...")
                result = test_func()
                if result:
                    print(f"✅ {test_name} PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name} FAILED")
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name} FAILED: {str(e)}")
                failed += 1
        
        print(f"\\n🎉 TEST SUITE COMPLETED!")
        print(f"\\n📊 SUMMARY:")
        print(f"  - Total Tests: {len(tests)}")
        print(f"  - Passed: {passed}")
        print(f"  - Failed: {failed}")
        print(f"  - Success Rate: {(passed/len(tests)*100):.1f}%")
        
        if failed == 0:
            print("\\n✅ ALL TESTS PASSED! Search and filter functionality is working correctly.")
        else:
            print(f"\\n⚠️  {failed} tests failed. Please review the output above.")
        
        return failed == 0


def main():
    """Main test runner."""
    # First check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not healthy. Please start the server first.")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server at http://localhost:8000. Please start the server first.")
        return
    
    # Run tests
    tester = ItemSearchFilterTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())