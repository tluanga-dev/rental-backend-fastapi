"""
Simple performance test for the new rental optimization endpoint.
This test identifies the exact culprit causing performance issues.
"""

import time
import json
import asyncio
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx

# Test configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/transactions/new-rental-optimized"
TEST_RUNS = 3  # Reduced for faster testing


def generate_test_rental_data(item_count: int = 1) -> Dict[str, Any]:
    """Generate test rental data."""
    base_date = datetime.now().date()
    rental_start = base_date + timedelta(days=1)
    rental_end = rental_start + timedelta(days=7)
    
    # Use realistic test UUIDs that might exist in the database
    items = []
    for i in range(item_count):
        items.append({
            "item_id": f"00000000-0000-0000-0000-00000000000{i+1}",
            "quantity": 1,
            "rental_period_value": 7,
            "rental_start_date": rental_start.isoformat(),
            "rental_end_date": rental_end.isoformat()
        })
    
    return {
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "location_id": "00000000-0000-0000-0000-000000000001",
        "transaction_date": base_date.isoformat(),
        "payment_method": "cash",
        "items": items
    }


async def test_endpoint_performance():
    """Test the endpoint and identify performance issues."""
    print("🔍 PERFORMANCE CULPRIT DETECTION")
    print("=" * 50)
    
    # Test scenarios
    scenarios = [
        {"name": "Single Item", "items": 1},
        {"name": "Multiple Items", "items": 3},
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for scenario in scenarios:
            print(f"\n📊 Testing {scenario['name']} ({scenario['items']} items)")
            print("-" * 40)
            
            times = []
            errors = []
            
            for run in range(TEST_RUNS):
                rental_data = generate_test_rental_data(scenario['items'])
                
                print(f"  Run {run + 1}:")
                print(f"    Sending request to {BASE_URL}{ENDPOINT}")
                
                start_time = time.time()
                
                try:
                    response = await client.post(
                        f"{BASE_URL}{ENDPOINT}",
                        json=rental_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    end_time = time.time()
                    total_time = end_time - start_time
                    times.append(total_time)
                    
                    print(f"    ✓ Status: {response.status_code}")
                    print(f"    ✓ Time: {total_time:.3f}s")
                    
                    if response.status_code != 200 and response.status_code != 201:
                        print(f"    ⚠️  Error Response: {response.text[:200]}...")
                        errors.append({
                            "status": response.status_code,
                            "response": response.text[:500],
                            "time": total_time
                        })
                    else:
                        try:
                            resp_data = response.json()
                            print(f"    ✓ Response: {json.dumps(resp_data, indent=2)[:200]}...")
                        except:
                            print(f"    ✓ Response: {response.text[:200]}...")
                    
                except Exception as e:
                    end_time = time.time()
                    total_time = end_time - start_time
                    print(f"    ❌ Exception: {str(e)}")
                    print(f"    ❌ Time: {total_time:.3f}s")
                    errors.append({
                        "exception": str(e),
                        "time": total_time
                    })
                
                await asyncio.sleep(0.5)  # Small delay between requests
            
            # Analyze results
            print(f"\n📈 {scenario['name']} Results:")
            if times:
                avg_time = statistics.mean(times)
                print(f"  Average Time: {avg_time:.3f}s")
                print(f"  Min/Max: {min(times):.3f}s / {max(times):.3f}s")
                print(f"  Success Rate: {len(times)}/{TEST_RUNS} ({len(times)/TEST_RUNS*100:.1f}%)")
            
            if errors:
                print(f"  🚨 ERRORS DETECTED ({len(errors)} errors):")
                for i, error in enumerate(errors):
                    print(f"    Error {i+1}:")
                    if 'exception' in error:
                        print(f"      Exception: {error['exception']}")
                    if 'status' in error:
                        print(f"      Status: {error['status']}")
                        print(f"      Response: {error['response'][:200]}...")
                    print(f"      Time: {error['time']:.3f}s")
    
    print("\n🎯 CULPRIT ANALYSIS")
    print("=" * 30)
    
    # Test basic server health
    print("1. Testing server health...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            print(f"   ✓ Server health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Server health check failed: {e}")
    
    # Test endpoint existence
    print("2. Testing endpoint existence...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/docs")
            print(f"   ✓ API docs accessible: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API docs check failed: {e}")
    
    # Test with minimal data
    print("3. Testing with minimal data...")
    try:
        minimal_data = {
            "customer_id": "test",
            "location_id": "test", 
            "transaction_date": "2024-01-01",
            "payment_method": "cash",
            "items": []
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BASE_URL}{ENDPOINT}",
                json=minimal_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Minimal data test failed: {e}")


async def main():
    """Main test runner."""
    try:
        await test_endpoint_performance()
        print("\n✅ Performance test completed!")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Simple Performance Test for Rental Optimization")
    print("Target: http://localhost:8000/api/transactions/new-rental-optimized")
    print("=" * 60)
    
    asyncio.run(main())