"""
Sales Services

Business logic for sales operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transaction_base.services import BaseTransactionService
from app.modules.transaction_base.models import TransactionType, TransactionStatus
from app.modules.sales.repository import SalesRepository, SaleLineRepository
from app.modules.sales.schemas import (
    SaleCreate,
    SaleUpdate,
    SaleResponse,
    SaleListResponse,
    SalesReportResponse,
    SaleInvoiceResponse,
    ShippingUpdateRequest,
    BackorderRequest,
    SaleLineUpdate,
    SaleLineResponse,
)


class SalesService(BaseTransactionService):
    """Service for sales operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.sales_repository = SalesRepository(session)
        self.sale_line_repository = SaleLineRepository(session)
    
    async def create_sale(self, sale_data: SaleCreate) -> SaleResponse:
        """Create a new sale."""
        # Validate sale data
        errors = self.validate_sale_data(sale_data)
        if errors:
            raise ValueError(f"Invalid sale data: {', '.join(errors)}")
        
        # Generate transaction number if not provided
        if not hasattr(sale_data, 'transaction_number') or not sale_data.transaction_number:
            transaction_number = self.generate_transaction_number(TransactionType.SALE)
        else:
            transaction_number = sale_data.transaction_number
        
        # Generate invoice number if not provided
        invoice_number = sale_data.invoice_number
        if not invoice_number:
            invoice_number = await self.sales_repository.generate_invoice_number()
        
        # Calculate totals
        totals = self.calculate_transaction_totals(sale_data.transaction_lines)
        
        # Prepare sale data
        sale_dict = sale_data.model_dump(exclude={'transaction_lines'})
        sale_dict.update({
            'transaction_number': transaction_number,
            'invoice_number': invoice_number,
            'transaction_type': TransactionType.SALE,
            **totals
        })
        
        # Create sale
        sale = await self.sales_repository.create_sale(sale_dict)
        
        # Create sale lines
        for line_data in sale_data.transaction_lines:
            line_dict = line_data.model_dump()
            line_dict.update({
                'transaction_id': sale.id,
                'line_total': (line_data.quantity * line_data.unit_price) - line_data.discount_amount + line_data.tax_amount
            })
            await self.sale_line_repository.create_sale_line(line_dict)
        
        # Refresh and return
        sale = await self.sales_repository.get_sale_by_id(sale.id)
        return SaleResponse.model_validate(sale)
    
    async def get_sale(self, sale_id: UUID) -> Optional[SaleResponse]:
        """Get sale by ID."""
        sale = await self.sales_repository.get_sale_by_id(sale_id)
        if not sale:
            return None
        return SaleResponse.model_validate(sale)
    
    async def get_sale_by_invoice_number(self, invoice_number: str) -> Optional[SaleResponse]:
        """Get sale by invoice number."""
        sale = await self.sales_repository.get_sale_by_invoice_number(invoice_number)
        if not sale:
            return None
        return SaleResponse.model_validate(sale)
    
    async def get_sales(
        self,
        page: int = 1,
        page_size: int = 100,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        sales_person_id: Optional[UUID] = None,
        status: Optional[TransactionStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> SaleListResponse:
        """Get sales with pagination and filters."""
        offset = (page - 1) * page_size
        
        sales = await self.sales_repository.get_by_type(
            transaction_type=TransactionType.SALE,
            limit=page_size,
            offset=offset,
            customer_id=customer_id,
            location_id=location_id,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        total = await self.sales_repository.count_by_type(
            transaction_type=TransactionType.SALE,
            customer_id=customer_id,
            location_id=location_id,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        sale_responses = [SaleResponse.model_validate(sale) for sale in sales]
        total_pages = (total + page_size - 1) // page_size
        
        return SaleListResponse(
            sales=sale_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_sale(self, sale_id: UUID, update_data: SaleUpdate) -> Optional[SaleResponse]:
        """Update sale."""
        sale = await self.sales_repository.get_sale_by_id(sale_id)
        if not sale:
            return None
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(sale, field, value)
        
        await self.session.commit()
        
        # Return updated sale
        return await self.get_sale(sale_id)
    
    async def delete_sale(self, sale_id: UUID) -> bool:
        """Delete sale."""
        sale = await self.sales_repository.get_sale_by_id(sale_id)
        if not sale:
            return False
        
        # Can only delete pending sales
        if sale.status != TransactionStatus.PENDING:
            raise ValueError("Can only delete pending sales")
        
        await self.sales_repository.delete(sale_id)
        return True
    
    async def complete_sale(self, sale_id: UUID) -> Optional[SaleResponse]:
        """Mark sale as completed."""
        sale = await self.sales_repository.get_sale_by_id(sale_id)
        if not sale:
            return None
        
        sale.status = TransactionStatus.COMPLETED
        await self.session.commit()
        
        return await self.get_sale(sale_id)
    
    async def cancel_sale(self, sale_id: UUID, reason: Optional[str] = None) -> Optional[SaleResponse]:
        """Cancel sale."""
        sale = await self.sales_repository.get_sale_by_id(sale_id)
        if not sale:
            return None
        
        sale.status = TransactionStatus.CANCELLED
        if reason:
            sale.notes = f"{sale.notes or ''}\nCancelled: {reason}".strip()
        
        await self.session.commit()
        
        return await self.get_sale(sale_id)
    
    async def update_shipping(
        self,
        sale_id: UUID,
        shipping_update: ShippingUpdateRequest
    ) -> Optional[SaleResponse]:
        """Update shipping information."""
        success = await self.sales_repository.update_shipping_info(
            sale_id=sale_id,
            shipped_date=shipping_update.shipped_date,
            tracking_number=shipping_update.tracking_number,
            carrier=shipping_update.carrier
        )
        
        if not success:
            return None
        
        # Update line item shipping quantities
        for line_item in shipping_update.line_items:
            await self.sale_line_repository.update_shipping_quantity(
                line_id=line_item["line_id"],
                shipped_quantity=line_item["shipped_quantity"]
            )
        
        return await self.get_sale(sale_id)
    
    async def create_backorder(
        self,
        sale_id: UUID,
        backorder_request: BackorderRequest
    ) -> Optional[SaleResponse]:
        """Create backorder for a line item."""
        success = await self.sale_line_repository.update_backorder_quantity(
            line_id=backorder_request.line_id,
            backorder_quantity=backorder_request.backorder_quantity
        )
        
        if not success:
            return None
        
        return await self.get_sale(sale_id)
    
    async def get_customer_sales(
        self,
        customer_id: str,
        page: int = 1,
        page_size: int = 100,
        status: Optional[TransactionStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> SaleListResponse:
        """Get sales for a specific customer."""
        offset = (page - 1) * page_size
        
        sales = await self.sales_repository.get_sales_by_customer(
            customer_id=customer_id,
            limit=page_size,
            offset=offset,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        total = len(sales)  # Simplified for now
        sale_responses = [SaleResponse.model_validate(sale) for sale in sales]
        total_pages = (total + page_size - 1) // page_size
        
        return SaleListResponse(
            sales=sale_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def get_pending_shipments(
        self,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SaleResponse]:
        """Get sales with pending shipments."""
        sales = await self.sales_repository.get_pending_shipments(
            location_id=location_id,
            limit=limit
        )
        
        return [SaleResponse.model_validate(sale) for sale in sales]
    
    async def get_backorders(
        self,
        customer_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SaleResponse]:
        """Get sales with backorders."""
        sales = await self.sales_repository.get_backorders(
            customer_id=customer_id,
            limit=limit
        )
        
        return [SaleResponse.model_validate(sale) for sale in sales]
    
    async def get_sales_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        sales_person_id: Optional[UUID] = None
    ) -> SalesReportResponse:
        """Generate sales report."""
        summary = await self.sales_repository.get_sales_summary(
            date_from=date_from,
            date_to=date_to,
            customer_id=customer_id,
            location_id=location_id,
            sales_person_id=sales_person_id
        )
        
        # Get detailed sales for the report
        sales = await self.sales_repository.get_by_type(
            transaction_type=TransactionType.SALE,
            customer_id=customer_id,
            location_id=location_id,
            date_from=date_from,
            date_to=date_to,
            limit=1000  # Limit for performance
        )
        
        sale_responses = [SaleResponse.model_validate(sale) for sale in sales]
        
        # Calculate additional metrics
        total_shipped = sum(1 for sale in sale_responses if sale.is_fully_shipped)
        total_backorders = sum(1 for sale in sale_responses if sale.has_backorders)
        
        return SalesReportResponse(
            period_start=date_from,
            period_end=date_to,
            total_sales=summary["total_sales"],
            total_revenue=summary["total_revenue"],
            total_cost=Decimal("0"),  # Would need cost calculation
            gross_profit=summary["total_revenue"],  # Simplified
            average_sale_amount=summary["average_sale"],
            total_tax_collected=summary["total_tax"],
            total_discounts_given=summary["total_discounts"],
            pending_sales=summary["pending_sales"],
            completed_sales=summary["completed_sales"],
            cancelled_sales=summary["cancelled_sales"],
            total_shipped=total_shipped,
            total_backorders=total_backorders,
            sales=sale_responses
        )
    
    async def get_invoice(self, sale_id: UUID) -> Optional[SaleInvoiceResponse]:
        """Get invoice information for a sale."""
        sale = await self.sales_repository.get_sale_by_id(sale_id)
        if not sale:
            return None
        
        return SaleInvoiceResponse.model_validate(sale)
    
    def validate_sale_data(self, sale_data: SaleCreate) -> List[str]:
        """Validate sale data."""
        errors = []
        
        # Call base validation
        errors.extend(self.validate_transaction_data(sale_data))
        
        # Sales-specific validation
        if sale_data.customer_id is None:
            errors.append("Customer ID is required for sales")
        
        if sale_data.sales_rep_commission and sale_data.sales_rep_commission > 100:
            errors.append("Sales rep commission cannot exceed 100%")
        
        if sale_data.customer_discount_percent and sale_data.customer_discount_percent > 100:
            errors.append("Customer discount cannot exceed 100%")
        
        # Validate line items
        for line in sale_data.transaction_lines:
            if line.shipped_quantity > line.quantity:
                errors.append(f"Shipped quantity cannot exceed ordered quantity for line {line.line_number}")
            
            if line.backorder_quantity > line.quantity:
                errors.append(f"Backorder quantity cannot exceed ordered quantity for line {line.line_number}")
        
        return errors