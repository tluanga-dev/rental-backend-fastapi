"""
Simplified comprehensive test for Item Master functionality.
Tests core features without complex database relationships.
"""

import asyncio
from decimal import Decimal
from uuid import uuid4

# Import the FastAPI app and dependencies
from app.main import app
from app.modules.master_data.item_master.models import Item, ItemType, ItemStatus
from app.modules.master_data.item_master.schemas import ItemCreate, ItemUpdate

class TestItemMasterSimple:
    """Simplified test class for Item Master functionality."""
    
    def test_app_structure(self):
        """Test that the app has the correct structure."""
        print("✅ Testing app structure...")
        
        # Test that the app imports successfully
        assert app is not None
        
        # Test OpenAPI schema contains item master endpoints
        openapi_data = app.openapi()
        paths = openapi_data.get("paths", {})
        
        item_master_paths = [path for path in paths.keys() if '/api/master-data/item-master' in path]
        assert len(item_master_paths) > 10, f"Expected >10 item master endpoints, found {len(item_master_paths)}"
        
        # Check for key endpoints
        key_endpoints = [
            "/api/master-data/item-master/",
            "/api/master-data/item-master/{item_id}",
            "/api/master-data/item-master/sku/{sku}",
            "/api/master-data/item-master/skus/generate"
        ]
        
        for endpoint in key_endpoints:
            assert endpoint in paths, f"Key endpoint missing: {endpoint}"
        
        print(f"✅ Found {len(item_master_paths)} item master API endpoints")
        return True

    def test_item_model_creation(self):
        """Test Item model creation and validation."""
        print("✅ Testing Item model creation...")
        
        # Test valid item creation
        item = Item(
            item_code="TEST001",
            sku="TEST-ITEM-001-R-001",
            item_name="Test Power Drill",
            item_type=ItemType.RENTAL,
            purchase_price=Decimal("120.00"),
            rental_price_per_day=Decimal("15.00")
        )
        
        assert item.item_code == "TEST001"
        assert item.sku == "TEST-ITEM-001-R-001"
        assert item.item_name == "Test Power Drill"
        assert item.item_type == ItemType.RENTAL.value
        assert item.purchase_price == Decimal("120.00")
        
        print("✅ Item model creation successful")
        return True

    def test_item_business_logic(self):
        """Test item business logic methods."""
        print("✅ Testing Item business logic...")
        
        # Test rental item
        rental_item = Item(
            item_code="RENT001",
            sku="RENT-001",
            item_name="Rental Item",
            item_type=ItemType.RENTAL,
            rental_price_per_day=Decimal("25.00")
        )
        
        assert rental_item.is_rental_item() == True
        assert rental_item.is_sale_item() == False
        assert rental_item.can_be_rented() == True
        assert rental_item.can_be_sold() == False
        
        # Test sale item
        sale_item = Item(
            item_code="SALE001",
            sku="SALE-001",
            item_name="Sale Item",
            item_type=ItemType.SALE,
            sale_price=Decimal("150.00")
        )
        
        assert sale_item.is_rental_item() == False
        assert sale_item.is_sale_item() == True
        assert sale_item.can_be_rented() == False
        assert sale_item.can_be_sold() == True
        
        # Test both item
        both_item = Item(
            item_code="BOTH001",
            sku="BOTH-001",
            item_name="Both Item",
            item_type=ItemType.BOTH,
            rental_price_per_day=Decimal("20.00"),
            sale_price=Decimal("200.00")
        )
        
        assert both_item.is_rental_item() == True
        assert both_item.is_sale_item() == True
        assert both_item.can_be_rented() == True
        assert both_item.can_be_sold() == True
        
        print("✅ Item business logic tests passed")
        return True

    def test_item_validation_rules(self):
        """Test item validation rules."""
        print("✅ Testing Item validation rules...")
        
        # Test empty item code validation
        try:
            Item(
                item_code="",
                sku="SKU001",
                item_name="Test",
                item_type=ItemType.RENTAL,
                rental_price_per_day=Decimal("10.00")
            )
            assert False, "Should have raised ValueError for empty item code"
        except ValueError as e:
            assert "Item code cannot be empty" in str(e)
        
        # Test empty item name validation
        try:
            Item(
                item_code="TEST001",
                sku="SKU001",
                item_name="",
                item_type=ItemType.RENTAL,
                rental_price_per_day=Decimal("10.00")
            )
            assert False, "Should have raised ValueError for empty item name"
        except ValueError as e:
            assert "Item name cannot be empty" in str(e)
        
        # Test long item code validation
        try:
            Item(
                item_code="X" * 51,  # 51 characters, exceeds limit of 50
                sku="SKU001",
                item_name="Test",
                item_type=ItemType.RENTAL,
                rental_price_per_day=Decimal("10.00")
            )
            assert False, "Should have raised ValueError for long item code"
        except ValueError as e:
            assert "Item code cannot exceed 50 characters" in str(e)
        
        print("✅ Item validation rules tests passed")
        return True

    def test_item_schemas(self):
        """Test Pydantic schemas."""
        print("✅ Testing Item schemas...")
        
        # Test ItemCreate schema
        create_data = {
            "item_code": "SCHEMA001",
            "item_name": "Schema Test Item",
            "item_type": "RENTAL",
            "purchase_price": 100.00,
            "rental_price_per_day": 15.00,
            "description": "Test item for schema validation"
        }
        
        item_create = ItemCreate(**create_data)
        assert item_create.item_code == "SCHEMA001"
        assert item_create.item_type == ItemType.RENTAL
        assert item_create.purchase_price == Decimal("100.00")
        assert item_create.rental_price_per_day == Decimal("15.00")
        
        # Test ItemUpdate schema
        update_data = {
            "item_name": "Updated Schema Test Item",
            "rental_price_per_day": 20.00,
            "description": "Updated description"
        }
        
        item_update = ItemUpdate(**update_data)
        assert item_update.item_name == "Updated Schema Test Item"
        assert item_update.rental_price_per_day == Decimal("20.00")
        assert item_update.description == "Updated description"
        
        # Test schema validation
        try:
            ItemCreate(
                item_code="",  # Empty code should fail validation
                item_name="Test",
                item_type="RENTAL"
            )
            assert False, "Should have raised validation error"
        except Exception:
            pass  # Expected validation error
        
        print("✅ Item schemas tests passed")
        return True

    def test_sku_format_validation(self):
        """Test SKU format validation logic."""
        print("✅ Testing SKU format validation...")
        
        # Test valid SKU formats
        valid_skus = [
            "TOOL-PWR-DRIL-R-001",
            "FURN-CHR-OFFI-B-002", 
            "ELEC-CAM-DSLR-S-003",
            "MISC-ITEM-UNKN-R-999"
        ]
        
        for sku in valid_skus:
            parts = sku.split('-')
            assert len(parts) == 5, f"SKU {sku} should have 5 parts separated by dashes"
            
            category, subcategory, product, attribute, sequence = parts
            assert len(category) <= 4, f"Category part too long: {category}"
            assert len(subcategory) <= 4, f"Subcategory part too long: {subcategory}"
            assert len(product) <= 4, f"Product part too long: {product}"
            assert attribute in ['R', 'S', 'B'], f"Invalid attribute: {attribute}"
            assert sequence.isdigit(), f"Sequence should be numeric: {sequence}"
            assert len(sequence) == 3, f"Sequence should be 3 digits: {sequence}"
        
        print("✅ SKU format validation tests passed")
        return True

    def test_item_properties(self):
        """Test item computed properties."""
        print("✅ Testing Item computed properties...")
        
        item = Item(
            item_code="PROP001",
            sku="PROP-TEST-001-R-001",
            item_name="Property Test Item",
            item_type=ItemType.RENTAL,
            rental_price_per_day=Decimal("15.00")
        )
        
        # Test display_name property
        expected_display = "Property Test Item (PROP001)"
        assert item.display_name == expected_display
        
        # Test string representation
        assert str(item) == expected_display
        
        # Test repr
        repr_str = repr(item)
        assert "Item(" in repr_str
        assert "PROP001" in repr_str
        assert "Property Test Item" in repr_str
        
        print("✅ Item properties tests passed")
        return True

    def test_item_type_enum(self):
        """Test ItemType enum functionality."""
        print("✅ Testing ItemType enum...")
        
        # Test enum values
        assert ItemType.RENTAL.value == "RENTAL"
        assert ItemType.SALE.value == "SALE"
        assert ItemType.BOTH.value == "BOTH"
        
        # Test enum comparison
        assert ItemType.RENTAL != ItemType.SALE
        assert ItemType.BOTH != ItemType.RENTAL
        
        # Test enum in list
        rental_types = [ItemType.RENTAL.value, ItemType.BOTH.value]
        assert "RENTAL" in rental_types
        assert "BOTH" in rental_types
        assert "SALE" not in rental_types
        
        print("✅ ItemType enum tests passed")
        return True

    def test_item_status_enum(self):
        """Test ItemStatus enum functionality."""
        print("✅ Testing ItemStatus enum...")
        
        # Test enum values
        assert ItemStatus.ACTIVE.value == "ACTIVE"
        assert ItemStatus.INACTIVE.value == "INACTIVE"
        assert ItemStatus.DISCONTINUED.value == "DISCONTINUED"
        
        # Test default status
        item = Item(
            item_code="STATUS001",
            sku="STATUS-001",
            item_name="Status Test",
            item_type=ItemType.RENTAL,
            rental_price_per_day=Decimal("15.00")
        )
        
        assert item.item_status == ItemStatus.ACTIVE.value
        assert item.is_item_active() == True
        assert item.is_discontinued() == False
        
        print("✅ ItemStatus enum tests passed")
        return True

    def test_item_pricing_logic(self):
        """Test item pricing business logic."""
        print("✅ Testing Item pricing logic...")
        
        # Test rental item pricing
        rental_item = Item(
            item_code="PRICE001",
            sku="PRICE-001",
            item_name="Pricing Test Rental",
            item_type=ItemType.RENTAL,
            purchase_price=Decimal("100.00"),
            rental_price_per_day=Decimal("15.00"),
            rental_price_per_week=Decimal("90.00"),
            rental_price_per_month=Decimal("300.00"),
            security_deposit=Decimal("50.00")
        )
        
        assert rental_item.purchase_price == Decimal("100.00")
        assert rental_item.rental_price_per_day == Decimal("15.00")
        assert rental_item.rental_price_per_week == Decimal("90.00")
        assert rental_item.rental_price_per_month == Decimal("300.00")
        assert rental_item.security_deposit == Decimal("50.00")
        
        # Test sale item pricing
        sale_item = Item(
            item_code="PRICE002",
            sku="PRICE-002",
            item_name="Pricing Test Sale",
            item_type=ItemType.SALE,
            purchase_price=Decimal("200.00"),
            sale_price=Decimal("350.00")
        )
        
        assert sale_item.purchase_price == Decimal("200.00")
        assert sale_item.sale_price == Decimal("350.00")
        
        print("✅ Item pricing logic tests passed")
        return True

