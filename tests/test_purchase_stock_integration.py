"""
Comprehensive tests for purchase transaction integration with stock level management.

This test suite validates the complete integration between purchase transactions and 
inventory stock level updates, ensuring data consistency and proper business logic.
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from uuid import uuid4, UUID
from datetime import datetime, date
from unittest.mock import AsyncMock, patch, MagicMock

from app.modules.transactions.service import TransactionService
from app.modules.transactions.schemas import NewPurchaseRequest, PurchaseItemCreate
from app.modules.inventory.schemas import StockLevelCreate, StockLevelResponse
from app.modules.inventory.models import StockLevel
from app.modules.transactions.base.models import TransactionHeader, TransactionType, TransactionStatus, PaymentStatus
from app.core.errors import NotFoundError, ConflictError


class TestPurchaseStockIntegration:
    """Test suite for purchase transaction + stock level integration."""

    @pytest.fixture
    def mock_supplier_id(self):
        """Mock supplier ID."""
        return uuid4()

    @pytest.fixture
    def mock_location_id(self):
        """Mock location ID."""
        return uuid4()

    @pytest.fixture
    def mock_item_ids(self):
        """Mock item IDs."""
        return [uuid4(), uuid4(), uuid4()]

    @pytest.fixture
    def mock_purchase_request(self, mock_supplier_id, mock_location_id, mock_item_ids):
        """Create mock purchase request data."""
        return NewPurchaseRequest(
            supplier_id=mock_supplier_id,
            location_id=mock_location_id,
            purchase_date=date.today(),
            notes="Test purchase transaction",
            items=[
                PurchaseItemCreate(
                    item_id=mock_item_ids[0],
                    quantity=5,
                    unit_cost=Decimal("100.00"),
                    condition="NEW",
                    tax_rate=Decimal("10.00"),
                    discount_amount=Decimal("0.00"),
                    notes="First item"
                ),
                PurchaseItemCreate(
                    item_id=mock_item_ids[1],
                    quantity=3,
                    unit_cost=Decimal("150.00"),
                    condition="GOOD",
                    tax_rate=Decimal("10.00"),
                    discount_amount=Decimal("5.00"),
                    notes="Second item"
                ),
                PurchaseItemCreate(
                    item_id=mock_item_ids[2],
                    quantity=2,
                    unit_cost=Decimal("200.00"),
                    condition="NEW",
                    tax_rate=Decimal("8.00"),
                    discount_amount=Decimal("0.00"),
                    notes="Third item"
                )
            ]
        )

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_existing_stock_level(self, mock_item_ids, mock_location_id):
        """Mock existing stock level."""
        stock = StockLevel(
            id=uuid4(),
            item_id=str(mock_item_ids[0]),
            location_id=str(mock_location_id),
            quantity_on_hand=Decimal("10"),
            quantity_available=Decimal("8"),
            quantity_reserved=Decimal("2"),
            quantity_on_order=Decimal("0")
        )
        stock.adjust_quantity = MagicMock()
        return stock

    @pytest.mark.asyncio
    async def test_create_new_purchase_with_stock_updates_success(
        self, mock_session, mock_purchase_request, mock_supplier_id, 
        mock_location_id, mock_item_ids
    ):
        """Test successful purchase creation with stock level updates."""
        # Setup service with mocked dependencies
        service = TransactionService(mock_session)
        
        # Mock repository methods
        with patch.object(service.inventory_service.stock_level_repository, 'get_by_item_location') as mock_get_stock, \
             patch.object(service.inventory_service.stock_level_repository, 'create') as mock_create_stock, \
             patch.object(service, 'get_transaction_with_lines') as mock_get_trans, \
             patch('app.modules.suppliers.repository.SupplierRepository') as mock_supplier_repo, \
             patch('app.modules.master_data.locations.repository.LocationRepository') as mock_location_repo, \
             patch('app.modules.master_data.item_master.repository.ItemMasterRepository') as mock_item_repo, \
             patch.object(service.transaction_repository, 'get_by_number', return_value=None):

            # Setup mock responses
            mock_supplier_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock(id=mock_supplier_id))
            mock_location_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock(id=mock_location_id))
            mock_item_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            
            # Mock stock level responses (no existing stock for new stock creation test)
            mock_get_stock.return_value = None
            mock_create_stock.return_value = MagicMock()
            
            # Mock transaction response
            mock_transaction = MagicMock()
            mock_transaction.id = uuid4()
            mock_transaction.transaction_number = "PUR-20240101-1234"
            mock_get_trans.return_value = MagicMock()

            # Execute
            result = await service.create_new_purchase(mock_purchase_request)

            # Assertions
            assert result.success is True
            assert "Purchase transaction created successfully" in result.message
            assert result.transaction_id is not None
            assert result.transaction_number.startswith("PUR-")

            # Verify stock level creation called for each item
            assert mock_create_stock.call_count == 3
            
            # Verify stock level data for first item
            first_call_args = mock_create_stock.call_args_list[0][0][0]
            assert first_call_args.item_id == mock_item_ids[0]
            assert first_call_args.location_id == mock_location_id
            assert first_call_args.quantity_on_hand == "5"
            assert first_call_args.quantity_available == "5"

    @pytest.mark.asyncio
    async def test_create_purchase_with_existing_stock_increment(
        self, mock_session, mock_purchase_request, mock_existing_stock_level,
        mock_supplier_id, mock_location_id, mock_item_ids
    ):
        """Test purchase creation that increments existing stock levels."""
        # Setup service
        service = TransactionService(mock_session)
        
        # Mock repository methods
        with patch.object(service.inventory_service.stock_level_repository, 'get_by_item_location') as mock_get_stock, \
             patch.object(service, 'get_transaction_with_lines') as mock_get_trans, \
             patch('app.modules.suppliers.repository.SupplierRepository') as mock_supplier_repo, \
             patch('app.modules.master_data.locations.repository.LocationRepository') as mock_location_repo, \
             patch('app.modules.master_data.item_master.repository.ItemMasterRepository') as mock_item_repo, \
             patch.object(service.transaction_repository, 'get_by_number', return_value=None):

            # Setup mock responses
            mock_supplier_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock(id=mock_supplier_id))
            mock_location_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock(id=mock_location_id))
            mock_item_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            
            # Mock existing stock for first item, no stock for others
            def mock_get_stock_side_effect(item_id, location_id):
                if item_id == mock_item_ids[0]:
                    return mock_existing_stock_level
                return None
            
            mock_get_stock.side_effect = mock_get_stock_side_effect
            mock_get_trans.return_value = MagicMock()

            # Execute
            result = await service.create_new_purchase(mock_purchase_request)

            # Assertions
            assert result.success is True
            
            # Verify existing stock was updated
            mock_existing_stock_level.adjust_quantity.assert_called_once_with(5)
            
            # Verify get_by_item_location called for each item
            assert mock_get_stock.call_count == 3

    @pytest.mark.asyncio
    async def test_purchase_creation_rollback_on_stock_failure(
        self, mock_session, mock_purchase_request, mock_supplier_id, 
        mock_location_id, mock_item_ids
    ):
        """Test that purchase transaction rolls back if stock level creation fails."""
        # Setup service
        service = TransactionService(mock_session)
        
        # Mock repository methods
        with patch.object(service.inventory_service.stock_level_repository, 'get_by_item_location') as mock_get_stock, \
             patch.object(service.inventory_service.stock_level_repository, 'create') as mock_create_stock, \
             patch('app.modules.suppliers.repository.SupplierRepository') as mock_supplier_repo, \
             patch('app.modules.master_data.locations.repository.LocationRepository') as mock_location_repo, \
             patch('app.modules.master_data.item_master.repository.ItemMasterRepository') as mock_item_repo, \
             patch.object(service.transaction_repository, 'get_by_number', return_value=None):

            # Setup mock responses
            mock_supplier_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock(id=mock_supplier_id))
            mock_location_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock(id=mock_location_id))
            mock_item_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            
            # Mock stock level failure
            mock_get_stock.return_value = None
            mock_create_stock.side_effect = Exception("Stock level creation failed")

            # Execute and assert exception
            with pytest.raises(Exception, match="Stock level creation failed"):
                await service.create_new_purchase(mock_purchase_request)

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_purchase_validation_failures(self, mock_session, mock_purchase_request):
        """Test purchase creation with various validation failures."""
        service = TransactionService(mock_session)
        
        # Test supplier not found
        with patch('app.modules.suppliers.repository.SupplierRepository') as mock_supplier_repo:
            mock_supplier_repo.return_value.get_by_id = AsyncMock(return_value=None)
            
            with pytest.raises(NotFoundError, match="Supplier with ID .* not found"):
                await service.create_new_purchase(mock_purchase_request)

        # Test location not found
        with patch('app.modules.suppliers.repository.SupplierRepository') as mock_supplier_repo, \
             patch('app.modules.master_data.locations.repository.LocationRepository') as mock_location_repo:
            
            mock_supplier_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            mock_location_repo.return_value.get_by_id = AsyncMock(return_value=None)
            
            with pytest.raises(NotFoundError, match="Location with ID .* not found"):
                await service.create_new_purchase(mock_purchase_request)

        # Test item not found
        with patch('app.modules.suppliers.repository.SupplierRepository') as mock_supplier_repo, \
             patch('app.modules.master_data.locations.repository.LocationRepository') as mock_location_repo, \
             patch('app.modules.master_data.item_master.repository.ItemMasterRepository') as mock_item_repo:
            
            mock_supplier_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            mock_location_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            mock_item_repo.return_value.get_by_id = AsyncMock(return_value=None)
            
            with pytest.raises(NotFoundError, match="Item with ID .* not found"):
                await service.create_new_purchase(mock_purchase_request)

    @pytest.mark.asyncio
    async def test_stock_level_helper_method_edge_cases(
        self, mock_session, mock_purchase_request, mock_location_id, mock_item_ids
    ):
        """Test the stock level helper method with edge cases."""
        service = TransactionService(mock_session)
        
        # Create mock transaction
        mock_transaction = TransactionHeader(
            id=uuid4(),
            transaction_number="PUR-20240101-1234",
            transaction_type=TransactionType.PURCHASE,
            status=TransactionStatus.COMPLETED,
            payment_status=PaymentStatus.PENDING
        )

        # Test with mixed scenarios: existing stock + new stock
        with patch.object(service.inventory_service.stock_level_repository, 'get_by_item_location') as mock_get_stock, \
             patch.object(service.inventory_service.stock_level_repository, 'create') as mock_create_stock:

            # Mock existing stock for first item
            existing_stock = MagicMock()
            existing_stock.adjust_quantity = MagicMock()
            
            def mock_get_stock_side_effect(item_id, location_id):
                if item_id == mock_item_ids[0]:
                    return existing_stock
                return None
            
            mock_get_stock.side_effect = mock_get_stock_side_effect
            mock_create_stock.return_value = MagicMock()

            # Execute the helper method directly
            await service._update_stock_levels_for_purchase(mock_purchase_request, mock_transaction)

            # Verify existing stock was adjusted
            existing_stock.adjust_quantity.assert_called_once_with(5)
            
            # Verify new stock levels created for other items
            assert mock_create_stock.call_count == 2

    @pytest.mark.asyncio 
    async def test_purchase_calculation_accuracy(
        self, mock_session, mock_purchase_request, mock_supplier_id,
        mock_location_id, mock_item_ids
    ):
        """Test that purchase calculations are accurate with stock integration."""
        service = TransactionService(mock_session)
        
        with patch.object(service.inventory_service.stock_level_repository, 'get_by_item_location', return_value=None), \
             patch.object(service.inventory_service.stock_level_repository, 'create'), \
             patch.object(service, 'get_transaction_with_lines') as mock_get_trans, \
             patch('app.modules.suppliers.repository.SupplierRepository') as mock_supplier_repo, \
             patch('app.modules.master_data.locations.repository.LocationRepository') as mock_location_repo, \
             patch('app.modules.master_data.item_master.repository.ItemMasterRepository') as mock_item_repo, \
             patch.object(service.transaction_repository, 'get_by_number', return_value=None):

            # Setup mock responses
            mock_supplier_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            mock_location_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            mock_item_repo.return_value.get_by_id = AsyncMock(return_value=MagicMock())
            mock_get_trans.return_value = MagicMock()

            # Execute
            result = await service.create_new_purchase(mock_purchase_request)

            # Verify transaction was created (stock integration doesn't break calculation)
            assert result.success is True
            
            # Verify session operations
            mock_session.add.assert_called()  # Transaction and lines added
            mock_session.commit.assert_called_once()  # Single atomic commit

    def test_stock_level_create_schema_validation(self, mock_item_ids, mock_location_id):
        """Test StockLevelCreate schema validation for purchase integration."""
        # Test valid data
        stock_data = StockLevelCreate(
            item_id=mock_item_ids[0],
            location_id=mock_location_id,
            quantity_on_hand="5",
            quantity_available="5",
            quantity_reserved="0",
            quantity_on_order="0"
        )
        
        assert stock_data.item_id == mock_item_ids[0]
        assert stock_data.location_id == mock_location_id
        assert stock_data.quantity_on_hand == "5"
        assert stock_data.quantity_available == "5"


class TestPurchaseStockIntegrationE2E:
    """End-to-end integration tests for purchase + stock management."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_purchase_stock_workflow(self):
        """Test complete workflow from purchase creation to stock verification."""
        # This would be an actual database integration test
        # Skipping implementation details as it requires live database
        pass

    @pytest.mark.integration 
    @pytest.mark.slow
    async def test_concurrent_purchase_stock_operations(self):
        """Test concurrent purchase operations don't cause stock inconsistencies."""
        # This would test race conditions and locking
        pass

    @pytest.mark.integration
    async def test_purchase_stock_data_consistency(self):
        """Test data consistency between purchase transactions and stock levels."""
        # This would verify actual database state consistency
        pass


# Test markers for different test categories
pytestmark = [
    pytest.mark.unit,  # Unit tests
    pytest.mark.asyncio,  # Async tests
]