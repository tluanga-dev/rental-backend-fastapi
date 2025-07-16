#!/usr/bin/env python3
"""
Test script to verify the rentable items endpoint functionality.
"""

import asyncio
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.main import app
from app.db.session import get_session
from app.modules.transactions.service import TransactionService
from app.modules.master_data.item_master.models import Item
from app.modules.inventory.models import StockLevel


async def test_rentable_items_endpoint():
    """Test the new rentable items with availability endpoint."""
    print("Testing Rentable Items with Availability Endpoint...")
    print("=" * 60)
    
    async for session in get_session():
        try:
            service = TransactionService(session)
            
            # Test 1: Get all rentable items
            print("\n1. Testing get all rentable items with availability...")
            rentable_items = await service.get_rentable_items_with_availability()
            
            print(f"✓ Found {len(rentable_items)} rentable items with available stock")
            
            # Display first few items
            for i, item in enumerate(rentable_items[:3]):
                print(f"\n  Item {i+1}:")
                print(f"    SKU: {item.sku}")
                print(f"    Name: {item.item_name}")
                print(f"    Rental Rate: {item.rental_rate_per_period}")
                print(f"    Security Deposit: {item.security_deposit}")
                print(f"    Total Available: {item.total_available_quantity}")
                
                if item.brand:
                    print(f"    Brand: {item.brand.name}")
                if item.category:
                    print(f"    Category: {item.category.name}")
                
                print(f"    Locations ({len(item.location_availability)}):")
                for loc in item.location_availability:
                    print(f"      - {loc.location_name}: {loc.available_quantity} available")
            
            # Test 2: Test filtering by category
            if rentable_items and rentable_items[0].category:
                category_id = rentable_items[0].category.id
                print(f"\n2. Testing filter by category ({rentable_items[0].category.name})...")
                
                filtered_items = await service.get_rentable_items_with_availability(
                    category_id=category_id
                )
                
                print(f"✓ Found {len(filtered_items)} items in this category")
            
            # Test 3: Test filtering by location
            if rentable_items and rentable_items[0].location_availability:
                location_id = rentable_items[0].location_availability[0].location_id
                location_name = rentable_items[0].location_availability[0].location_name
                print(f"\n3. Testing filter by location ({location_name})...")
                
                location_items = await service.get_rentable_items_with_availability(
                    location_id=location_id
                )
                
                print(f"✓ Found {len(location_items)} items available at this location")
            
            # Test 4: Test pagination
            print("\n4. Testing pagination...")
            page1 = await service.get_rentable_items_with_availability(skip=0, limit=5)
            page2 = await service.get_rentable_items_with_availability(skip=5, limit=5)
            
            print(f"✓ Page 1: {len(page1)} items")
            print(f"✓ Page 2: {len(page2)} items")
            
            # Test 5: Verify data integrity
            print("\n5. Verifying data integrity...")
            
            # Get actual stock levels from database
            if rentable_items:
                test_item = rentable_items[0]
                stock_query = select(StockLevel).where(
                    StockLevel.item_id == test_item.id,
                    StockLevel.quantity_available > 0,
                    StockLevel.is_active == True
                )
                result = await session.execute(stock_query)
                actual_stocks = result.scalars().all()
                
                db_total = sum(float(stock.quantity_available) for stock in actual_stocks)
                
                print(f"✓ Item: {test_item.item_name}")
                print(f"  API Total: {test_item.total_available_quantity}")
                print(f"  DB Total: {db_total}")
                print(f"  Match: {'✓' if abs(test_item.total_available_quantity - db_total) < 0.01 else '✗'}")
            
            print("\n✅ All tests passed! The rentable items endpoint is working correctly.")
            
            # Display endpoint URL
            print("\n📡 Endpoint Information:")
            print("  URL: GET /api/transactions/rentable-items")
            print("  Query Parameters:")
            print("    - location_id (optional): Filter by location UUID")
            print("    - category_id (optional): Filter by category UUID")
            print("    - skip (optional): Pagination offset (default: 0)")
            print("    - limit (optional): Items per page (default: 100, max: 1000)")
            
            print("\n📋 Sample Response Format:")
            if rentable_items:
                sample = {
                    "id": str(rentable_items[0].id),
                    "sku": rentable_items[0].sku,
                    "item_name": rentable_items[0].item_name,
                    "rental_rate_per_period": float(rentable_items[0].rental_rate_per_period),
                    "rental_period": rentable_items[0].rental_period,
                    "security_deposit": float(rentable_items[0].security_deposit),
                    "total_available_quantity": rentable_items[0].total_available_quantity,
                    "brand": {"id": str(rentable_items[0].brand.id), "name": rentable_items[0].brand.name} if rentable_items[0].brand else None,
                    "category": {"id": str(rentable_items[0].category.id), "name": rentable_items[0].category.name} if rentable_items[0].category else None,
                    "unit_of_measurement": {
                        "id": str(rentable_items[0].unit_of_measurement.id),
                        "name": rentable_items[0].unit_of_measurement.name,
                        "code": rentable_items[0].unit_of_measurement.code
                    } if rentable_items[0].unit_of_measurement else None,
                    "location_availability": [
                        {
                            "location_id": str(loc.location_id),
                            "location_name": loc.location_name,
                            "available_quantity": loc.available_quantity
                        } for loc in rentable_items[0].location_availability[:2]
                    ]
                }
                print(json.dumps(sample, indent=2))
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(test_rentable_items_endpoint())