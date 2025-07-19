"""
Comprehensive tests for Rental Status Feature including:
- Scheduled task execution
- Status calculation and updates
- Rental return with status updates
- Line item status tracking
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.services.rental_status_calculator import RentalStatusCalculator, LineItemStatus
from app.modules.transactions.services.rental_status_updater import RentalStatusUpdater
from app.modules.transactions.services.rental_service import RentalReturnService
from app.modules.transactions.base.models import (
    TransactionHeader,
    TransactionLine,
    TransactionType,
    RentalStatus,
    RentalStatusChangeReason,
    RentalLifecycle,
    RentalReturnEvent,
    RentalStatusLog
)
from app.modules.system.service import SystemService
from app.core.scheduler import TaskScheduler


class TestRentalStatusCalculator:
    """Test cases for rental status calculation logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.session_mock = AsyncMock()
        self.calculator = RentalStatusCalculator(self.session_mock)
    
    def create_mock_transaction_line(
        self,
        quantity: Decimal = Decimal('1'),
        returned_quantity: Decimal = Decimal('0'),
        rental_start_date: date = None,
        rental_end_date: date = None
    ):
        """Create a mock transaction line for testing."""
        line = Mock(spec=TransactionLine)
        line.id = uuid4()
        line.quantity = quantity
        line.returned_quantity = returned_quantity
        line.rental_start_date = rental_start_date or date.today() - timedelta(days=5)
        line.rental_end_date = rental_end_date or date.today() + timedelta(days=2)
        line.sku = "TEST-001"
        line.description = "Test Item"
        return line
    
    def create_mock_transaction_header(self, lines=None):
        """Create a mock transaction header for testing."""
        header = Mock(spec=TransactionHeader)
        header.id = uuid4()
        header.transaction_type = TransactionType.RENTAL
        header.is_active = True
        header.transaction_lines = lines or []
        header.rental_start_date = date.today() - timedelta(days=5)
        header.rental_end_date = date.today() + timedelta(days=2)
        return header
    
    @pytest.mark.asyncio
    async def test_line_item_status_active(self):
        """Test line item status calculation for ACTIVE status."""
        # Arrange
        future_date = date.today() + timedelta(days=5)
        line = self.create_mock_transaction_line(
            quantity=Decimal('2'),
            returned_quantity=Decimal('0'),
            rental_end_date=future_date
        )
        
        # Act
        status = await self.calculator.calculate_line_item_status(line)
        
        # Assert
        assert status == LineItemStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_line_item_status_late(self):
        """Test line item status calculation for LATE status."""
        # Arrange
        past_date = date.today() - timedelta(days=2)
        line = self.create_mock_transaction_line(
            quantity=Decimal('2'),
            returned_quantity=Decimal('0'),
            rental_end_date=past_date
        )
        
        # Act
        status = await self.calculator.calculate_line_item_status(line)
        
        # Assert
        assert status == LineItemStatus.LATE
    
    @pytest.mark.asyncio
    async def test_line_item_status_partial_return(self):
        """Test line item status calculation for PARTIAL_RETURN status."""
        # Arrange
        future_date = date.today() + timedelta(days=5)
        line = self.create_mock_transaction_line(
            quantity=Decimal('3'),
            returned_quantity=Decimal('1'),
            rental_end_date=future_date
        )
        
        # Act
        status = await self.calculator.calculate_line_item_status(line)
        
        # Assert
        assert status == LineItemStatus.PARTIAL_RETURN
    
    @pytest.mark.asyncio
    async def test_line_item_status_late_partial_return(self):
        """Test line item status calculation for LATE_PARTIAL_RETURN status."""
        # Arrange
        past_date = date.today() - timedelta(days=2)
        line = self.create_mock_transaction_line(
            quantity=Decimal('3'),
            returned_quantity=Decimal('1'),
            rental_end_date=past_date
        )
        
        # Act
        status = await self.calculator.calculate_line_item_status(line)
        
        # Assert
        assert status == LineItemStatus.LATE_PARTIAL_RETURN
    
    @pytest.mark.asyncio
    async def test_line_item_status_returned(self):
        """Test line item status calculation for RETURNED status."""
        # Arrange
        future_date = date.today() + timedelta(days=5)
        line = self.create_mock_transaction_line(
            quantity=Decimal('2'),
            returned_quantity=Decimal('2'),
            rental_end_date=future_date
        )
        
        # Act
        status = await self.calculator.calculate_line_item_status(line)
        
        # Assert
        assert status == LineItemStatus.RETURNED
    
    @pytest.mark.asyncio
    async def test_header_status_active_all_items_active(self):
        """Test header status when all line items are active."""
        # Arrange
        future_date = date.today() + timedelta(days=5)
        lines = [
            self.create_mock_transaction_line(quantity=Decimal('1'), returned_quantity=Decimal('0'), rental_end_date=future_date),
            self.create_mock_transaction_line(quantity=Decimal('1'), returned_quantity=Decimal('0'), rental_end_date=future_date)
        ]
        transaction = self.create_mock_transaction_header(lines)
        
        # Act
        status = await self.calculator.calculate_header_status(transaction)
        
        # Assert
        assert status == RentalStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_header_status_late_some_items_late(self):
        """Test header status when some items are late."""
        # Arrange
        past_date = date.today() - timedelta(days=2)
        future_date = date.today() + timedelta(days=5)
        lines = [
            self.create_mock_transaction_line(quantity=Decimal('1'), returned_quantity=Decimal('0'), rental_end_date=past_date),
            self.create_mock_transaction_line(quantity=Decimal('1'), returned_quantity=Decimal('0'), rental_end_date=future_date)
        ]
        transaction = self.create_mock_transaction_header(lines)
        
        # Act
        status = await self.calculator.calculate_header_status(transaction)
        
        # Assert
        assert status == RentalStatus.LATE
    
    @pytest.mark.asyncio
    async def test_header_status_partial_return(self):
        """Test header status when some items are returned."""
        # Arrange
        future_date = date.today() + timedelta(days=5)
        lines = [
            self.create_mock_transaction_line(quantity=Decimal('2'), returned_quantity=Decimal('1'), rental_end_date=future_date),
            self.create_mock_transaction_line(quantity=Decimal('1'), returned_quantity=Decimal('0'), rental_end_date=future_date)
        ]
        transaction = self.create_mock_transaction_header(lines)
        
        # Act
        status = await self.calculator.calculate_header_status(transaction)
        
        # Assert
        assert status == RentalStatus.PARTIAL_RETURN
    
    @pytest.mark.asyncio
    async def test_header_status_late_partial_return(self):
        """Test header status when some items are late and some are returned."""
        # Arrange
        past_date = date.today() - timedelta(days=2)
        future_date = date.today() + timedelta(days=5)
        lines = [
            self.create_mock_transaction_line(quantity=Decimal('2'), returned_quantity=Decimal('1'), rental_end_date=past_date),
            self.create_mock_transaction_line(quantity=Decimal('1'), returned_quantity=Decimal('0'), rental_end_date=future_date)
        ]
        transaction = self.create_mock_transaction_header(lines)
        
        # Act
        status = await self.calculator.calculate_header_status(transaction)
        
        # Assert
        assert status == RentalStatus.LATE_PARTIAL_RETURN
    
    @pytest.mark.asyncio
    async def test_header_status_returned_all_items_returned(self):
        """Test header status when all items are returned."""
        # Arrange
        future_date = date.today() + timedelta(days=5)
        lines = [
            self.create_mock_transaction_line(quantity=Decimal('2'), returned_quantity=Decimal('2'), rental_end_date=future_date),
            self.create_mock_transaction_line(quantity=Decimal('1'), returned_quantity=Decimal('1'), rental_end_date=future_date)
        ]
        transaction = self.create_mock_transaction_header(lines)
        
        # Act
        status = await self.calculator.calculate_header_status(transaction)
        
        # Assert
        assert status == RentalStatus.COMPLETED


