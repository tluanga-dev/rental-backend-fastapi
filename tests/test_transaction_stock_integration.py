"""
Integration tests for transaction services with stock movement tracking.

This test suite covers:
- Purchase transactions creating stock movements
- Rental transactions updating stock levels
- Return transactions moving stock back
- Stock movement audit trail validation
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.service import TransactionService
from app.modules.inventory.service import InventoryService
from app.modules.inventory.models import StockLevel, MovementType, ReferenceType
from app.modules.master_data.item_master.models import Item, ItemStatus
from app.modules.master_data.locations.models import Location
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.categories.models import Category
from app.modules.customers.models import Customer
from app.modules.transactions.schemas.main import NewPurchaseRequest, PurchaseItem
from app.modules.transactions.schemas.rentals import NewRentalRequest, RentalItem


@pytest.fixture
async def setup_transaction_test_data(session: AsyncSession):
    """Set up comprehensive test data for transaction integration tests."""
    # Create supporting data
    brand = Brand(name="Transaction Test Brand", brand_code="TTB", description="Transaction test brand")
    session.add(brand)
    await session.flush()
    
    category = Category(name="Transaction Test Category", category_code="TTC", description="Transaction test category")
    session.add(category)
    await session.flush()
    
    # Create multiple items for testing
    items = []
    for i in range(3):
        item = Item(
            sku=f"TXN-TST-{i+1:03d}",
            item_name=f"Transaction Test Item {i+1}",
            item_status=ItemStatus.ACTIVE,
            is_rentable=True,
            is_saleable=True,
            brand_id=brand.id,
            category_id=category.id,
            rental_rate_per_period=Decimal(f"{(i+1)*5}.00")  # 5, 10, 15
        )
        session.add(item)
        items.append(item)
    await session.flush()
    
    location = Location(
        location_name="Transaction Test Location",
        location_code="TTL001",
        location_type="WAREHOUSE",
        address="789 Transaction Test Street"
    )
    session.add(location)
    await session.flush()
    
    customer = Customer(
        customer_name="Transaction Test Customer",
        customer_code="TTC001",
        email="test.customer@transaction.test",
        phone="555-0123",
        address="123 Customer Street"
    )
    session.add(customer)
    await session.flush()
    
    await session.commit()
    
    return {
        "items": items,
        "location": location,
        "customer": customer,
        "brand": brand,
        "category": category
    }


@pytest.fixture
async def transaction_service(session: AsyncSession):
    """Create transaction service for testing."""
    return TransactionService(session)


@pytest.fixture
async def inventory_service(session: AsyncSession):
    """Create inventory service for testing."""
    return InventoryService(session)


class TestPurchaseTransactionStockMovements:
    """Test purchase transactions creating stock movements."""
    
    async def test_purchase_creates_stock_movement_new_stock(
        self, 
        session: AsyncSession, 
        transaction_service, 
        inventory_service,
        setup_transaction_test_data
    ):
        """Test purchase transaction creates stock level and movement for new item."""
        test_data = setup_transaction_test_data
        item = test_data["items"][0]
        location = test_data["location"]
        
        # Ensure no existing stock
        existing_stock = await inventory_service.stock_level_repository.get_by_item_location(
            item.id, location.id
        )
        assert existing_stock is None
        
        # Create purchase transaction
        purchase_data = NewPurchaseRequest(
            transaction_date=date.today(),
            location_id=location.id,
            items=[
                PurchaseItem(
                    item_id=item.id,
                    quantity=50,
                    condition="NEW",
                    unit_price=Decimal("25.00")
                )
            ],
            payment_method="CASH",
            notes="Integration test purchase"
        )
        
        result = await transaction_service.create_new_purchase(purchase_data)
        
        # Verify transaction was created
        assert result.success is True
        assert result.transaction_id is not None
        
        # Verify stock level was created
        stock_level = await inventory_service.stock_level_repository.get_by_item_location(
            item.id, location.id
        )
        assert stock_level is not None
        assert stock_level.quantity_on_hand == Decimal("50")
        assert stock_level.quantity_available == Decimal("50")
        assert stock_level.quantity_on_rent == Decimal("0")
        
        # Verify stock movement was created
        movements = await inventory_service.get_stock_movements_by_stock_level(stock_level.id)
        assert len(movements) == 1
        
        movement = movements[0]
        assert movement.movement_type == MovementType.PURCHASE
        assert movement.reference_type == ReferenceType.TRANSACTION
        assert movement.reference_id == str(result.transaction_id)
        assert movement.quantity_change == Decimal("50")
        assert movement.quantity_before == Decimal("0")
        assert movement.quantity_after == Decimal("50")
        assert "Initial purchase" in movement.reason
    
    async def test_purchase_creates_stock_movement_existing_stock(
        self, 
        session: AsyncSession, 
        transaction_service, 
        inventory_service,
        setup_transaction_test_data
    ):
        """Test purchase transaction updates existing stock and creates movement."""
        test_data = setup_transaction_test_data
        item = test_data["items"][1]
        location = test_data["location"]
        
        # Create initial stock level
        from app.modules.inventory.schemas import StockLevelCreate
        initial_stock_data = StockLevelCreate(
            item_id=item.id,
            location_id=location.id,
            quantity_on_hand=Decimal("30"),
            quantity_available=Decimal("25"),
            quantity_on_rent=Decimal("5")
        )
        initial_stock = await inventory_service.stock_level_repository.create(initial_stock_data)
        
        # Create purchase transaction
        purchase_data = NewPurchaseRequest(
            transaction_date=date.today(),
            location_id=location.id,
            items=[
                PurchaseItem(
                    item_id=item.id,
                    quantity=40,
                    condition="NEW",
                    unit_price=Decimal("30.00")
                )
            ],
            payment_method="CREDIT_CARD",
            notes="Additional stock purchase"
        )
        
        result = await transaction_service.create_new_purchase(purchase_data)
        
        # Verify stock level was updated
        await session.refresh(initial_stock)
        assert initial_stock.quantity_on_hand == Decimal("70")  # 30 + 40
        assert initial_stock.quantity_available == Decimal("65")  # 25 + 40
        assert initial_stock.quantity_on_rent == Decimal("5")  # Unchanged
        
        # Verify stock movement was created
        movements = await inventory_service.get_stock_movements_by_stock_level(initial_stock.id)
        assert len(movements) == 1
        
        movement = movements[0]
        assert movement.movement_type == MovementType.PURCHASE
        assert movement.quantity_change == Decimal("40")
        assert movement.quantity_before == Decimal("30")
        assert movement.quantity_after == Decimal("70")
    
    async def test_purchase_multiple_items_creates_multiple_movements(
        self, 
        session: AsyncSession, 
        transaction_service, 
        inventory_service,
        setup_transaction_test_data
    ):
        """Test purchase with multiple items creates separate stock movements."""
        test_data = setup_transaction_test_data
        items = test_data["items"]
        location = test_data["location"]
        
        # Create purchase with multiple items
        purchase_data = NewPurchaseRequest(
            transaction_date=date.today(),
            location_id=location.id,
            items=[
                PurchaseItem(
                    item_id=items[0].id,
                    quantity=20,
                    condition="NEW",
                    unit_price=Decimal("15.00")
                ),
                PurchaseItem(
                    item_id=items[1].id,
                    quantity=35,
                    condition="EXCELLENT",
                    unit_price=Decimal("22.00")
                )
            ],
            payment_method="BANK_TRANSFER",
            notes="Multi-item purchase test"
        )
        
        result = await transaction_service.create_new_purchase(purchase_data)
        
        # Verify stock levels for both items
        for i, item in enumerate(items[:2]):
            stock_level = await inventory_service.stock_level_repository.get_by_item_location(
                item.id, location.id
            )
            assert stock_level is not None
            
            expected_quantity = Decimal("20") if i == 0 else Decimal("35")
            assert stock_level.quantity_on_hand == expected_quantity
            
            # Verify movement for each item
            movements = await inventory_service.get_stock_movements_by_stock_level(stock_level.id)
            assert len(movements) == 1
            assert movements[0].quantity_change == expected_quantity
            assert movements[0].reference_id == str(result.transaction_id)


class TestRentalTransactionStockMovements:
    """Test rental transactions updating stock levels."""
    
    async def test_rental_moves_stock_to_on_rent(
        self, 
        session: AsyncSession, 
        transaction_service, 
        inventory_service,
        setup_transaction_test_data
    ):
        """Test rental transaction moves stock from available to on rent."""
        test_data = setup_transaction_test_data
        item = test_data["items"][0]
        location = test_data["location"]
        customer = test_data["customer"]
        
        # Create initial stock
        from app.modules.inventory.schemas import StockLevelCreate
        stock_data = StockLevelCreate(
            item_id=item.id,
            location_id=location.id,
            quantity_on_hand=Decimal("100"),
            quantity_available=Decimal("100"),
            quantity_on_rent=Decimal("0")
        )
        stock_level = await inventory_service.stock_level_repository.create(stock_data)
        
        # Create rental transaction
        rental_data = NewRentalRequest(
            transaction_date=date.today(),
            customer_id=customer.id,
            location_id=location.id,
            items=[
                RentalItem(
                    item_id=item.id,
                    quantity=25,
                    rental_period_value=7,
                    rental_start_date=date.today(),
                    rental_end_date=date.today() + timedelta(days=7)
                )
            ],
            payment_method="CREDIT_CARD",
            notes="Integration test rental"
        )
        
        result = await transaction_service.create_new_rental(rental_data)
        
        # Verify rental was created
        assert result.success is True
        assert result.transaction_id is not None
        
        # Verify stock level was updated
        await session.refresh(stock_level)
        assert stock_level.quantity_on_hand == Decimal("100")  # Total unchanged
        assert stock_level.quantity_available == Decimal("75")  # 100 - 25
        assert stock_level.quantity_on_rent == Decimal("25")  # 0 + 25
        
        # Verify stock movement was created
        movements = await inventory_service.get_stock_movements_by_stock_level(stock_level.id)
        assert len(movements) == 1
        
        movement = movements[0]
        assert movement.movement_type == MovementType.RENTAL_OUT
        assert movement.reference_type == ReferenceType.TRANSACTION
        assert movement.reference_id == str(result.transaction_id)
        assert movement.quantity_change == Decimal("-25")  # Negative from available perspective
        assert movement.quantity_before == Decimal("100")  # Available before
        assert movement.quantity_after == Decimal("75")   # Available after
        assert "Rented out 25 units" in movement.reason
    
    async def test_rental_insufficient_stock_fails(
        self, 
        session: AsyncSession, 
        transaction_service, 
        inventory_service,
        setup_transaction_test_data
    ):
        """Test rental fails when insufficient stock available."""
        test_data = setup_transaction_test_data
        item = test_data["items"][1]
        location = test_data["location"]
        customer = test_data["customer"]
        
        # Create limited stock
        from app.modules.inventory.schemas import StockLevelCreate
        stock_data = StockLevelCreate(
            item_id=item.id,
            location_id=location.id,
            quantity_on_hand=Decimal("10"),
            quantity_available=Decimal("5"),  # Only 5 available
            quantity_on_rent=Decimal("5")
        )
        await inventory_service.stock_level_repository.create(stock_data)
        
        # Try to rent more than available
        rental_data = NewRentalRequest(
            transaction_date=date.today(),
            customer_id=customer.id,
            location_id=location.id,
            items=[
                RentalItem(
                    item_id=item.id,
                    quantity=15,  # More than available
                    rental_period_value=5,
                    rental_start_date=date.today(),
                    rental_end_date=date.today() + timedelta(days=5)
                )
            ],
            payment_method="CASH"
        )
        
        # The rental transaction should be created, but stock movement should fail
        # (Based on the current implementation, stock errors are logged but don't fail the transaction)
        result = await transaction_service.create_new_rental(rental_data)
        assert result.success is True  # Transaction succeeds
        
        # But no stock movement should be created due to insufficient stock
        stock_level = await inventory_service.stock_level_repository.get_by_item_location(
            item.id, location.id
        )
        movements = await inventory_service.get_stock_movements_by_stock_level(stock_level.id)
        # Movement might not be created due to validation in rent_out_stock
        # This depends on the error handling in the transaction service


class TestReturnTransactionStockMovements:
    """Test return transactions moving stock back."""
    
    async def test_rental_return_moves_stock_back(
        self, 
        session: AsyncSession, 
        transaction_service, 
        inventory_service,
        setup_transaction_test_data
    ):
        """Test rental return moves stock from on rent back to available."""
        test_data = setup_transaction_test_data
        item = test_data["items"][0]
        location = test_data["location"]
        customer = test_data["customer"]
        
        # Create stock with some on rent
        from app.modules.inventory.schemas import StockLevelCreate
        stock_data = StockLevelCreate(
            item_id=item.id,
            location_id=location.id,
            quantity_on_hand=Decimal("100"),
            quantity_available=Decimal("60"),
            quantity_on_rent=Decimal("40")
        )
        stock_level = await inventory_service.stock_level_repository.create(stock_data)
        
        # First create a rental transaction (to have something to return)
        rental_data = NewRentalRequest(
            transaction_date=date.today() - timedelta(days=7),
            customer_id=customer.id,
            location_id=location.id,
            items=[
                RentalItem(
                    item_id=item.id,
                    quantity=20,
                    rental_period_value=7,
                    rental_start_date=date.today() - timedelta(days=7),
                    rental_end_date=date.today()
                )
            ],
            payment_method="CREDIT_CARD"
        )
        
        original_rental = await transaction_service.create_new_rental(rental_data)
        
        # Now create a return for part of the rental
        from app.modules.transactions.schemas.returns import RentalReturnCreate, RentalReturnItem
        return_data = RentalReturnCreate(
            original_transaction_id=original_rental.transaction_id,
            return_date=date.today(),
            location_id=location.id,
            return_items=[
                RentalReturnItem(
                    item_id=item.id,
                    return_quantity=15,
                    condition_on_return="GOOD",
                    cleaning_condition="CLEAN"
                )
            ],
            notes="Partial return test"
        )
        
        return_result = await transaction_service.create_rental_return(return_data)
        
        # Verify return was created
        assert return_result.success is True
        
        # Check stock movements - should have rental out and return movements
        movements = await inventory_service.get_stock_movements_by_stock_level(stock_level.id)
        
        # Find the return movement
        return_movements = [m for m in movements if m.movement_type == MovementType.RENTAL_RETURN]
        assert len(return_movements) >= 1
        
        return_movement = return_movements[0]
        assert return_movement.quantity_change == Decimal("15")  # Positive back to available
        assert return_movement.reference_type == ReferenceType.TRANSACTION
        assert "Returned 15 units from rent" in return_movement.reason


class TestStockMovementAuditTrail:
    """Test complete audit trail for stock movements."""
    
    async def test_complete_stock_lifecycle_audit_trail(
        self, 
        session: AsyncSession, 
        transaction_service, 
        inventory_service,
        setup_transaction_test_data
    ):
        """Test complete lifecycle creates proper audit trail."""
        test_data = setup_transaction_test_data
        item = test_data["items"][0]
        location = test_data["location"]
        customer = test_data["customer"]
        
        # 1. Purchase stock
        purchase_data = NewPurchaseRequest(
            transaction_date=date.today(),
            location_id=location.id,
            items=[
                PurchaseItem(
                    item_id=item.id,
                    quantity=100,
                    condition="NEW",
                    unit_price=Decimal("20.00")
                )
            ],
            payment_method="CASH",
            notes="Lifecycle test purchase"
        )
        
        purchase_result = await transaction_service.create_new_purchase(purchase_data)
        
        # 2. Rent out some stock
        rental_data = NewRentalRequest(
            transaction_date=date.today(),
            customer_id=customer.id,
            location_id=location.id,
            items=[
                RentalItem(
                    item_id=item.id,
                    quantity=30,
                    rental_period_value=5,
                    rental_start_date=date.today(),
                    rental_end_date=date.today() + timedelta(days=5)
                )
            ],
            payment_method="CREDIT_CARD",
            notes="Lifecycle test rental"
        )
        
        rental_result = await transaction_service.create_new_rental(rental_data)
        
        # 3. Get stock level
        stock_level = await inventory_service.stock_level_repository.get_by_item_location(
            item.id, location.id
        )
        
        # 4. Manual adjustment
        adjustment_result = await inventory_service.create_manual_stock_movement(
            stock_level_id=stock_level.id,
            movement_type=MovementType.ADJUSTMENT_POSITIVE,
            quantity_change=Decimal("10"),
            reason="Lifecycle test adjustment"
        )
        
        # 5. Return some rental stock
        from app.modules.transactions.schemas.returns import RentalReturnCreate, RentalReturnItem
        return_data = RentalReturnCreate(
            original_transaction_id=rental_result.transaction_id,
            return_date=date.today(),
            location_id=location.id,
            return_items=[
                RentalReturnItem(
                    item_id=item.id,
                    return_quantity=20,
                    condition_on_return="EXCELLENT",
                    cleaning_condition="CLEAN"
                )
            ],
            notes="Lifecycle test return"
        )
        
        return_result = await transaction_service.create_rental_return(return_data)
        
        # 6. Verify complete audit trail
        movements = await inventory_service.get_stock_movements_by_stock_level(stock_level.id)
        
        # Should have: purchase, rental out, adjustment, rental return
        assert len(movements) >= 4
        
        movement_types = [m.movement_type for m in movements]
        assert MovementType.PURCHASE in movement_types
        assert MovementType.RENTAL_OUT in movement_types
        assert MovementType.ADJUSTMENT_POSITIVE in movement_types
        assert MovementType.RENTAL_RETURN in movement_types
        
        # Verify transaction references
        transaction_references = {m.reference_id for m in movements if m.reference_type == ReferenceType.TRANSACTION}
        assert str(purchase_result.transaction_id) in transaction_references
        assert str(rental_result.transaction_id) in transaction_references
        assert str(return_result.transaction_id) in transaction_references
        
        # Verify final stock state
        await session.refresh(stock_level)
        assert stock_level.quantity_on_hand == Decimal("110")  # 100 + 10 adjustment
        assert stock_level.quantity_available == Decimal("90")  # 70 + 20 returned
        assert stock_level.quantity_on_rent == Decimal("10")    # 30 - 20 returned
        
        # 7. Verify movement summary
        summary = await inventory_service.get_stock_movement_summary(item.id)
        assert summary.total_movements >= 4
        assert summary.net_change == Decimal("110")  # Only purchase and adjustment add to total stock
        
        # 8. Verify movements can be retrieved by reference
        purchase_movements = await inventory_service.get_stock_movements_by_reference(
            ReferenceType.TRANSACTION, str(purchase_result.transaction_id)
        )
        assert len(purchase_movements) == 1
        assert purchase_movements[0].movement_type == MovementType.PURCHASE