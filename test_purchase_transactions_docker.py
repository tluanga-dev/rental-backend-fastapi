#!/usr/bin/env python3
"""
Test script for purchase transaction creation and fetching using Docker Compose.
"""

import requests
import json
from datetime import date, datetime
import uuid
import sys
import time

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "Admin@123"
}

def get_auth_token():
    """Get authentication token for the admin user."""
    print("🔑 Authenticating admin user...")
    
    url = f"{BASE_URL}/api/auth/login"
    response = requests.post(url, json=ADMIN_CREDENTIALS)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Authentication successful")
        return token_data["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_auth_headers(token):
    """Get authorization headers."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_sample_data():
    """Get sample data for testing."""
    print("📊 Fetching sample data...")
    
    # We'll use some sample UUIDs for the test
    # In a real scenario, these would come from actual database records
    sample_data = {
        "supplier_id": "550e8400-e29b-41d4-a716-446655440000",
        "location_id": "550e8400-e29b-41d4-a716-446655440001", 
        "item_id": "550e8400-e29b-41d4-a716-446655440002"
    }
    
    return sample_data

def create_purchase_transaction(token, sample_data):
    """Test creating a purchase transaction."""
    print("🛒 Testing purchase transaction creation...")
    
    url = f"{BASE_URL}/api/transactions/new-purchase"
    headers = get_auth_headers(token)
    
    # Create purchase transaction data
    purchase_data = {
        "supplier_id": sample_data["supplier_id"],
        "location_id": sample_data["location_id"],
        "purchase_date": date.today().isoformat(),
        "notes": "Test purchase transaction from Docker Compose",
        "reference_number": f"TEST-{int(time.time())}",
        "items": [
            {
                "item_id": sample_data["item_id"],
                "quantity": 5,
                "unit_cost": 25.99,
                "tax_rate": 10.0,
                "discount_amount": 2.50,
                "condition": "A",
                "notes": "Test item purchase"
            }
        ]
    }
    
    print(f"📤 Sending purchase data: {json.dumps(purchase_data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=purchase_data)
    
    print(f"📥 Response Status: {response.status_code}")
    print(f"📥 Response Headers: {dict(response.headers)}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Purchase transaction created successfully!")
        print(f"📊 Transaction ID: {result.get('data', {}).get('transaction_id')}")
        print(f"📊 Transaction Number: {result.get('data', {}).get('transaction_number')}")
        print(f"📊 Total Amount: ${result.get('data', {}).get('total_amount', 0):.2f}")
        return result.get('data', {}).get('transaction_id')
    else:
        print(f"❌ Purchase transaction creation failed")
        print(f"Error: {response.text}")
        
        # Try to parse error details
        try:
            error_data = response.json()
            print(f"Detailed error: {json.dumps(error_data, indent=2)}")
        except:
            pass
        
        return None

def fetch_purchase_transaction(token, transaction_id):
    """Test fetching a purchase transaction by ID."""
    print(f"📋 Testing purchase transaction fetch for ID: {transaction_id}")
    
    url = f"{BASE_URL}/api/transactions/purchases/{transaction_id}"
    headers = get_auth_headers(token)
    
    response = requests.get(url, headers=headers)
    
    print(f"📥 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Purchase transaction fetched successfully!")
        print(f"📊 Transaction Details:")
        print(f"   - Number: {result.get('data', {}).get('transaction_number')}")
        print(f"   - Date: {result.get('data', {}).get('transaction_date')}")
        print(f"   - Status: {result.get('data', {}).get('status')}")
        print(f"   - Total: ${result.get('data', {}).get('total_amount', 0):.2f}")
        print(f"   - Items: {len(result.get('data', {}).get('items', []))}")
        return True
    else:
        print(f"❌ Purchase transaction fetch failed")
        print(f"Error: {response.text}")
        return False

def fetch_purchase_transactions_list(token):
    """Test fetching the list of purchase transactions."""
    print("📋 Testing purchase transactions list fetch...")
    
    url = f"{BASE_URL}/api/transactions/purchases/"
    headers = get_auth_headers(token)
    
    # Test with query parameters
    params = {
        "limit": 10,
        "skip": 0,
        "sort_order": "desc"
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    print(f"📥 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Purchase transactions list fetched successfully!")
        print(f"📊 Found {len(result.get('data', []))} transactions")
        
        # Show pagination info
        pagination = result.get('pagination', {})
        print(f"📊 Pagination:")
        print(f"   - Total: {pagination.get('total', 0)}")
        print(f"   - Current Page: {pagination.get('current_page', 1)}")
        print(f"   - Has Next: {pagination.get('has_next', False)}")
        
        return True
    else:
        print(f"❌ Purchase transactions list fetch failed")
        print(f"Error: {response.text}")
        return False

def test_purchase_endpoints():
    """Run comprehensive tests for purchase transaction endpoints."""
    print("🧪 Starting Purchase Transaction Tests with Docker Compose")
    print("=" * 60)
    
    # Step 1: Authenticate
    token = get_auth_token()
    if not token:
        print("❌ Cannot continue without authentication")
        sys.exit(1)
    
    print("=" * 60)
    
    # Step 2: Get sample data
    sample_data = get_sample_data()
    print(f"📊 Using sample data: {sample_data}")
    
    print("=" * 60)
    
    # Step 3: Test purchase transaction creation
    transaction_id = create_purchase_transaction(token, sample_data)
    
    print("=" * 60)
    
    # Step 4: Test purchase transaction fetch (if creation was successful)
    if transaction_id:
        time.sleep(1)  # Give a moment for the transaction to be saved
        fetch_success = fetch_purchase_transaction(token, transaction_id)
    else:
        print("⚠️  Skipping fetch test due to creation failure")
        fetch_success = False
    
    print("=" * 60)
    
    # Step 5: Test purchase transactions list
    list_success = fetch_purchase_transactions_list(token)
    
    print("=" * 60)
    
    # Summary
    print("📊 Test Summary:")
    print(f"   - Authentication: ✅")
    print(f"   - Transaction Creation: {'✅' if transaction_id else '❌'}")
    print(f"   - Transaction Fetch: {'✅' if fetch_success else '❌'}")
    print(f"   - Transactions List: {'✅' if list_success else '❌'}")
    
    if transaction_id and fetch_success and list_success:
        print("🎉 All tests passed successfully!")
        return True
    else:
        print("⚠️  Some tests failed - check the logs above")
        return False

def check_service_health():
    """Check if the service is healthy before running tests."""
    print("🔍 Checking service health...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Service is healthy and accessible")
            return True
        else:
            print(f"⚠️  Service responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Service is not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Purchase Transaction Test Suite")
    print("Using Docker Compose environment")
    print("=" * 60)
    
    # Check service health first
    if not check_service_health():
        print("❌ Service is not healthy. Please check if Docker Compose is running.")
        sys.exit(1)
    
    # Run tests
    success = test_purchase_endpoints()
    
    if success:
        print("✅ All purchase transaction tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)
