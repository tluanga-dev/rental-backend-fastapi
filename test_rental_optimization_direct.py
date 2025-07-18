#!/usr/bin/env python3
"""
Direct test script for rental creation optimization.
This script tests the optimization logic directly without requiring a running server.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.database import get_database_url
from app.modules.transactions.service import TransactionService
from app.modules.transactions.schemas import NewRentalRequest, RentalItemCreate
from app.core.errors import NotFoundError, ValidationError

# Test configuration
TEST_DATABASE_URL = get_database_url()

async def create_test_data(session):
    """Create necessary test data in the database."""
    print("🔍 Creating test data...")
    
    # Create test customer
    from app.modules.customers.models import Customer
    customer = Customer(
        id="123e4567-e89b-12d3-a456-426614174000",
        customer_name="Test Customer",
        email="test@example.com",
        phone="+1234567890",
        address="123 Test Street",
        city="Test City",
        state="Test State",
        postal_code="12345",
        country="Test Country",
        is_active=True,
        can_transact=True
    )
    
    # Create test location
    from app.modules.master_data.locations.models import Location
    location = Location(
        id="123e4567-e89b-12d3-a456-426614174001",
        location_name="Test Location",
        address="456 Test Avenue",
        city="Test City",
        state="Test State",
        postal_code="67890",
        country="Test Country",
        is_active=True
    )
    
    # Create test items
    from app.modules.master_data.item_master.models import Item
    items = [
        Item(
            id="123e4567-e89b-12d3-a456-426614174002",
            item_name="Test Rental Item 1",
            sku="TEST-ITEM-001",
            description="Test rental item 1 for optimization testing",
            is_rentable=True,
            is_saleable=True,
            rental_rate_per_period=Decimal("25.00"),
            is_active=True
        ),
        Item(
            id="123e4567-e89b-12d3-a456-426614174003",
            item_name="Test Rental Item 2",
            sku="TEST-ITEM-002",
            description="Test rental item 2 for optimization testing",
            is_rentable=True,
            is_saleable=True,
            rental_rate_per_period=Decimal("30.00"),
            is_active=True
        ),
        Item(
            id="123e4567-e89b-12d3-a456-426614174004",
            item_name="Test Rental Item 3",
            sku="TEST-ITEM-003",
            description="Test rental item 3 for optimization testing",
            is_rentable=True,
            is_saleable=True,
            rental_rate_per_period=Decimal("35.00"),
            is_active=True
        )
    ]
    
    # Create stock levels
    from app.modules.inventory.models import StockLevel
    stock_levels = [
        StockLevel(
            item_id="123e4567-e89b-12d3-a456-426614174002",
            location_id="123e4567-e89b-12d3-a456-426614174001",
            quantity_available=Decimal("100.00"),
            on_rent_quantity=Decimal("0.00"),
            is_active=True
        ),
        StockLevel(
            item_id="123e4567-e89b-12d3-a456-426614174003",
            location_id="123e4567-e89b-12d3-a456-426614174001",
            quantity_available=Decimal("50.00"),
            on_rent_quantity=Decimal("0.00"),
            is_active=True
        ),
        StockLevel(
            item_id="123e4567-e89b-12d3-a456-426614174004",
            location_id="123e4567-e89b-12d3-a456-426614174001",
            quantity_available=Decimal("75.00"),
            on_rent_quantity=Decimal("0.00"),
            is_active=True
        )
    ]
    
    # Add all test data
    session.add(customer)
    session.add(location)
    for item in items:
        session.add(item)
    for stock_level in stock_levels:
        session.add(stock_level)
    
    await session.commit()
    print("✅ Test data created successfully")

def generate_rental_payload(item_count=3):
    """Generate rental payload with specified number of items."""
    today = datetime.now().date()
    end_date = today + timedelta(days=7)
    
    return NewRentalRequest(
        customer_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        location_id=UUID("123e4567-e89b-12d3-a456-426614174001"),
        transaction_date=today,
        payment_method="CASH",
        payment_reference="TEST-REF-001",
        notes="Test rental for performance optimization",
        deposit_amount=Decimal("100.00"),
        items=[
            RentalItemCreate(
                item_id=UUID(f"123e4567-e89b-12d3-a456-42661417400{i+2}"),
                quantity=2,
                rental_period_value=7,
                rental_start_date=today,
                rental_end_date=end_date,
                tax_rate=Decimal("10.00"),
                discount_amount=Decimal("5.00"),
                notes=f"Test item {i+1}"
            )
            for i in range(min(item_count, 3))
        ]
    )

async def test_optimized_rental_creation():
    """Test the optimized rental creation directly."""
    print("🚀 Starting Direct Rental Creation Test")
    print("=" * 50)
    
    # Create database engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Create test data
            await create_test_data(session)
            
            # Test with different item counts
            test_cases = [1, 2, 3]
            results = []
            
            for item_count in test_cases:
                print(f"\n{'='*50}")
                print(f"Testing with {item_count} items")
                print('='*50)
                
                payload = generate_rental_payload(item_count)
                
                # Create service instance
                service = TransactionService(session)
                
                # Measure performance
                start_time = time.time()
                
                try:
                    result = await service.create_new_rental_optimized(payload)
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    print(f"✅ OPTIMIZED: SUCCESS")
                    print(f"⏱️  Response time: {duration:.3f} seconds")
                    print(f"📋 Transaction ID: {result.transaction_id}")
                    print(f"🏷️  Transaction Number: {result.transaction_number}")
                    print(f"💰 Total Amount: ${result.data.get('total_amount', 0)}")
                    
                    # Verify transaction was created
                    transaction = await service.get_transaction_with_lines(result.transaction_id)
                    print(f"📊 Line Items: {len(transaction.transaction_lines)}")
                    
                    # Verify stock levels were updated
                    for line in transaction.transaction_lines:
                        item_id = line.item_id
                        stock_level = await service.inventory_service.stock_level_repository.get_by_item_location(
                            item_id, str(payload.location_id)
                        )
                        if stock_level:
                            print(f"📦 Item {item_id}: Available={stock_level.quantity_available}, On Rent={stock_level.on_rent_quantity}")
                    
                    results.append({
                        "item_count": item_count,
                        "success": True,
                        "duration": duration,
                        "transaction_id": result.transaction_id
                    })
                    
                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time
                    print(f"❌ OPTIMIZED: FAILED - {str(e)}")
                    print(f"⏱️  Response time: {duration:.3f} seconds")
                    
                    results.append({
                        "item_count": item_count,
                        "success": False,
                        "duration": duration,
                        "error": str(e)
                    })
            
            # Print summary
            print(f"\n{'='*50}")
            print("📊 PERFORMANCE SUMMARY")
            print('='*50)
            
            for result in results:
                item_count = result["item_count"]
                if result["success"]:
                    print(f"Items: {item_count:2d} | Time: {result['duration']:.3f}s | Status: ✅")
                else:
                    print(f"Items: {item_count:2d} | Time: {result['duration']:.3f}s | Status: ❌ | Error: {result['error']}")
            
            print(f"\n✅ Test completed! Check the results above.")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    import time
    asyncio.run(test_optimized_rental_creation())
