"""
Sales Repository

Data access layer for sales operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.modules.transaction_base.repository import BaseTransactionRepository, BaseTransactionLineRepository
from app.modules.transaction_base.models import TransactionHeader, TransactionLine, TransactionType, TransactionStatus
from app.modules.sales.models import Sale, SaleLine


class SalesRepository(BaseTransactionRepository):
    """Repository for sales operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def create_sale(self, sale_data: Dict[str, Any]) -> Sale:
        """Create a new sale."""
        sale = Sale(**sale_data)
        sale.transaction_type = TransactionType.SALE
        
        self.session.add(sale)
        await self.session.commit()
        await self.session.refresh(sale)
        return sale
    
    async def get_sale_by_id(self, sale_id: UUID) -> Optional[Sale]:
        """Get sale by ID with line items."""
        query = select(Sale).where(
            Sale.id == sale_id
        ).options(
            selectinload(Sale.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_sale_by_invoice_number(self, invoice_number: str) -> Optional[Sale]:
        """Get sale by invoice number."""
        query = select(Sale).where(
            Sale.invoice_number == invoice_number
        ).options(
            selectinload(Sale.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_sales_by_customer(
        self,
        customer_id: str,
        limit: int = 100,
        offset: int = 0,
        status: Optional[TransactionStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[Sale]:
        """Get sales for a specific customer."""
        query = select(Sale).where(
            Sale.customer_id == customer_id
        )
        
        if status:
            query = query.where(Sale.status == status)
        if date_from:
            query = query.where(Sale.transaction_date >= date_from)
        if date_to:
            query = query.where(Sale.transaction_date <= date_to)
        
        query = query.order_by(desc(Sale.transaction_date))
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_sales_by_salesperson(
        self,
        sales_person_id: UUID,
        limit: int = 100,
        offset: int = 0,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[Sale]:
        """Get sales for a specific salesperson."""
        query = select(Sale).where(
            Sale.sales_person_id == sales_person_id
        )
        
        if date_from:
            query = query.where(Sale.transaction_date >= date_from)
        if date_to:
            query = query.where(Sale.transaction_date <= date_to)
        
        query = query.order_by(desc(Sale.transaction_date))
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_shipments(
        self,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Sale]:
        """Get sales with pending shipments."""
        query = select(Sale).join(SaleLine).where(
            and_(
                Sale.status == TransactionStatus.COMPLETED,
                SaleLine.shipped_quantity < SaleLine.quantity
            )
        )
        
        if location_id:
            query = query.where(Sale.location_id == location_id)
        
        query = query.order_by(desc(Sale.transaction_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_backorders(
        self,
        customer_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Sale]:
        """Get sales with backorders."""
        query = select(Sale).join(SaleLine).where(
            SaleLine.backorder_quantity > 0
        )
        
        if customer_id:
            query = query.where(Sale.customer_id == customer_id)
        
        query = query.order_by(desc(Sale.transaction_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_sales_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        sales_person_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get sales summary statistics."""
        query = select(
            func.count(Sale.id).label("total_sales"),
            func.sum(Sale.total_amount).label("total_revenue"),
            func.sum(Sale.paid_amount).label("total_paid"),
            func.sum(Sale.tax_amount).label("total_tax"),
            func.sum(Sale.discount_amount).label("total_discounts"),
            func.avg(Sale.total_amount).label("average_sale"),
            func.count(Sale.id).filter(Sale.status == TransactionStatus.PENDING).label("pending_sales"),
            func.count(Sale.id).filter(Sale.status == TransactionStatus.COMPLETED).label("completed_sales"),
            func.count(Sale.id).filter(Sale.status == TransactionStatus.CANCELLED).label("cancelled_sales")
        ).where(
            Sale.transaction_type == TransactionType.SALE
        )
        
        # Apply filters
        if date_from:
            query = query.where(Sale.transaction_date >= date_from)
        if date_to:
            query = query.where(Sale.transaction_date <= date_to)
        if customer_id:
            query = query.where(Sale.customer_id == customer_id)
        if location_id:
            query = query.where(Sale.location_id == location_id)
        if sales_person_id:
            query = query.where(Sale.sales_person_id == sales_person_id)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        return {
            "total_sales": row.total_sales or 0,
            "total_revenue": row.total_revenue or Decimal("0"),
            "total_paid": row.total_paid or Decimal("0"),
            "total_tax": row.total_tax or Decimal("0"),
            "total_discounts": row.total_discounts or Decimal("0"),
            "average_sale": row.average_sale or Decimal("0"),
            "pending_sales": row.pending_sales or 0,
            "completed_sales": row.completed_sales or 0,
            "cancelled_sales": row.cancelled_sales or 0,
            "outstanding_amount": (row.total_revenue or Decimal("0")) - (row.total_paid or Decimal("0"))
        }
    
    async def update_shipping_info(
        self,
        sale_id: UUID,
        shipped_date: date,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None
    ) -> bool:
        """Update shipping information for a sale."""
        sale = await self.get_sale_by_id(sale_id)
        if not sale:
            return False
        
        sale.shipped_date = shipped_date
        if tracking_number:
            sale.tracking_number = tracking_number
        if carrier:
            sale.carrier = carrier
        
        await self.session.commit()
        return True
    
    async def generate_invoice_number(self) -> str:
        """Generate next invoice number."""
        query = select(func.max(Sale.invoice_number)).where(
            Sale.invoice_number.like("INV-%")
        )
        result = await self.session.execute(query)
        max_invoice = result.scalar()
        
        if max_invoice:
            # Extract number from format INV-000001
            try:
                number = int(max_invoice.split("-")[1]) + 1
            except (IndexError, ValueError):
                number = 1
        else:
            number = 1
        
        return f"INV-{number:06d}"


class SaleLineRepository(BaseTransactionLineRepository):
    """Repository for sale line operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def create_sale_line(self, line_data: Dict[str, Any]) -> SaleLine:
        """Create a new sale line."""
        line = SaleLine(**line_data)
        self.session.add(line)
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def get_sale_lines(self, sale_id: UUID) -> List[SaleLine]:
        """Get all line items for a sale."""
        query = select(SaleLine).where(
            SaleLine.transaction_id == sale_id
        ).order_by(SaleLine.line_number)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_shipping_quantity(
        self,
        line_id: UUID,
        shipped_quantity: Decimal
    ) -> bool:
        """Update shipped quantity for a line item."""
        line = await self.get_by_id(line_id)
        if not line:
            return False
        
        line.shipped_quantity = shipped_quantity
        await self.session.commit()
        return True
    
    async def update_backorder_quantity(
        self,
        line_id: UUID,
        backorder_quantity: Decimal
    ) -> bool:
        """Update backorder quantity for a line item."""
        line = await self.get_by_id(line_id)
        if not line:
            return False
        
        line.backorder_quantity = backorder_quantity
        await self.session.commit()
        return True
    
    async def get_items_to_ship(
        self,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SaleLine]:
        """Get line items that need to be shipped."""
        query = select(SaleLine).join(Sale).where(
            and_(
                Sale.status == TransactionStatus.COMPLETED,
                SaleLine.shipped_quantity < SaleLine.quantity
            )
        )
        
        if location_id:
            query = query.where(Sale.location_id == location_id)
        
        query = query.order_by(desc(Sale.transaction_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_backorder_items(
        self,
        customer_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SaleLine]:
        """Get line items on backorder."""
        query = select(SaleLine).join(Sale).where(
            SaleLine.backorder_quantity > 0
        )
        
        if customer_id:
            query = query.where(Sale.customer_id == customer_id)
        
        query = query.order_by(desc(Sale.transaction_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()