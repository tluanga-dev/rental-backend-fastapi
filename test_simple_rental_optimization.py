#!/usr/bin/env python3
"""
Simple test script for rental creation optimization using existing test infrastructure.
"""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test infrastructure
from tests.conftest import create_test_session, create_test_data
from app.modules.transactions.service import TransactionService
from app.modules.transactions.schemas import NewRentalRequest, RentalItemCreate

async def test_optimized_rental_creation():
    """Test the optimized rental creation using test infrastructure."""
    print("🚀 Starting Simple Rental Creation Test")
    print("=" * 50)
    
    # Create test session
    async with create_test_session() as session:
        try:
            # Create test data
            await create_test_data(session)
            print("✅ Test data created successfully")
            
            # Test with different item counts
            test_cases = [1, 2, 3]
            results = []
            
            for item_count in test_cases:
                print(f"\n{'='*50}")
                print(f"Testing with {item_count} items")
                print('='*50)
                
                # Generate test payload
                today = datetime.now().date()
                end_date = today + timedelta(days=7)
                
                payload = NewRentalRequest(
                    customer_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
                    location_id=UUID("123e4567-e89b-12d3-a456-426614174001"),
                    transaction_date=today,
                    payment_method="CASH",
                    payment_reference="TEST-REF-001",
                    notes="Test rental for performance optimization",
                    deposit_amount=Decimal("100.00"),
                    items=[
                        RentalItemCreate(
                            item_id=UUID("123e4567-e89b-12d3-a456-426614174002"),
                            quantity=2,
                            rental_period_value=7,
                            rental_start_date=today,
                            rental_end_date=end_date,
                            tax_rate=Decimal("10.00"),
                            discount_amount=Decimal("5.00"),
                            notes=f"Test item {i+1}"
                        )
                        for i in range(item_count)
                    ]
                )
                
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

if __name__ == "__main__":
    asyncio.run(test_optimized_rental_creation())
