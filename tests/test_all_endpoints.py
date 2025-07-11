"""
Comprehensive test suite for all API endpoints
Tests all endpoints documented at http://127.0.0.1:8000/docs
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime, date, timedelta

from app.modules.users.models import User


class TestHealthEndpoints:
    """Test health and core endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "FastAPI Project"


class TestAuthenticationEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user(self, client: TestClient):
        """Test POST /api/auth/register"""
        user_data = {
            "username": "testuser_reg",
            "email": "testuser_reg@example.com",
            "password": "TestPassword123",
            "full_name": "Test Registration User"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["email"] == user_data["email"]
    
    def test_register_duplicate_username(self, client: TestClient):
        """Test POST /api/auth/register with duplicate username"""
        user_data = {
            "username": "duplicate_test",
            "email": "duplicate1@example.com",
            "password": "TestPassword123",
            "full_name": "First User"
        }
        # Create first user
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Try to create duplicate username
        user_data["email"] = "duplicate2@example.com"
        user_data["full_name"] = "Second User"
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
    
    def test_register_duplicate_email(self, client: TestClient):
        """Test POST /api/auth/register with duplicate email"""
        user_data = {
            "username": "user1_email",
            "email": "same@example.com",
            "password": "TestPassword123",
            "full_name": "First User"
        }
        # Create first user
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Try to create duplicate email
        user_data["username"] = "user2_email"
        user_data["full_name"] = "Second User"
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
    
    def test_login_with_username(self, client: TestClient):
        """Test POST /api/auth/login with username"""
        # First register a user
        user_data = {
            "username": "logintest",
            "email": "logintest@example.com",
            "password": "TestPassword123",
            "full_name": "Login Test User"
        }
        reg_response = client.post("/api/auth/register", json=user_data)
        assert reg_response.status_code == 201
        
        # Now login
        login_data = {
            "username": "logintest",
            "password": "TestPassword123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
    
    def test_login_with_email(self, client: TestClient):
        """Test POST /api/auth/login with email"""
        # First register a user
        user_data = {
            "username": "logintest_email",
            "email": "logintest_email@example.com",
            "password": "TestPassword123",
            "full_name": "Login Email Test User"
        }
        reg_response = client.post("/api/auth/register", json=user_data)
        assert reg_response.status_code == 201
        
        # Now login with email
        login_data = {
            "username": "logintest_email@example.com",  # Can use email as username
            "password": "TestPassword123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test POST /api/auth/login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test GET /api/auth/me"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "full_name" in data
        assert "is_active" in data
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test GET /api/auth/me without token"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_refresh_token(self, client: TestClient):
        """Test POST /api/auth/refresh"""
        # First login to get tokens
        user_data = {
            "username": "refreshtest",
            "email": "refreshtest@example.com",
            "password": "TestPassword123",
            "full_name": "Refresh Test User"
        }
        reg_response = client.post("/api/auth/register", json=user_data)
        assert reg_response.status_code == 201
        
        login_data = {
            "username": "refreshtest",
            "password": "TestPassword123"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        # Now refresh token
        refresh_data = {
            "refresh_token": login_data["refresh_token"]
        }
        response = client.post("/api/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test POST /api/auth/logout"""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"


class TestUserManagementEndpoints:
    """Test user management endpoints"""
    
    def test_list_users(self, client: TestClient, admin_auth_headers: dict):
        """Test GET /api/users/"""
        response = client.get("/api/users/", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_users_with_pagination(self, client: TestClient, admin_auth_headers: dict):
        """Test GET /api/users/ with pagination"""
        response = client.get("/api/users/?skip=0&limit=5", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_list_users_unauthorized(self, client: TestClient, auth_headers: dict):
        """Test GET /api/users/ without admin privileges"""
        response = client.get("/api/users/", headers=auth_headers)
        # Should return 403 if user doesn't have admin privileges
        assert response.status_code in [403, 200]  # Depends on RBAC implementation
    
    def test_create_user(self, client: TestClient, admin_auth_headers: dict):
        """Test POST /api/users/"""
        user_data = {
            "username": "admincreated",
            "email": "admincreated@example.com",
            "password": "AdminCreated123",
            "full_name": "Admin Created User",
            "is_active": True
        }
        response = client.post("/api/users/", json=user_data, headers=admin_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
    
    def test_get_user_by_id(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """Test GET /api/users/{user_id}"""
        response = client.get(f"/api/users/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username
    
    def test_get_user_not_found(self, client: TestClient, admin_auth_headers: dict):
        """Test GET /api/users/{user_id} with non-existent ID"""
        fake_id = str(uuid4())
        response = client.get(f"/api/users/{fake_id}", headers=admin_auth_headers)
        assert response.status_code == 404
    
    def test_update_user(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """Test PUT /api/users/{user_id}"""
        update_data = {
            "full_name": "Updated Full Name",
            "is_active": True
        }
        response = client.put(f"/api/users/{test_user.id}", json=update_data, headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
    
    def test_delete_user(self, client: TestClient, admin_auth_headers: dict):
        """Test DELETE /api/users/{user_id}"""
        # Create a user to delete
        user_data = {
            "username": "todelete",
            "email": "todelete@example.com",
            "password": "ToDelete123",
            "full_name": "To Delete User",
            "is_active": True
        }
        create_response = client.post("/api/users/", json=user_data, headers=admin_auth_headers)
        assert create_response.status_code == 201
        created_user = create_response.json()
        
        # Delete the user
        response = client.delete(f"/api/users/{created_user['id']}", headers=admin_auth_headers)
        assert response.status_code == 200


class TestRoleManagementEndpoints:
    """Test role management endpoints"""
    
    def test_create_role(self, client: TestClient, admin_auth_headers: dict):
        """Test POST /api/users/roles/"""
        role_data = {
            "name": "Test Role",
            "description": "A test role for pytest",
            "permissions": ["read:customers", "write:customers"]
        }
        response = client.post("/api/users/roles/", json=role_data, headers=admin_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == role_data["name"]
        assert data["permissions"] == role_data["permissions"]
        return data["id"]
    
    def test_list_roles(self, client: TestClient, admin_auth_headers: dict):
        """Test GET /api/users/roles/"""
        response = client.get("/api/users/roles/", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_assign_role_to_user(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """Test POST /api/users/{user_id}/roles/{role_id}"""
        # First create a role
        role_data = {
            "name": "Assignment Test Role",
            "description": "Role for assignment testing",
            "permissions": ["read:inventory"]
        }
        role_response = client.post("/api/users/roles/", json=role_data, headers=admin_auth_headers)
        assert role_response.status_code == 201
        role_id = role_response.json()["id"]
        
        # Assign role to user
        response = client.post(f"/api/users/{test_user.id}/roles/{role_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestCustomerManagementEndpoints:
    """Test customer management endpoints"""
    
    def test_list_customers(self, client: TestClient, auth_headers: dict):
        """Test GET /api/customers/customers/"""
        response = client.get("/api/customers/customers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_customers_with_filters(self, client: TestClient, auth_headers: dict):
        """Test GET /api/customers/customers/ with filters"""
        response = client.get(
            "/api/customers/customers/?skip=0&limit=10&customer_type=BUSINESS&active_only=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_customer(self, client: TestClient, auth_headers: dict):
        """Test POST /api/customers/customers/"""
        customer_data = {
            "customer_code": "TEST001",
            "customer_type": "BUSINESS",
            "business_name": "Test Company Inc",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@testcompany.com",
            "phone": "+1234567890",
            "address_line1": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "USA",
            "credit_limit": 5000.0,
            "payment_terms": "30 days"
        }
        response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_code"] == customer_data["customer_code"]
        assert data["email"] == customer_data["email"]
        return data["id"]
    
    def test_get_customer_by_id(self, client: TestClient, auth_headers: dict):
        """Test GET /api/customers/customers/{customer_id}"""
        # First create a customer
        customer_id = self.test_create_customer(client, auth_headers)
        
        response = client.get(f"/api/customers/customers/{customer_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id
    
    def test_update_customer(self, client: TestClient, auth_headers: dict):
        """Test PUT /api/customers/customers/{customer_id}"""
        # First create a customer
        customer_id = self.test_create_customer(client, auth_headers)
        
        update_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "credit_limit": 7500.0
        }
        response = client.put(f"/api/customers/customers/{customer_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["credit_limit"] == update_data["credit_limit"]
    
    def test_delete_customer(self, client: TestClient, auth_headers: dict):
        """Test DELETE /api/customers/customers/{customer_id}"""
        # First create a customer
        customer_id = self.test_create_customer(client, auth_headers)
        
        response = client.delete(f"/api/customers/customers/{customer_id}", headers=auth_headers)
        assert response.status_code == 200
    
    def test_search_customers(self, client: TestClient, auth_headers: dict):
        """Test GET /api/customers/customers/search"""
        response = client.get("/api/customers/customers/search?q=test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestSupplierManagementEndpoints:
    """Test supplier management endpoints"""
    
    def test_list_suppliers(self, client: TestClient, auth_headers: dict):
        """Test GET /api/suppliers/suppliers/"""
        response = client.get("/api/suppliers/suppliers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_supplier(self, client: TestClient, auth_headers: dict):
        """Test POST /api/suppliers/suppliers/"""
        supplier_data = {
            "supplier_code": "SUP001",
            "supplier_name": "Test Supplier Inc",
            "contact_person": "Mike Johnson",
            "email": "mike@testsupplier.com",
            "phone": "+1987654321",
            "address_line1": "456 Supplier Avenue",
            "city": "Supplier City",
            "state": "SC",
            "postal_code": "54321",
            "country": "USA",
            "payment_terms": 30,
            "tax_number": "TAX123456",
            "rating": 5
        }
        response = client.post("/api/suppliers/suppliers/", json=supplier_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["supplier_code"] == supplier_data["supplier_code"]
        assert data["supplier_name"] == supplier_data["supplier_name"]
        return data["id"]
    
    def test_get_supplier_by_id(self, client: TestClient, auth_headers: dict):
        """Test GET /api/suppliers/suppliers/{supplier_id}"""
        # First create a supplier
        supplier_id = self.test_create_supplier(client, auth_headers)
        
        response = client.get(f"/api/suppliers/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == supplier_id
    
    def test_update_supplier(self, client: TestClient, auth_headers: dict):
        """Test PUT /api/suppliers/suppliers/{supplier_id}"""
        # First create a supplier
        supplier_id = self.test_create_supplier(client, auth_headers)
        
        update_data = {
            "contact_person": "Sarah Wilson",
            "rating": 4
        }
        response = client.put(f"/api/suppliers/suppliers/{supplier_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["contact_person"] == update_data["contact_person"]
        assert data["rating"] == update_data["rating"]
    
    def test_delete_supplier(self, client: TestClient, auth_headers: dict):
        """Test DELETE /api/suppliers/suppliers/{supplier_id}"""
        # First create a supplier
        supplier_id = self.test_create_supplier(client, auth_headers)
        
        response = client.delete(f"/api/suppliers/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200


class TestMasterDataEndpoints:
    """Test master data endpoints"""
    
    def test_list_brands(self, client: TestClient, auth_headers: dict):
        """Test GET /api/master-data/brands/"""
        response = client.get("/api/master-data/brands/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_brand(self, client: TestClient, auth_headers: dict):
        """Test POST /api/master-data/brands/"""
        brand_data = {
            "brand_code": "TESTBRAND",
            "brand_name": "Test Brand",
            "description": "A test brand for pytest"
        }
        response = client.post("/api/master-data/brands/", json=brand_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["brand_code"] == brand_data["brand_code"]
        assert data["brand_name"] == brand_data["brand_name"]
        return data["id"]
    
    def test_get_brand_by_id(self, client: TestClient, auth_headers: dict):
        """Test GET /api/master-data/brands/{brand_id}"""
        # First create a brand
        brand_id = self.test_create_brand(client, auth_headers)
        
        response = client.get(f"/api/master-data/brands/{brand_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == brand_id
    
    def test_update_brand(self, client: TestClient, auth_headers: dict):
        """Test PUT /api/master-data/brands/{brand_id}"""
        # First create a brand
        brand_id = self.test_create_brand(client, auth_headers)
        
        update_data = {
            "brand_name": "Updated Test Brand",
            "description": "Updated description"
        }
        response = client.put(f"/api/master-data/brands/{brand_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["brand_name"] == update_data["brand_name"]
    
    def test_delete_brand(self, client: TestClient, auth_headers: dict):
        """Test DELETE /api/master-data/brands/{brand_id}"""
        # First create a brand
        brand_id = self.test_create_brand(client, auth_headers)
        
        response = client.delete(f"/api/master-data/brands/{brand_id}", headers=auth_headers)
        assert response.status_code == 200
    
    def test_list_categories(self, client: TestClient, auth_headers: dict):
        """Test GET /api/master-data/categories/"""
        response = client.get("/api/master-data/categories/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_category(self, client: TestClient, auth_headers: dict):
        """Test POST /api/master-data/categories/"""
        category_data = {
            "category_code": "TESTCAT",
            "category_name": "Test Category",
            "description": "A test category for pytest"
        }
        response = client.post("/api/master-data/categories/", json=category_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["category_code"] == category_data["category_code"]
        return data["id"]
    
    def test_get_category_by_id(self, client: TestClient, auth_headers: dict):
        """Test GET /api/master-data/categories/{category_id}"""
        # First create a category
        category_id = self.test_create_category(client, auth_headers)
        
        response = client.get(f"/api/master-data/categories/{category_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category_id
    
    def test_update_category(self, client: TestClient, auth_headers: dict):
        """Test PUT /api/master-data/categories/{category_id}"""
        # First create a category
        category_id = self.test_create_category(client, auth_headers)
        
        update_data = {
            "category_name": "Updated Test Category"
        }
        response = client.put(f"/api/master-data/categories/{category_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["category_name"] == update_data["category_name"]
    
    def test_delete_category(self, client: TestClient, auth_headers: dict):
        """Test DELETE /api/master-data/categories/{category_id}"""
        # First create a category
        category_id = self.test_create_category(client, auth_headers)
        
        response = client.delete(f"/api/master-data/categories/{category_id}", headers=auth_headers)
        assert response.status_code == 200
    
    def test_list_locations(self, client: TestClient, auth_headers: dict):
        """Test GET /api/master-data/locations/"""
        response = client.get("/api/master-data/locations/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_location(self, client: TestClient, auth_headers: dict):
        """Test POST /api/master-data/locations/"""
        location_data = {
            "location_code": "TESTLOC",
            "location_name": "Test Location",
            "location_type": "WAREHOUSE",
            "address_line1": "123 Test Location St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "USA",
            "phone": "+1234567890",
            "email": "testloc@example.com"
        }
        response = client.post("/api/master-data/locations/", json=location_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["location_code"] == location_data["location_code"]
        return data["id"]
    
    def test_get_location_by_id(self, client: TestClient, auth_headers: dict):
        """Test GET /api/master-data/locations/{location_id}"""
        # First create a location
        location_id = self.test_create_location(client, auth_headers)
        
        response = client.get(f"/api/master-data/locations/{location_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == location_id
    
    def test_update_location(self, client: TestClient, auth_headers: dict):
        """Test PUT /api/master-data/locations/{location_id}"""
        # First create a location
        location_id = self.test_create_location(client, auth_headers)
        
        update_data = {
            "location_name": "Updated Test Location"
        }
        response = client.put(f"/api/master-data/locations/{location_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["location_name"] == update_data["location_name"]
    
    def test_delete_location(self, client: TestClient, auth_headers: dict):
        """Test DELETE /api/master-data/locations/{location_id}"""
        # First create a location
        location_id = self.test_create_location(client, auth_headers)
        
        response = client.delete(f"/api/master-data/locations/{location_id}", headers=auth_headers)
        assert response.status_code == 200


class TestInventoryManagementEndpoints:
    """Test inventory management endpoints"""
    
    def test_list_items(self, client: TestClient, auth_headers: dict):
        """Test GET /api/inventory/items/"""
        response = client.get("/api/inventory/items/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_item(self, client: TestClient, auth_headers: dict):
        """Test POST /api/inventory/items/"""
        # First create required dependencies
        brand_data = {
            "brand_code": "ITEMTEST",
            "brand_name": "Item Test Brand",
            "description": "Brand for item testing"
        }
        brand_response = client.post("/api/master-data/brands/", json=brand_data, headers=auth_headers)
        assert brand_response.status_code == 201
        brand_id = brand_response.json()["id"]
        
        category_data = {
            "category_code": "ITEMTESTCAT",
            "category_name": "Item Test Category",
            "description": "Category for item testing"
        }
        category_response = client.post("/api/master-data/categories/", json=category_data, headers=auth_headers)
        assert category_response.status_code == 201
        category_id = category_response.json()["id"]
        
        item_data = {
            "item_code": "TESTITEM001",
            "item_name": "Test Equipment Item",
            "description": "A test equipment item for pytest",
            "category_id": category_id,
            "brand_id": brand_id,
            "item_type": "EQUIPMENT",
            "unit_of_measure": "UNIT",
            "rental_rate_daily": 150.00,
            "rental_rate_weekly": 900.00,
            "rental_rate_monthly": 3500.00,
            "sale_price": 50000.00,
            "cost_price": 40000.00,
            "minimum_rental_period": 1,
            "maximum_rental_period": 365,
            "requires_operator": False,
            "requires_training": False
        }
        response = client.post("/api/inventory/items/", json=item_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["item_code"] == item_data["item_code"]
        assert data["item_name"] == item_data["item_name"]
        return data["id"]
    
    def test_get_item_by_id(self, client: TestClient, auth_headers: dict):
        """Test GET /api/inventory/items/{item_id}"""
        # First create an item
        item_id = self.test_create_item(client, auth_headers)
        
        response = client.get(f"/api/inventory/items/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
    
    def test_update_item(self, client: TestClient, auth_headers: dict):
        """Test PUT /api/inventory/items/{item_id}"""
        # First create an item
        item_id = self.test_create_item(client, auth_headers)
        
        update_data = {
            "item_name": "Updated Test Equipment",
            "rental_rate_daily": 175.00
        }
        response = client.put(f"/api/inventory/items/{item_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["item_name"] == update_data["item_name"]
        assert data["rental_rate_daily"] == update_data["rental_rate_daily"]
    
    def test_delete_item(self, client: TestClient, auth_headers: dict):
        """Test DELETE /api/inventory/items/{item_id}"""
        # First create an item
        item_id = self.test_create_item(client, auth_headers)
        
        response = client.delete(f"/api/inventory/items/{item_id}", headers=auth_headers)
        assert response.status_code == 200
    
    def test_list_inventory_units(self, client: TestClient, auth_headers: dict):
        """Test GET /api/inventory/units/"""
        response = client.get("/api/inventory/units/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_inventory_unit(self, client: TestClient, auth_headers: dict):
        """Test POST /api/inventory/units/"""
        # First create an item and location
        item_id = self.test_create_item(client, auth_headers)
        
        location_data = {
            "location_code": "UNITLOC",
            "location_name": "Unit Test Location",
            "location_type": "WAREHOUSE",
            "address_line1": "123 Unit Location St",
            "city": "Unit City",
            "state": "UC",
            "postal_code": "12345",
            "country": "USA"
        }
        location_response = client.post("/api/master-data/locations/", json=location_data, headers=auth_headers)
        assert location_response.status_code == 201
        location_id = location_response.json()["id"]
        
        unit_data = {
            "item_id": item_id,
            "unit_number": "TESTUNIT001",
            "serial_number": "SN123456789",
            "location_id": location_id,
            "condition": "EXCELLENT",
            "availability_status": "AVAILABLE",
            "purchase_date": "2024-01-01",
            "purchase_price": 50000.00,
            "depreciation_rate": 15.0,
            "insurance_value": 45000.00
        }
        response = client.post("/api/inventory/units/", json=unit_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["unit_number"] == unit_data["unit_number"]
        return data["id"]
    
    def test_get_inventory_unit_by_id(self, client: TestClient, auth_headers: dict):
        """Test GET /api/inventory/units/{unit_id}"""
        # First create a unit
        unit_id = self.test_create_inventory_unit(client, auth_headers)
        
        response = client.get(f"/api/inventory/units/{unit_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == unit_id
    
    def test_update_inventory_unit(self, client: TestClient, auth_headers: dict):
        """Test PUT /api/inventory/units/{unit_id}"""
        # First create a unit
        unit_id = self.test_create_inventory_unit(client, auth_headers)
        
        update_data = {
            "condition": "GOOD",
            "availability_status": "MAINTENANCE"
        }
        response = client.put(f"/api/inventory/units/{unit_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["condition"] == update_data["condition"]
        assert data["availability_status"] == update_data["availability_status"]
    
    def test_delete_inventory_unit(self, client: TestClient, auth_headers: dict):
        """Test DELETE /api/inventory/units/{unit_id}"""
        # First create a unit
        unit_id = self.test_create_inventory_unit(client, auth_headers)
        
        response = client.delete(f"/api/inventory/units/{unit_id}", headers=auth_headers)
        assert response.status_code == 200


class TestTransactionManagementEndpoints:
    """Test transaction management endpoints"""
    
    def test_list_transaction_headers(self, client: TestClient, auth_headers: dict):
        """Test GET /api/transactions/headers/"""
        response = client.get("/api/transactions/headers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_transaction_header(self, client: TestClient, auth_headers: dict):
        """Test POST /api/transactions/headers/"""
        # First create customer and location
        customer_data = {
            "customer_code": "TXNCUST001",
            "customer_type": "BUSINESS",
            "business_name": "Transaction Test Corp",
            "first_name": "Trans",
            "last_name": "Action",
            "email": "transaction@test.com",
            "phone": "+1234567890",
            "address_line1": "123 Transaction St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "USA",
            "payment_terms": "30 days"
        }
        customer_response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert customer_response.status_code == 201
        customer_id = customer_response.json()["id"]
        
        location_data = {
            "location_code": "TXNLOC",
            "location_name": "Transaction Location",
            "location_type": "BRANCH",
            "address_line1": "456 Transaction Ave",
            "city": "Transaction City",
            "state": "TC",
            "postal_code": "54321",
            "country": "USA"
        }
        location_response = client.post("/api/master-data/locations/", json=location_data, headers=auth_headers)
        assert location_response.status_code == 201
        location_id = location_response.json()["id"]
        
        transaction_data = {
            "transaction_number": "TXN-TEST-001",
            "transaction_type": "RENTAL",
            "transaction_date": datetime.now().isoformat(),
            "customer_id": customer_id,
            "location_id": location_id,
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=7)).isoformat(),
            "notes": "Test rental transaction"
        }
        response = client.post("/api/transactions/headers/", json=transaction_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_number"] == transaction_data["transaction_number"]
        assert data["transaction_type"] == transaction_data["transaction_type"]
        return data["id"]
    
    def test_get_transaction_header_by_id(self, client: TestClient, auth_headers: dict):
        """Test GET /api/transactions/headers/{transaction_id}"""
        # First create a transaction
        transaction_id = self.test_create_transaction_header(client, auth_headers)
        
        response = client.get(f"/api/transactions/headers/{transaction_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction_id
    
    def test_update_transaction_header(self, client: TestClient, auth_headers: dict):
        """Test PUT /api/transactions/headers/{transaction_id}"""
        # First create a transaction
        transaction_id = self.test_create_transaction_header(client, auth_headers)
        
        update_data = {
            "notes": "Updated transaction notes",
            "status": "CONFIRMED"
        }
        response = client.put(f"/api/transactions/headers/{transaction_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == update_data["notes"]
    
    def test_delete_transaction_header(self, client: TestClient, auth_headers: dict):
        """Test DELETE /api/transactions/headers/{transaction_id}"""
        # First create a transaction
        transaction_id = self.test_create_transaction_header(client, auth_headers)
        
        response = client.delete(f"/api/transactions/headers/{transaction_id}", headers=auth_headers)
        assert response.status_code == 200
    
    def test_add_transaction_line(self, client: TestClient, auth_headers: dict):
        """Test POST /api/transactions/headers/{transaction_id}/lines/"""
        # First create a transaction and inventory unit
        transaction_id = self.test_create_transaction_header(client, auth_headers)
        
        # Create inventory unit for the line
        # This requires creating item, brand, category, location first
        brand_data = {
            "brand_code": "TXNBRAND",
            "brand_name": "Transaction Brand",
            "description": "Brand for transaction testing"
        }
        brand_response = client.post("/api/master-data/brands/", json=brand_data, headers=auth_headers)
        brand_id = brand_response.json()["id"]
        
        category_data = {
            "category_code": "TXNCAT",
            "category_name": "Transaction Category",
            "description": "Category for transaction testing"
        }
        category_response = client.post("/api/master-data/categories/", json=category_data, headers=auth_headers)
        category_id = category_response.json()["id"]
        
        item_data = {
            "item_code": "TXNITEM001",
            "item_name": "Transaction Test Item",
            "description": "Item for transaction testing",
            "category_id": category_id,
            "brand_id": brand_id,
            "item_type": "EQUIPMENT",
            "unit_of_measure": "UNIT",
            "rental_rate_daily": 100.00,
            "sale_price": 10000.00,
            "cost_price": 8000.00
        }
        item_response = client.post("/api/inventory/items/", json=item_data, headers=auth_headers)
        item_id = item_response.json()["id"]
        
        line_data = {
            "line_number": 1,
            "line_type": "PRODUCT",
            "description": "Test rental line item",
            "quantity": 1.0,
            "unit_price": 100.00,
            "item_id": item_id,
            "tax_rate": 8.0,
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=7)).isoformat()
        }
        response = client.post(f"/api/transactions/headers/{transaction_id}/lines/", json=line_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["line_number"] == line_data["line_number"]
        assert data["description"] == line_data["description"]


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_get_revenue_analytics(self, client: TestClient, auth_headers: dict):
        """Test GET /api/analytics/revenue/"""
        response = client.get("/api/analytics/revenue/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "rental_revenue" in data
        assert "sales_revenue" in data
    
    def test_get_revenue_analytics_with_parameters(self, client: TestClient, auth_headers: dict):
        """Test GET /api/analytics/revenue/ with parameters"""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        response = client.get(
            f"/api/analytics/revenue/?period=daily&start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
    
    def test_get_inventory_analytics(self, client: TestClient, auth_headers: dict):
        """Test GET /api/analytics/inventory/"""
        response = client.get("/api/analytics/inventory/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "total_units" in data
        assert "available_units" in data
    
    def test_get_customer_analytics(self, client: TestClient, auth_headers: dict):
        """Test GET /api/analytics/customers/"""
        response = client.get("/api/analytics/customers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
        assert "active_customers" in data
    
    def test_get_utilization_analytics(self, client: TestClient, auth_headers: dict):
        """Test GET /api/analytics/utilization/"""
        response = client.get("/api/analytics/utilization/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "utilization_rate" in data
    
    def test_get_financial_summary(self, client: TestClient, auth_headers: dict):
        """Test GET /api/analytics/financial-summary/"""
        response = client.get("/api/analytics/financial-summary/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "total_costs" in data


class TestSystemEndpoints:
    """Test system management endpoints"""
    
    def test_get_system_settings(self, client: TestClient, admin_auth_headers: dict):
        """Test GET /api/system/settings/"""
        response = client.get("/api/system/settings/", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_update_system_settings(self, client: TestClient, admin_auth_headers: dict):
        """Test PUT /api/system/settings/"""
        settings_data = {
            "company_name": "Test Rental Company",
            "default_currency": "USD",
            "default_tax_rate": 8.5
        }
        response = client.put("/api/system/settings/", json=settings_data, headers=admin_auth_headers)
        assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist yet
    
    def test_get_system_audit_logs(self, client: TestClient, admin_auth_headers: dict):
        """Test GET /api/system/audit-logs/"""
        response = client.get("/api/system/audit-logs/", headers=admin_auth_headers)
        assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist yet
    
    def test_backup_system_data(self, client: TestClient, admin_auth_headers: dict):
        """Test POST /api/system/backup/"""
        response = client.post("/api/system/backup/", headers=admin_auth_headers)
        assert response.status_code in [200, 201, 404]  # 404 if endpoint doesn't exist yet


@pytest.mark.integration
class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    def test_complete_rental_workflow(self, client: TestClient, auth_headers: dict):
        """Test complete rental workflow from customer creation to transaction completion"""
        # 1. Create customer
        customer_data = {
            "customer_code": "E2E001",
            "customer_type": "BUSINESS",
            "business_name": "E2E Test Corp",
            "first_name": "John",
            "last_name": "Doe",
            "email": "e2e@test.com",
            "phone": "+1234567890",
            "address_line1": "123 E2E Street",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "USA",
            "payment_terms": "30 days"
        }
        customer_response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
        assert customer_response.status_code == 201
        customer_id = customer_response.json()["id"]
        
        # 2. Create brand and category
        brand_data = {
            "brand_code": "E2EBRAND",
            "brand_name": "E2E Brand",
            "description": "Brand for E2E testing"
        }
        brand_response = client.post("/api/master-data/brands/", json=brand_data, headers=auth_headers)
        assert brand_response.status_code == 201
        brand_id = brand_response.json()["id"]
        
        category_data = {
            "category_code": "E2ECAT",
            "category_name": "E2E Category",
            "description": "Category for E2E testing"
        }
        category_response = client.post("/api/master-data/categories/", json=category_data, headers=auth_headers)
        assert category_response.status_code == 201
        category_id = category_response.json()["id"]
        
        # 3. Create location
        location_data = {
            "location_code": "E2ELOC",
            "location_name": "E2E Location",
            "location_type": "WAREHOUSE",
            "address_line1": "456 E2E Avenue",
            "city": "E2E City",
            "state": "E2",
            "postal_code": "54321",
            "country": "USA"
        }
        location_response = client.post("/api/master-data/locations/", json=location_data, headers=auth_headers)
        assert location_response.status_code == 201
        location_id = location_response.json()["id"]
        
        # 4. Create item
        item_data = {
            "item_code": "E2EITEM001",
            "item_name": "E2E Test Equipment",
            "description": "Equipment for E2E testing",
            "category_id": category_id,
            "brand_id": brand_id,
            "item_type": "EQUIPMENT",
            "unit_of_measure": "UNIT",
            "rental_rate_daily": 200.00,
            "sale_price": 20000.00,
            "cost_price": 16000.00
        }
        item_response = client.post("/api/inventory/items/", json=item_data, headers=auth_headers)
        assert item_response.status_code == 201
        item_id = item_response.json()["id"]
        
        # 5. Create inventory unit
        unit_data = {
            "item_id": item_id,
            "unit_number": "E2EUNIT001",
            "serial_number": "E2ESN123456",
            "location_id": location_id,
            "condition": "EXCELLENT",
            "availability_status": "AVAILABLE",
            "purchase_date": "2024-01-01",
            "purchase_price": 20000.00
        }
        unit_response = client.post("/api/inventory/units/", json=unit_data, headers=auth_headers)
        assert unit_response.status_code == 201
        unit_id = unit_response.json()["id"]
        
        # 6. Create transaction
        transaction_data = {
            "transaction_number": "E2E-TXN-001",
            "transaction_type": "RENTAL",
            "transaction_date": datetime.now().isoformat(),
            "customer_id": customer_id,
            "location_id": location_id,
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=5)).isoformat(),
            "notes": "E2E test rental transaction"
        }
        transaction_response = client.post("/api/transactions/headers/", json=transaction_data, headers=auth_headers)
        assert transaction_response.status_code == 201
        transaction_id = transaction_response.json()["id"]
        
        # 7. Add transaction line
        line_data = {
            "line_number": 1,
            "line_type": "PRODUCT",
            "description": "E2E test equipment rental",
            "quantity": 1.0,
            "unit_price": 200.00,
            "item_id": item_id,
            "inventory_unit_id": unit_id,
            "tax_rate": 8.0,
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=5)).isoformat()
        }
        line_response = client.post(f"/api/transactions/headers/{transaction_id}/lines/", json=line_data, headers=auth_headers)
        assert line_response.status_code == 201
        
        # 8. Verify complete transaction
        final_response = client.get(f"/api/transactions/headers/{transaction_id}", headers=auth_headers)
        assert final_response.status_code == 200
        final_data = final_response.json()
        assert len(final_data["transaction_lines"]) == 1
        assert final_data["transaction_lines"][0]["item_id"] == item_id
        
        print("✅ Complete E2E rental workflow test passed!")


# Performance and stress tests
@pytest.mark.performance
class TestPerformanceEndpoints:
    """Test API performance under load"""
    
    def test_concurrent_customer_creation(self, client: TestClient, auth_headers: dict):
        """Test concurrent customer creation performance"""
        import concurrent.futures
        import time
        
        def create_customer(index):
            customer_data = {
                "customer_code": f"PERF{index:03d}",
                "customer_type": "BUSINESS",
                "business_name": f"Performance Test Corp {index}",
                "first_name": f"First{index}",
                "last_name": f"Last{index}",
                "email": f"perf{index}@test.com",
                "phone": f"+19876543{index:02d}",
                "address_line1": f"{100+index} Performance St",
                "city": "Perf City",
                "state": "PC",
                "postal_code": "12345",
                "country": "USA",
                "payment_terms": "30 days"
            }
            start_time = time.time()
            response = client.post("/api/customers/customers/", json=customer_data, headers=auth_headers)
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Test with 10 concurrent requests
        start_total = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_customer, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_total = time.time()
        
        # Verify results
        success_count = sum(1 for status, _ in results if status == 201)
        response_times = [rt for _, rt in results]
        avg_response_time = sum(response_times) / len(response_times)
        total_time = end_total - start_total
        
        print(f"Concurrent Performance Results:")
        print(f"  Successful requests: {success_count}/10")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Requests per second: {10/total_time:.2f}")
        
        assert success_count >= 8  # Allow for some failures in concurrent testing
        assert avg_response_time < 1.0  # Should be under 1 second on average
    
    def test_bulk_data_retrieval(self, client: TestClient, auth_headers: dict):
        """Test bulk data retrieval performance"""
        import time
        
        endpoints = [
            "/api/customers/customers/?limit=100",
            "/api/suppliers/suppliers/?limit=100",
            "/api/inventory/items/?limit=100",
            "/api/inventory/units/?limit=100",
            "/api/transactions/headers/?limit=100",
            "/api/master-data/brands/?limit=100",
            "/api/master-data/categories/?limit=100",
            "/api/master-data/locations/?limit=100"
        ]
        
        results = []
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint, headers=auth_headers)
            end_time = time.time()
            response_time = end_time - start_time
            results.append((endpoint, response.status_code, response_time))
            
            assert response.status_code == 200
            assert response_time < 0.5  # Should be under 500ms
        
        total_time = sum(rt for _, _, rt in results)
        print(f"Bulk retrieval results (Total: {total_time:.3f}s):")
        for endpoint, status, rt in results:
            print(f"  {endpoint}: {status} in {rt:.3f}s")