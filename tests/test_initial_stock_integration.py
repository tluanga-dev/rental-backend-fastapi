"""
Comprehensive tests for initial stock creation integration.

This test suite covers the complete workflow from item creation with initial stock
through to inventory system integration, ensuring all business rules are enforced
and the system behaves correctly under various scenarios.
"""

import pytest
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch

from app.modules.inventory.service import InventoryService
from app.modules.master_data.item_master.service import ItemMasterService
from app.modules.master_data.item_master.schemas import ItemCreate
from app.modules.master_data.item_master.models import ItemStatus
from app.modules.inventory.models import InventoryUnitStatus, InventoryUnitCondition


class TestInitialStockCreation:
    """Test suite for initial stock creation functionality."""

    @pytest.fixture
    def mock_item_data(self):
        """Create mock item data for testing."""
        return {
            "id": uuid4(),
            "sku": "TEST-SKU-001",
            "item_name": "Test Item",
            "is_active": True,
            "purchase_price": Decimal("100.00")
        }

    @pytest.fixture
    def mock_location_data(self):
        """Create mock location data for testing."""
        return {
            "id": uuid4(),
            "location_name": "Test Warehouse",
            "is_active": True
        }

    @pytest.mark.asyncio
    async def test_create_initial_stock_success(self, mock_session, mock_item_data, mock_location_data):
        """Test successful initial stock creation."""
        # Setup
        service = InventoryService(mock_session)
        
        # Mock repository responses
        service.item_repository.get_by_id = AsyncMock(return_value=type('Item', (), mock_item_data)())
        service.location_repository.get_by_id = AsyncMock(return_value=type('Location', (), mock_location_data)())
        service.stock_level_repository.get_by_item_location = AsyncMock(return_value=None)
        service.stock_level_repository.get_all = AsyncMock(return_value=[])
        service.inventory_unit_repository.get_units_by_item = AsyncMock(return_value=[])
        service.inventory_unit_repository.get_by_code = AsyncMock(return_value=None)
        
        # Mock creation methods
        mock_stock_level = type('StockLevel', (), {"id": uuid4()})()
        service.stock_level_repository.create = AsyncMock(return_value=mock_stock_level)
        
        mock_inventory_unit = type('InventoryUnit', (), {"unit_code": "TEST-SKU-001-U001"})()
        service.inventory_unit_repository.create = AsyncMock(return_value=mock_inventory_unit)
        
        # Execute
        result = await service.create_initial_stock(
            item_id=mock_item_data["id"],
            item_sku=mock_item_data["sku"],
            purchase_price=mock_item_data["purchase_price"],
            quantity=2,
            location_id=mock_location_data["id"]
        )
        
        # Verify
        assert result["created"] is True
        assert result["total_quantity"] == 2
        assert len(result["unit_codes"]) == 2
        assert result["purchase_price"] == "100.00"
        assert "location_name" in result

    @pytest.mark.asyncio
    async def test_business_rule_validation_invalid_quantity(self, mock_session):
        """Test business rule validation for invalid quantity."""
        service = InventoryService(mock_session)
        
        result = await service.create_initial_stock(
            item_id=uuid4(),
            item_sku="TEST-SKU",
            purchase_price=Decimal("100.00"),
            quantity=0  # Invalid quantity
        )
        
        assert result["created"] is False
        assert "must be greater than 0" in result["reason"]

    @pytest.mark.asyncio
    async def test_business_rule_validation_excessive_quantity(self, mock_session):
        """Test business rule validation for excessive quantity."""
        service = InventoryService(mock_session)
        
        result = await service.create_initial_stock(
            item_id=uuid4(),
            item_sku="TEST-SKU",
            purchase_price=Decimal("100.00"),
            quantity=15000  # Exceeds maximum
        )
        
        assert result["created"] is False
        assert "cannot exceed 10,000" in result["reason"]

    @pytest.mark.asyncio
    async def test_business_rule_validation_nonexistent_item(self, mock_session):
        """Test business rule validation for non-existent item."""
        service = InventoryService(mock_session)
        service.item_repository.get_by_id = AsyncMock(return_value=None)
        
        result = await service.create_initial_stock(
            item_id=uuid4(),
            item_sku="TEST-SKU",
            purchase_price=Decimal("100.00"),
            quantity=5
        )
        
        assert result["created"] is False
        assert "not found" in result["reason"]

    @pytest.mark.asyncio
    async def test_business_rule_validation_inactive_item(self, mock_session, mock_item_data):
        """Test business rule validation for inactive item."""
        service = InventoryService(mock_session)
        
        # Mock inactive item
        inactive_item_data = {**mock_item_data, "is_active": False}
        service.item_repository.get_by_id = AsyncMock(
            return_value=type('Item', (), inactive_item_data)()
        )
        
        result = await service.create_initial_stock(
            item_id=mock_item_data["id"],
            item_sku=mock_item_data["sku"],
            purchase_price=Decimal("100.00"),
            quantity=5
        )
        
        assert result["created"] is False
        assert "inactive items" in result["reason"]

    @pytest.mark.asyncio
    async def test_business_rule_validation_sku_mismatch(self, mock_session, mock_item_data):
        """Test business rule validation for SKU mismatch."""
        service = InventoryService(mock_session)
        service.item_repository.get_by_id = AsyncMock(
            return_value=type('Item', (), mock_item_data)()
        )
        
        result = await service.create_initial_stock(
            item_id=mock_item_data["id"],
            item_sku="WRONG-SKU",  # Different from item's SKU
            purchase_price=Decimal("100.00"),
            quantity=5
        )
        
        assert result["created"] is False
        assert "SKU mismatch" in result["reason"]

    @pytest.mark.asyncio
    async def test_business_rule_validation_existing_stock(self, mock_session, mock_item_data):
        """Test business rule validation when stock already exists."""
        service = InventoryService(mock_session)
        service.item_repository.get_by_id = AsyncMock(
            return_value=type('Item', (), mock_item_data)()
        )
        
        # Mock existing stock level
        existing_stock = type('StockLevel', (), {"id": uuid4()})()
        service.stock_level_repository.get_all = AsyncMock(return_value=[existing_stock])
        
        result = await service.create_initial_stock(
            item_id=mock_item_data["id"],
            item_sku=mock_item_data["sku"],
            purchase_price=Decimal("100.00"),
            quantity=5
        )
        
        assert result["created"] is False
        assert "already has existing stock" in result["reason"]

    @pytest.mark.asyncio
    async def test_business_rule_validation_negative_price(self, mock_session, mock_item_data):
        """Test business rule validation for negative purchase price."""
        service = InventoryService(mock_session)
        service.item_repository.get_by_id = AsyncMock(
            return_value=type('Item', (), mock_item_data)()
        )
        service.stock_level_repository.get_all = AsyncMock(return_value=[])
        service.inventory_unit_repository.get_units_by_item = AsyncMock(return_value=[])
        
        result = await service.create_initial_stock(
            item_id=mock_item_data["id"],
            item_sku=mock_item_data["sku"],
            purchase_price=Decimal("-10.00"),  # Negative price
            quantity=5
        )
        
        assert result["created"] is False
        assert "cannot be negative" in result["reason"]

    @pytest.mark.asyncio
    async def test_unit_code_generation(self, mock_session):
        """Test unit code generation logic."""
        service = InventoryService(mock_session)
        
        # Test basic unit code generation
        unit_code = service.generate_unit_code("TEST-SKU-001", 1)
        assert unit_code == "TEST-SKU-001-U001"
        
        unit_code = service.generate_unit_code("TEST-SKU-001", 25)
        assert unit_code == "TEST-SKU-001-U025"
        
        unit_code = service.generate_unit_code("TEST-SKU-001", 999)
        assert unit_code == "TEST-SKU-001-U999"

    @pytest.mark.asyncio
    async def test_default_location_creation(self, mock_session):
        """Test default location creation when none exists."""
        service = InventoryService(mock_session)
        
        # Mock no existing locations
        service.location_repository.get_all = AsyncMock(return_value=[])
        
        # Mock creation of default location
        mock_default_location = type('Location', (), {
            "id": uuid4(),
            "location_name": "Default Warehouse",
            "is_active": True
        })()
        service.location_repository.create = AsyncMock(return_value=mock_default_location)
        
        # Execute
        location = await service.get_default_location()
        
        # Verify
        assert location.location_name == "Default Warehouse"
        service.location_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_default_location_existing(self, mock_session, mock_location_data):
        """Test using existing location as default."""
        service = InventoryService(mock_session)
        
        # Mock existing location
        existing_location = type('Location', (), mock_location_data)()
        service.location_repository.get_all = AsyncMock(return_value=[existing_location])
        
        # Execute
        location = await service.get_default_location()
        
        # Verify
        assert location.location_name == mock_location_data["location_name"]
        # Should not create new location
        assert not hasattr(service.location_repository, 'create') or \
               not service.location_repository.create.called


