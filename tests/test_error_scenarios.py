"""
Test error scenarios and edge cases for all API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


class TestAuthenticationErrors:
    """Test authentication error scenarios"""
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format"""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "TestPassword123",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
        assert "value_error" in str(response.json()) or "email" in str(response.json()).lower()
    
    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
            # Missing password and full_name
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        login_data = {
            "username": "nonexistent_user",
            "password": "SomePassword123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password"""
        # First register a user
        user_data = {
            "username": "wrongpasstest",
            "email": "wrongpass@example.com",
            "password": "CorrectPassword123",
            "full_name": "Wrong Pass Test"
        }
        reg_response = client.post("/api/auth/register", json=user_data)
        assert reg_response.status_code == 201
        
        # Try to login with wrong password
        login_data = {
            "username": "wrongpasstest",
            "password": "WrongPassword123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_refresh_invalid_token(self, client: TestClient):
        """Test refresh with invalid token"""
        refresh_data = {
            "refresh_token": "invalid.jwt.token"
        }
        response = client.post("/api/auth/refresh", json=refresh_data)
        assert response.status_code == 401
    
    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/users/")
        assert response.status_code == 401
    
    def test_access_protected_endpoint_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = client.get("/api/users/", headers=headers)
        assert response.status_code == 401


class TestValidationErrors:
    """Test validation error scenarios"""
    
    def test_create_customer_invalid_email(self, client: TestClient, auth_headers: dict):
        """Test customer creation with invalid email"""
        customer_data = {
            "customer_code": "INVALID001",
            "customer_type": "BUSINESS",
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email-format",
            "phone": "+1234567890",
            "address_line1": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "USA"
        }
        response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_customer_missing_required_fields(self, client: TestClient, auth_headers: dict):
        """Test customer creation with missing required fields"""
        customer_data = {
            "customer_code": "MISSING001",
            "customer_type": "BUSINESS"
            # Missing required fields like first_name, last_name, email, etc.
        }
        response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_customer_invalid_customer_type(self, client: TestClient, auth_headers: dict):
        """Test customer creation with invalid customer type"""
        customer_data = {
            "customer_code": "INVALIDTYPE001",
            "customer_type": "INVALID_TYPE",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "address_line1": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "USA"
        }
        response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_item_negative_price(self, client: TestClient, auth_headers: dict):
        """Test item creation with negative price"""
        # First create required dependencies
        brand_data = {
            "brand_code": "TESTBRAND",
            "brand_name": "Test Brand",
            "description": "Test brand"
        }
        brand_response = client.post("/api/master-data/brands/", json=brand_data, headers=auth_headers)
        brand_id = brand_response.json()["id"]
        
        category_data = {
            "category_code": "TESTCAT",
            "category_name": "Test Category",
            "description": "Test category"
        }
        category_response = client.post("/api/master-data/categories/", json=category_data, headers=auth_headers)
        category_id = category_response.json()["id"]
        
        item_data = {
            "item_code": "NEGATIVE001",
            "item_name": "Negative Price Item",
            "description": "Item with negative price",
            "category_id": category_id,
            "brand_id": brand_id,
            "item_type": "EQUIPMENT",
            "unit_of_measure": "UNIT",
            "rental_rate_daily": -50.00,  # Invalid negative price
            "sale_price": 1000.00,
            "cost_price": 800.00
        }
        response = client.post("/api/inventory/items/", json=item_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_transaction_invalid_date_range(self, client: TestClient, auth_headers: dict):
        """Test transaction creation with invalid date range"""
        # Create customer first
        customer_data = {
            "customer_code": "DATECUST001",
            "customer_type": "BUSINESS",
            "first_name": "Date",
            "last_name": "Test",
            "email": "date@test.com",
            "phone": "+1234567890",
            "address_line1": "123 Date Street",
            "city": "Date City",
            "state": "DC",
            "postal_code": "12345",
            "country": "USA",
            "payment_terms": "30 days"
        }
        customer_response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        customer_id = customer_response.json()["id"]
        
        # Create location
        location_data = {
            "location_code": "DATELOC",
            "location_name": "Date Location",
            "location_type": "WAREHOUSE",
            "address_line1": "456 Date Avenue",
            "city": "Date City",
            "state": "DC",
            "postal_code": "54321",
            "country": "USA"
        }
        location_response = client.post("/api/master-data/locations/", json=location_data, headers=auth_headers)
        location_id = location_response.json()["id"]
        
        transaction_data = {
            "transaction_number": "INVALIDDATE001",
            "transaction_type": "RENTAL",
            "transaction_date": "2024-01-01T12:00:00",
            "customer_id": customer_id,
            "location_id": location_id,
            "rental_start_date": "2024-01-10",
            "rental_end_date": "2024-01-05",  # End date before start date
            "notes": "Invalid date range transaction"
        }
        response = client.post("/api/transactions/headers/", json=transaction_data, headers=auth_headers)
        assert response.status_code == 422


class TestNotFoundErrors:
    """Test not found error scenarios"""
    
    def test_get_nonexistent_customer(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent customer"""
        fake_id = str(uuid4())
        response = client.get(f"/api/customers/customers/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_nonexistent_customer(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent customer"""
        fake_id = str(uuid4())
        update_data = {
            "first_name": "Updated Name"
        }
        response = client.put(f"/api/customers/customers/{fake_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_nonexistent_customer(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent customer"""
        fake_id = str(uuid4())
        response = client.delete(f"/api/customers/customers/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_nonexistent_supplier(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent supplier"""
        fake_id = str(uuid4())
        response = client.get(f"/api/suppliers/suppliers/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_nonexistent_item(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent item"""
        fake_id = str(uuid4())
        response = client.get(f"/api/inventory/items/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_nonexistent_inventory_unit(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent inventory unit"""
        fake_id = str(uuid4())
        response = client.get(f"/api/inventory/units/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_nonexistent_transaction(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent transaction"""
        fake_id = str(uuid4())
        response = client.get(f"/api/transactions/headers/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_nonexistent_brand(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent brand"""
        fake_id = str(uuid4())
        response = client.get(f"/api/master-data/brands/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_nonexistent_category(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent category"""
        fake_id = str(uuid4())
        response = client.get(f"/api/master-data/categories/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_nonexistent_location(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent location"""
        fake_id = str(uuid4())
        response = client.get(f"/api/master-data/locations/{fake_id}", headers=auth_headers)
        assert response.status_code == 404


class TestConflictErrors:
    """Test conflict error scenarios"""
    
    def test_create_duplicate_customer_code(self, client: TestClient, auth_headers: dict):
        """Test creating customer with duplicate customer code"""
        customer_data = {
            "customer_code": "DUPLICATE001",
            "customer_type": "BUSINESS",
            "first_name": "First",
            "last_name": "Customer",
            "email": "first@example.com",
            "phone": "+1234567890",
            "address_line1": "123 First Street",
            "city": "First City",
            "state": "FC",
            "postal_code": "12345",
            "country": "USA",
            "payment_terms": "30 days"
        }
        
        # Create first customer
        response1 = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create duplicate
        customer_data["first_name"] = "Second"
        customer_data["email"] = "second@example.com"
        response2 = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert response2.status_code == 400  # Should be conflict error
    
    def test_create_duplicate_brand_code(self, client: TestClient, auth_headers: dict):
        """Test creating brand with duplicate brand code"""
        brand_data = {
            "brand_code": "DUPBRAND",
            "brand_name": "First Brand",
            "description": "First brand"
        }
        
        # Create first brand
        response1 = client.post("/api/master-data/brands/", json=brand_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create duplicate
        brand_data["brand_name"] = "Second Brand"
        response2 = client.post("/api/master-data/brands/", json=brand_data, headers=auth_headers)
        assert response2.status_code == 400  # Should be conflict error
    
    def test_create_duplicate_item_code(self, client: TestClient, auth_headers: dict):
        """Test creating item with duplicate item code"""
        # Create dependencies first
        brand_data = {
            "brand_code": "ITEMBRAND",
            "brand_name": "Item Brand",
            "description": "Brand for item testing"
        }
        brand_response = client.post("/api/master-data/brands/", json=brand_data, headers=auth_headers)
        brand_id = brand_response.json()["id"]
        
        category_data = {
            "category_code": "ITEMCAT",
            "category_name": "Item Category",
            "description": "Category for item testing"
        }
        category_response = client.post("/api/master-data/categories/", json=category_data, headers=auth_headers)
        category_id = category_response.json()["id"]
        
        item_data = {
            "item_code": "DUPITEM001",
            "item_name": "First Item",
            "description": "First item",
            "category_id": category_id,
            "brand_id": brand_id,
            "item_type": "EQUIPMENT",
            "unit_of_measure": "UNIT",
            "rental_rate_daily": 100.00,
            "sale_price": 10000.00,
            "cost_price": 8000.00
        }
        
        # Create first item
        response1 = client.post("/api/inventory/items/", json=item_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create duplicate
        item_data["item_name"] = "Second Item"
        response2 = client.post("/api/inventory/items/", json=item_data, headers=auth_headers)
        assert response2.status_code == 400  # Should be conflict error


class TestPermissionErrors:
    """Test permission and authorization error scenarios"""
    
    def test_regular_user_access_admin_endpoints(self, client: TestClient, auth_headers: dict):
        """Test regular user accessing admin-only endpoints"""
        # These should return 403 if proper RBAC is implemented
        admin_endpoints = [
            "/api/users/",
            "/api/users/roles/",
            "/api/system/settings/",
            "/api/system/audit-logs/"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            # Should be 403 (Forbidden) or 401 (Unauthorized) depending on implementation
            assert response.status_code in [401, 403, 404]
    
    def test_create_user_without_admin_privileges(self, client: TestClient, auth_headers: dict):
        """Test creating user without admin privileges"""
        user_data = {
            "username": "unauthorizedcreate",
            "email": "unauth@example.com",
            "password": "Password123",
            "full_name": "Unauthorized User"
        }
        response = client.post("/api/users/", json=user_data, headers=auth_headers)
        assert response.status_code in [401, 403, 404]
    
    def test_delete_user_without_admin_privileges(self, client: TestClient, auth_headers: dict):
        """Test deleting user without admin privileges"""
        fake_id = str(uuid4())
        response = client.delete(f"/api/users/{fake_id}", headers=auth_headers)
        assert response.status_code in [401, 403, 404]


class TestMalformedRequestErrors:
    """Test malformed request error scenarios"""
    
    def test_invalid_json_format(self, client: TestClient, auth_headers: dict):
        """Test sending invalid JSON format"""
        invalid_json = '{"customer_code": "TEST001", "invalid_json"}'
        response = client.post(
            "/api/customers/customers/",
            data=invalid_json,
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_invalid_uuid_format(self, client: TestClient, auth_headers: dict):
        """Test using invalid UUID format in path parameters"""
        invalid_uuid = "not-a-valid-uuid"
        response = client.get(f"/api/customers/customers/{invalid_uuid}", headers=auth_headers)
        assert response.status_code == 422
    
    def test_invalid_query_parameters(self, client: TestClient, auth_headers: dict):
        """Test invalid query parameters"""
        # Test with negative skip/limit values
        response = client.get("/api/customers/customers/?skip=-1&limit=-5", headers=auth_headers)
        assert response.status_code == 422
    
    def test_missing_content_type_header(self, client: TestClient, auth_headers: dict):
        """Test POST request without Content-Type header"""
        customer_data = {
            "customer_code": "NOHEADER001",
            "customer_type": "BUSINESS",
            "first_name": "No",
            "last_name": "Header",
            "email": "noheader@example.com"
        }
        
        # Remove Content-Type header
        headers_without_content_type = {k: v for k, v in auth_headers.items() if k != "Content-Type"}
        
        response = client.post(
            "/api/customers/customers/",
            json=customer_data,
            headers=headers_without_content_type
        )
        # FastAPI usually handles this gracefully, but test behavior
        assert response.status_code in [200, 201, 422, 415]


class TestBusinessLogicErrors:
    """Test business logic validation errors"""
    
    def test_rental_transaction_without_rental_dates(self, client: TestClient, auth_headers: dict):
        """Test creating rental transaction without rental dates"""
        # Create customer and location first
        customer_data = {
            "customer_code": "RENTALCUST001",
            "customer_type": "BUSINESS",
            "first_name": "Rental",
            "last_name": "Customer",
            "email": "rental@test.com",
            "phone": "+1234567890",
            "address_line1": "123 Rental Street",
            "city": "Rental City",
            "state": "RC",
            "postal_code": "12345",
            "country": "USA",
            "payment_terms": "30 days"
        }
        customer_response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        customer_id = customer_response.json()["id"]
        
        location_data = {
            "location_code": "RENTALLOC",
            "location_name": "Rental Location",
            "location_type": "WAREHOUSE",
            "address_line1": "456 Rental Avenue",
            "city": "Rental City",
            "state": "RC",
            "postal_code": "54321",
            "country": "USA"
        }
        location_response = client.post("/api/master-data/locations/", json=location_data, headers=auth_headers)
        location_id = location_response.json()["id"]
        
        transaction_data = {
            "transaction_number": "NORENTAL001",
            "transaction_type": "RENTAL",
            "transaction_date": "2024-01-01T12:00:00",
            "customer_id": customer_id,
            "location_id": location_id,
            # Missing rental_start_date and rental_end_date for RENTAL type
            "notes": "Rental without dates"
        }
        response = client.post("/api/transactions/headers/", json=transaction_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_negative_credit_limit(self, client: TestClient, auth_headers: dict):
        """Test creating customer with negative credit limit"""
        customer_data = {
            "customer_code": "NEGCREDIT001",
            "customer_type": "BUSINESS",
            "first_name": "Negative",
            "last_name": "Credit",
            "email": "negcredit@test.com",
            "phone": "+1234567890",
            "address_line1": "123 Negative Street",
            "city": "Negative City",
            "state": "NC",
            "postal_code": "12345",
            "country": "USA",
            "credit_limit": -1000.0,  # Negative credit limit
            "payment_terms": "30 days"
        }
        response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_zero_quantity_transaction_line(self, client: TestClient, auth_headers: dict):
        """Test creating transaction line with zero quantity"""
        # This test would require creating a full transaction first
        # Then trying to add a line with zero quantity
        # Implementation depends on business rules
        pass  # Skip for now as it requires complex setup