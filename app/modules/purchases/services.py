"""
Purchase Services

Business logic for purchase operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.base.services import BaseTransactionService
from app.modules.transactions.base.models import TransactionType, TransactionStatus
from app.modules.purchases.repository import PurchasesRepository, PurchaseLineRepository
from app.modules.purchases.schemas import (
    PurchaseCreate,
    PurchaseUpdate,
    PurchaseResponse,
    PurchaseListResponse,
    PurchaseReportResponse,
    PurchaseOrderResponse,
    ReceivingUpdateRequest,
    ApprovalRequest,
    InspectionRequest,
    PurchaseLineUpdate,
    PurchaseLineResponse,
)


class PurchasesService(BaseTransactionService):
    """Service for purchase operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.purchases_repository = PurchasesRepository(session)
        self.purchase_line_repository = PurchaseLineRepository(session)
    
    async def create_purchase(self, purchase_data: PurchaseCreate) -> PurchaseResponse:
        """Create a new purchase."""
        # Validate purchase data
        errors = self.validate_purchase_data(purchase_data)
        if errors:
            raise ValueError(f"Invalid purchase data: {', '.join(errors)}")
        
        # Generate transaction number if not provided
        if not hasattr(purchase_data, 'transaction_number') or not purchase_data.transaction_number:
            transaction_number = self.generate_transaction_number(TransactionType.PURCHASE)
        else:
            transaction_number = purchase_data.transaction_number
        
        # Generate PO number if not provided
        po_number = purchase_data.purchase_order_number
        if not po_number:
            po_number = await self.purchases_repository.generate_po_number()
        
        # Calculate totals
        totals = self.calculate_transaction_totals(purchase_data.transaction_lines)
        
        # Prepare purchase data
        purchase_dict = purchase_data.model_dump(exclude={'transaction_lines'})
        purchase_dict.update({
            'transaction_number': transaction_number,
            'purchase_order_number': po_number,
            'transaction_type': TransactionType.PURCHASE,
            **totals
        })
        
        # Create purchase
        purchase = await self.purchases_repository.create_purchase(purchase_dict)
        
        # Create purchase lines
        for line_data in purchase_data.transaction_lines:
            line_dict = line_data.model_dump()
            line_dict.update({
                'transaction_id': purchase.id,
                'line_total': (line_data.quantity * line_data.unit_price) - line_data.discount_amount + line_data.tax_amount
            })
            await self.purchase_line_repository.create_purchase_line(line_dict)
        
        # Refresh and return
        purchase = await self.purchases_repository.get_purchase_by_id(purchase.id)
        return PurchaseResponse.model_validate(purchase)
    
    async def get_purchase(self, purchase_id: UUID) -> Optional[PurchaseResponse]:
        """Get purchase by ID."""
        purchase = await self.purchases_repository.get_purchase_by_id(purchase_id)
        if not purchase:
            return None
        return PurchaseResponse.model_validate(purchase)
    
    async def get_purchase_by_po_number(self, po_number: str) -> Optional[PurchaseResponse]:
        """Get purchase by PO number."""
        purchase = await self.purchases_repository.get_purchase_by_po_number(po_number)
        if not purchase:
            return None
        return PurchaseResponse.model_validate(purchase)
    
    async def get_purchases(
        self,
        page: int = 1,
        page_size: int = 100,
        supplier_id: Optional[str] = None,
        location_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        approval_status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> PurchaseListResponse:
        """Get purchases with pagination and filters."""
        offset = (page - 1) * page_size
        
        purchases = await self.purchases_repository.get_by_type(
            transaction_type=TransactionType.PURCHASE,
            limit=page_size,
            offset=offset,
            customer_id=supplier_id,  # Using customer_id field for supplier
            location_id=location_id,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        total = await self.purchases_repository.count_by_type(
            transaction_type=TransactionType.PURCHASE,
            customer_id=supplier_id,
            location_id=location_id,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        purchase_responses = [PurchaseResponse.model_validate(purchase) for purchase in purchases]
        total_pages = (total + page_size - 1) // page_size
        
        return PurchaseListResponse(
            purchases=purchase_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_purchase(self, purchase_id: UUID, update_data: PurchaseUpdate) -> Optional[PurchaseResponse]:
        """Update purchase."""
        purchase = await self.purchases_repository.get_purchase_by_id(purchase_id)
        if not purchase:
            return None
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(purchase, field, value)
        
        await self.session.commit()
        
        # Return updated purchase
        return await self.get_purchase(purchase_id)
    
    async def delete_purchase(self, purchase_id: UUID) -> bool:
        """Delete purchase."""
        purchase = await self.purchases_repository.get_purchase_by_id(purchase_id)
        if not purchase:
            return False
        
        # Can only delete pending purchases
        if purchase.status != TransactionStatus.PENDING:
            raise ValueError("Can only delete pending purchases")
        
        await self.purchases_repository.delete(purchase_id)
        return True
    
    async def approve_purchase(self, purchase_id: UUID, approval_request: ApprovalRequest) -> Optional[PurchaseResponse]:
        """Approve purchase."""
        success = await self.purchases_repository.approve_purchase(
            purchase_id=purchase_id,
            approved_by=approval_request.approved_by,
            approved_date=approval_request.approval_date
        )
        
        if not success:
            return None
        
        return await self.get_purchase(purchase_id)
    
    async def update_receiving(
        self,
        purchase_id: UUID,
        receiving_update: ReceivingUpdateRequest
    ) -> Optional[PurchaseResponse]:
        """Update receiving information."""
        success = await self.purchases_repository.update_receiving_info(
            purchase_id=purchase_id,
            received_date=receiving_update.received_date
        )
        
        if not success:
            return None
        
        # Update line item received quantities
        for line_item in receiving_update.line_items:
            await self.purchase_line_repository.update_received_quantity(
                line_id=line_item["line_id"],
                received_quantity=line_item["received_quantity"]
            )
        
        return await self.get_purchase(purchase_id)
    
    async def update_inspection(
        self,
        purchase_id: UUID,
        inspection_request: InspectionRequest
    ) -> Optional[PurchaseResponse]:
        """Update inspection information."""
        success = await self.purchase_line_repository.update_inspection_status(
            line_id=inspection_request.line_id,
            inspection_status=inspection_request.inspection_status,
            quality_rating=inspection_request.quality_rating
        )
        
        if not success:
            return None
        
        return await self.get_purchase(purchase_id)
    
    async def get_supplier_purchases(
        self,
        supplier_id: str,
        page: int = 1,
        page_size: int = 100
    ) -> PurchaseListResponse:
        """Get purchases for a specific supplier."""
        offset = (page - 1) * page_size
        
        purchases = await self.purchases_repository.get_purchases_by_supplier(
            supplier_id=supplier_id,
            limit=page_size,
            offset=offset
        )
        
        total = len(purchases)  # Simplified for now
        purchase_responses = [PurchaseResponse.model_validate(purchase) for purchase in purchases]
        total_pages = (total + page_size - 1) // page_size
        
        return PurchaseListResponse(
            purchases=purchase_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def get_pending_approvals(self, limit: int = 100) -> List[PurchaseResponse]:
        """Get purchases pending approval."""
        purchases = await self.purchases_repository.get_pending_approvals(limit=limit)
        return [PurchaseResponse.model_validate(purchase) for purchase in purchases]
    
    async def get_pending_receipts(
        self,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[PurchaseResponse]:
        """Get purchases with pending receipts."""
        purchases = await self.purchases_repository.get_pending_receipts(
            location_id=location_id,
            limit=limit
        )
        return [PurchaseResponse.model_validate(purchase) for purchase in purchases]
    
    async def get_overdue_purchases(self, limit: int = 100) -> List[PurchaseResponse]:
        """Get overdue purchases."""
        purchases = await self.purchases_repository.get_overdue_purchases(limit=limit)
        return [PurchaseResponse.model_validate(purchase) for purchase in purchases]
    
    async def get_purchase_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        supplier_id: Optional[str] = None,
        location_id: Optional[str] = None,
        approval_status: Optional[str] = None
    ) -> PurchaseReportResponse:
        """Generate purchase report."""
        summary = await self.purchases_repository.get_purchase_summary(
            date_from=date_from,
            date_to=date_to,
            supplier_id=supplier_id
        )
        
        # Get detailed purchases for the report
        purchases = await self.purchases_repository.get_by_type(
            transaction_type=TransactionType.PURCHASE,
            customer_id=supplier_id,
            location_id=location_id,
            date_from=date_from,
            date_to=date_to,
            limit=1000  # Limit for performance
        )
        
        purchase_responses = [PurchaseResponse.model_validate(purchase) for purchase in purchases]
        
        # Calculate additional metrics
        total_received = sum(1 for purchase in purchase_responses if purchase.is_fully_received)
        total_pending_receipt = sum(1 for purchase in purchase_responses if purchase.has_pending_receipts)
        
        return PurchaseReportResponse(
            period_start=date_from,
            period_end=date_to,
            total_purchases=summary["total_purchases"],
            total_spending=summary["total_spending"],
            average_purchase_amount=summary["average_purchase"],
            total_tax_paid=summary["total_tax"],
            total_discounts_received=summary["total_discounts"],
            pending_purchases=summary["pending_purchases"],
            approved_purchases=summary["approved_purchases"],
            completed_purchases=summary["completed_purchases"],
            cancelled_purchases=summary["cancelled_purchases"],
            total_received=total_received,
            total_pending_receipt=total_pending_receipt,
            purchases=purchase_responses
        )
    
    async def get_purchase_order(self, purchase_id: UUID) -> Optional[PurchaseOrderResponse]:
        """Get purchase order information."""
        purchase = await self.purchases_repository.get_purchase_by_id(purchase_id)
        if not purchase:
            return None
        
        return PurchaseOrderResponse.model_validate(purchase)
    
    def validate_purchase_data(self, purchase_data: PurchaseCreate) -> List[str]:
        """Validate purchase data."""
        errors = []
        
        # Call base validation
        errors.extend(self.validate_transaction_data(purchase_data))
        
        # Purchase-specific validation
        if not purchase_data.supplier_id:
            errors.append("Supplier ID is required for purchases")
        
        # Validate line items
        for line in purchase_data.transaction_lines:
            if line.received_quantity > line.quantity:
                errors.append(f"Received quantity cannot exceed ordered quantity for line {line.line_number}")
            
            if line.pending_quantity > line.quantity:
                errors.append(f"Pending quantity cannot exceed ordered quantity for line {line.line_number}")
        
        return errors