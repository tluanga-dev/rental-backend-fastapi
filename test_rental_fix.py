"""
Simple test to verify the rental optimization fix works.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the service directly
from app.modules.transactions.service import TransactionService
from app.modules.transactions.schemas.main import NewRentalRequest
from datetime import date

async def test_method_exists():
    """Test if the optimized method exists in the service."""
    print("🔍 Testing if rental optimization method exists...")
    
    # Check if the service has the method
    service_methods = dir(TransactionService)
    
    print("\n📋 Available rental methods in TransactionService:")
    rental_methods = [m for m in service_methods if 'rental' in m.lower()]
    for method in rental_methods:
        print(f"  - {method}")
    
    # Check for the problematic method names
    print("\n❓ Checking for method names:")
    print(f"  - create_new_rental_minimal_test: {'✅' if 'create_new_rental_minimal_test' in service_methods else '❌ NOT FOUND'}")
    print(f"  - create_new_rental_optimized: {'✅' if 'create_new_rental_optimized' in service_methods else '❌ NOT FOUND'}")
    print(f"  - create_new_rental: {'✅' if 'create_new_rental' in service_methods else '❌ NOT FOUND'}")
    
    # Read the route file to check what method is being called
    print("\n📄 Checking route handler...")
    with open('app/modules/transactions/routes/main.py', 'r') as f:
        content = f.read()
        
    # Find the line that calls the service method
    import re
    pattern = r'service\.create_new_rental_\w+\('
    matches = re.findall(pattern, content)
    
    if matches:
        print(f"  Route is calling: {matches[0]}")
        method_name = matches[0].replace('service.', '').replace('(', '')
        
        if method_name in service_methods:
            print(f"  ✅ Method '{method_name}' exists in service!")
        else:
            print(f"  ❌ Method '{method_name}' does NOT exist in service!")
            print(f"  💡 This is why the endpoint hangs - it's trying to call a non-existent method")
    else:
        print("  ❓ Could not find service method call in route")
    
    print("\n🎯 CULPRIT ANALYSIS:")
    if 'create_new_rental_optimized' in service_methods and 'create_new_rental_minimal_test' not in service_methods:
        if 'create_new_rental_optimized(' in content:
            print("  ✅ The fix has been applied! Route now calls the correct method.")
            print("  ✅ The endpoint should now work properly without hanging.")
        else:
            print("  ❌ The route is still calling the wrong method name!")
            print("  ❌ This causes an AttributeError and makes the endpoint hang.")
            print("  🔧 FIX: Change 'create_new_rental_minimal_test' to 'create_new_rental_optimized' in routes/main.py")

if __name__ == "__main__":
    print("🧪 Rental Optimization Method Test")
    print("=" * 50)
    
    asyncio.run(test_method_exists())