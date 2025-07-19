#!/usr/bin/env python3
"""
Script to verify that all transaction endpoints are properly configured in Swagger
"""
import requests
import json

def verify_swagger_transactions():
    """Verify transaction endpoints in OpenAPI spec"""
    try:
        # Get OpenAPI spec
        response = requests.get("http://localhost:8000/openapi.json")
        if response.status_code != 200:
            print(f"❌ Failed to fetch OpenAPI spec: {response.status_code}")
            return False
        
        openapi_spec = response.json()
        
        # Check if transactions section exists in tags
        tags = openapi_spec.get("tags", [])
        transaction_tags = [tag for tag in tags if "transaction" in tag.get("name", "").lower()]
        
        print("🏷️  Available Transaction Tags:")
        for tag in transaction_tags:
            print(f"   • {tag.get('name')}: {tag.get('description', 'No description')}")
        
        # Check transaction endpoints
        paths = openapi_spec.get("paths", {})
        transaction_endpoints = {path: info for path, info in paths.items() 
                               if path.startswith("/api/transactions")}
        
        print(f"\n📋 Transaction Endpoints Found: {len(transaction_endpoints)}")
        
        # Group by sub-module
        modules = {
            "purchases": [],
            "sales": [],
            "rentals": [],
            "rental_returns": [],
            "queries": []
        }
        
        for path, info in transaction_endpoints.items():
            if "/purchases" in path:
                modules["purchases"].append(path)
            elif "/sales" in path:
                modules["sales"].append(path)
            elif "/rentals" in path:
                modules["rentals"].append(path)
            elif "/rental-returns" in path or "/rental_returns" in path:
                modules["rental_returns"].append(path)
            elif "/queries" in path:
                modules["queries"].append(path)
        
        for module_name, endpoints in modules.items():
            if endpoints:
                print(f"\n📦 {module_name.title()} Module ({len(endpoints)} endpoints):")
                for endpoint in sorted(endpoints):
                    methods = list(transaction_endpoints[endpoint].keys())
                    print(f"   • {endpoint} [{', '.join(methods)}]")
        
        # Verify app structure
        print(f"\n✅ Total Transaction Endpoints: {len(transaction_endpoints)}")
        print(f"✅ Transaction Tags: {len(transaction_tags)}")
        
        if len(transaction_endpoints) > 0 and len(transaction_tags) > 0:
            print("\n🎉 SUCCESS: Transactions section is properly configured in Swagger!")
            return True
        else:
            print("\n❌ ISSUE: Missing transaction endpoints or tags")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying Swagger: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying Transaction Section in Swagger UI...")
    print("=" * 60)
    success = verify_swagger_transactions()
    print("=" * 60)
    if success:
        print("✅ All checks passed! Visit http://localhost:8000/docs to see the result.")
    else:
        print("❌ Some issues found. Check the output above.")
