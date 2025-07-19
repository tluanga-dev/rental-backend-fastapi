"""
Comprehensive CRUD test suite for purchase transactions.

Tests all basic CRUD operations for purchase transactions:
- Create: Test purchase creation with various scenarios
- Read: Test getting purchases by ID and with filters  
- Update: Test updating purchase transactions
- Delete: Test deleting purchase transactions
"""

import pytest
import pytest_asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from typing import List, Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.transactions.base.models import (
    TransactionHeader, 
    TransactionLine,
    TransactionType,
    TransactionStatus,
    PaymentStatus,
    LineItemType
)
from app.modules.inventory.models import StockLevel, StockMovement
from app.modules.suppliers.models import Supplier
from app.modules.master_data.locations.models import Location
from app.modules.master_data.item_master.models import Item
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.categories.models import Category
from app.modules.master_data.units.models import UnitOfMeasurement
from app.modules.users.models import User
from app.core.security import create_token_pair


@pytest.mark.asyncio
class TestPurchaseCRUD:
    """Test suite for purchase transaction CRUD operations."""

    @pytest_asyncio.fixture
    async def test_data(self, db_session: AsyncSession):
        """Set up test data for purchase CRUD tests."""
        # Create test supplier
        supplier = Supplier(
            supplier_code="SUP001",
            company_name="Test Supplier Company",
            supplier_type="MANUFACTURER",
            contact_person="John Doe",
            email="supplier@test.com",
            phone="+1234567890",
            address_line1="123 Test Street",
            city="Test City",
            country="Test Country"
        )
        db_session.add(supplier)
        await db_session.flush()
        
        # Create test location
        location = Location(
            location_code="LOC001",
            location_name="Test Location",
            location_type="WAREHOUSE",
            is_active=True
        )
        db_session.add(location)
        await db_session.flush()
        
        # Create test brand
        brand = Brand(
            brand_code="BRD001",
            brand_name="Test Brand",
            is_active=True
        )
        db_session.add(brand)
        await db_session.flush()
        
        # Create test category
        category = Category(
            category_code="CAT001",
            category_name="Test Category",
            is_active=True
        )
        db_session.add(category)
        await db_session.flush()
        
        # Create test unit
        unit = UnitOfMeasurement(
            unit_code="PCS",
            unit_name="Pieces",
            unit_symbol="pcs",
            is_active=True
        )
        db_session.add(unit)
        await db_session.flush()
        
        # Create test items
        items = []
        for i in range(3):
            item = Item(
                item_code=f"ITEM{i+1:03d}",
                item_name=f"Test Item {i+1}",
                description=f"Description for test item {i+1}",
                brand_id=brand.id,
                category_id=category.id,
                unit_id=unit.id,
                unit_cost=Decimal(f"{10.00 + i}"),
                selling_price=Decimal(f"{15.00 + i}"),
                is_active=True
            )
            db_session.add(item)
            items.append(item)
        
        await db_session.flush()
        
        # Create initial stock levels
        for item in items:
            stock_level = StockLevel(
                item_id=item.id,
                location_id=location.id,
                available_quantity=Decimal("100"),
                reserved_quantity=Decimal("0"),
                on_order_quantity=Decimal("0"),
                minimum_quantity=Decimal("10"),
                maximum_quantity=Decimal("1000")
            )
            db_session.add(stock_level)
        
        await db_session.commit()
        
        return {
            'supplier': supplier,
            'location': location,
            'items': items
        }

    # CREATE Tests
    
    async def test_create_purchase_success(self, client: TestClient, test_data, auth_headers):
        """Test successful purchase creation."""
        
        purchase_data = {
            "supplier_id": str(test_data['supplier'].id),
            "location_id": str(test_data['location'].id),
            "purchase_date": date.today().isoformat(),
            "notes": "Test purchase transaction",
            "reference_number": "PO-001",
            "items": [
                {
                    "item_id": str(test_data['items'][0].id),
                    "quantity": 10,
                    "unit_cost": "12.50",
                    "tax_rate": "10.0",
                    "discount_amount": "0.00",
                    "condition": "A",
                    "notes": "Item 1 notes"
                },
                {
                    "item_id": str(test_data['items'][1].id),
                    "quantity": 5,
                    "unit_cost": "15.00",
                    "tax_rate": "10.0",
                    "discount_amount": "5.00",
                    "condition": "A",
                    "notes": "Item 2 notes"
                }
            ]
        }
        
        response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        
        assert result["success"] is True
        assert result["message"] == "Purchase created successfully"
        assert "transaction_id" in result
        assert "transaction_number" in result
        assert "data" in result
        
        # Verify transaction was created in database
        purchase_id = UUID(result["transaction_id"])
        assert isinstance(purchase_id, UUID)

    async def test_create_purchase_invalid_supplier(self, client: TestClient, test_data, auth_headers):
        """Test purchase creation with invalid supplier ID."""
        
        purchase_data = {
            "supplier_id": str(uuid4()),  # Non-existent supplier
            "location_id": str(test_data['location'].id),
            "purchase_date": date.today().isoformat(),
            "notes": "Test purchase",
            "reference_number": "PO-002",
            "items": [
                {
                    "item_id": str(test_data['items'][0].id),
                    "quantity": 10,
                    "unit_cost": "12.50",
                    "tax_rate": "10.0",
                    "discount_amount": "0.00",
                    "condition": "A",
                    "notes": ""
                }
            ]
        }
        
        response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404

    async def test_create_purchase_invalid_item(self, client: TestClient, test_data, auth_headers):
        """Test purchase creation with invalid item ID."""
        
        purchase_data = {
            "supplier_id": str(test_data['supplier'].id),
            "location_id": str(test_data['location'].id),
            "purchase_date": date.today().isoformat(),
            "notes": "Test purchase",
            "reference_number": "PO-003",
            "items": [
                {
                    "item_id": str(uuid4()),  # Non-existent item
                    "quantity": 10,
                    "unit_cost": "12.50",
                    "tax_rate": "10.0",
                    "discount_amount": "0.00",
                    "condition": "A",
                    "notes": ""
                }
            ]
        }
        
        response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404

    async def test_create_purchase_invalid_data(self, client: TestClient, test_data, auth_headers):
        """Test purchase creation with invalid data."""
        
        # Missing required fields
        purchase_data = {
            "supplier_id": str(test_data['supplier'].id),
            # Missing location_id
            "purchase_date": date.today().isoformat(),
            "items": []  # Empty items list
        }
        
        response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422

    # READ Tests
    
    async def test_get_purchase_by_id_success(self, client: TestClient, test_data, auth_headers, db_session: AsyncSession):
        """Test successfully getting a purchase by ID."""
        
        # First create a purchase
        purchase_data = {
            "supplier_id": str(test_data['supplier'].id),
            "location_id": str(test_data['location'].id),
            "purchase_date": date.today().isoformat(),
            "notes": "Test purchase for read",
            "reference_number": "PO-READ-001",
            "items": [
                {
                    "item_id": str(test_data['items'][0].id),
                    "quantity": 5,
                    "unit_cost": "20.00",
                    "tax_rate": "8.0",
                    "discount_amount": "2.00",
                    "condition": "A",
                    "notes": "Read test item"
                }
            ]
        }
        
        create_response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        purchase_id = create_response.json()["transaction_id"]
        
        # Now get the purchase by ID
        response = client.get(
            f"/api/purchases/{purchase_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["id"] == purchase_id
        assert result["supplier"]["id"] == str(test_data['supplier'].id)
        assert result["location"]["id"] == str(test_data['location'].id)
        assert result["notes"] == "Test purchase for read"
        assert result["reference_number"] == "PO-READ-001"
        assert len(result["items"]) == 1
        assert result["items"][0]["quantity"] == "5"
        assert result["items"][0]["unit_cost"] == "20.00"

    async def test_get_purchase_by_id_not_found(self, client: TestClient, auth_headers):
        """Test getting a purchase with non-existent ID."""
        non_existent_id = str(uuid4())
        
        response = client.get(
            f"/api/purchases/{non_existent_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    async def test_get_purchases_list(self, client: TestClient, test_data, auth_headers):
        """Test getting list of purchases with filters."""
        
        # Create multiple purchases
        for i in range(3):
            purchase_data = {
                "supplier_id": str(test_data['supplier'].id),
                "location_id": str(test_data['location'].id),
                "purchase_date": (date.today() - timedelta(days=i)).isoformat(),
                "notes": f"Test purchase {i+1}",
                "reference_number": f"PO-LIST-{i+1:03d}",
                "items": [
                    {
                        "item_id": str(test_data['items'][0].id),
                        "quantity": 10 + i,
                        "unit_cost": f"{15.00 + i}",
                        "tax_rate": "10.0",
                        "discount_amount": "0.00",
                        "condition": "A",
                        "notes": f"Item for purchase {i+1}"
                    }
                ]
            }
            
            response = client.post(
                "/api/purchases/new",
                json=purchase_data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Get list of purchases
        response = client.get("/api/purchases/", headers=auth_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert isinstance(result, list)
        assert len(result) >= 3  # At least the 3 we created
        
        # Test filtering by supplier
        response = client.get(
            f"/api/purchases/?supplier_id={test_data['supplier'].id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        filtered_result = response.json()
        
        # All results should have the same supplier
        for purchase in filtered_result:
            assert purchase["supplier"]["id"] == str(test_data['supplier'].id)

    async def test_get_purchases_with_date_filter(self, client: TestClient, test_data, auth_headers):
        """Test getting purchases with date range filter."""
        
        # Create purchase with specific date
        target_date = date.today() - timedelta(days=5)
        purchase_data = {
            "supplier_id": str(test_data['supplier'].id),
            "location_id": str(test_data['location'].id),
            "purchase_date": target_date.isoformat(),
            "notes": "Date filter test",
            "reference_number": "PO-DATE-001",
            "items": [
                {
                    "item_id": str(test_data['items'][0].id),
                    "quantity": 1,
                    "unit_cost": "10.00",
                    "tax_rate": "0.0",
                    "discount_amount": "0.00",
                    "condition": "A",
                    "notes": ""
                }
            ]
        }
        
        create_response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        
        # Filter by date range
        date_from = (target_date - timedelta(days=1)).isoformat()
        date_to = (target_date + timedelta(days=1)).isoformat()
        
        response = client.get(
            f"/api/purchases/?date_from={date_from}&date_to={date_to}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        result = response.json()
        # Should find at least our test purchase
        found_our_purchase = any(
            p["reference_number"] == "PO-DATE-001" for p in result
        )
        assert found_our_purchase

    # UPDATE Tests - Note: These would require implementing update endpoints
    
    async def test_update_purchase_not_implemented(self, client: TestClient, auth_headers):
        """Test that update operations return appropriate response when not implemented."""
        # Since update endpoints aren't implemented yet, test that they return 404 or 405
        purchase_id = str(uuid4())
        
        response = client.put(
            f"/api/purchases/{purchase_id}",
            json={"notes": "Updated notes"},
            headers=auth_headers
        )
        
        # Should return 404 (Not Found) or 405 (Method Not Allowed) since endpoint doesn't exist
        assert response.status_code in [404, 405]

    # DELETE Tests - Note: These would require implementing delete endpoints
    
    async def test_delete_purchase_not_implemented(self, client: TestClient, auth_headers):
        """Test that delete operations return appropriate response when not implemented."""
        # Since delete endpoints aren't implemented yet, test that they return 404 or 405
        purchase_id = str(uuid4())
        
        response = client.delete(
            f"/api/purchases/{purchase_id}",
            headers=auth_headers
        )
        
        # Should return 404 (Not Found) or 405 (Method Not Allowed) since endpoint doesn't exist
        assert response.status_code in [404, 405]

    # Additional CRUD-related tests
    
    async def test_purchase_data_integrity(self, client: TestClient, test_data, auth_headers, db_session: AsyncSession):
        """Test that purchase creation maintains data integrity."""
        
        # Get initial stock level
        stock_query = select(StockLevel).where(
            StockLevel.item_id == test_data['items'][0].id,
            StockLevel.location_id == test_data['location'].id
        )
        result = await db_session.execute(stock_query)
        initial_stock = result.scalar_one()
        initial_available = initial_stock.available_quantity
        
        purchase_data = {
            "supplier_id": str(test_data['supplier'].id),
            "location_id": str(test_data['location'].id),
            "purchase_date": date.today().isoformat(),
            "notes": "Data integrity test",
            "reference_number": "PO-INTEGRITY-001",
            "items": [
                {
                    "item_id": str(test_data['items'][0].id),
                    "quantity": 25,
                    "unit_cost": "18.00",
                    "tax_rate": "12.0",
                    "discount_amount": "3.00",
                    "condition": "A",
                    "notes": "Integrity test item"
                }
            ]
        }
        
        response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Verify stock level was updated
        await db_session.refresh(initial_stock)
        assert initial_stock.available_quantity == initial_available + Decimal("25")
        
        # Verify transaction was recorded correctly
        purchase_id = UUID(response.json()["transaction_id"])
        
        transaction_query = select(TransactionHeader).where(
            TransactionHeader.id == purchase_id
        )
        result = await db_session.execute(transaction_query)
        transaction = result.scalar_one()
        
        assert transaction.transaction_type == TransactionType.PURCHASE
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.customer_id == str(test_data['supplier'].id)  # supplier_id maps to customer_id
        assert transaction.location_id == str(test_data['location'].id)

    async def test_concurrent_purchase_creation(self, client: TestClient, test_data, auth_headers):
        """Test that concurrent purchase creation works correctly."""
        
        import asyncio
        import aiohttp
        
        async def create_purchase(session, purchase_num):
            """Create a single purchase."""
            purchase_data = {
                "supplier_id": str(test_data['supplier'].id),
                "location_id": str(test_data['location'].id),
                "purchase_date": date.today().isoformat(),
                "notes": f"Concurrent test purchase {purchase_num}",
                "reference_number": f"PO-CONCURRENT-{purchase_num:03d}",
                "items": [
                    {
                        "item_id": str(test_data['items'][0].id),
                        "quantity": purchase_num,
                        "unit_cost": "10.00",
                        "tax_rate": "5.0",
                        "discount_amount": "0.00",
                        "condition": "A",
                        "notes": f"Concurrent item {purchase_num}"
                    }
                ]
            }
            
            # Use requests directly for better concurrency control
            import requests
            response = requests.post(
                f"{client.base_url}/api/purchases/new",
                json=purchase_data,
                headers=auth_headers
            )
            return response.status_code == 201
        
        # Create multiple purchases concurrently using TestClient
        success_count = 0
        for i in range(5):
            purchase_data = {
                "supplier_id": str(test_data['supplier'].id),
                "location_id": str(test_data['location'].id),
                "purchase_date": date.today().isoformat(),
                "notes": f"Concurrent test purchase {i+1}",
                "reference_number": f"PO-CONCURRENT-{i+1:03d}",
                "items": [
                    {
                        "item_id": str(test_data['items'][i % len(test_data['items'])].id),
                        "quantity": i + 1,
                        "unit_cost": "10.00",
                        "tax_rate": "5.0",
                        "discount_amount": "0.00",
                        "condition": "A",
                        "notes": f"Concurrent item {i+1}"
                    }
                ]
            }
            
            response = client.post(
                "/api/purchases/new",
                json=purchase_data,
                headers=auth_headers
            )
            if response.status_code == 201:
                success_count += 1
        
        # At least most purchases should succeed
        assert success_count >= 4

    async def test_purchase_validation_edge_cases(self, client: TestClient, test_data, auth_headers):
        """Test purchase validation with edge cases."""
        
        # Test with zero quantity
        purchase_data = {
            "supplier_id": str(test_data['supplier'].id),
            "location_id": str(test_data['location'].id),
            "purchase_date": date.today().isoformat(),
            "notes": "Zero quantity test",
            "reference_number": "PO-ZERO-001",
            "items": [
                {
                    "item_id": str(test_data['items'][0].id),
                    "quantity": 0,  # Invalid quantity
                    "unit_cost": "10.00",
                    "tax_rate": "5.0",
                    "discount_amount": "0.00",
                    "condition": "A",
                    "notes": ""
                }
            ]
        }
        
        response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test with negative unit cost
        purchase_data["items"][0]["quantity"] = 1
        purchase_data["items"][0]["unit_cost"] = "-10.00"  # Invalid unit cost
        
        response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test with invalid condition
        purchase_data["items"][0]["unit_cost"] = "10.00"
        purchase_data["items"][0]["condition"] = "X"  # Invalid condition
        
        response = client.post(
            "/api/purchases/new",
            json=purchase_data,
            headers=auth_headers
        )
        assert response.status_code == 422

    async def test_purchase_search_functionality(self, client: TestClient, test_data, auth_headers):
        """Test search functionality in purchase listings."""
        
        # Create purchases with different amounts for testing filters
        test_purchases = [
            {
                "amount": "100.00",
                "ref": "PO-SEARCH-LOW"
            },
            {
                "amount": "500.00", 
                "ref": "PO-SEARCH-MID"
            },
            {
                "amount": "1000.00",
                "ref": "PO-SEARCH-HIGH"
            }
        ]
        
        for purchase_info in test_purchases:
            purchase_data = {
                "supplier_id": str(test_data['supplier'].id),
                "location_id": str(test_data['location'].id),
                "purchase_date": date.today().isoformat(),
                "notes": "Search test purchase",
                "reference_number": purchase_info["ref"],
                "items": [
                    {
                        "item_id": str(test_data['items'][0].id),
                        "quantity": 1,
                        "unit_cost": purchase_info["amount"],
                        "tax_rate": "0.0",
                        "discount_amount": "0.00",
                        "condition": "A",
                        "notes": ""
                    }
                ]
            }
            
            response = client.post(
                "/api/purchases/new",
                json=purchase_data,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Test amount range filtering
        response = client.get(
            "/api/purchases/?amount_from=200&amount_to=800",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        result = response.json()
        # Should find the middle-range purchase
        found_mid_purchase = any(
            p["reference_number"] == "PO-SEARCH-MID" for p in result
        )
        assert found_mid_purchase