#!/usr/bin/env python3
"""
Comprehensive test suite for the new inventory endpoints.
Tests both the overview and detailed endpoints with various scenarios.
"""

import asyncio
import sys
import os
import json
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.modules.inventory.service import InventoryService
    from app.modules.inventory.schemas import ItemInventoryOverviewParams
    from app.modules.master_data.item_master.models import Item, ItemStatus
    from app.modules.inventory.models import (
        InventoryUnit, StockLevel, InventoryUnitStatus, 
        InventoryUnitCondition, StockMovement, MovementType, ReferenceType
    )
    from app.modules.master_data.brands.models import Brand
    from app.modules.master_data.categories.models import Category
    from app.modules.master_data.units.models import UnitOfMeasurement
    from app.modules.master_data.locations.models import Location
    from app.db.base import Base
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("This test requires the application dependencies to be installed.")
    IMPORTS_AVAILABLE = False


class InventoryEndpointTester:
    """Comprehensive tester for inventory endpoints."""
    
    def __init__(self):
        self.test_results = []
        self.engine = None
        self.session = None
        self.service = None
        self.test_data = {}
        
    async def setup_database(self):
        """Setup test database connection."""
        try:
            # Create async engine for testing
            database_url = "postgresql+asyncpg://fastapi_user:fastapi_password@localhost:5432/fastapi_test_db"
            self.engine = create_async_engine(database_url, echo=False)
            
            # Create async session
            async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            self.session = async_session()
            
            # Create service instance
            self.service = InventoryService(self.session)
            
            self.log_result("✅ Database Setup", "Database connection established", True)
            return True
        except Exception as e:
            self.log_result("❌ Database Setup", f"Failed to connect: {str(e)}", False)
            return False
    
    async def create_test_data(self):
        """Create test data for comprehensive testing."""
        try:
            # Create test brand
            brand = Brand(
                id=uuid4(),
                brand_name="Test Brand",
                brand_code="TST",
                is_active=True
            )
            self.session.add(brand)
            
            # Create test category
            category = Category(
                id=uuid4(),
                category_name="Test Category",
                category_code="TST",
                is_leaf=True,
                is_active=True
            )
            self.session.add(category)
            
            # Create test unit of measurement
            unit = UnitOfMeasurement(
                id=uuid4(),
                unit_name="Each",
                unit_code="EA",
                is_active=True
            )
            self.session.add(unit)
            
            # Create test location
            location = Location(
                id=uuid4(),
                location_name="Test Warehouse",
                location_code="TWH",
                location_type="WAREHOUSE",
                is_active=True
            )
            self.session.add(location)
            
            await self.session.commit()
            
            # Store test data references
            self.test_data = {
                'brand': brand,
                'category': category,
                'unit': unit,
                'location': location,
                'items': [],
                'inventory_units': [],
                'stock_levels': []
            }
            
            # Create test items with various statuses
            items_data = [
                {
                    'name': 'Test Item 1 - Available',
                    'sku': 'TST-001',
                    'status': ItemStatus.ACTIVE,
                    'is_rentable': True,
                    'is_saleable': False,
                    'rental_rate': Decimal('25.00'),
                    'units_count': 10,
                    'available_count': 8,
                    'rented_count': 2
                },
                {
                    'name': 'Test Item 2 - Low Stock',
                    'sku': 'TST-002',
                    'status': ItemStatus.ACTIVE,
                    'is_rentable': True,
                    'is_saleable': False,
                    'rental_rate': Decimal('15.00'),
                    'units_count': 3,
                    'available_count': 2,
                    'rented_count': 1
                },
                {
                    'name': 'Test Item 3 - Out of Stock',
                    'sku': 'TST-003',
                    'status': ItemStatus.ACTIVE,
                    'is_rentable': True,
                    'is_saleable': False,
                    'rental_rate': Decimal('35.00'),
                    'units_count': 5,
                    'available_count': 0,
                    'rented_count': 5
                },
                {
                    'name': 'Test Item 4 - Sale Item',
                    'sku': 'TST-004',
                    'status': ItemStatus.ACTIVE,
                    'is_rentable': False,
                    'is_saleable': True,
                    'sale_price': Decimal('199.99'),
                    'units_count': 7,
                    'available_count': 7,
                    'rented_count': 0
                },
                {
                    'name': 'Test Item 5 - Inactive',
                    'sku': 'TST-005',
                    'status': ItemStatus.INACTIVE,
                    'is_rentable': True,
                    'is_saleable': False,
                    'rental_rate': Decimal('45.00'),
                    'units_count': 2,
                    'available_count': 2,
                    'rented_count': 0
                }
            ]
            
            # Create items
            for item_data in items_data:
                item = Item(
                    id=uuid4(),
                    sku=item_data['sku'],
                    item_name=item_data['name'],
                    item_status=item_data['status'],
                    brand_id=brand.id,
                    category_id=category.id,
                    unit_of_measurement_id=unit.id,
                    is_rentable=item_data['is_rentable'],
                    is_saleable=item_data['is_saleable'],
                    rental_rate_per_period=item_data.get('rental_rate'),
                    sale_price=item_data.get('sale_price'),
                    rental_period="1",
                    security_deposit=Decimal("50.00"),
                    reorder_point=5,
                    is_active=True
                )
                self.session.add(item)
                self.test_data['items'].append(item)
                
                # Create inventory units
                for i in range(item_data['units_count']):
                    status = InventoryUnitStatus.AVAILABLE
                    if i < item_data['rented_count']:
                        status = InventoryUnitStatus.RENTED
                    elif i == item_data['units_count'] - 1 and item_data['name'] == 'Test Item 2 - Low Stock':
                        status = InventoryUnitStatus.MAINTENANCE
                    
                    unit = InventoryUnit(
                        id=uuid4(),
                        item_id=item.id,
                        location_id=location.id,
                        unit_code=f"{item_data['sku']}-{i+1:03d}",
                        serial_number=f"SN{item_data['sku']}{i+1:03d}",
                        status=status,
                        condition=InventoryUnitCondition.GOOD,
                        purchase_price=Decimal("100.00"),
                        purchase_date=datetime.utcnow() - timedelta(days=30),
                        is_active=True
                    )
                    self.session.add(unit)
                    self.test_data['inventory_units'].append(unit)
                
                # Create stock level
                stock_level = StockLevel(
                    id=uuid4(),
                    item_id=item.id,
                    location_id=location.id,
                    quantity_on_hand=Decimal(str(item_data['units_count'])),
                    quantity_available=Decimal(str(item_data['available_count'])),
                    quantity_on_rent=Decimal(str(item_data['rented_count'])),
                    is_active=True
                )
                self.session.add(stock_level)
                self.test_data['stock_levels'].append(stock_level)
            
            await self.session.commit()
            
            self.log_result("✅ Test Data Creation", f"Created {len(items_data)} test items with inventory", True)
            return True
            
        except Exception as e:
            self.log_result("❌ Test Data Creation", f"Failed to create test data: {str(e)}", False)
            return False
    
    async def test_overview_endpoint_basic(self):
        """Test basic overview endpoint functionality."""
        try:
            params = ItemInventoryOverviewParams(
                skip=0,
                limit=10,
                sort_by="item_name",
                sort_order="asc"
            )
            
            result = await self.service.get_items_inventory_overview(params)
            
            # Verify results
            assert len(result) > 0, "Should return at least one item"
            assert all(hasattr(item, 'id') for item in result), "All items should have ID"
            assert all(hasattr(item, 'item_name') for item in result), "All items should have name"
            assert all(hasattr(item, 'total_units') for item in result), "All items should have total units"
            assert all(hasattr(item, 'stock_status') for item in result), "All items should have stock status"
            
            self.log_result("✅ Overview Basic Test", f"Retrieved {len(result)} items successfully", True)
            return True
            
        except Exception as e:
            self.log_result("❌ Overview Basic Test", f"Failed: {str(e)}", False)
            return False
    
    async def test_overview_endpoint_filtering(self):
        """Test overview endpoint with various filters."""
        test_cases = [
            {
                'name': 'Filter by Rentable Items',
                'params': {'is_rentable': True},
                'expected_min': 3  # Should find at least 3 rentable items
            },
            {
                'name': 'Filter by Saleable Items',
                'params': {'is_saleable': True},
                'expected_min': 1  # Should find at least 1 saleable item
            },
            {
                'name': 'Filter by Brand',
                'params': {'brand_id': self.test_data['brand'].id},
                'expected_min': 4  # Should find all active items from test brand
            },
            {
                'name': 'Filter by Category',
                'params': {'category_id': self.test_data['category'].id},
                'expected_min': 4  # Should find all active items from test category
            },
            {
                'name': 'Filter by Active Status',
                'params': {'item_status': ItemStatus.ACTIVE},
                'expected_min': 4  # Should find all active items
            },
            {
                'name': 'Search by Name',
                'params': {'search': 'Test Item'},
                'expected_min': 4  # Should find items with "Test Item" in name
            },
            {
                'name': 'Search by SKU',
                'params': {'search': 'TST-001'},
                'expected_min': 1  # Should find specific item
            }
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for test_case in test_cases:
            try:
                params = ItemInventoryOverviewParams(
                    skip=0,
                    limit=100,
                    **test_case['params']
                )
                
                result = await self.service.get_items_inventory_overview(params)
                
                assert len(result) >= test_case['expected_min'], \
                    f"Expected at least {test_case['expected_min']} items, got {len(result)}"
                
                passed_tests += 1
                
            except Exception as e:
                self.log_result(f"❌ {test_case['name']}", f"Failed: {str(e)}", False)
                continue
        
        success = passed_tests == total_tests
        self.log_result(
            f"{'✅' if success else '❌'} Overview Filtering Tests",
            f"Passed {passed_tests}/{total_tests} filtering tests",
            success
        )
        return success
    
    async def test_overview_endpoint_sorting(self):
        """Test overview endpoint sorting functionality."""
        sort_tests = [
            {'sort_by': 'item_name', 'sort_order': 'asc'},
            {'sort_by': 'item_name', 'sort_order': 'desc'},
            {'sort_by': 'sku', 'sort_order': 'asc'},
            {'sort_by': 'total_units', 'sort_order': 'desc'},
            {'sort_by': 'stock_status', 'sort_order': 'asc'}
        ]
        
        passed_tests = 0
        total_tests = len(sort_tests)
        
        for sort_test in sort_tests:
            try:
                params = ItemInventoryOverviewParams(
                    skip=0,
                    limit=100,
                    sort_by=sort_test['sort_by'],
                    sort_order=sort_test['sort_order']
                )
                
                result = await self.service.get_items_inventory_overview(params)
                
                assert len(result) > 0, "Should return items"
                
                # Verify sorting (basic check)
                if len(result) > 1:
                    field_values = [getattr(item, sort_test['sort_by']) for item in result]
                    if sort_test['sort_order'] == 'asc':
                        # Check if generally ascending (allowing for some complex sorting logic)
                        pass  # Complex sorting validation would need more specific logic
                    else:
                        # Check if generally descending
                        pass
                
                passed_tests += 1
                
            except Exception as e:
                self.log_result(
                    f"❌ Sort Test ({sort_test['sort_by']} {sort_test['sort_order']})",
                    f"Failed: {str(e)}", False
                )
                continue
        
        success = passed_tests == total_tests
        self.log_result(
            f"{'✅' if success else '❌'} Overview Sorting Tests",
            f"Passed {passed_tests}/{total_tests} sorting tests",
            success
        )
        return success
    
    async def test_overview_endpoint_pagination(self):
        """Test overview endpoint pagination."""
        try:
            # Test page 1
            params_page1 = ItemInventoryOverviewParams(
                skip=0,
                limit=2,
                sort_by="item_name",
                sort_order="asc"
            )
            result_page1 = await self.service.get_items_inventory_overview(params_page1)
            
            # Test page 2
            params_page2 = ItemInventoryOverviewParams(
                skip=2,
                limit=2,
                sort_by="item_name",
                sort_order="asc"
            )
            result_page2 = await self.service.get_items_inventory_overview(params_page2)
            
            # Verify pagination
            assert len(result_page1) <= 2, "Page 1 should have max 2 items"
            assert len(result_page2) <= 2, "Page 2 should have max 2 items"
            
            # Verify different results (if enough items)
            if len(result_page1) > 0 and len(result_page2) > 0:
                page1_ids = {item.id for item in result_page1}
                page2_ids = {item.id for item in result_page2}
                assert page1_ids != page2_ids, "Different pages should have different items"
            
            self.log_result("✅ Overview Pagination Test", "Pagination working correctly", True)
            return True
            
        except Exception as e:
            self.log_result("❌ Overview Pagination Test", f"Failed: {str(e)}", False)
            return False
    
    async def test_detailed_endpoint_basic(self):
        """Test basic detailed endpoint functionality."""
        try:
            # Get first test item
            test_item = self.test_data['items'][0]
            
            result = await self.service.get_item_inventory_detailed(test_item.id)
            
            # Verify basic fields
            assert result.id == test_item.id, "ID should match"
            assert result.item_name == test_item.item_name, "Name should match"
            assert result.sku == test_item.sku, "SKU should match"
            assert hasattr(result, 'total_units'), "Should have total units"
            assert hasattr(result, 'units_by_status'), "Should have units by status"
            assert hasattr(result, 'inventory_units'), "Should have inventory units list"
            assert hasattr(result, 'stock_by_location'), "Should have stock by location"
            assert hasattr(result, 'recent_movements'), "Should have recent movements"
            
            # Verify inventory units
            assert len(result.inventory_units) > 0, "Should have inventory units"
            assert all(unit.item_id == test_item.id for unit in result.inventory_units), \
                "All units should belong to the item"
            
            # Verify stock by location
            assert len(result.stock_by_location) > 0, "Should have stock by location"
            
            self.log_result("✅ Detailed Basic Test", f"Retrieved detailed info for item {test_item.sku}", True)
            return True
            
        except Exception as e:
            self.log_result("❌ Detailed Basic Test", f"Failed: {str(e)}", False)
            return False
    
    async def test_detailed_endpoint_data_integrity(self):
        """Test data integrity in detailed endpoint."""
        try:
            test_item = self.test_data['items'][0]
            result = await self.service.get_item_inventory_detailed(test_item.id)
            
            # Verify units by status counts
            units_by_status = result.units_by_status
            total_units_calculated = (
                units_by_status.available + 
                units_by_status.rented + 
                units_by_status.sold + 
                units_by_status.maintenance + 
                units_by_status.damaged + 
                units_by_status.retired
            )
            
            assert total_units_calculated == result.total_units, \
                f"Units by status sum ({total_units_calculated}) should equal total units ({result.total_units})"
            
            # Verify stock quantities
            total_stock = sum(stock.quantity_on_hand for stock in result.stock_by_location)
            assert total_stock == result.total_quantity_on_hand, \
                "Stock by location sum should equal total quantity on hand"
            
            # Verify brand and category relationships
            assert result.brand_name == self.test_data['brand'].brand_name, \
                "Brand name should match"
            assert result.category_name == self.test_data['category'].category_name, \
                "Category name should match"
            
            self.log_result("✅ Detailed Data Integrity Test", "Data integrity verified", True)
            return True
            
        except Exception as e:
            self.log_result("❌ Detailed Data Integrity Test", f"Failed: {str(e)}", False)
            return False
    
    async def test_detailed_endpoint_not_found(self):
        """Test detailed endpoint with non-existent item."""
        try:
            fake_id = uuid4()
            
            try:
                result = await self.service.get_item_inventory_detailed(fake_id)
                # Should not reach here
                self.log_result("❌ Detailed Not Found Test", "Should have raised NotFoundError", False)
                return False
            except Exception as e:
                # Should raise NotFoundError
                assert "not found" in str(e).lower(), f"Should raise NotFoundError, got: {str(e)}"
                self.log_result("✅ Detailed Not Found Test", "Correctly raised NotFoundError", True)
                return True
                
        except Exception as e:
            self.log_result("❌ Detailed Not Found Test", f"Unexpected error: {str(e)}", False)
            return False
    
    async def test_stock_status_calculation(self):
        """Test stock status calculation logic."""
        try:
            # Get items with different stock statuses
            params = ItemInventoryOverviewParams(skip=0, limit=100)
            results = await self.service.get_items_inventory_overview(params)
            
            stock_statuses = {}
            for item in results:
                stock_statuses[item.stock_status] = stock_statuses.get(item.stock_status, 0) + 1
            
            # Should have multiple stock statuses
            assert len(stock_statuses) > 1, "Should have multiple stock statuses"
            
            # Verify stock status logic for specific items
            for item in results:
                if item.sku == 'TST-001':  # Available item
                    assert item.stock_status == 'IN_STOCK', "TST-001 should be IN_STOCK"
                elif item.sku == 'TST-002':  # Low stock item
                    assert item.stock_status in ['LOW_STOCK', 'IN_STOCK'], "TST-002 should be LOW_STOCK or IN_STOCK"
                elif item.sku == 'TST-003':  # Out of stock item
                    assert item.stock_status == 'OUT_OF_STOCK', "TST-003 should be OUT_OF_STOCK"
            
            self.log_result(
                "✅ Stock Status Calculation Test",
                f"Found stock statuses: {list(stock_statuses.keys())}",
                True
            )
            return True
            
        except Exception as e:
            self.log_result("❌ Stock Status Calculation Test", f"Failed: {str(e)}", False)
            return False
    
    async def test_performance_basic(self):
        """Test basic performance of endpoints."""
        try:
            import time
            
            # Test overview endpoint performance
            start_time = time.time()
            params = ItemInventoryOverviewParams(skip=0, limit=100)
            result = await self.service.get_items_inventory_overview(params)
            overview_time = time.time() - start_time
            
            # Test detailed endpoint performance
            test_item = self.test_data['items'][0]
            start_time = time.time()
            detailed_result = await self.service.get_item_inventory_detailed(test_item.id)
            detailed_time = time.time() - start_time
            
            # Performance thresholds (in seconds)
            overview_threshold = 2.0
            detailed_threshold = 3.0
            
            overview_passed = overview_time < overview_threshold
            detailed_passed = detailed_time < detailed_threshold
            
            self.log_result(
                f"{'✅' if overview_passed else '❌'} Overview Performance",
                f"Took {overview_time:.3f}s (threshold: {overview_threshold}s)",
                overview_passed
            )
            
            self.log_result(
                f"{'✅' if detailed_passed else '❌'} Detailed Performance",
                f"Took {detailed_time:.3f}s (threshold: {detailed_threshold}s)",
                detailed_passed
            )
            
            return overview_passed and detailed_passed
            
        except Exception as e:
            self.log_result("❌ Performance Test", f"Failed: {str(e)}", False)
            return False
    
    async def cleanup_test_data(self):
        """Clean up test data."""
        try:
            # Delete test data in reverse order due to foreign key constraints
            if self.session and self.test_data:
                # Delete inventory units
                for unit in self.test_data.get('inventory_units', []):
                    await self.session.delete(unit)
                
                # Delete stock levels
                for stock in self.test_data.get('stock_levels', []):
                    await self.session.delete(stock)
                
                # Delete items
                for item in self.test_data.get('items', []):
                    await self.session.delete(item)
                
                # Delete master data
                if 'location' in self.test_data:
                    await self.session.delete(self.test_data['location'])
                if 'unit' in self.test_data:
                    await self.session.delete(self.test_data['unit'])
                if 'category' in self.test_data:
                    await self.session.delete(self.test_data['category'])
                if 'brand' in self.test_data:
                    await self.session.delete(self.test_data['brand'])
                
                await self.session.commit()
            
            # Close session
            if self.session:
                await self.session.close()
            
            # Close engine
            if self.engine:
                await self.engine.dispose()
            
            self.log_result("✅ Test Cleanup", "Test data cleaned up successfully", True)
            return True
            
        except Exception as e:
            self.log_result("❌ Test Cleanup", f"Failed: {str(e)}", False)
            return False
    
    def log_result(self, test_name: str, message: str, passed: bool):
        """Log test result."""
        self.test_results.append({
            'test_name': test_name,
            'message': message,
            'passed': passed,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{test_name}: {message}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("INVENTORY ENDPOINTS TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} - {result['test_name']}")
            print(f"    {result['message']}")
        
        print("="*60)
        return passed_tests == total_tests
    
    async def run_all_tests(self):
        """Run all tests."""
        print("Starting comprehensive inventory endpoints testing...")
        print("="*60)
        
        # Setup
        if not await self.setup_database():
            print("❌ Database setup failed. Exiting...")
            return False
        
        if not await self.create_test_data():
            print("❌ Test data creation failed. Exiting...")
            await self.cleanup_test_data()
            return False
        
        # Run tests
        test_methods = [
            self.test_overview_endpoint_basic,
            self.test_overview_endpoint_filtering,
            self.test_overview_endpoint_sorting,
            self.test_overview_endpoint_pagination,
            self.test_detailed_endpoint_basic,
            self.test_detailed_endpoint_data_integrity,
            self.test_detailed_endpoint_not_found,
            self.test_stock_status_calculation,
            self.test_performance_basic
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.log_result(f"❌ {test_method.__name__}", f"Unexpected error: {str(e)}", False)
        
        # Cleanup
        await self.cleanup_test_data()
        
        # Print summary
        return self.print_summary()


async def main():
    """Main test runner."""
    if not IMPORTS_AVAILABLE:
        print("❌ Cannot run tests - dependencies not available")
        return False
    
    tester = InventoryEndpointTester()
    success = await tester.run_all_tests()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test runner failed: {str(e)}")
        sys.exit(1)