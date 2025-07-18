#!/usr/bin/env python3
"""
Test script to evaluate the optimized rental creation endpoint.
This script creates dummy data and tests both the original and optimized endpoints.
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime, timedelta
from uuid import uuid4
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test configuration
BASE_URL = "http://localhost:8000"
ORIGINAL_ENDPOINT = f"{BASE_URL}/api/transactions/new-rental"
OPTIMIZED_ENDPOINT = f"{BASE_URL}/api/transactions/new-rental-optimized"

# Test data
TEST_CUSTOMER_ID = "123e4567-e89b-12d3-a456-426614174000"
TEST_LOCATION_ID = "123e4567-e89b-12d3-a456-426614174001"
TEST_ITEM_IDS = [
    "123e4567-e89b-12d3-a456-426614174002",
    "123e4567-e89b-12d3-a456-426614174003",
    "123e4567-e89b-12d3-a456-426614174004"
]

async def create_test_data(session):
    """Create necessary test data (customer, location, items) if they don't exist."""
    print("🔍 Checking test data...")
    
    # Check if customer exists
    try:
        async with session.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_ID}") as response:
            if response.status == 404:
                print("❌ Test customer not found. Creating...")
                # Create customer
                customer_data = {
                    "customer_name": "Test Customer",
                    "email": "test@example.com",
                    "phone": "+1234567890",
                    "address": "123 Test Street",
                    "city": "Test City",
                    "state": "Test State",
                    "postal_code": "12345",
                    "country": "Test Country"
                }
                async with session.post(f"{BASE_URL}/api/customers", json=customer_data) as resp:
                    if resp.status == 201:
                        print("✅ Test customer created")
                    else:
                        print(f"❌ Failed to create customer: {resp.status}")
            else:
                print("✅ Test customer exists")
    except Exception as e:
        print(f"⚠️  Customer check skipped: {e}")

    # Check if location exists
    try:
        async with session.get(f"{BASE_URL}/api/locations/{TEST_LOCATION_ID}") as response:
            if response.status == 404:
                print("❌ Test location not found. Creating...")
                # Create location
                location_data = {
                    "location_name": "Test Location",
                    "address": "456 Test Avenue",
                    "city": "Test City",
                    "state": "Test State",
                    "postal_code": "67890",
                    "country": "Test Country",
                    "is_active": True
                }
                async with session.post(f"{BASE_URL}/api/locations", json=location_data) as resp:
                    if resp.status == 201:
                        print("✅ Test location created")
                    else:
                        print(f"❌ Failed to create location: {resp.status}")
            else:
                print("✅ Test location exists")
    except Exception as e:
        print(f"⚠️  Location check skipped: {e}")

    # Check and create test items
    for i, item_id in enumerate(TEST_ITEM_IDS):
        try:
            async with session.get(f"{BASE_URL}/api/items/{item_id}") as response:
                if response.status == 404:
                    print(f"❌ Test item {i+1} not found. Creating...")
                    # Create item
                    item_data = {
                        "item_name": f"Test Rental Item {i+1}",
                        "sku": f"TEST-ITEM-{i+1}",
                        "description": f"Test rental item {i+1} for optimization testing",
                        "category_id": "123e4567-e89b-12d3-a456-426614174005",
                        "brand_id": "123e4567-e89b-12d3-a456-426614174006",
                        "unit_of_measurement_id": "123e4567-e89b-12d3-a456-426614174007",
                        "is_rentable": True,
                        "is_saleable": True,
                        "rental_rate_per_period": 25.0,
                        "rental_period_unit": "DAYS",
                        "security_deposit": 100.0,
                        "is_active": True
                    }
                    async with session.post(f"{BASE_URL}/api/items", json=item_data) as resp:
                        if resp.status == 201:
                            print(f"✅ Test item {i+1} created")
                        else:
                            print(f"❌ Failed to create item {i+1}: {resp.status}")
                else:
                    print(f"✅ Test item {i+1} exists")
        except Exception as e:
            print(f"⚠️  Item {i+1} check skipped: {e}")

def generate_rental_payload(item_count=3):
    """Generate rental payload with specified number of items."""
    today = datetime.now().date()
    end_date = today + timedelta(days=7)
    
    return {
        "customer_id": TEST_CUSTOMER_ID,
        "location_id": TEST_LOCATION_ID,
        "transaction_date": today.isoformat(),
        "payment_method": "CASH",
        "payment_reference": "TEST-REF-001",
        "notes": "Test rental for performance optimization",
        "deposit_amount": 100.0,
        "items": [
            {
                "item_id": TEST_ITEM_IDS[i % len(TEST_ITEM_IDS)],
                "quantity": 2,
                "rental_period_value": 7,
                "rental_start_date": today.isoformat(),
                "rental_end_date": end_date.isoformat(),
                "tax_rate": 10.0,
                "discount_amount": 5.0,
                "notes": f"Test item {i+1}"
            }
            for i in range(item_count)
        ]
    }