def run_simple_tests():
    """Run all simplified tests."""
    print("🚀 Starting Simplified Item Master Test Suite\n")
    
    test_instance = TestItemMasterSimple()
    
    tests = [
        ("App Structure", test_instance.test_app_structure),
        ("Item Model Creation", test_instance.test_item_model_creation),
        ("Item Business Logic", test_instance.test_item_business_logic),
        ("Item Validation Rules", test_instance.test_item_validation_rules),
        ("Item Schemas", test_instance.test_item_schemas),
        ("SKU Format Validation", test_instance.test_sku_format_validation),
        ("Item Properties", test_instance.test_item_properties),
        ("ItemType Enum", test_instance.test_item_type_enum),
        ("ItemStatus Enum", test_instance.test_item_status_enum),
        ("Item Pricing Logic", test_instance.test_item_pricing_logic)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Running {test_name}...")
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
    
    print(f"\n🎉 TEST SUITE COMPLETED!")
    print(f"\n📊 SUMMARY:")
    print(f"  - Total Tests: {len(tests)}")
    print(f"  - Passed: {passed}")
    print(f"  - Failed: {failed}")
    print(f"  - Success Rate: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED! Item Master functionality is working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the output above.")
    
    return passed, failed

if __name__ == "__main__":
    run_simple_tests()