"""
Comprehensive tests for the unified return system.
"""
import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from uuid import uuid4

from app.modules.transactions.base.models import (
    TransactionHeader,
    TransactionLine,
    TransactionType,
    TransactionStatus,
    LineItemType
)
from app.modules.transactions.models.metadata import TransactionMetadata
from app.modules.transactions.schemas.returns import (
    SaleReturnCreate,
    PurchaseReturnCreate,
    RentalReturnCreate,
    SaleReturnLineItem,
    PurchaseReturnLineItem,
    RentalReturnLineItem,
    ReturnWorkflowState
)
from app.modules.transactions.services.unified_returns import UnifiedReturnService
from app.modules.transactions.services.return_workflows import WorkflowManager


class TestUnifiedReturns:
    """Test cases for unified return system."""
    
    @pytest.fixture
    async def unified_return_service(self, db_session, transaction_service, inventory_service):
        """Get unified return service instance."""
        return UnifiedReturnService(transaction_service, inventory_service, db_session)
    
    @pytest.fixture
    async def workflow_manager(self, db_session):
        """Get workflow manager instance."""
        return WorkflowManager(db_session)
    
    # Helper methods to create test transactions
    
    async def create_test_sale_transaction(self, db_session, customer_id, location_id):
        """Create a test sale transaction."""
        transaction = TransactionHeader(
            transaction_number=f"SALE-{datetime.now().timestamp()}",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.now() - timedelta(days=5),
            customer_id=str(customer_id),
            location_id=str(location_id),
            status=TransactionStatus.COMPLETED,
            subtotal=Decimal("200.00"),
            tax_amount=Decimal("20.00"),
            total_amount=Decimal("220.00"),
            paid_amount=Decimal("220.00")
        )
        
        # Add line items
        line1 = TransactionLine(
            transaction_id=str(transaction.id),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            item_id=str(uuid4()),
            description="Test Product 1",
            quantity=Decimal("2"),
            unit_price=Decimal("50.00"),
            line_total=Decimal("100.00")
        )
        
        line2 = TransactionLine(
            transaction_id=str(transaction.id),
            line_number=2,
            line_type=LineItemType.PRODUCT,
            item_id=str(uuid4()),
            description="Test Product 2",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("100.00")
        )
        
        transaction.transaction_lines = [line1, line2]
        
        db_session.add(transaction)
        await db_session.commit()
        
        return transaction
    
    async def create_test_purchase_transaction(self, db_session, supplier_id, location_id):
        """Create a test purchase transaction."""
        transaction = TransactionHeader(
            transaction_number=f"PUR-{datetime.now().timestamp()}",
            transaction_type=TransactionType.PURCHASE,
            transaction_date=datetime.now() - timedelta(days=10),
            customer_id=str(supplier_id),  # Supplier stored as customer
            location_id=str(location_id),
            status=TransactionStatus.COMPLETED,
            subtotal=Decimal("1000.00"),
            total_amount=Decimal("1000.00")
        )
        
        # Add line items
        line = TransactionLine(
            transaction_id=str(transaction.id),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            item_id=str(uuid4()),
            description="Bulk Purchase Item",
            quantity=Decimal("100"),
            unit_price=Decimal("10.00"),
            line_total=Decimal("1000.00")
        )
        
        transaction.transaction_lines = [line]
        
        db_session.add(transaction)
        await db_session.commit()
        
        return transaction
    
    async def create_test_rental_transaction(self, db_session, customer_id, location_id):
        """Create a test rental transaction."""
        transaction = TransactionHeader(
            transaction_number=f"RENT-{datetime.now().timestamp()}",
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime.now() - timedelta(days=7),
            customer_id=str(customer_id),
            location_id=str(location_id),
            status=TransactionStatus.IN_PROGRESS,
            rental_start_date=date.today() - timedelta(days=7),
            rental_end_date=date.today() - timedelta(days=1),  # Should have been returned yesterday
            deposit_amount=Decimal("500.00"),
            subtotal=Decimal("200.00"),
            total_amount=Decimal("200.00")
        )
        
        # Add rental line item
        line = TransactionLine(
            transaction_id=str(transaction.id),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            item_id=str(uuid4()),
            inventory_unit_id=str(uuid4()),
            description="Rental Equipment",
            quantity=Decimal("1"),
            unit_price=Decimal("200.00"),
            line_total=Decimal("200.00"),
            rental_start_date=transaction.rental_start_date,
            rental_end_date=transaction.rental_end_date
        )
        
        transaction.transaction_lines = [line]
        
        db_session.add(transaction)
        await db_session.commit()
        
        return transaction
    
    # Sale Return Tests
    
    async def test_sale_return_validation_success(self, unified_return_service, db_session):
        """Test successful sale return validation."""
        # Create test sale
        sale = await self.create_test_sale_transaction(
            db_session, uuid4(), uuid4()
        )
        
        # Create return data
        return_data = SaleReturnCreate(
            original_transaction_id=sale.id,
            return_reason_code="CHANGED_MIND",
            return_reason_notes="Customer changed their mind",
            customer_return_method="IN_STORE",
            refund_method="ORIGINAL_PAYMENT",
            quality_check_required=True,
            return_items=[
                SaleReturnLineItem(
                    original_line_id=sale.transaction_lines[0].id,
                    return_quantity=Decimal("1"),
                    condition="NEW",
                    return_to_stock=True,
                    original_packaging=True,
                    all_accessories_included=True
                )
            ]
        )
        
        # Validate return
        validation_result = await unified_return_service.validate_return(return_data)
        
        assert validation_result.is_valid
        assert len(validation_result.errors) == 0
        assert validation_result.estimated_refund == Decimal("50.00")  # 1 item at $50
    
    async def test_sale_return_validation_expired_period(self, unified_return_service, db_session):
        """Test sale return validation with expired return period."""
        # Create old sale
        sale = await self.create_test_sale_transaction(
            db_session, uuid4(), uuid4()
        )
        sale.transaction_date = datetime.now() - timedelta(days=45)  # 45 days old
        await db_session.commit()
        
        # Create return data
        return_data = SaleReturnCreate(
            original_transaction_id=sale.id,
            return_reason_code="DEFECTIVE",
            customer_return_method="IN_STORE",
            refund_method="ORIGINAL_PAYMENT",
            return_items=[
                SaleReturnLineItem(
                    original_line_id=sale.transaction_lines[0].id,
                    return_quantity=Decimal("1"),
                    condition="NEW",
                    return_to_stock=True
                )
            ]
        )
        
        # Validate return
        validation_result = await unified_return_service.validate_return(return_data)
        
        assert not validation_result.is_valid
        assert any("period expired" in error for error in validation_result.errors)
    
    async def test_sale_return_create_with_exchange(self, unified_return_service, db_session):
        """Test creating sale return as exchange."""
        # Create test sale
        sale = await self.create_test_sale_transaction(
            db_session, uuid4(), uuid4()
        )
        
        # Create exchange transaction
        exchange_id = uuid4()
        
        # Create return data
        return_data = SaleReturnCreate(
            original_transaction_id=sale.id,
            return_reason_code="WRONG_SIZE",
            customer_return_method="IN_STORE",
            refund_method="EXCHANGE",
            exchange_transaction_id=exchange_id,
            return_items=[
                SaleReturnLineItem(
                    original_line_id=sale.transaction_lines[0].id,
                    return_quantity=Decimal("2"),
                    condition="NEW",
                    return_to_stock=True,
                    original_packaging=True
                )
            ]
        )
        
        # Create return
        return_txn = await unified_return_service.create_return(return_data)
        
        assert return_txn.transaction_type == TransactionType.RETURN
        assert return_txn.reference_transaction_id == sale.id
        assert return_txn.transaction_lines[0].quantity == Decimal("-2")  # Negative
        assert return_txn.total_amount < 0  # Negative amount
        
        # Check metadata
        metadata = await db_session.execute(
            select(TransactionMetadata).where(
                TransactionMetadata.transaction_id == str(return_txn.id)
            )
        )
        metadata_entry = metadata.scalar_one()
        assert metadata_entry.metadata_content['refund_method'] == "EXCHANGE"
        assert metadata_entry.metadata_content['exchange_transaction_id'] == str(exchange_id)
    
    async def test_sale_return_with_restocking_fee(self, unified_return_service, db_session):
        """Test sale return with restocking fee for opened items."""
        # Create test sale
        sale = await self.create_test_sale_transaction(
            db_session, uuid4(), uuid4()
        )
        
        # Create return data with opened item
        return_data = SaleReturnCreate(
            original_transaction_id=sale.id,
            return_reason_code="CHANGED_MIND",
            customer_return_method="IN_STORE",
            refund_method="ORIGINAL_PAYMENT",
            return_items=[
                SaleReturnLineItem(
                    original_line_id=sale.transaction_lines[0].id,
                    return_quantity=Decimal("1"),
                    condition="OPENED",
                    return_to_stock=True,
                    original_packaging=False,  # No original packaging
                    all_accessories_included=True
                )
            ]
        )
        
        # Validate to check fees
        validation_result = await unified_return_service.validate_return(return_data)
        
        assert validation_result.is_valid
        assert 'restocking_fee' in validation_result.estimated_fees
        assert validation_result.estimated_fees['restocking_fee'] > 0
    
    # Purchase Return Tests
    
    async def test_purchase_return_with_quality_claim(self, unified_return_service, db_session):
        """Test purchase return with quality claim."""
        # Create test purchase
        purchase = await self.create_test_purchase_transaction(
            db_session, uuid4(), uuid4()
        )
        
        # Create return data
        return_data = PurchaseReturnCreate(
            original_transaction_id=purchase.id,
            return_reason_code="QUALITY_ISSUE",
            supplier_rma_number="RMA-2024-001",
            quality_claim=True,
            supplier_credit_expected=True,
            expected_credit_date=date.today() + timedelta(days=30),
            return_items=[
                PurchaseReturnLineItem(
                    original_line_id=purchase.transaction_lines[0].id,
                    return_quantity=Decimal("10"),
                    defect_code="MANUF_DEFECT",
                    supplier_fault=True,
                    batch_number="BATCH-123"
                )
            ]
        )
        
        # Create return
        return_txn = await unified_return_service.create_return(return_data)
        
        assert return_txn.transaction_type == TransactionType.RETURN
        assert return_txn.reference_transaction_id == purchase.id
        
        # Check metadata
        metadata = await db_session.execute(
            select(TransactionMetadata).where(
                TransactionMetadata.transaction_id == str(return_txn.id)
            )
        )
        metadata_entry = metadata.scalar_one()
        assert metadata_entry.metadata_content['quality_claim'] == True
        assert metadata_entry.metadata_content['supplier_rma_number'] == "RMA-2024-001"
    
    async def test_purchase_return_validation_no_rma(self, unified_return_service, db_session):
        """Test purchase return validation without RMA number."""
        # Create test purchase
        purchase = await self.create_test_purchase_transaction(
            db_session, uuid4(), uuid4()
        )
        
        # Create return data without RMA
        return_data = PurchaseReturnCreate(
            original_transaction_id=purchase.id,
            return_reason_code="OVERSTOCK",
            supplier_rma_number=None,  # No RMA
            return_items=[
                PurchaseReturnLineItem(
                    original_line_id=purchase.transaction_lines[0].id,
                    return_quantity=Decimal("10")
                )
            ]
        )
        
        # Validate return
        validation_result = await unified_return_service.validate_return(return_data)
        
        assert not validation_result.is_valid
        assert any("RMA number" in error for error in validation_result.errors)
    
    # Rental Return Tests
    
    async def test_rental_return_with_late_fee(self, unified_return_service, db_session):
        """Test rental return with late fee calculation."""
        # Create test rental
        rental = await self.create_test_rental_transaction(
            db_session, uuid4(), uuid4()
        )
        
        # Create return data (returning late)
        return_data = RentalReturnCreate(
            original_transaction_id=rental.id,
            return_reason_code="SCHEDULED_RETURN",
            scheduled_return_date=rental.rental_end_date,
            actual_return_date=date.today(),  # Late by several days
            damage_assessment_required=True,
            deposit_amount=Decimal("500.00"),
            return_items=[
                RentalReturnLineItem(
                    original_line_id=rental.transaction_lines[0].id,
                    return_quantity=Decimal("1"),
                    condition_on_return="GOOD",
                    cleaning_condition="CLEAN",
                    functionality_check="WORKING"
                )
            ]
        )
        
        # Create return
        return_txn = await unified_return_service.create_return(return_data)
        
        # Check metadata for late fee
        metadata = await db_session.execute(
            select(TransactionMetadata).where(
                TransactionMetadata.transaction_id == str(return_txn.id)
            )
        )
        metadata_entry = metadata.scalar_one()
        assert metadata_entry.metadata_content['late_fee_applicable'] == True
        assert metadata_entry.metadata_content['late_fee_amount'] > 0
    
    async def test_rental_return_with_damage(self, unified_return_service, db_session):
        """Test rental return with damage assessment."""
        # Create test rental
        rental = await self.create_test_rental_transaction(
            db_session, uuid4(), uuid4()
        )
        
        # Create return data with damage
        return_data = RentalReturnCreate(
            original_transaction_id=rental.id,
            return_reason_code="SCHEDULED_RETURN",
            scheduled_return_date=rental.rental_end_date,
            actual_return_date=date.today(),
            damage_assessment_required=True,
            deposit_amount=Decimal("500.00"),
            photos_required=True,
            photo_urls=["https://example.com/damage1.jpg", "https://example.com/damage2.jpg"],
            return_items=[
                RentalReturnLineItem(
                    original_line_id=rental.transaction_lines[0].id,
                    return_quantity=Decimal("1"),
                    condition_on_return="DAMAGED",
                    damage_description="Screen cracked, housing dented",
                    cleaning_condition="MINOR_CLEANING",
                    functionality_check="PARTIAL",
                    estimated_repair_cost=Decimal("150.00"),
                    beyond_normal_wear=True
                )
            ]
        )
        
        # Validate to check deposit calculation
        validation_result = await unified_return_service.validate_return(return_data)
        
        assert validation_result.is_valid
        
        # Create return
        return_txn = await unified_return_service.create_return(return_data)
        
        # Check that deposit was reduced
        metadata = await db_session.execute(
            select(TransactionMetadata).where(
                TransactionMetadata.transaction_id == str(return_txn.id)
            )
        )
        metadata_entry = metadata.scalar_one()
        deposit_refund = metadata_entry.metadata_content.get('deposit_refund_amount', 0)
        assert deposit_refund < Decimal("500.00")  # Less than original deposit
    
    async def test_rental_return_validation_partial_return(self, unified_return_service, db_session):
        """Test rental return validation with partial return (not allowed)."""
        # Create test rental with multiple items
        rental = await self.create_test_rental_transaction(
            db_session, uuid4(), uuid4()
        )
        
        # Add another line item
        line2 = TransactionLine(
            transaction_id=str(rental.id),
            line_number=2,
            line_type=LineItemType.PRODUCT,
            item_id=str(uuid4()),
            description="Rental Equipment 2",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("100.00")
        )
        rental.transaction_lines.append(line2)
        await db_session.commit()
        
        # Try to return only one item
        return_data = RentalReturnCreate(
            original_transaction_id=rental.id,
            return_reason_code="SCHEDULED_RETURN",
            scheduled_return_date=rental.rental_end_date,
            actual_return_date=date.today(),
            deposit_amount=Decimal("500.00"),
            return_items=[
                RentalReturnLineItem(
                    original_line_id=rental.transaction_lines[0].id,
                    return_quantity=Decimal("1"),
                    condition_on_return="GOOD",
                    cleaning_condition="CLEAN",
                    functionality_check="WORKING"
                )
                # Missing second item
            ]
        )
        
        # Validate return
        validation_result = await unified_return_service.validate_return(return_data)
        
        assert not validation_result.is_valid
        assert any("All rental items must be returned" in error for error in validation_result.errors)
    
    # Workflow Tests
    
    async def test_sale_return_workflow_transitions(self, workflow_manager):
        """Test sale return workflow transitions."""
        workflow = workflow_manager.get_workflow("SALE_RETURN")
        
        # Test allowed transitions
        from_initiated = workflow.get_allowed_transitions(ReturnWorkflowState.INITIATED)
        assert ReturnWorkflowState.VALIDATED in from_initiated
        assert ReturnWorkflowState.CANCELLED in from_initiated
        
        from_items_received = workflow.get_allowed_transitions(ReturnWorkflowState.ITEMS_RECEIVED)
        assert ReturnWorkflowState.INSPECTION_PENDING in from_items_received
        assert ReturnWorkflowState.REFUND_APPROVED in from_items_received
        
        # Test transition validation
        assert workflow.can_transition(
            ReturnWorkflowState.INITIATED,
            ReturnWorkflowState.VALIDATED
        )
        
        assert not workflow.can_transition(
            ReturnWorkflowState.COMPLETED,
            ReturnWorkflowState.CANCELLED  # Can't cancel completed returns
        )
    
    async def test_return_details_response(self, unified_return_service, db_session):
        """Test getting comprehensive return details."""
        # Create and process a sale return
        sale = await self.create_test_sale_transaction(
            db_session, uuid4(), uuid4()
        )
        
        return_data = SaleReturnCreate(
            original_transaction_id=sale.id,
            return_reason_code="DEFECTIVE",
            customer_return_method="SHIPPED",
            refund_method="STORE_CREDIT",
            return_shipping_cost=Decimal("15.00"),
            customer_pays_shipping=True,
            return_items=[
                SaleReturnLineItem(
                    original_line_id=sale.transaction_lines[0].id,
                    return_quantity=Decimal("1"),
                    condition="DAMAGED",
                    return_to_stock=False
                )
            ]
        )
        
        return_txn = await unified_return_service.create_return(return_data)
        
        # Get return details
        details = await unified_return_service.get_return_details(return_txn.id)
        
        assert details.return_type == "SALE_RETURN"
        assert details.original_transaction_id == sale.id
        assert details.specific_details.customer_return_method == "SHIPPED"
        assert details.specific_details.refund_method == "STORE_CREDIT"
        assert len(details.return_lines) == 1
        assert details.return_lines[0]['return_condition'] == "DAMAGED"


# Import for query support
from sqlalchemy import select