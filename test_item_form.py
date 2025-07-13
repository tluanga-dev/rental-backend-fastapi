import requests
import json

# Test the item creation endpoint
def test_item_creation():
    base_url = "http://localhost:8000"
    
    # First, let's login as admin
    login_data = {
        "username": "admin@admin.com",
        "password": "Admin@123"
    }
    
    print("1. Logging in...")
    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    login_json = login_response.json()
    # Check if response has 'data' key or direct access_token
    if "data" in login_json:
        token = login_json["data"]["access_token"]
    else:
        token = login_json.get("access_token")
    
    if not token:
        print(f"No access token found in response: {login_json}")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get units of measurement to use one
    print("\n2. Getting units of measurement...")
    unit_id = None
    units_response = requests.get(f"{base_url}/api/master-data/units-of-measurement/", headers=headers)
    if units_response.status_code == 200:
        units = units_response.json()["data"]["items"]
        if units:
            unit_id = units[0]["id"]
            print(f"Using unit: {units[0]['name']} (ID: {unit_id})")
        else:
            print("No units found. Creating a default unit...")
            unit_data = {
                "name": "Piece",
                "abbreviation": "pc",
                "description": "Individual piece"
            }
            create_unit_response = requests.post(
                f"{base_url}/api/master-data/units-of-measurement/", 
                json=unit_data, 
                headers=headers
            )
            if create_unit_response.status_code == 201:
                unit_id = create_unit_response.json()["data"]["id"]
                print(f"Created unit with ID: {unit_id}")
            else:
                print(f"Failed to create unit: {create_unit_response.text}")
                return
    else:
        print(f"Failed to get units: {units_response.text}")
        return
    
    if not unit_id:
        print("No unit ID available, cannot proceed")
        return
    
    # Create item
    print("\n3. Creating item...")
    item_data = {
        "item_name": "Test Power Drill",
        "unit_of_measurement_id": unit_id,
        "description": "High-performance cordless drill",
        "model_number": "DWD110K",
        "sale_price": 15000,
        "rental_rate_per_period": 500,
        "rental_period": "1",
        "is_rentable": True,
        "is_saleable": False,
        "serial_number_required": False,
        "item_status": "ACTIVE"
    }
    
    create_response = requests.post(
        f"{base_url}/api/master-data/item-master/", 
        json=item_data, 
        headers=headers
    )
    
    if create_response.status_code == 201:
        item = create_response.json()["data"]
        print(f"✅ Item created successfully!")
        print(f"   ID: {item['id']}")
        print(f"   SKU: {item['sku']}")
        print(f"   Name: {item['item_name']}")
    else:
        print(f"❌ Failed to create item:")
        print(f"   Status: {create_response.status_code}")
        print(f"   Response: {create_response.text}")

if __name__ == "__main__":
    test_item_creation()