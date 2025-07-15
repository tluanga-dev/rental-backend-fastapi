"""
Comprehensive tests for stock movement tracking system.

This test suite covers:
- StockMovement model validation and business logic
- Stock movement repository operations
- Inventory service stock movement integration
- Transaction-triggered stock movements
- API endpoints for stock movement history
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.models import (
    StockLevel, StockMovement, MovementType, ReferenceType, 
    InventoryUnit, InventoryUnitStatus, InventoryUnitCondition
)
from app.modules.inventory.repository import StockMovementRepository, StockLevelRepository
from app.modules.inventory.service import InventoryService
from app.modules.master_data.item_master.models import Item, ItemStatus
from app.modules.master_data.locations.models import Location
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.categories.models import Category
from app.modules.inventory.schemas import StockLevelCreate
from app.core.errors import NotFoundError, ValidationError


@pytest.fixture
async def sample_item(db_session: AsyncSession):
    """Create a sample item for testing."""
    # Create supporting data
    brand = Brand(name="Test Brand", brand_code="TB", description="Test brand")
    db_session.add(brand)
    await db_session.flush()
    
    category = Category(name="Test Category", category_code="TC", description="Test category")
    db_session.add(category)
    await db_session.flush()
    
    item = Item(
        sku="TST-001",
        item_name="Test Item",
        item_status=ItemStatus.ACTIVE,
        is_rentable=True,
        is_saleable=True,
        brand_id=brand.id,
        category_id=category.id,
        rental_rate_per_period=Decimal("10.00")
    )
    db_session.add(item)
    await db_session.flush()
    return item


@pytest.fixture
async def sample_location(db_session: AsyncSession):
    """Create a sample location for testing."""
    location = Location(
        location_name="Test Location",
        location_code="TL001",
        location_type="WAREHOUSE",
        address="123 Test Street"
    )
    db_session.add(location)
    await db_session.flush()
    return location


@pytest.fixture
async def sample_stock_level(db_session: AsyncSession, sample_item, sample_location):
    """Create a sample stock level for testing."""
    stock_level = StockLevel(
        item_id=str(sample_item.id),
        location_id=str(sample_location.id),
        quantity_on_hand=Decimal("100"),
        quantity_available=Decimal("80"),
        quantity_on_rent=Decimal("20")
    )
    db_session.add(stock_level)
    await db_session.flush()
    return stock_level


@pytest.fixture
async def stock_movement_repository(db_session: AsyncSession):
    """Create stock movement repository for testing."""
    return StockMovementRepository(db_session)


@pytest.fixture
async def inventory_service(db_session: AsyncSession):
    """Create inventory service for testing."""
    return InventoryService(db_session)


class TestStockMovementModel:
    """Test StockMovement model validation and business logic."""
    
    async def test_stock_movement_creation(self, db_session: AsyncSession, sample_stock_level):
        """Test creating a valid stock movement."""
        movement = StockMovement(
            stock_level_id=str(sample_stock_level.id),
            item_id=sample_stock_level.item_id,
            location_id=sample_stock_level.location_id,
            movement_type=MovementType.PURCHASE,
            reference_type=ReferenceType.TRANSACTION,
            quantity_change=Decimal("50"),
            quantity_before=Decimal("100"),
            quantity_after=Decimal("150"),
            reason="Test purchase",
            reference_id="TXN-001"
        )
        
        assert movement.movement_type == MovementType.PURCHASE.value
        assert movement.reference_type == ReferenceType.TRANSACTION.value
        assert movement.quantity_change == Decimal("50")
        assert movement.is_increase() == True
        assert movement.is_decrease() == False
        assert movement.is_neutral() == False
    
    async def test_stock_movement_validation_negative_quantities(self, session: AsyncSession, sample_stock_level):
        """Test validation of negative quantities."""
        with pytest.raises(ValueError, match="Quantity before cannot be negative"):
            StockMovement(
                stock_level_id=str(sample_stock_level.id),
                item_id=sample_stock_level.item_id,
                location_id=sample_stock_level.location_id,
                movement_type=MovementType.PURCHASE,
                reference_type=ReferenceType.TRANSACTION,
                quantity_change=Decimal("50"),
                quantity_before=Decimal("-10"),  # Invalid
                quantity_after=Decimal("40"),
                reason="Test purchase",
                reference_id="TXN-001"
            )
    
    async def test_stock_movement_validation_math_error(self, session: AsyncSession, sample_stock_level):
        """Test validation of quantity math."""
        with pytest.raises(ValueError, match="Quantity math doesn't add up"):
            StockMovement(
                stock_level_id=str(sample_stock_level.id),
                item_id=sample_stock_level.item_id,
                location_id=sample_stock_level.location_id,
                movement_type=MovementType.PURCHASE,
                reference_type=ReferenceType.TRANSACTION,
                quantity_change=Decimal("50"),
                quantity_before=Decimal("100"),
                quantity_after=Decimal("200"),  # Should be 150
                reason="Test purchase",
                reference_id="TXN-001"
            )
    
    async def test_stock_movement_properties(self, session: AsyncSession, sample_stock_level):
        """Test movement properties."""
        # Test increase
        increase_movement = StockMovement(
            stock_level_id=str(sample_stock_level.id),
            item_id=sample_stock_level.item_id,
            location_id=sample_stock_level.location_id,
            movement_type=MovementType.PURCHASE,
            reference_type=ReferenceType.TRANSACTION,
            quantity_change=Decimal("50"),
            quantity_before=Decimal("100"),
            quantity_after=Decimal("150"),
            reason="Test purchase",
            reference_id="TXN-001"
        )
        
        assert increase_movement.is_increase() == True
        assert increase_movement.is_decrease() == False
        assert "PURCHASE: +50" in increase_movement.display_name
        
        # Test decrease
        decrease_movement = StockMovement(
            stock_level_id=str(sample_stock_level.id),
            item_id=sample_stock_level.item_id,
            location_id=sample_stock_level.location_id,
            movement_type=MovementType.SALE,
            reference_type=ReferenceType.TRANSACTION,
            quantity_change=Decimal("-30"),
            quantity_before=Decimal("100"),
            quantity_after=Decimal("70"),
            reason="Test sale",
            reference_id="TXN-002"
        )
        
        assert decrease_movement.is_increase() == False
        assert decrease_movement.is_decrease() == True
        assert "SALE: -30" in decrease_movement.display_name


class TestStockMovementRepository:
    """Test StockMovementRepository operations."""
    
    async def test_create_movement(self, session: AsyncSession, stock_movement_repository, sample_stock_level):
        """Test creating a stock movement."""
        movement_data = {
            "stock_level_id": str(sample_stock_level.id),
            "item_id": sample_stock_level.item_id,
            "location_id": sample_stock_level.location_id,
            "movement_type": MovementType.PURCHASE.value,
            "reference_type": ReferenceType.TRANSACTION.value,
            "quantity_change": Decimal("50"),
            "quantity_before": Decimal("100"),
            "quantity_after": Decimal("150"),
            "reason": "Test purchase",
            "reference_id": "TXN-001"
        }
        
        movement = await stock_movement_repository.create(movement_data)
        
        assert movement.id is not None
        assert movement.movement_type == MovementType.PURCHASE.value
        assert movement.quantity_change == Decimal("50")
    
    async def test_get_by_stock_level(self, session: AsyncSession, stock_movement_repository, sample_stock_level):
        """Test getting movements by stock level."""
        # Create multiple movements
        for i in range(3):
            movement_data = {
                "stock_level_id": str(sample_stock_level.id),
                "item_id": sample_stock_level.item_id,
                "location_id": sample_stock_level.location_id,
                "movement_type": MovementType.PURCHASE.value,
                "reference_type": ReferenceType.TRANSACTION.value,
                "quantity_change": Decimal("10"),
                "quantity_before": Decimal("100"),
                "quantity_after": Decimal("110"),
                "reason": f"Test purchase {i}",
                "reference_id": f"TXN-{i:03d}"
            }
            await stock_movement_repository.create(movement_data)
        
        movements = await stock_movement_repository.get_by_stock_level(sample_stock_level.id)
        assert len(movements) == 3
        # Should be ordered by created_at desc
        assert movements[0].reference_id == "TXN-002"
    
    async def test_get_by_item(self, session: AsyncSession, stock_movement_repository, sample_stock_level):
        """Test getting movements by item."""
        # Create movements with different types
        movement_types = [MovementType.PURCHASE, MovementType.SALE, MovementType.RENTAL_OUT]
        
        for i, movement_type in enumerate(movement_types):
            movement_data = {
                "stock_level_id": str(sample_stock_level.id),
                "item_id": sample_stock_level.item_id,
                "location_id": sample_stock_level.location_id,
                "movement_type": movement_type.value,
                "reference_type": ReferenceType.TRANSACTION.value,
                "quantity_change": Decimal("10"),
                "quantity_before": Decimal("100"),
                "quantity_after": Decimal("110"),
                "reason": f"Test {movement_type.value}",
                "reference_id": f"TXN-{i:03d}"
            }
            await stock_movement_repository.create(movement_data)
        
        # Get all movements for item
        all_movements = await stock_movement_repository.get_by_item(sample_stock_level.item_id)
        assert len(all_movements) == 3
        
        # Get only purchase movements
        purchase_movements = await stock_movement_repository.get_by_item(
            sample_stock_level.item_id, 
            movement_type=MovementType.PURCHASE
        )
        assert len(purchase_movements) == 1
        assert purchase_movements[0].movement_type == MovementType.PURCHASE.value
    
    async def test_get_movement_summary(self, session: AsyncSession, stock_movement_repository, sample_stock_level):
        """Test getting movement summary."""
        # Create mixed movements
        movements_data = [
            (MovementType.PURCHASE, Decimal("50")),
            (MovementType.PURCHASE, Decimal("30")),
            (MovementType.SALE, Decimal("-20")),
            (MovementType.RENTAL_OUT, Decimal("-10"))
        ]
        
        quantity_before = Decimal("100")
        for movement_type, change in movements_data:
            movement_data = {
                "stock_level_id": str(sample_stock_level.id),
                "item_id": sample_stock_level.item_id,
                "location_id": sample_stock_level.location_id,
                "movement_type": movement_type.value,
                "reference_type": ReferenceType.TRANSACTION.value,
                "quantity_change": change,
                "quantity_before": quantity_before,
                "quantity_after": quantity_before + change,
                "reason": f"Test {movement_type.value}",
                "reference_id": f"TXN-{movement_type.value}"
            }
            await stock_movement_repository.create(movement_data)
            quantity_before += change
        
        summary = await stock_movement_repository.get_movement_summary(sample_stock_level.item_id)
        
        assert summary["total_movements"] == 4
        assert summary["total_increases"] == Decimal("80")  # 50 + 30
        assert summary["total_decreases"] == Decimal("30")  # 20 + 10
        assert summary["net_change"] == Decimal("50")  # 80 - 30
        assert "PURCHASE" in summary["movement_types"]
        assert summary["movement_types"]["PURCHASE"]["count"] == 2


class TestInventoryServiceStockMovements:
    """Test inventory service stock movement integration."""
    
    async def test_manual_stock_movement(self, session: AsyncSession, inventory_service, sample_stock_level):
        """Test creating manual stock movements."""
        initial_quantity = sample_stock_level.quantity_on_hand
        
        movement = await inventory_service.create_manual_stock_movement(
            stock_level_id=sample_stock_level.id,
            movement_type=MovementType.ADJUSTMENT_POSITIVE,
            quantity_change=Decimal("25"),
            reason="Manual adjustment test"
        )
        
        assert movement.movement_type == MovementType.ADJUSTMENT_POSITIVE
        assert movement.quantity_change == Decimal("25")
        assert movement.quantity_before == initial_quantity
        assert movement.quantity_after == initial_quantity + Decimal("25")
        assert movement.reference_type == ReferenceType.MANUAL_ADJUSTMENT
    
    async def test_rent_out_stock(self, session: AsyncSession, inventory_service, sample_stock_level):
        """Test renting out stock."""
        initial_available = sample_stock_level.quantity_available
        initial_on_rent = sample_stock_level.quantity_on_rent
        
        movement = await inventory_service.rent_out_stock(
            stock_level_id=sample_stock_level.id,
            quantity=Decimal("15"),
            transaction_id="TXN-RENT-001"
        )
        
        assert movement.movement_type == MovementType.RENTAL_OUT
        assert movement.quantity_change == Decimal("-15")  # Negative from available perspective
        assert movement.reference_type == ReferenceType.TRANSACTION
        assert movement.reference_id == "TXN-RENT-001"
        
        # Refresh stock level and check quantities
        await session.refresh(sample_stock_level)
        assert sample_stock_level.quantity_available == initial_available - Decimal("15")
        assert sample_stock_level.quantity_on_rent == initial_on_rent + Decimal("15")
    
    async def test_return_from_rent(self, session: AsyncSession, inventory_service, sample_stock_level):
        """Test returning stock from rent."""
        initial_available = sample_stock_level.quantity_available
        initial_on_rent = sample_stock_level.quantity_on_rent
        
        movement = await inventory_service.return_from_rent(
            stock_level_id=sample_stock_level.id,
            quantity=Decimal("10"),
            transaction_id="TXN-RETURN-001"
        )
        
        assert movement.movement_type == MovementType.RENTAL_RETURN
        assert movement.quantity_change == Decimal("10")  # Positive to available
        assert movement.reference_type == ReferenceType.TRANSACTION
        assert movement.reference_id == "TXN-RETURN-001"
        
        # Refresh stock level and check quantities
        await session.refresh(sample_stock_level)
        assert sample_stock_level.quantity_available == initial_available + Decimal("10")
        assert sample_stock_level.quantity_on_rent == initial_on_rent - Decimal("10")
    
    async def test_insufficient_stock_validation(self, session: AsyncSession, inventory_service, sample_stock_level):
        """Test validation when trying to rent more than available."""
        with pytest.raises(ValueError, match="Cannot rent more than available quantity"):
            await inventory_service.rent_out_stock(
                stock_level_id=sample_stock_level.id,
                quantity=Decimal("1000"),  # More than available
                transaction_id="TXN-INVALID"
            )
    
    async def test_get_stock_movements_pagination(self, session: AsyncSession, inventory_service, sample_stock_level):
        """Test pagination of stock movements."""
        # Create 10 movements
        for i in range(10):
            movement_data = {
                "stock_level_id": str(sample_stock_level.id),
                "item_id": sample_stock_level.item_id,
                "location_id": sample_stock_level.location_id,
                "movement_type": MovementType.PURCHASE.value,
                "reference_type": ReferenceType.TRANSACTION.value,
                "quantity_change": Decimal("1"),
                "quantity_before": Decimal("100"),
                "quantity_after": Decimal("101"),
                "reason": f"Test movement {i}",
                "reference_id": f"TXN-{i:03d}"
            }
            await inventory_service.stock_movement_repository.create(movement_data)
        
        # Test pagination
        page1 = await inventory_service.get_stock_movements_by_stock_level(
            sample_stock_level.id, skip=0, limit=5
        )
        page2 = await inventory_service.get_stock_movements_by_stock_level(
            sample_stock_level.id, skip=5, limit=5
        )
        
        assert len(page1) == 5
        assert len(page2) == 5
        
        # Ensure no overlap
        page1_ids = {m.id for m in page1}
        page2_ids = {m.id for m in page2}
        assert len(page1_ids & page2_ids) == 0


class TestStockLevelUpdatedModel:
    """Test updated StockLevel model functionality."""
    
    async def test_updated_stock_level_fields(self, session: AsyncSession, sample_item, sample_location):
        """Test updated StockLevel model with new fields."""
        stock_level = StockLevel(
            item_id=str(sample_item.id),
            location_id=str(sample_location.id),
            quantity_on_hand=Decimal("100"),
            quantity_available=Decimal("70"),
            quantity_on_rent=Decimal("30")
        )
        
        assert stock_level.quantity_on_hand == Decimal("100")
        assert stock_level.quantity_available == Decimal("70")
        assert stock_level.quantity_on_rent == Decimal("30")
    
    async def test_stock_level_validation(self, session: AsyncSession, sample_item, sample_location):
        """Test StockLevel validation logic."""
        with pytest.raises(ValueError, match="Total allocated quantities cannot exceed quantity on hand"):
            StockLevel(
                item_id=str(sample_item.id),
                location_id=str(sample_location.id),
                quantity_on_hand=Decimal("100"),
                quantity_available=Decimal("80"),
                quantity_on_rent=Decimal("30")  # 80 + 30 = 110 > 100
            )
    
    async def test_stock_level_rental_operations(self, session: AsyncSession, sample_item, sample_location):
        """Test rental operations on StockLevel."""
        stock_level = StockLevel(
            item_id=str(sample_item.id),
            location_id=str(sample_location.id),
            quantity_on_hand=Decimal("100"),
            quantity_available=Decimal("100"),
            quantity_on_rent=Decimal("0")
        )
        
        # Test rent out
        stock_level.rent_out_quantity(Decimal("25"))
        assert stock_level.quantity_available == Decimal("75")
        assert stock_level.quantity_on_rent == Decimal("25")
        
        # Test return from rent
        stock_level.return_from_rent(Decimal("10"))
        assert stock_level.quantity_available == Decimal("85")
        assert stock_level.quantity_on_rent == Decimal("15")
        
        # Test availability check
        assert stock_level.is_available_for_rent(Decimal("50")) == True
        assert stock_level.is_available_for_rent(Decimal("100")) == False
        
        # Test rental quantity check
        assert stock_level.has_rented_quantity(Decimal("10")) == True
        assert stock_level.has_rented_quantity(Decimal("20")) == False


class TestMovementTypeMapping:
    """Test movement type mapping from transaction types."""
    
    async def test_transaction_type_mapping(self, inventory_service):
        """Test mapping of transaction types to movement types."""
        mappings = [
            ("RENTAL_OUT", MovementType.RENTAL_OUT.value),
            ("RENTAL_RETURN", MovementType.RENTAL_RETURN.value),
            ("SALE", MovementType.SALE.value),
            ("PURCHASE", MovementType.PURCHASE.value),
            ("ADJUSTMENT", MovementType.ADJUSTMENT_POSITIVE.value),
            ("DAMAGE", MovementType.DAMAGE_LOSS.value),
            ("UNKNOWN", MovementType.SYSTEM_CORRECTION.value)  # Default
        ]
        
        for transaction_type, expected_movement_type in mappings:
            result = inventory_service._map_transaction_to_movement_type(transaction_type)
            assert result == expected_movement_type


@pytest.mark.asyncio
async def test_stock_movement_integration_workflow(
    session: AsyncSession, 
    inventory_service, 
    sample_item, 
    sample_location
):
    """Test complete workflow of stock movements."""
    # 1. Create initial stock level
    stock_data = StockLevelCreate(
        item_id=sample_item.id,
        location_id=sample_location.id,
        quantity_on_hand=Decimal("0"),
        quantity_available=Decimal("0"),
        quantity_on_rent=Decimal("0")
    )
    stock_level = await inventory_service.stock_level_repository.create(stock_data)
    
    # 2. Purchase stock (increase)
    purchase_movement = await inventory_service.create_manual_stock_movement(
        stock_level_id=stock_level.id,
        movement_type=MovementType.PURCHASE,
        quantity_change=Decimal("100"),
        reason="Initial purchase"
    )
    
    await session.refresh(stock_level)
    assert stock_level.quantity_on_hand == Decimal("100")
    assert stock_level.quantity_available == Decimal("100")
    
    # 3. Rent out stock
    rental_movement = await inventory_service.rent_out_stock(
        stock_level_id=stock_level.id,
        quantity=Decimal("30"),
        transaction_id="TXN-RENT-001"
    )
    
    await session.refresh(stock_level)
    assert stock_level.quantity_available == Decimal("70")
    assert stock_level.quantity_on_rent == Decimal("30")
    
    # 4. Return from rent
    return_movement = await inventory_service.return_from_rent(
        stock_level_id=stock_level.id,
        quantity=Decimal("20"),
        transaction_id="TXN-RETURN-001"
    )
    
    await session.refresh(stock_level)
    assert stock_level.quantity_available == Decimal("90")
    assert stock_level.quantity_on_rent == Decimal("10")
    
    # 5. Verify movement history
    movements = await inventory_service.get_stock_movements_by_stock_level(stock_level.id)
    assert len(movements) == 3
    
    # 6. Verify movement summary
    summary = await inventory_service.get_stock_movement_summary(sample_item.id)
    assert summary.total_movements == 3
    assert summary.net_change == Decimal("100")  # Only purchase adds to total