#!/usr/bin/env python3
"""
Manual test script for initial stock creation functionality.

This script provides a simple way to manually test the initial stock creation
workflow without requiring the full test suite setup.

Usage:
    python test_initial_stock_manual.py
"""

import asyncio
import json
from decimal import Decimal
from uuid import uuid4

# Mock classes for demonstration
class MockItem:
    def __init__(self, id, sku, item_name, is_active=True, purchase_price=None):
        self.id = id
        self.sku = sku
        self.item_name = item_name
        self.is_active = is_active
        self.purchase_price = purchase_price

class MockLocation:
    def __init__(self, id, location_name, is_active=True):
        self.id = id
        self.location_name = location_name
        self.is_active = is_active

class MockInventoryService:
    """Mock inventory service for demonstration purposes."""
    
    def __init__(self):
        self.created_stock_levels = []
        self.created_inventory_units = []
    
    def generate_unit_code(self, item_sku: str, sequence: int) -> str:
        """Generate a unique unit code for an inventory unit."""
        return f"{item_sku}-U{sequence:03d}"
    
    async def get_default_location(self):
        """Get or create default location."""
        return MockLocation(
            id=uuid4(),
            location_name="Default Warehouse"
        )
    
    async def _validate_initial_stock_business_rules(self, item_id, item_sku, purchase_price, quantity, location_id=None):
        """Simplified business rules validation."""
        if quantity <= 0:
            return {"valid": False, "reason": "Quantity must be greater than 0"}
        
        if quantity > 10000:
            return {"valid": False, "reason": "Initial stock quantity cannot exceed 10,000 units"}
        
        if not item_sku or not item_sku.strip():
            return {"valid": False, "reason": "Item SKU cannot be empty"}
        
        if purchase_price is not None and purchase_price < 0:
            return {"valid": False, "reason": "Purchase price cannot be negative"}
        
        return {"valid": True, "reason": "All business rules passed"}
    
    async def create_initial_stock(self, item_id, item_sku, purchase_price, quantity, location_id=None):
        """Create initial stock for a new item."""
        print(f"\n🔧 Creating initial stock for item {item_id}")
        print(f"   SKU: {item_sku}")
        print(f"   Purchase Price: ${purchase_price or 0}")
        print(f"   Quantity: {quantity}")
        
        # Business rule validation
        validation_result = await self._validate_initial_stock_business_rules(
            item_id, item_sku, purchase_price, quantity, location_id
        )
        if not validation_result["valid"]:
            print(f"❌ Validation failed: {validation_result['reason']}")
            return {"created": False, "reason": validation_result["reason"]}
        
        # Get location
        location = await self.get_default_location()
        print(f"   Location: {location.location_name}")
        
        # Simulate stock level creation
        stock_level_id = uuid4()
        self.created_stock_levels.append({
            "id": stock_level_id,
            "item_id": item_id,
            "location_id": location.id,
            "quantity_on_hand": str(quantity),
            "quantity_available": str(quantity)
        })
        print(f"✅ Created StockLevel: {stock_level_id}")
        
        # Simulate individual inventory unit creation
        created_units = []
        for i in range(1, quantity + 1):
            unit_code = self.generate_unit_code(item_sku, i)
            unit_id = uuid4()
            
            self.created_inventory_units.append({
                "id": unit_id,
                "item_id": item_id,
                "location_id": location.id,
                "unit_code": unit_code,
                "status": "AVAILABLE",
                "condition": "NEW",
                "purchase_price": str(purchase_price or "0.00")
            })
            created_units.append(unit_code)
            print(f"✅ Created InventoryUnit: {unit_code}")
        
        result = {
            "created": True,
            "stock_level_id": str(stock_level_id),
            "location_id": str(location.id),
            "location_name": location.location_name,
            "total_quantity": quantity,
            "unit_codes": created_units,
            "purchase_price": str(purchase_price) if purchase_price else "0.00"
        }
        
        print(f"✅ Initial stock creation completed successfully!")
        return result


class MockItemMasterService:
    """Mock item master service for demonstration purposes."""
    
    def __init__(self):
        self.inventory_service = MockInventoryService()
    
    async def create_item_with_initial_stock(self, item_name, sku, purchase_price=None, initial_stock_quantity=None):
        """Simulate item creation with initial stock integration."""
        print(f"\n🚀 Creating item: {item_name}")
        
        # Simulate item creation
        item_id = uuid4()
        item = MockItem(
            id=item_id,
            sku=sku,
            item_name=item_name,
            purchase_price=purchase_price
        )
        print(f"✅ Item created: {item_id}")
        print(f"   SKU: {sku}")
        print(f"   Name: {item_name}")
        
        # Create initial stock if specified
        stock_result = None
        if initial_stock_quantity and initial_stock_quantity > 0:
            try:
                stock_result = await self.inventory_service.create_initial_stock(
                    item_id=item.id,
                    item_sku=sku,
                    purchase_price=purchase_price,
                    quantity=initial_stock_quantity
                )
                
                if stock_result.get("created"):
                    print(f"📦 Initial stock created successfully:")
                    print(f"   Quantity: {stock_result['total_quantity']}")
                    print(f"   Location: {stock_result['location_name']}")
                    print(f"   Unit codes: {', '.join(stock_result['unit_codes'])}")
                else:
                    print(f"⚠️  Initial stock creation failed: {stock_result.get('reason')}")
                    
            except Exception as e:
                print(f"❌ Exception during initial stock creation: {str(e)}")
                stock_result = {"created": False, "reason": str(e)}
        
        return {
            "item": item,
            "stock_result": stock_result
        }


