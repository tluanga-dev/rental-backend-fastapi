#!/usr/bin/env python3
"""
Simple test script to verify purchase CRUD functionality.
"""

import asyncio
import sys
from decimal import Decimal
from datetime import date
from uuid import uuid4

# Add the app directory to the path
sys.path.insert(0, '/app')

from app.core.database import get_db
from app.modules.transactions.purchase.service import PurchaseService
from app.modules.transactions.purchase.schemas import NewPurchaseRequest, PurchaseItemCreate
from app.modules.suppliers.models import Supplier
from app.modules.master_data.locations.models import Location
from app.modules.master_data.item_master.models import Item
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.categories.models import Category
from app.modules.master_data.units.models import UnitOfMeasurement
from app.modules.inventory.models import StockLevel


async def test_purchase_service():
    """Test purchase service functionality directly."""
    print("Testing Purchase Service...")
    
    # Get database session
    async for session in get_db():
        try:
            # Create test data
            print("Creating test data...")
            
            # Create supplier
            supplier = Supplier(
                supplier_code="TEST001",
                company_name="Test Supplier",
                supplier_type="MANUFACTURER",
                contact_person="John Doe",
                email="test@supplier.com"
            )
            session.add(supplier)
            await session.flush()
            print(f"Created supplier: {supplier.id}")
            
            # Create location
            location = Location(
                location_code="LOC001",
                location_name="Test Location",
                location_type="WAREHOUSE"
            )
            session.add(location)
            await session.flush()
            print(f"Created location: {location.id}")
            
            # Create supporting data
            brand = Brand(
                brand_code="BR001",
                brand_name="Test Brand"
            )
            session.add(brand)
            await session.flush()
            
            category = Category(
                category_code="CAT001",
                category_name="Test Category"
            )
            session.add(category)
            await session.flush()
            
            unit = UnitOfMeasurement(
                unit_code="PCS",
                unit_name="Pieces",
                unit_symbol="pcs"
            )
            session.add(unit)
            await session.flush()
            
            # Create item
            item = Item(
                item_code="ITEM001",
                item_name="Test Item",
                description="Test item description",
                brand_id=brand.id,
                category_id=category.id,
                unit_id=unit.id,
                unit_cost=Decimal("10.00"),
                selling_price=Decimal("15.00")
            )
            session.add(item)
            await session.flush()
            print(f"Created item: {item.id}")
            
            # Create initial stock level
            stock = StockLevel(
                item_id=item.id,
                location_id=location.id,
                available_quantity=Decimal("100"),
                reserved_quantity=Decimal("0"),
                on_order_quantity=Decimal("0"),
                minimum_quantity=Decimal("10"),
                maximum_quantity=Decimal("1000")
            )
            session.add(stock)
            await session.commit()
            
            # Test purchase service
            print("Testing purchase service...")
            purchase_service = PurchaseService(session)
            
            # Create purchase request
            purchase_request = NewPurchaseRequest(
                supplier_id=str(supplier.id),
                location_id=str(location.id),
                purchase_date=date.today().isoformat(),
                notes="Test purchase",
                reference_number="PO-TEST-001",
                items=[
                    PurchaseItemCreate(
                        item_id=str(item.id),
                        quantity=10,
                        unit_cost=Decimal("12.50"),
                        tax_rate=Decimal("10.0"),
                        discount_amount=Decimal("0.00"),
                        condition="A",
                        notes="Test item"
                    )
                ]
            )
            
            # Create purchase
            print("Creating purchase...")
            result = await purchase_service.create_new_purchase(purchase_request)
            
            print(f"Purchase created successfully!")
            print(f"Transaction ID: {result.transaction_id}")
            print(f"Transaction Number: {result.transaction_number}")
            print(f"Success: {result.success}")
            print(f"Message: {result.message}")
            
            # Test getting purchase by ID
            print("Testing get purchase by ID...")
            purchase_detail = await purchase_service.get_purchase_by_id(result.transaction_id)
            
            print(f"Retrieved purchase: {purchase_detail.id}")
            print(f"Supplier: {purchase_detail.supplier['name'] if purchase_detail.supplier else 'None'}")
            print(f"Location: {purchase_detail.location['name'] if purchase_detail.location else 'None'}")
            print(f"Total Amount: {purchase_detail.total_amount}")
            print(f"Items Count: {len(purchase_detail.items)}")
            
            # Test getting purchases list
            print("Testing get purchases list...")
            purchases_list = await purchase_service.get_purchase_transactions(limit=10)
            
            print(f"Found {len(purchases_list)} purchases")
            for purchase in purchases_list:
                print(f"  - {purchase.transaction_number}: {purchase.total_amount}")
            
            print("✅ All purchase service tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up
            await session.rollback()
            await session.close()
            break


if __name__ == "__main__":
    success = asyncio.run(test_purchase_service())
    sys.exit(0 if success else 1)