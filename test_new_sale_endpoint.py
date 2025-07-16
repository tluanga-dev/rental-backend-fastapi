#!/usr/bin/env python3
"""
Test script for the new sale endpoint
"""
import json
import requests
from datetime import datetime
from uuid import uuid4

# Test data
BASE_URL = "http://localhost:8000"
SALE_ENDPOINT = f"{BASE_URL}/api/transactions/new-sale"

def test_new_sale_endpoint():
    """Test the new sale endpoint with sample data"""
    
    # Sample sale data
    sale_data = {
        "customer_id": str(uuid4()),  # Random UUID for testing
        "transaction_date": datetime.now().strftime('%Y-%m-%d'),
        "notes": "Test sale transaction",
        "reference_number": "REF-TEST-001",
        "items": [
            {
                "item_id": str(uuid4()),  # Random UUID for testing
                "quantity": 2,
                "unit_cost": 25.50,
                "tax_rate": 8.5,
                "discount_amount": 5.00,
                "notes": "Test item 1"
            },
            {
                "item_id": str(uuid4()),  # Random UUID for testing
                "quantity": 1,
                "unit_cost": 100.00,
                "tax_rate": 8.5,
                "discount_amount": 0.00,
                "notes": "Test item 2"
            }
        ]
    }
    
    print("Testing new sale endpoint...")
    print(f"URL: {SALE_ENDPOINT}")
    print(f"Data: {json.dumps(sale_data, indent=2)}")
    
    try:
        response = requests.post(SALE_ENDPOINT, json=sale_data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Sale endpoint is working!")
            response_data = response.json()
            print(f"Transaction ID: {response_data.get('transaction_id')}")
            print(f"Transaction Number: {response_data.get('transaction_number')}")
        else:
            print(f"❌ ERROR: Status code {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server. Make sure the FastAPI server is running.")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_new_sale_endpoint()