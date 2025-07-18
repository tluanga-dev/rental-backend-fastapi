#!/usr/bin/env python3
"""Script to create a test rental transaction"""

import requests
import json
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVzZXJfaWQiOjEsInNjb3BlcyI6WyJyZWFkIiwid3JpdGUiXSwiZXhwIjoxNzUyODE1MTU0LCJ0eXBlIjoiYWNjZXNzIn0.upljvIFqjhVSAKawYokE8M9gBC9oEZC4CpX4OZWLgvU"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def get_first_customer():
    """Get the first available customer"""
    response = requests.get(f"{BASE_URL}/api/customers/?limit=1", headers=headers)
    if response.status_code == 200:
        customers = response.json()
        if customers:
            return customers[0]['id']
    return None

def get_first_location():
    """Get the first available location"""
    response = requests.get(f"{BASE_URL}/api/master-data/locations/?limit=1", headers=headers)
    if response.status_code == 200:
        locations = response.json()
        if locations:
            return locations[0]['id']
    return None

def get_first_rental_item():
    """Get the first available rental item"""
    response = requests.get(f"{BASE_URL}/api/inventory/items/rental?active_only=true&limit=1", headers=headers)
    if response.status_code == 200:
        items = response.json()
        if items:
            return items[0]['id']
    return None

def create_rental():
    """Create a rental transaction"""
    customer_id = get_first_customer()
    location_id = get_first_location()
    item_id = get_first_rental_item()
    
    if not all([customer_id, location_id, item_id]):
        print("Missing required data:")
        print(f"Customer ID: {customer_id}")
        print(f"Location ID: {location_id}")
        print(f"Item ID: {item_id}")
        return None
    
    today = date.today()
    end_date = today + timedelta(days=7)
    
    rental_data = {
        "transaction_date": today.strftime("%Y-%m-%d"),
        "customer_id": customer_id,
        "location_id": location_id,
        "payment_method": "CASH",
        "payment_reference": "TEST-001",
        "notes": "Test rental for API verification",
        "items": [
            {
                "item_id": item_id,
                "quantity": 1,
                "rental_period_value": 7,
                "tax_rate": 0,
                "discount_amount": 0,
                "rental_start_date": today.strftime("%Y-%m-%d"),
                "rental_end_date": end_date.strftime("%Y-%m-%d"),
                "notes": "Test item"
            }
        ],
        "delivery_required": False,
        "pickup_required": False
    }
    
    print("Creating rental with data:")
    print(json.dumps(rental_data, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/transactions/new-rental",
        headers=headers,
        json=rental_data,
        timeout=30  # 30 second timeout
    )
    
    print(f"\nResponse status: {response.status_code}")
    if response.status_code in [200, 201]:
        print("Success! Rental created:")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    else:
        print("Error creating rental:")
        print(response.text)
        return None

def test_rental_endpoint(rental_id=None):
    """Test the rentals filtering endpoint"""
    print("\n\nTesting /api/transactions/rentals endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/transactions/rentals", headers=headers)
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        rentals = response.json()
        print(f"Found {len(rentals)} rental(s)")
        
        if rentals:
            print("\nFirst rental:")
            print(json.dumps(rentals[0], indent=2))
            
            if rental_id:
                matching = [r for r in rentals if r.get('id') == rental_id]
                if matching:
                    print(f"\nFound our created rental with ID {rental_id}")
                else:
                    print(f"\nOur rental with ID {rental_id} not found in results")
    else:
        print("Error fetching rentals:")
        print(response.text)

if __name__ == "__main__":
    print("Creating test rental transaction...")
    rental = create_rental()
    
    if rental and rental.get('success'):
        rental_id = rental.get('transaction', {}).get('id')
        test_rental_endpoint(rental_id)
    else:
        # Test anyway to see if there are any existing rentals
        test_rental_endpoint()