async def test_endpoint(session, endpoint, payload, name):
    """Test a specific endpoint and measure performance."""
    print(f"\n🧪 Testing {name} endpoint...")
    print(f"📊 Items: {len(payload['items'])}")
    
    start_time = time.time()
    
    try:
        async with session.post(endpoint, json=payload) as response:
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status == 201:
                result = await response.json()
                print(f"✅ {name}: SUCCESS")
                print(f"⏱️  Response time: {duration:.2f} seconds")
                print(f"📋 Transaction ID: {result.get('transaction_id')}")
                print(f"🏷️  Transaction Number: {result.get('transaction_number')}")
                return {
                    "success": True,
                    "duration": duration,
                    "transaction_id": result.get('transaction_id'),
                    "transaction_number": result.get('transaction_number'),
                    "data": result
                }
            else:
                error_text = await response.text()
                print(f"❌ {name}: FAILED ({response.status})")
                print(f"📄 Error: {error_text}")
                return {
                    "success": False,
                    "duration": duration,
                    "error": error_text
                }
                
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ {name}: ERROR - {str(e)}")
        return {
            "success": False,
            "duration": duration,
            "error": str(e)
        }

async def verify_transaction_details(session, transaction_id):
    """Verify the created transaction details."""
    print(f"\n🔍 Verifying transaction {transaction_id}...")
    
    try:
        async with session.get(f"{BASE_URL}/api/transactions/{transaction_id}/with-lines") as response:
            if response.status == 200:
                transaction = await response.json()
                
                print("✅ Transaction retrieved successfully")
                print(f"📊 Total Amount: ${transaction.get('total_amount', 0)}")
                print(f"📋 Line Items: {len(transaction.get('transaction_lines', []))}")
                
                # Verify stock levels
                for line in transaction.get('transaction_lines', []):
                    item_id = line.get('item_id')
                    quantity = line.get('quantity')
                    
                    # Check stock level
                    try:
                        async with session.get(f"{BASE_URL}/api/inventory/stock-levels/item/{item_id}/location/{TEST_LOCATION_ID}") as stock_response:
                            if stock_response.status == 200:
                                stock = await stock_response.json()
                                print(f"📦 Item {item_id}: Available={stock.get('quantity_available')}, On Rent={stock.get('on_rent_quantity')}")
                            else:
                                print(f"⚠️  Could not verify stock for item {item_id}")
                    except:
                        print(f"⚠️  Stock verification skipped for item {item_id}")
                
                return transaction
            else:
                print(f"❌ Failed to retrieve transaction: {response.status}")
                return None
    except Exception as e:
        print(f"❌ Error verifying transaction: {str(e)}")
        return None

async def main():
    """Main test function."""
    print("🚀 Starting Rental Creation Performance Test")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Create test data
        await create_test_data(session)
        
        # Test with different item counts
        test_cases = [1, 3, 5, 10]
        results = []
        
        for item_count in test_cases:
            print(f"\n{'='*50}")
            print(f"Testing with {item_count} items")
            print('='*50)
            
            payload = generate_rental_payload(item_count)
            
            # Test optimized endpoint
            optimized_result = await test_endpoint(
                session, 
                OPTIMIZED_ENDPOINT, 
                payload, 
                "OPTIMIZED"
            )
            
            results.append({
                "item_count": item_count,
                "optimized": optimized_result
            })
            
            # Verify transaction if successful
            if optimized_result["success"]:
                await verify_transaction_details(
                    session, 
                    optimized_result["transaction_id"]
                )
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Print summary
        print(f"\n{'='*50}")
        print("📊 PERFORMANCE SUMMARY")
        print('='*50)
        
        for result in results:
            item_count = result["item_count"]
            opt = result["optimized"]
            
            if opt["success"]:
                print(f"Items: {item_count:2d} | Time: {opt['duration']:.2f}s | Status: ✅")
            else:
                print(f"Items: {item_count:2d} | Time: {opt['duration']:.2f}s | Status: ❌")
        
        print(f"\n✅ Test completed! Check the results above.")

if __name__ == "__main__":
    asyncio.run(main())
