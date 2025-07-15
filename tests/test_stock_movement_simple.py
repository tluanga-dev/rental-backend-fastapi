"""
Simple test to validate stock movement tracking functionality.
"""

import pytest
from decimal import Decimal
from app.modules.inventory.models import StockMovement, MovementType, ReferenceType


def test_stock_movement_model_creation():
    """Test creating a StockMovement model instance."""
    movement = StockMovement(
        stock_level_id="123e4567-e89b-12d3-a456-426614174000",
        item_id="123e4567-e89b-12d3-a456-426614174001",
        location_id="123e4567-e89b-12d3-a456-426614174002",
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


def test_stock_movement_validation_negative_change():
    """Test stock movement with negative change."""
    movement = StockMovement(
        stock_level_id="123e4567-e89b-12d3-a456-426614174000",
        item_id="123e4567-e89b-12d3-a456-426614174001",
        location_id="123e4567-e89b-12d3-a456-426614174002",
        movement_type=MovementType.SALE,
        reference_type=ReferenceType.TRANSACTION,
        quantity_change=Decimal("-30"),
        quantity_before=Decimal("100"),
        quantity_after=Decimal("70"),
        reason="Test sale",
        reference_id="TXN-002"
    )
    
    assert movement.is_decrease() == True
    assert movement.is_increase() == False
    assert "SALE: -30" in movement.display_name


def test_movement_type_enum():
    """Test MovementType enum values."""
    assert MovementType.PURCHASE.value == "PURCHASE"
    assert MovementType.SALE.value == "SALE"
    assert MovementType.RENTAL_OUT.value == "RENTAL_OUT"
    assert MovementType.RENTAL_RETURN.value == "RENTAL_RETURN"


def test_reference_type_enum():
    """Test ReferenceType enum values."""
    assert ReferenceType.TRANSACTION.value == "TRANSACTION"
    assert ReferenceType.MANUAL_ADJUSTMENT.value == "MANUAL_ADJUSTMENT"
    assert ReferenceType.SYSTEM_CORRECTION.value == "SYSTEM_CORRECTION"


def test_stock_movement_math_validation():
    """Test that stock movement validates quantity math."""
    with pytest.raises(ValueError, match="Quantity math doesn't add up"):
        StockMovement(
            stock_level_id="123e4567-e89b-12d3-a456-426614174000",
            item_id="123e4567-e89b-12d3-a456-426614174001",
            location_id="123e4567-e89b-12d3-a456-426614174002",
            movement_type=MovementType.PURCHASE,
            reference_type=ReferenceType.TRANSACTION,
            quantity_change=Decimal("50"),
            quantity_before=Decimal("100"),
            quantity_after=Decimal("200"),  # Should be 150
            reason="Test purchase",
            reference_id="TXN-001"
        )


def test_stock_movement_negative_quantities():
    """Test that stock movement rejects negative quantities."""
    with pytest.raises(ValueError, match="Quantity before cannot be negative"):
        StockMovement(
            stock_level_id="123e4567-e89b-12d3-a456-426614174000",
            item_id="123e4567-e89b-12d3-a456-426614174001",
            location_id="123e4567-e89b-12d3-a456-426614174002",
            movement_type=MovementType.PURCHASE,
            reference_type=ReferenceType.TRANSACTION,
            quantity_change=Decimal("50"),
            quantity_before=Decimal("-10"),  # Invalid
            quantity_after=Decimal("40"),
            reason="Test purchase",
            reference_id="TXN-001"
        )


if __name__ == "__main__":
    test_stock_movement_model_creation()
    test_stock_movement_validation_negative_change()
    test_movement_type_enum()
    test_reference_type_enum()
    test_stock_movement_math_validation()
    test_stock_movement_negative_quantities()
    print("All simple stock movement tests passed!")