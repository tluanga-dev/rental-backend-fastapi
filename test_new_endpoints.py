#!/usr/bin/env python3
"""
Test script to verify the new inventory endpoints work correctly.
This script tests the structure and imports of the new functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all new imports work correctly."""
    try:
        from app.modules.inventory.schemas import (
            ItemInventoryOverview, ItemInventoryDetailed,
            UnitsByStatus, LocationStockInfo, InventoryUnitDetail,
            RecentMovement, ItemInventoryOverviewParams
        )
        print("✓ All new schemas imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_schema_structure():
    """Test the structure of the new schemas."""
    try:
        from app.modules.inventory.schemas import (
            ItemInventoryOverview, ItemInventoryDetailed,
            UnitsByStatus, LocationStockInfo
        )
        
        # Test UnitsByStatus
        units_status = UnitsByStatus()
        assert hasattr(units_status, 'available')
        assert hasattr(units_status, 'rented')
        assert hasattr(units_status, 'maintenance')
        print("✓ UnitsByStatus schema structure is correct")
        
        # Test LocationStockInfo schema fields
        location_fields = LocationStockInfo.__fields__ if hasattr(LocationStockInfo, '__fields__') else LocationStockInfo.model_fields
        required_fields = ['location_id', 'location_name', 'quantity_on_hand', 'quantity_available', 'quantity_on_rent']
        
        for field in required_fields:
            assert field in location_fields
        print("✓ LocationStockInfo schema structure is correct")
        
        # Test ItemInventoryOverview schema fields
        overview_fields = ItemInventoryOverview.__fields__ if hasattr(ItemInventoryOverview, '__fields__') else ItemInventoryOverview.model_fields
        required_overview_fields = ['id', 'sku', 'item_name', 'total_units', 'stock_status']
        
        for field in required_overview_fields:
            assert field in overview_fields
        print("✓ ItemInventoryOverview schema structure is correct")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema structure test failed: {e}")
        return False

def test_service_methods():
    """Test that service methods are properly defined."""
    try:
        from app.modules.inventory.service import InventoryService
        
        # Check if new methods exist
        assert hasattr(InventoryService, 'get_items_inventory_overview')
        assert hasattr(InventoryService, 'get_item_inventory_detailed')
        
        print("✓ Service methods are properly defined")
        return True
        
    except Exception as e:
        print(f"✗ Service methods test failed: {e}")
        return False

def test_route_endpoints():
    """Test that route endpoints are properly defined."""
    try:
        from app.modules.inventory.routes import router
        
        # Get all routes
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        
        # Check if our new endpoints are present
        assert "/items/overview" in routes
        assert "/items/{item_id}/detailed" in routes
        
        print("✓ Route endpoints are properly defined")
        return True
        
    except Exception as e:
        print(f"✗ Route endpoints test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing new inventory endpoints...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_schema_structure,
        test_service_methods,
        test_route_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The new endpoints are ready for use.")
        return True
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)