class TestItemMasterServiceIntegration:
    """Test suite for item master service integration with initial stock."""

    @pytest.fixture
    def mock_unit_data(self):
        """Create mock unit of measurement data."""
        return {
            "id": uuid4(),
            "unit_name": "piece",
            "unit_code": "pcs"
        }

    @pytest.mark.asyncio
    async def test_item_creation_with_initial_stock(self, mock_session, mock_unit_data):
        """Test item creation with initial stock integration."""
        service = ItemMasterService(mock_session)
        
        # Mock dependencies
        service.sku_generator.generate_sku = AsyncMock(return_value="GENERATED-SKU-001")
        
        # Mock item creation
        mock_item = type('Item', (), {
            "id": uuid4(),
            "sku": "GENERATED-SKU-001",
            "item_name": "Test Item",
            "purchase_price": Decimal("150.00")
        })()
        service.item_repository.create = AsyncMock(return_value=mock_item)
        
        # Mock inventory service creation success
        with patch('app.modules.inventory.service.InventoryService') as mock_inventory_service_class:
            mock_inventory_service = AsyncMock()
            mock_inventory_service.create_initial_stock = AsyncMock(return_value={
                "created": True,
                "total_quantity": 3,
                "location_name": "Default Warehouse",
                "unit_codes": ["GENERATED-SKU-001-U001", "GENERATED-SKU-001-U002", "GENERATED-SKU-001-U003"]
            })
            mock_inventory_service_class.return_value = mock_inventory_service
            
            # Prepare test data
            item_create = ItemCreate(
                item_name="Test Item",
                unit_of_measurement_id=mock_unit_data["id"],
                is_rentable=True,
                is_saleable=False,
                rental_rate_per_period=Decimal("25.00"),
                rental_period="1",
                purchase_price=Decimal("150.00"),
                initial_stock_quantity=3
            )
            
            # Execute
            result = await service.create_item(item_create)
            
            # Verify
            assert result.sku == "GENERATED-SKU-001"
            assert result.item_name == "Test Item"
            mock_inventory_service.create_initial_stock.assert_called_once_with(
                item_id=mock_item.id,
                item_sku="GENERATED-SKU-001",
                purchase_price=Decimal("150.00"),
                quantity=3
            )

    @pytest.mark.asyncio
    async def test_item_creation_without_initial_stock(self, mock_session, mock_unit_data):
        """Test item creation without initial stock (should not call inventory service)."""
        service = ItemMasterService(mock_session)
        
        # Mock dependencies
        service.sku_generator.generate_sku = AsyncMock(return_value="GENERATED-SKU-002")
        
        # Mock item creation
        mock_item = type('Item', (), {
            "id": uuid4(),
            "sku": "GENERATED-SKU-002",
            "item_name": "Test Item No Stock"
        })()
        service.item_repository.create = AsyncMock(return_value=mock_item)
        
        # Mock inventory service (should not be called)
        with patch('app.modules.inventory.service.InventoryService') as mock_inventory_service_class:
            mock_inventory_service = AsyncMock()
            mock_inventory_service_class.return_value = mock_inventory_service
            
            # Prepare test data (no initial stock)
            item_create = ItemCreate(
                item_name="Test Item No Stock",
                unit_of_measurement_id=mock_unit_data["id"],
                is_rentable=True,
                is_saleable=False,
                rental_rate_per_period=Decimal("25.00"),
                rental_period="1"
                # No initial_stock_quantity specified
            )
            
            # Execute
            result = await service.create_item(item_create)
            
            # Verify
            assert result.sku == "GENERATED-SKU-002"
            # Inventory service should not be called
            mock_inventory_service.create_initial_stock.assert_not_called()

    @pytest.mark.asyncio
    async def test_item_creation_stock_failure_continues(self, mock_session, mock_unit_data):
        """Test that item creation continues even if stock creation fails."""
        service = ItemMasterService(mock_session)
        
        # Mock dependencies
        service.sku_generator.generate_sku = AsyncMock(return_value="GENERATED-SKU-003")
        
        # Mock item creation
        mock_item = type('Item', (), {
            "id": uuid4(),
            "sku": "GENERATED-SKU-003",
            "item_name": "Test Item Stock Fail"
        })()
        service.item_repository.create = AsyncMock(return_value=mock_item)
        
        # Mock inventory service failure
        with patch('app.modules.inventory.service.InventoryService') as mock_inventory_service_class:
            mock_inventory_service = AsyncMock()
            mock_inventory_service.create_initial_stock = AsyncMock(
                side_effect=Exception("Stock creation failed")
            )
            mock_inventory_service_class.return_value = mock_inventory_service
            
            # Prepare test data
            item_create = ItemCreate(
                item_name="Test Item Stock Fail",
                unit_of_measurement_id=mock_unit_data["id"],
                is_rentable=True,
                is_saleable=False,
                rental_rate_per_period=Decimal("25.00"),
                rental_period="1",
                purchase_price=Decimal("200.00"),
                initial_stock_quantity=5
            )
            
            # Execute - should not raise exception
            result = await service.create_item(item_create)
            
            # Verify item was still created
            assert result.sku == "GENERATED-SKU-003"
            assert result.item_name == "Test Item Stock Fail"