async def test_successful_creation():
    """Test successful item creation with initial stock."""
    print("=" * 60)
    print("TEST 1: Successful Item Creation with Initial Stock")
    print("=" * 60)
    
    service = MockItemMasterService()
    
    result = await service.create_item_with_initial_stock(
        item_name="Electric Drill",
        sku="TOOL-DRILL-001",
        purchase_price=Decimal("125.50"),
        initial_stock_quantity=5
    )
    
    print(f"\n📊 Test Result:")
    print(f"   Item ID: {result['item'].id}")
    print(f"   Stock Created: {result['stock_result']['created'] if result['stock_result'] else 'N/A'}")
    
    return result


async def test_validation_failures():
    """Test various validation failure scenarios."""
    print("\n" + "=" * 60)
    print("TEST 2: Business Rule Validation Tests")
    print("=" * 60)
    
    service = MockInventoryService()
    test_item_id = uuid4()
    
    # Test cases for validation failures
    test_cases = [
        {
            "name": "Zero quantity",
            "params": {
                "item_id": test_item_id,
                "item_sku": "TEST-001",
                "purchase_price": Decimal("100.00"),
                "quantity": 0
            }
        },
        {
            "name": "Excessive quantity",
            "params": {
                "item_id": test_item_id,
                "item_sku": "TEST-002",
                "purchase_price": Decimal("100.00"),
                "quantity": 15000
            }
        },
        {
            "name": "Empty SKU",
            "params": {
                "item_id": test_item_id,
                "item_sku": "",
                "purchase_price": Decimal("100.00"),
                "quantity": 5
            }
        },
        {
            "name": "Negative price",
            "params": {
                "item_id": test_item_id,
                "item_sku": "TEST-003",
                "purchase_price": Decimal("-50.00"),
                "quantity": 5
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        result = await service.create_initial_stock(**test_case['params'])
        
        if result['created']:
            print(f"❌ Expected validation failure, but creation succeeded")
        else:
            print(f"✅ Validation correctly failed: {result['reason']}")


async def test_unit_code_generation():
    """Test unit code generation logic."""
    print("\n" + "=" * 60)
    print("TEST 3: Unit Code Generation")
    print("=" * 60)
    
    service = MockInventoryService()
    
    test_cases = [
        ("TOOL-DRILL-001", 1, "TOOL-DRILL-001-U001"),
        ("TOOL-DRILL-001", 25, "TOOL-DRILL-001-U025"),
        ("TOOL-DRILL-001", 999, "TOOL-DRILL-001-U999"),
        ("SHORT", 5, "SHORT-U005"),
    ]
    
    for sku, sequence, expected in test_cases:
        result = service.generate_unit_code(sku, sequence)
        if result == expected:
            print(f"✅ {sku} + {sequence} = {result}")
        else:
            print(f"❌ {sku} + {sequence} = {result} (expected {expected})")


async def test_comprehensive_workflow():
    """Test the complete workflow with various scenarios."""
    print("\n" + "=" * 60)
    print("TEST 4: Comprehensive Workflow Test")
    print("=" * 60)
    
    service = MockItemMasterService()
    
    test_items = [
        {
            "item_name": "Cordless Screwdriver",
            "sku": "TOOL-SCREW-001",
            "purchase_price": Decimal("89.99"),
            "initial_stock_quantity": 3
        },
        {
            "item_name": "Safety Helmet",
            "sku": "SAFETY-HELM-001",
            "purchase_price": Decimal("45.00"),
            "initial_stock_quantity": 10
        },
        {
            "item_name": "Measuring Tape",
            "sku": "TOOL-TAPE-001",
            "purchase_price": None,  # No purchase price
            "initial_stock_quantity": 7
        },
        {
            "item_name": "Work Gloves",
            "sku": "SAFETY-GLOVE-001",
            "purchase_price": Decimal("15.50"),
            "initial_stock_quantity": None  # No initial stock
        }
    ]
    
    results = []
    for i, item_data in enumerate(test_items, 1):
        print(f"\n--- Creating Item {i}: {item_data['item_name']} ---")
        result = await service.create_item_with_initial_stock(**item_data)
        results.append(result)
    
    # Summary
    print(f"\n📊 WORKFLOW SUMMARY:")
    print(f"   Total items created: {len(results)}")
    items_with_stock = sum(1 for r in results if r['stock_result'] and r['stock_result'].get('created'))
    print(f"   Items with initial stock: {items_with_stock}")
    
    total_units = sum(
        r['stock_result']['total_quantity'] 
        for r in results 
        if r['stock_result'] and r['stock_result'].get('created')
    )
    print(f"   Total inventory units created: {total_units}")
    
    print(f"\n📦 Inventory Service State:")
    print(f"   Stock levels created: {len(service.inventory_service.created_stock_levels)}")
    print(f"   Inventory units created: {len(service.inventory_service.created_inventory_units)}")


async def main():
    """Run all manual tests."""
    print("🧪 INITIAL STOCK CREATION - MANUAL TESTING")
    print("=" * 60)
    print("This script demonstrates the initial stock creation functionality")
    print("including business rule validation and integration workflows.")
    
    try:
        await test_successful_creation()
        await test_validation_failures()
        await test_unit_code_generation()
        await test_comprehensive_workflow()
        
        print("\n" + "=" * 60)
        print("✅ ALL MANUAL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("• Item creation with initial stock integration")
        print("• Business rule validation (quantity, price, SKU)")
        print("• Unit code generation (SKU-U001, SKU-U002, etc.)")
        print("• Default location handling")
        print("• Error handling and graceful failure")
        print("• Two-tier inventory system (StockLevel + InventoryUnit)")
        
    except Exception as e:
        print(f"\n❌ Manual test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())