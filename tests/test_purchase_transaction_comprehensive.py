"""
Comprehensive test suite for purchase transaction flow.
Tests all aspects of the purchase process including validation, database updates,
stock level management, and movement tracking.
"""

import pytest
import pytest_asyncio
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import asyncio
from typing import List, Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.base.models import (
    TransactionHeader, 
    TransactionLine,
    TransactionType,
    TransactionStatus,
    PaymentStatus,
    LineItemType
)
from app.modules.inventory.models import StockLevel, StockMovement, MovementType, ReferenceType
from app.modules.suppliers.models import Supplier
from app.modules.master_data.locations.models import Location
from app.modules.master_data.item_master.models import Item
from app.modules.users.models import User
from app.modules.users.services import UserService


class TestPurchaseTransactionComprehensive:
    """Comprehensive test suite for purchase transactions."""

    @pytest_asyncio.fixture
    async def setup_test_data(self, db_session: AsyncSession):
        """Set up test data before each test."""
        # Create test suppliers
        suppliers = []
        for i in range(5):
            supplier = Supplier(
                supplier_code=f"SUP{i+1:03d}",
                supplier_name=f"Test Supplier {i+1}",
                contact_person=f"Contact {i+1}",
                email=f"supplier{i+1}@test.com",
                phone=f"+1234567890{i}",
                address=f"Address {i+1}",
                city="Test City",
                state="Test State",
                country="Test Country",
                postal_code=f"1234{i}",
                is_active=True
            )
            db_session.add(supplier)
            suppliers.append(supplier)
        
        # Create test locations
        locations = []
        for i in range(3):
            location = Location(
                location_code=f"LOC{i+1:03d}",
                location_name=f"Test Location {i+1}",
                location_type="WAREHOUSE" if i == 0 else "STORE",
                address=f"Location Address {i+1}",
                city="Test City",
                state="Test State",
                country="Test Country",
                postal_code=f"5432{i}",
                is_active=True
            )
            db_session.add(location)
            locations.append(location)
        
        # Create test items
        items = []
        for i in range(20):
            item = Item(
                item_code=f"ITEM{i+1:04d}",
                item_name=f"Test Item {i+1}",
                description=f"Description for test item {i+1}",
                category_id=str(uuid4()),  # Mock category
                brand_id=str(uuid4()),      # Mock brand
                unit_of_measure="PCS",
                is_active=True,
                is_rentable=i % 2 == 0,     # Half rentable
                is_sellable=True,
                purchase_price=Decimal(str(10 + i * 5)),
                rental_rate=Decimal(str(5 + i * 2)) if i % 2 == 0 else None,
                selling_price=Decimal(str(15 + i * 7))
            )
            db_session.add(item)
            items.append(item)
        
        await db_session.commit()
        
        return {
            "suppliers": suppliers,
            "locations": locations,
            "items": items
        }

    def _generate_purchase_data(
        self,
        test_data: Dict,
        supplier_idx: int = 0,
        location_idx: int = 0,
        item_indices: List[int] = None,
        quantities: List[int] = None,
        conditions: List[str] = None,
        include_tax: bool = True,
        include_discount: bool = False,
        purchase_date: date = None,
        notes: str = "",
        reference_number: str = ""
    ) -> Dict[str, Any]:
        """Generate purchase request data with specified parameters."""
        if item_indices is None:
            item_indices = [0, 1]
        if quantities is None:
            quantities = [10] * len(item_indices)
        if conditions is None:
            conditions = ["A"] * len(item_indices)
        if purchase_date is None:
            purchase_date = date.today()
        
        items = []
        for i, (item_idx, qty, condition) in enumerate(zip(item_indices, quantities, conditions)):
            item_data = {
                "item_id": str(test_data["items"][item_idx].id),
                "quantity": qty,
                "unit_cost": float(test_data["items"][item_idx].purchase_price),
                "tax_rate": 8.5 if include_tax else 0,
                "discount_amount": float(qty * 2) if include_discount else 0,
                "condition": condition,
                "notes": f"Item {i+1} notes"
            }
            items.append(item_data)
        
        return {
            "supplier_id": str(test_data["suppliers"][supplier_idx].id),
            "location_id": str(test_data["locations"][location_idx].id),
            "purchase_date": purchase_date.strftime("%Y-%m-%d"),
            "notes": notes or f"Test purchase on {purchase_date}",
            "reference_number": reference_number or f"REF-{purchase_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "items": items
        }

    def test_valid_purchase_single_item(self, client: TestClient, db_session: AsyncSession, setup_test_data):
        """Test valid purchase with single item."""
        # Arrange
        test_data = setup_test_data
        purchase_data = self._generate_purchase_data(
            test_data,
            item_indices=[0],
            quantities=[50],
            conditions=["A"]
        )
        
        # Act
        response = await client.post(
            "/api/transactions/new-purchase",
            json=purchase_data,
        )
        
        # Assert - Response
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Purchase transaction created successfully"
        assert "transaction_id" in data
        assert "transaction_number" in data
        assert data["transaction_number"].startswith("PUR-")
        
        # Assert - Transaction Header
        transaction_id = UUID(data["transaction_id"])
        transaction = await db_session.get(TransactionHeader, transaction_id)
        assert transaction is not None
        assert transaction.transaction_type == TransactionType.PURCHASE
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.payment_status == PaymentStatus.PENDING
        assert str(transaction.customer_id) == purchase_data["supplier_id"]
        assert str(transaction.location_id) == purchase_data["location_id"]
        
        # Calculate expected totals
        item = test_data["items"][0]
        quantity = Decimal("50")
        unit_cost = item.purchase_price
        subtotal = quantity * unit_cost
        tax_amount = (subtotal * Decimal("8.5")) / 100
        total = subtotal + tax_amount
        
        assert transaction.subtotal == subtotal
        assert transaction.tax_amount == tax_amount
        assert transaction.discount_amount == Decimal("0")
        assert transaction.total_amount == total
        assert transaction.paid_amount == Decimal("0")
        
        # Assert - Transaction Lines
        lines = await db_session.execute(
            select(TransactionLine).where(TransactionLine.transaction_id == transaction_id)
        )
        lines = lines.scalars().all()
        assert len(lines) == 1
        
        line = lines[0]
        assert line.line_number == 1
        assert line.line_type == LineItemType.PRODUCT
        assert str(line.item_id) == purchase_data["items"][0]["item_id"]
        assert line.quantity == quantity
        assert line.unit_price == unit_cost
        assert line.tax_rate == Decimal("8.5")
        assert line.tax_amount == tax_amount
        assert line.line_total == total
        assert "Condition: A" in line.description
        
        # Assert - Stock Level
        stock_level = await db_session.execute(
            select(StockLevel).where(
                StockLevel.item_id == UUID(purchase_data["items"][0]["item_id"]),
                StockLevel.location_id == UUID(purchase_data["location_id"])
            )
        )
        stock_level = stock_level.scalar_one_or_none()
        assert stock_level is not None
        assert stock_level.quantity_on_hand == quantity
        assert stock_level.quantity_available == quantity
        assert stock_level.quantity_on_rent == Decimal("0")
        
        # Assert - Stock Movement
        movements = await db_session.execute(
            select(StockMovement).where(
                StockMovement.item_id == UUID(purchase_data["items"][0]["item_id"]),
                StockMovement.reference_id == str(transaction_id)
            )
        )
        movements = movements.scalars().all()
        assert len(movements) == 1
        
        movement = movements[0]
        assert movement.movement_type == MovementType.PURCHASE.value
        assert movement.reference_type == ReferenceType.TRANSACTION.value
        assert movement.quantity_change == quantity
        assert movement.quantity_before == Decimal("0")
        assert movement.quantity_after == quantity
        assert "Condition: A" in movement.notes

    @pytest.mark.asyncio
    async def test_valid_purchase_multiple_items(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test valid purchase with multiple items."""
        # Arrange
        test_data = setup_test_data
        purchase_data = self._generate_purchase_data(
            test_data,
            item_indices=[0, 1, 2, 3, 4],
            quantities=[10, 20, 30, 40, 50],
            conditions=["A", "B", "C", "D", "A"],
            include_tax=True,
            include_discount=True
        )
        
        # Act
        response = await client.post(
            "/api/transactions/new-purchase",
            json=purchase_data,
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        transaction_id = UUID(data["transaction_id"])
        
        # Verify line count
        lines = await db_session.execute(
            select(TransactionLine).where(TransactionLine.transaction_id == transaction_id)
        )
        lines = lines.scalars().all()
        assert len(lines) == 5
        
        # Verify each line
        for i, line in enumerate(sorted(lines, key=lambda x: x.line_number)):
            assert line.line_number == i + 1
            assert line.quantity == Decimal(str(purchase_data["items"][i]["quantity"]))
            assert f"Condition: {purchase_data['items'][i]['condition']}" in line.description
        
        # Verify stock movements
        movements = await db_session.execute(
            select(StockMovement).where(
                StockMovement.reference_id == str(transaction_id)
            )
        )
        movements = movements.scalars().all()
        assert len(movements) == 5

    @pytest.mark.asyncio
    async def test_purchase_with_existing_stock(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test purchase that updates existing stock levels."""
        # Arrange - Create initial stock
        test_data = setup_test_data
        initial_quantity = Decimal("100")
        stock_level = StockLevel(
            item_id=test_data["items"][0].id,
            location_id=test_data["locations"][0].id,
            quantity_on_hand=initial_quantity,
            quantity_available=initial_quantity,
            quantity_on_rent=Decimal("0")
        )
        db_session.add(stock_level)
        await db_session.commit()
        
        # Purchase more of the same item
        purchase_quantity = 50
        purchase_data = self._generate_purchase_data(
            test_data,
            item_indices=[0],
            quantities=[purchase_quantity],
            conditions=["A"]
        )
        
        # Act
        response = await client.post(
            "/api/transactions/new-purchase",
            json=purchase_data,
        )
        
        # Assert
        assert response.status_code == 201
        
        # Verify stock level was updated
        await db_session.refresh(stock_level)
        expected_total = initial_quantity + Decimal(str(purchase_quantity))
        assert stock_level.quantity_on_hand == expected_total
        assert stock_level.quantity_available == expected_total
        
        # Verify stock movement shows correct before/after
        transaction_id = UUID(response.json()["transaction_id"])
        movement = await db_session.execute(
            select(StockMovement).where(
                StockMovement.reference_id == str(transaction_id)
            )
        )
        movement = movement.scalar_one()
        assert movement.quantity_before == initial_quantity
        assert movement.quantity_after == expected_total
        assert movement.quantity_change == Decimal(str(purchase_quantity))

    @pytest.mark.asyncio
    async def test_purchase_different_conditions(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test purchases with all different item conditions (A, B, C, D)."""
        test_data = setup_test_data
        
        # Test each condition separately
        for condition in ["A", "B", "C", "D"]:
            purchase_data = self._generate_purchase_data(
                test_data,
                supplier_idx=0,
                location_idx=0,
                item_indices=[5],  # Use different item to avoid conflicts
                quantities=[25],
                conditions=[condition]
            )
            
            response = await client.post(
                "/api/transactions/new-purchase",
                json=purchase_data,
                )
            
            assert response.status_code == 201
            
            # Verify condition is stored in line description
            transaction_id = UUID(response.json()["transaction_id"])
            line = await db_session.execute(
                select(TransactionLine).where(
                    TransactionLine.transaction_id == transaction_id
                )
            )
            line = line.scalar_one()
            assert f"Condition: {condition}" in line.description
            
            # Verify condition in stock movement notes
            movement = await db_session.execute(
                select(StockMovement).where(
                    StockMovement.reference_id == str(transaction_id)
                )
            )
            movement = movement.scalar_one()
            assert f"Condition: {condition}" in movement.notes

    @pytest.mark.asyncio
    async def test_validation_nonexistent_supplier(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test validation for non-existent supplier."""
        test_data = setup_test_data
        purchase_data = self._generate_purchase_data(test_data)
        purchase_data["supplier_id"] = str(uuid4())  # Non-existent UUID
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=purchase_data,
        )
        
        assert response.status_code == 404
        assert "Supplier with ID" in response.json()["detail"]
        assert "not found" in response.json()["detail"]
        
        # Verify no transaction was created
        count = await db_session.execute(
            select(func.count()).select_from(TransactionHeader).where(
                TransactionHeader.transaction_type == TransactionType.PURCHASE
            )
        )
        assert count.scalar() == 0

    @pytest.mark.asyncio
    async def test_validation_invalid_date_format(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test validation for invalid date format."""
        test_data = setup_test_data
        purchase_data = self._generate_purchase_data(test_data)
        purchase_data["purchase_date"] = "15-01-2024"  # Wrong format
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=purchase_data,
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("Invalid date format" in str(err) for err in error_detail)

    @pytest.mark.asyncio
    async def test_validation_negative_quantity(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test validation for negative quantity."""
        test_data = setup_test_data
        purchase_data = self._generate_purchase_data(test_data)
        purchase_data["items"][0]["quantity"] = -10
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=purchase_data,
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_purchase_financial_calculations(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test various financial calculation scenarios."""
        test_data = setup_test_data
        
        # Test 1: No tax, no discount
        purchase_data = self._generate_purchase_data(
            test_data,
            item_indices=[9],
            quantities=[10],
            include_tax=False,
            include_discount=False
        )
        response = await client.post(
            "/api/transactions/new-purchase", 
            json=purchase_data,
        )
        assert response.status_code == 201
        
        transaction_id = UUID(response.json()["transaction_id"])
        transaction = await db_session.get(TransactionHeader, transaction_id)
        expected_total = Decimal("10") * test_data["items"][9].purchase_price
        assert transaction.subtotal == expected_total
        assert transaction.tax_amount == Decimal("0")
        assert transaction.discount_amount == Decimal("0")
        assert transaction.total_amount == expected_total

    @pytest.mark.asyncio
    async def test_purchase_transaction_number_uniqueness(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test that transaction numbers are always unique."""
        test_data = setup_test_data
        
        # Create multiple purchases on the same date
        purchase_date = date.today()
        transaction_numbers = set()
        
        for i in range(10):
            purchase_data = self._generate_purchase_data(
                test_data,
                item_indices=[14],
                quantities=[1],
                purchase_date=purchase_date
            )
            
            response = await client.post(
                "/api/transactions/new-purchase",
                json=purchase_data,
                )
            
            assert response.status_code == 201
            transaction_number = response.json()["transaction_number"]
            
            # Verify format
            assert transaction_number.startswith(f"PUR-{purchase_date.strftime('%Y%m%d')}-")
            
            # Verify uniqueness
            assert transaction_number not in transaction_numbers
            transaction_numbers.add(transaction_number)

    @pytest.mark.asyncio
    async def test_large_batch_purchase(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test purchase with large number of items."""
        test_data = setup_test_data
        
        # Create purchase with multiple items (limited by available test items)
        num_items = min(10, len(test_data["items"]))
        item_indices = list(range(num_items))
        quantities = [random.randint(10, 100) for _ in item_indices]
        conditions = [random.choice(["A", "B", "C", "D"]) for _ in item_indices]
        
        purchase_data = self._generate_purchase_data(
            test_data,
            item_indices=item_indices,
            quantities=quantities,
            conditions=conditions
        )
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=purchase_data,
        )
        
        assert response.status_code == 201
        
        # Verify all lines were created
        transaction_id = UUID(response.json()["transaction_id"])
        lines = await db_session.execute(
            select(TransactionLine).where(TransactionLine.transaction_id == transaction_id)
        )
        lines = lines.scalars().all()
        assert len(lines) == len(item_indices)
        
        # Verify all stock movements were created
        movements = await db_session.execute(
            select(StockMovement).where(
                StockMovement.reference_id == str(transaction_id)
            )
        )
        movements = movements.scalars().all()
        assert len(movements) == len(item_indices)

    @pytest.mark.asyncio
    async def test_purchase_response_structure(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test that purchase response has correct structure and data."""
        test_data = setup_test_data
        purchase_data = self._generate_purchase_data(
            test_data,
            item_indices=[16, 17],
            quantities=[25, 35],
            conditions=["B", "C"],
            include_tax=True,
            include_discount=True
        )
        
        response = await client.post(
            "/api/transactions/new-purchase",
            json=purchase_data,
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify top-level structure
        assert data["success"] is True
        assert data["message"] == "Purchase transaction created successfully"
        assert "transaction_id" in data
        assert "transaction_number" in data
        assert "data" in data
        
        # Verify transaction data structure
        transaction_data = data["data"]
        assert "id" in transaction_data
        assert "transaction_number" in transaction_data
        assert "transaction_type" in transaction_data
        assert transaction_data["transaction_type"] == "PURCHASE"
        assert "status" in transaction_data
        assert "payment_status" in transaction_data
        assert "subtotal" in transaction_data
        assert "tax_amount" in transaction_data
        assert "discount_amount" in transaction_data
        assert "total_amount" in transaction_data
        assert "transaction_lines" in transaction_data
        
        # Verify lines structure
        lines = transaction_data["transaction_lines"]
        assert len(lines) == 2
        
        for line in lines:
            assert "id" in line
            assert "line_number" in line
            assert "item_id" in line
            assert "quantity" in line
            assert "unit_price" in line
            assert "tax_rate" in line
            assert "tax_amount" in line
            assert "discount_amount" in line
            assert "line_total" in line
            assert "description" in line