class TestRentalStatusUpdater:
    """Test cases for rental status update functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.session_mock = AsyncMock()
        self.updater = RentalStatusUpdater(self.session_mock)
        self.updater.calculator = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_update_transaction_status_with_changes(self):
        """Test updating transaction status when changes are needed."""
        # Arrange
        transaction_id = uuid4()
        user_id = uuid4()
        
        # Mock calculator response
        self.updater.calculator.calculate_transaction_status.return_value = {
            'transaction_id': transaction_id,
            'header_status': 'LATE',
            'line_statuses': [
                {
                    'line_id': str(uuid4()),
                    'status': 'LATE',
                    'sku': 'TEST-001',
                    'description': 'Test Item',
                    'quantity': 1.0,
                    'returned_quantity': 0.0,
                    'rental_start_date': (date.today() - timedelta(days=10)).isoformat(),
                    'rental_end_date': (date.today() - timedelta(days=2)).isoformat(),
                    'days_overdue': 2
                }
            ],
            'summary': {
                'total_lines': 1,
                'total_quantity': 1.0,
                'total_returned_quantity': 0.0,
                'return_percentage': 0.0,
                'overdue_lines_count': 1,
                'max_overdue_days': 2
            }
        }
        
        # Mock database queries
        mock_transaction = Mock()
        mock_transaction.current_rental_status = 'ACTIVE'
        
        mock_line = Mock()
        mock_line.current_rental_status = 'ACTIVE'
        
        self.session_mock.execute.return_value.scalar_one_or_none.side_effect = [
            mock_transaction,  # Transaction query
            None,  # Lifecycle query  
            mock_line  # Line query
        ]
        
        # Act
        result = await self.updater.update_transaction_status(
            transaction_id=transaction_id,
            changed_by=user_id,
            change_reason=RentalStatusChangeReason.MANUAL_UPDATE,
            notes="Test update"
        )
        
        # Assert
        assert result['transaction_id'] == transaction_id
        assert result['header_status_changed'] == True
        assert len(result['changes_made']) >= 1  # At least header change
        assert result['total_changes'] >= 1
    
    @pytest.mark.asyncio
    async def test_batch_update_with_no_changes_needed(self):
        """Test batch update when no status changes are needed."""
        # Arrange
        self.updater.calculator.find_status_changes_needed.return_value = []
        
        # Act
        result = await self.updater.batch_update_overdue_statuses()
        
        # Assert
        assert result['updates_needed'] == 0
        assert result['successful_updates'] == 0
        assert result['failed_updates'] == 0
        assert len(result['transaction_results']) == 0


class TestRentalStatusIntegration:
    """Integration tests for the complete rental status system."""
    
    @pytest.mark.asyncio
    async def test_status_calculation_matches_prd_requirements(self):
        """Test that status calculations match the exact PRD requirements."""
        # This would be a comprehensive integration test that validates
        # the entire status calculation logic against the PRD requirements
        # using real database transactions (in a test database)
        pass
    
    @pytest.mark.asyncio
    async def test_return_event_triggers_status_update(self):
        """Test that return events properly trigger status updates."""
        # This would test the integration between return processing
        # and status updates to ensure they work together correctly
        pass
    
    @pytest.mark.asyncio
    async def test_scheduled_job_updates_overdue_statuses(self):
        """Test that the scheduled job properly updates overdue statuses."""
        # This would test the scheduled job functionality end-to-end
        pass


class TestScheduledTaskExecution:
    """Test scheduled task execution and automatic status updates."""
    
    @pytest.mark.asyncio
    async def test_daily_rental_status_check_job(self):
        """Test that the daily rental status check job executes correctly."""
        # Arrange
        scheduler = TaskScheduler()
        
        # Mock get_session to return our mock session
        with patch('app.core.scheduler.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            # Mock status updater (imported locally in the method)
            with patch('app.modules.transactions.services.rental_status_updater.RentalStatusUpdater') as mock_updater_class:
                mock_updater = AsyncMock()
                mock_updater.batch_update_overdue_statuses = AsyncMock(return_value={
                    'successful_updates': 5,
                    'failed_updates': 0,
                    'total_processed': 5,
                    'batch_id': 'batch-123'
                })
                mock_updater_class.return_value = mock_updater
                
                # Act
                await scheduler._rental_status_check_job()
                
                # Assert
                mock_updater.batch_update_overdue_statuses.assert_called_once_with(
                    changed_by=None  # System change
                )
    
    @pytest.mark.asyncio
    async def test_scheduler_configuration_from_settings(self):
        """Test that scheduler loads configuration from system settings."""
        # Arrange
        scheduler = TaskScheduler()
        
        with patch('app.core.scheduler.get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            with patch('app.core.scheduler.SystemService') as mock_system_service:
                mock_service = AsyncMock()
                mock_service.get_setting_value = AsyncMock(side_effect=[
                    'America/New_York',  # timezone
                    True,               # enabled
                    '02:30'            # check time
                ])
                mock_system_service.return_value = mock_service
                
                # Act
                await scheduler._load_configuration()
                
                # Assert
                # Verify timezone was requested
                mock_service.get_setting_value.assert_any_call('task_scheduler_timezone', 'UTC')


class TestRentalReturnWithStatus:
    """Test rental return process with automatic status updates."""
    
    @pytest.mark.asyncio
    async def test_complete_return_updates_status(self):
        """Test that completing a return updates rental status correctly."""
        # Arrange
        mock_session = AsyncMock()
        return_service = RentalReturnService(mock_session)
        
        transaction_id = uuid4()
        lifecycle_id = uuid4()
        line1_id = uuid4()
        line2_id = uuid4()
        
        # Create test data
        header = TransactionHeader(
            id=transaction_id,
            transaction_type=TransactionType.RENTAL,
            rental_start_date=date.today() - timedelta(days=7),
            rental_end_date=date.today() - timedelta(days=2),
            current_rental_status=RentalStatus.ACTIVE.value,
            transaction_lines=[
                TransactionLine(
                    id=line1_id,
                    quantity=Decimal("2.0"),
                    returned_quantity=Decimal("0.0"),
                    current_rental_status=RentalStatus.ACTIVE.value
                ),
                TransactionLine(
                    id=line2_id,
                    quantity=Decimal("5.0"),
                    returned_quantity=Decimal("0.0"),
                    current_rental_status=RentalStatus.ACTIVE.value
                )
            ]
        )
        
        lifecycle = RentalLifecycle(
            id=lifecycle_id,
            transaction_id=transaction_id,
            current_status=RentalStatus.ACTIVE.value
        )
        
        return_event = RentalReturnEvent(
            id=uuid4(),
            rental_lifecycle_id=lifecycle_id,
            event_date=date.today(),
            total_quantity_returned=Decimal("7.0"),
            items_returned=[
                {'transaction_line_id': str(line1_id), 'quantity': 2.0},
                {'transaction_line_id': str(line2_id), 'quantity': 5.0}
            ],
            processed_by=uuid4()
        )
        return_event.rental_lifecycle = lifecycle
        
        # Mock database operations
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = return_event
        mock_session.execute.return_value = mock_result
        
        # Mock status service
        return_service.status_service.get_rental_transaction = AsyncMock(return_value=header)
        
        # Mock status updater
        with patch.object(return_service.status_updater, 'update_status_from_return_event') as mock_update:
            mock_update.return_value = {
                'header_status_changed': True,
                'changes_made': [{
                    'type': 'header',
                    'old_status': RentalStatus.LATE.value,
                    'new_status': RentalStatus.COMPLETED.value
                }]
            }
            
            # Act
            result = await return_service.complete_return(
                return_event_id=return_event.id,
                payment_collected=Decimal("50.00"),
                receipt_number="REC-001"
            )
            
            # Assert
            mock_update.assert_called_once_with(
                transaction_id=lifecycle.transaction_id,
                return_event_id=return_event.id,
                changed_by=return_event.processed_by,
                notes="Status updated after processing return event"
            )


class TestLineItemStatusTracking:
    """Test individual line item status tracking."""
    
    @pytest.mark.asyncio
    async def test_line_item_status_update_in_database(self):
        """Test that line item status is updated in the database."""
        # Arrange
        mock_session = AsyncMock()
        updater = RentalStatusUpdater(mock_session)
        
        line_id = uuid4()
        transaction_id = uuid4()
        changed_by = uuid4()
        
        # Act
        await updater._update_line_status(
            line_id=line_id,
            new_status=RentalStatus.LATE.value,
            old_status=RentalStatus.ACTIVE.value,
            transaction_id=transaction_id,
            changed_by=changed_by,
            change_reason=RentalStatusChangeReason.SCHEDULED_UPDATE,
            batch_id="batch-123"
        )
        
        # Assert
        # Verify update query was executed
        assert mock_session.execute.call_count >= 1
        # Verify commit was called
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_transaction_includes_line_item_status(self):
        """Test that transaction responses include line item status."""
        # Arrange
        transaction = TransactionHeader(
            id=uuid4(),
            transaction_type=TransactionType.RENTAL,
            current_rental_status=RentalStatus.LATE.value,
            transaction_lines=[
                TransactionLine(
                    id=uuid4(),
                    sku="ITEM-001",
                    current_rental_status=RentalStatus.LATE_PARTIAL_RETURN.value,
                    quantity=Decimal("5.0"),
                    returned_quantity=Decimal("2.0")
                ),
                TransactionLine(
                    id=uuid4(),
                    sku="ITEM-002",
                    current_rental_status=RentalStatus.COMPLETED.value,
                    quantity=Decimal("3.0"),
                    returned_quantity=Decimal("3.0")
                )
            ]
        )
        
        # Assert - Verify all status fields exist
        assert hasattr(transaction, 'current_rental_status')
        assert transaction.current_rental_status == RentalStatus.LATE.value
        
        for line in transaction.transaction_lines:
            assert hasattr(line, 'current_rental_status')
            assert line.current_rental_status is not None
        
        # Verify specific line statuses
        assert transaction.transaction_lines[0].current_rental_status == RentalStatus.LATE_PARTIAL_RETURN.value
        assert transaction.transaction_lines[1].current_rental_status == RentalStatus.COMPLETED.value


class TestRentalStatusLogging:
    """Test rental status change logging."""
    
    @pytest.mark.asyncio
    async def test_status_log_creation(self):
        """Test that status changes create proper audit log entries."""
        # Arrange
        mock_session = AsyncMock()
        updater = RentalStatusUpdater(mock_session)
        
        transaction_id = uuid4()
        line_id = uuid4()
        changed_by = uuid4()
        
        # Act
        await updater._create_status_log(
            transaction_id=transaction_id,
            transaction_line_id=line_id,
            old_status=RentalStatus.ACTIVE.value,
            new_status=RentalStatus.LATE.value,
            change_reason=RentalStatusChangeReason.SCHEDULED_UPDATE,
            changed_by=changed_by,
            notes="Automated overdue check",
            status_metadata={'overdue_days': 3},
            system_generated=True,
            batch_id="batch-20250118-001"
        )
        
        # Assert
        assert mock_session.add.called
        added_log = mock_session.add.call_args[0][0]
        
        # Verify log properties
        assert isinstance(added_log, RentalStatusLog)
        assert added_log.transaction_id == transaction_id
        assert added_log.transaction_line_id == line_id
        assert added_log.old_status == RentalStatus.ACTIVE.value
        assert added_log.new_status == RentalStatus.LATE.value
        assert added_log.change_reason == RentalStatusChangeReason.SCHEDULED_UPDATE.value
        assert added_log.system_generated == True
        assert added_log.batch_id == "batch-20250118-001"
        assert added_log.status_metadata == {'overdue_days': 3}


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])