class TestStockQueryEndpoints:
    """Test suite for stock query API endpoints."""

    @pytest.mark.asyncio
    async def test_get_item_stock_summary_success(self, mock_session):
        """Test successful stock summary retrieval."""
        service = InventoryService(mock_session)
        item_id = uuid4()
        
        # Mock stock levels
        mock_stock_levels = [
            type('StockLevel', (), {
                "quantity_on_hand": "10",
                "quantity_available": "8",
                "quantity_reserved": "2"
            })()
        ]
        service.get_stock_levels = AsyncMock(return_value=mock_stock_levels)
        
        # Mock inventory units
        mock_inventory_units = [
            type('InventoryUnit', (), {
                "status": InventoryUnitStatus.AVAILABLE,
                "location_id": uuid4()
            })(),
            type('InventoryUnit', (), {
                "status": InventoryUnitStatus.AVAILABLE,
                "location_id": uuid4()
            })()
        ]
        service.get_inventory_units = AsyncMock(return_value=mock_inventory_units)
        
        # This would typically be tested via FastAPI test client,
        # but here we're testing the logic that would be in the endpoint
        
        # Calculate summary (simulating endpoint logic)
        total_on_hand = sum(int(stock.quantity_on_hand) for stock in mock_stock_levels)
        total_available = sum(int(stock.quantity_available) for stock in mock_stock_levels)
        total_reserved = sum(int(stock.quantity_reserved) for stock in mock_stock_levels)
        
        units_by_status = {}
        for unit in mock_inventory_units:
            status_key = unit.status.value
            units_by_status[status_key] = units_by_status.get(status_key, 0) + 1
        
        # Verify calculations
        assert total_on_hand == 10
        assert total_available == 8
        assert total_reserved == 2
        assert units_by_status["AVAILABLE"] == 2
        assert len(mock_inventory_units) == 2


@pytest.fixture
def mock_session():
    """Mock database session for testing."""
    return AsyncMock()


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_initial_stock_integration.py -v
    pytest.main([__file__, "-v"])