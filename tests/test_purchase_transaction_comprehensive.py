"""
Comprehensive test suite for purchase transaction endpoint.

This test suite covers all aspects of the purchase transaction functionality including:
- Input validation (UUIDs, dates, amounts, conditions)
- Successful transaction creation
- Error handling (404, 409, 422, 500)
- Stock level integration
- Financial calculations
- Authentication and authorization
- Edge cases and boundary conditions
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from uuid import uuid4
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.suppliers.models import Supplier
from app.modules.master_data.locations.models import Location
from app.modules.master_data.item_master.models import Item
from app.modules.inventory.models import StockLevel
from app.modules.transactions.models.transaction_headers import TransactionHeader, TransactionType
from app.modules.transactions.models.transaction_lines import TransactionLine
from app.modules.users.models import User
from app.core.security import create_access_token


class TestPurchaseTransactionEndpoint:
    """Comprehensive test suite for purchase transaction endpoint."""
    
    @pytest.fixture
    async def auth_headers(self, test_user: User) -> dict:
        """Create authentication headers for test requests."""
        access_token = create_access_token(subject=str(test_user.id))
        return {"Authorization": f"Bearer {access_token}"}
    
    @pytest.fixture
    async def test_supplier(self, async_session: AsyncSession) -> Supplier:
        """Create a test supplier."""
        supplier = Supplier(
            id=uuid4(),
            supplier_name="Test Supplier Co.",
            supplier_type="COMPANY",
            status="ACTIVE",
            contact_email="supplier@test.com",
            contact_phone="555-0123",
            address="123 Supplier St, Test City, TC 12345"
        )
        async_session.add(supplier)
        await async_session.commit()
        await async_session.refresh(supplier)
        return supplier
    
    @pytest.fixture
    async def test_location(self, async_session: AsyncSession) -> Location:
        """Create a test location."""
        location = Location(
            id=uuid4(),
            location_name="Test Warehouse",
            location_type="WAREHOUSE",
            status="ACTIVE",
            address="456 Warehouse Ave, Test City, TC 12345"
        )
        async_session.add(location)
        await async_session.commit()
        await async_session.refresh(location)
        return location
    
    @pytest.fixture
    async def test_items(self, async_session: AsyncSession) -> list[Item]:
        """Create test items."""
        items = []
        for i in range(3):
            item = Item(
                id=uuid4(),
                item_name=f"Test Item {i + 1}",
                item_code=f"TEST-{i + 1:03d}",
                category="EQUIPMENT",
                status="ACTIVE",
                description=f"Test item {i + 1} for purchase testing",
                unit_price=Decimal("25.00") + (i * Decimal("10.00"))
            )
            async_session.add(item)
            items.append(item)
        
        await async_session.commit()
        for item in items:
            await async_session.refresh(item)
        return items
    
    @pytest.fixture
    async def valid_purchase_request(self, test_supplier: Supplier, test_location: Location, test_items: list[Item]) -> dict:
        """Create a valid purchase request payload."""
        return {
            "supplier_id": str(test_supplier.id),
            "location_id": str(test_location.id),
            "purchase_date": "2024-01-15",
            "notes": "Test purchase transaction",
            "reference_number": "PO-TEST-001",
            "items": [
                {
                    "item_id": str(test_items[0].id),
                    "quantity": 10,
                    "unit_cost": 25.50,
                    "tax_rate": 8.5,
                    "discount_amount": 5.00,
                    "condition": "A",
                    "notes": "First test item"
                },
                {
                    "item_id": str(test_items[1].id),
                    "quantity": 5,
                    "unit_cost": 35.00,
                    "tax_rate": 10.0,
                    "discount_amount": 0,
                    "condition": "B",
                    "notes": "Second test item"
                }
            ]
        }
    
    @pytest.fixture
    async def client(self) -> AsyncClient:
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    # ========================================================================
    # SUCCESSFUL TRANSACTION TESTS
    # ========================================================================
    
    async def test_create_purchase_transaction_success(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict,
        async_session: AsyncSession
    ):
        """Test successful purchase transaction creation."""
        response = await client.post(
            "/api/transactions/new-purchase",
            json=valid_purchase_request,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert "transaction_id" in data
        assert "transaction_number" in data
        assert data["message"] == "Purchase transaction created successfully"
        assert "data" in data
        
        # Verify transaction data
        transaction_data = data["data"]
        assert transaction_data["transaction_type"] == "PURCHASE"
        assert transaction_data["status"] == "COMPLETED"
        assert transaction_data["payment_status"] == "PENDING"
        assert transaction_data["customer_id"] == valid_purchase_request["supplier_id"]
        assert transaction_data["location_id"] == valid_purchase_request["location_id"]
        
        # Verify financial calculations
        assert transaction_data["subtotal"] == 430.00  # (10 * 25.50) + (5 * 35.00)
        assert transaction_data["discount_amount"] == 5.00
        assert transaction_data["tax_amount"] == 38.75  # ((255-5) * 0.085) + (175 * 0.10)
        assert transaction_data["total_amount"] == 463.75
        
        # Verify line items
        assert len(transaction_data["transaction_lines"]) == 2
        line1 = transaction_data["transaction_lines"][0]
        assert line1["quantity"] == 10
        assert line1["unit_price"] == 25.50
        assert line1["discount_amount"] == 5.00
        assert line1["tax_rate"] == 8.5
        assert "A" in line1["description"]
        
        line2 = transaction_data["transaction_lines"][1]
        assert line2["quantity"] == 5
        assert line2["unit_price"] == 35.00
        assert line2["discount_amount"] == 0
        assert line2["tax_rate"] == 10.0
        assert "B" in line2["description"]
    
    async def test_transaction_number_generation(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test transaction number generation format."""
        response = await client.post(
            "/api/transactions/new-purchase",
            json=valid_purchase_request,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        transaction_number = data["transaction_number"]
        today = datetime.now().strftime("%Y%m%d")
        
        # Verify format: PUR-YYYYMMDD-XXXX
        assert transaction_number.startswith(f"PUR-{today}-")
        assert len(transaction_number) == 17  # PUR-YYYYMMDD-XXXX
        assert transaction_number[-4:].isdigit()
    
    # ========================================================================
    # VALIDATION TESTS
    # ========================================================================
    
    async def test_invalid_supplier_id(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with invalid supplier ID."""
        # Test with non-existent supplier
        request_data = valid_purchase_request.copy()
        request_data["supplier_id"] = str(uuid4())
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Supplier" in response.json()["detail"]
        
        # Test with invalid UUID format
        request_data["supplier_id"] = "invalid-uuid"
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_invalid_location_id(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with invalid location ID."""
        request_data = valid_purchase_request.copy()
        request_data["location_id"] = str(uuid4())
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Location" in response.json()["detail"]
    
    async def test_invalid_item_id(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with invalid item ID."""
        request_data = valid_purchase_request.copy()
        request_data["items"][0]["item_id"] = str(uuid4())
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Item" in response.json()["detail"]
    
    async def test_invalid_date_format(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with invalid date format."""
        request_data = valid_purchase_request.copy()
        request_data["purchase_date"] = "2024-13-45"  # Invalid date
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_invalid_quantity_values(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with invalid quantity values."""
        # Test zero quantity
        request_data = valid_purchase_request.copy()
        request_data["items"][0]["quantity"] = 0
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test negative quantity
        request_data["items"][0]["quantity"] = -5
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_invalid_cost_values(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with invalid cost values."""
        # Test negative unit cost
        request_data = valid_purchase_request.copy()
        request_data["items"][0]["unit_cost"] = -10.00
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test negative discount amount
        request_data["items"][0]["unit_cost"] = 25.50
        request_data["items"][0]["discount_amount"] = -5.00
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_invalid_tax_rate(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with invalid tax rate."""
        # Test tax rate over 100%
        request_data = valid_purchase_request.copy()
        request_data["items"][0]["tax_rate"] = 150.0
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test negative tax rate
        request_data["items"][0]["tax_rate"] = -10.0
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_invalid_condition_code(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with invalid condition code."""
        request_data = valid_purchase_request.copy()
        request_data["items"][0]["condition"] = "X"  # Invalid condition
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_string_length_validation(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation of string length limits."""
        request_data = valid_purchase_request.copy()
        
        # Test notes too long
        request_data["notes"] = "x" * 1001  # Over 1000 character limit
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test reference number too long
        request_data["notes"] = "Valid notes"
        request_data["reference_number"] = "x" * 51  # Over 50 character limit
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test item notes too long
        request_data["reference_number"] = "Valid ref"
        request_data["items"][0]["notes"] = "x" * 501  # Over 500 character limit
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_empty_items_list(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with empty items list."""
        request_data = valid_purchase_request.copy()
        request_data["items"] = []
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_missing_required_fields(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        valid_purchase_request: dict
    ):
        """Test validation with missing required fields."""
        # Test missing supplier_id
        request_data = valid_purchase_request.copy()
        del request_data["supplier_id"]
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing item_id in items
        request_data = valid_purchase_request.copy()
        del request_data["items"][0]["item_id"]
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ========================================================================
    # AUTHENTICATION TESTS
    # ========================================================================
    
    async def test_no_authentication(
        self, 
        client: AsyncClient, 
        valid_purchase_request: dict
    ):
        """Test endpoint without authentication."""
        response = await client.post(
            "/api/transactions/new-purchase",
            json=valid_purchase_request
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_invalid_token(
        self, 
        client: AsyncClient, 
        valid_purchase_request: dict
    ):
        """Test endpoint with invalid token."""
        response = await client.post(
            "/api/transactions/new-purchase",
            json=valid_purchase_request,
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # ========================================================================
    # FINANCIAL CALCULATION TESTS
    # ========================================================================
    
    async def test_financial_calculations_precision(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        test_supplier: Supplier,
        test_location: Location,
        test_items: list[Item]
    ):
        """Test financial calculations with decimal precision."""
        request_data = {
            "supplier_id": str(test_supplier.id),
            "location_id": str(test_location.id),
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(test_items[0].id),
                    "quantity": 3,
                    "unit_cost": 33.333,  # Repeating decimal
                    "tax_rate": 7.75,     # Non-standard tax rate
                    "discount_amount": 1.99,
                    "condition": "A"
                }
            ]
        }
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Verify calculations
        transaction_data = data["data"]
        expected_subtotal = 3 * 33.333  # 99.999
        expected_after_discount = expected_subtotal - 1.99  # 98.009
        expected_tax = expected_after_discount * 0.0775  # 7.595697
        expected_total = expected_after_discount + expected_tax  # 105.604697
        
        assert abs(transaction_data["subtotal"] - expected_subtotal) < 0.01
        assert abs(transaction_data["total_amount"] - expected_total) < 0.01
    
    async def test_zero_tax_and_discount(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        test_supplier: Supplier,
        test_location: Location,
        test_items: list[Item]
    ):
        """Test calculations with zero tax and discount."""
        request_data = {
            "supplier_id": str(test_supplier.id),
            "location_id": str(test_location.id),
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(test_items[0].id),
                    "quantity": 5,
                    "unit_cost": 20.00,
                    "condition": "A"
                    # No tax_rate or discount_amount provided
                }
            ]
        }
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        transaction_data = data["data"]
        assert transaction_data["subtotal"] == 100.00
        assert transaction_data["discount_amount"] == 0.00
        assert transaction_data["tax_amount"] == 0.00
        assert transaction_data["total_amount"] == 100.00
    
    # ========================================================================
    # CONDITION CODE TESTS
    # ========================================================================
    
    async def test_all_condition_codes(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        test_supplier: Supplier,
        test_location: Location,
        test_items: list[Item]
    ):
        """Test all valid condition codes."""
        conditions = ["A", "B", "C", "D"]
        
        for condition in conditions:
            request_data = {
                "supplier_id": str(test_supplier.id),
                "location_id": str(test_location.id),
                "purchase_date": "2024-01-15",
                "items": [
                    {
                        "item_id": str(test_items[0].id),
                        "quantity": 1,
                        "unit_cost": 10.00,
                        "condition": condition
                    }
                ]
            }
            
            response = await client.post(
                "/api/transactions/new-purchase",
                json=request_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert condition in data["data"]["transaction_lines"][0]["description"]
    
    async def test_condition_code_case_sensitivity(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        test_supplier: Supplier,
        test_location: Location,
        test_items: list[Item]
    ):
        """Test condition code case sensitivity."""
        request_data = {
            "supplier_id": str(test_supplier.id),
            "location_id": str(test_location.id),
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(test_items[0].id),
                    "quantity": 1,
                    "unit_cost": 10.00,
                    "condition": "a"  # lowercase
                }
            ]
        }
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=request_data,
            headers=auth_headers
        )
        
        # Should fail - condition codes are case-sensitive
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY