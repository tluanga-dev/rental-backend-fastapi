"""
Purchase Repository

Data access layer for purchase operations.
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
from app.modules.purchases.models import Purchase, PurchaseLine


class PurchasesRepository(BaseTransactionRepository):
    """Repository for purchase operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def create_purchase(self, purchase_data: Dict[str, Any]) -> Purchase:
        """Create a new purchase."""
        purchase = Purchase(**purchase_data)
        purchase.transaction_type = TransactionType.PURCHASE
        
        self.session.add(purchase)
        await self.session.commit()
        await self.session.refresh(purchase)
        return purchase
    
    async def get_purchase_by_id(self, purchase_id: UUID) -> Optional[Purchase]:
        """Get purchase by ID with line items."""
        query = select(Purchase).where(
            Purchase.id == purchase_id
        ).options(
            selectinload(Purchase.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_purchase_by_po_number(self, po_number: str) -> Optional[Purchase]:
        """Get purchase by purchase order number."""
        query = select(Purchase).where(
            Purchase.purchase_order_number == po_number
        ).options(
            selectinload(Purchase.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_purchases_by_supplier(self, supplier_id: str, limit: int = 100, offset: int = 0) -> List[Purchase]:
        """Get purchases for a specific supplier."""
        query = select(Purchase).where(
            Purchase.supplier_id == supplier_id
        ).order_by(desc(Purchase.transaction_date))
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_approvals(self, limit: int = 100) -> List[Purchase]:
        """Get purchases pending approval."""
        query = select(Purchase).where(
            Purchase.approval_status == "PENDING"
        ).order_by(desc(Purchase.transaction_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_receipts(self, location_id: Optional[str] = None, limit: int = 100) -> List[Purchase]:
        """Get purchases with pending receipts."""
        query = select(Purchase).join(PurchaseLine).where(
            and_(
                Purchase.approval_status == "APPROVED",
                PurchaseLine.received_quantity < PurchaseLine.quantity
            )
        )
        
        if location_id:
            query = query.where(Purchase.location_id == location_id)
        
        query = query.order_by(desc(Purchase.transaction_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_overdue_purchases(self, limit: int = 100) -> List[Purchase]:
        """Get purchases that are overdue for receipt."""
        today = date.today()
        query = select(Purchase).where(
            and_(
                Purchase.expected_date < today,
                Purchase.received_date.is_(None),
                Purchase.approval_status == "APPROVED"
            )
        ).order_by(desc(Purchase.expected_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_purchase_summary(self, date_from: Optional[date] = None, date_to: Optional[date] = None, supplier_id: Optional[str] = None) -> Dict[str, Any]:
        """Get purchase summary statistics."""
        query = select(
            func.count(Purchase.id).label("total_purchases"),
            func.sum(Purchase.total_amount).label("total_spending"),
            func.sum(Purchase.paid_amount).label("total_paid"),
            func.sum(Purchase.tax_amount).label("total_tax"),
            func.sum(Purchase.discount_amount).label("total_discounts"),
            func.avg(Purchase.total_amount).label("average_purchase"),
            func.count(Purchase.id).filter(Purchase.approval_status == "PENDING").label("pending_purchases"),
            func.count(Purchase.id).filter(Purchase.approval_status == "APPROVED").label("approved_purchases"),
            func.count(Purchase.id).filter(Purchase.status == TransactionStatus.COMPLETED).label("completed_purchases"),
            func.count(Purchase.id).filter(Purchase.status == TransactionStatus.CANCELLED).label("cancelled_purchases")
        ).where(
            Purchase.transaction_type == TransactionType.PURCHASE
        )
        
        # Apply filters
        if date_from:
            query = query.where(Purchase.transaction_date >= date_from)
        if date_to:
            query = query.where(Purchase.transaction_date <= date_to)
        if supplier_id:
            query = query.where(Purchase.supplier_id == supplier_id)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        return {
            "total_purchases": row.total_purchases or 0,
            "total_spending": row.total_spending or Decimal("0"),
            "total_paid": row.total_paid or Decimal("0"),
            "total_tax": row.total_tax or Decimal("0"),
            "total_discounts": row.total_discounts or Decimal("0"),
            "average_purchase": row.average_purchase or Decimal("0"),
            "pending_purchases": row.pending_purchases or 0,
            "approved_purchases": row.approved_purchases or 0,
            "completed_purchases": row.completed_purchases or 0,
            "cancelled_purchases": row.cancelled_purchases or 0,
            "outstanding_amount": (row.total_spending or Decimal("0")) - (row.total_paid or Decimal("0"))
        }
    
    async def approve_purchase(self, purchase_id: UUID, approved_by: str, approved_date: date) -> bool:
        """Approve a purchase."""
        purchase = await self.get_purchase_by_id(purchase_id)
        if not purchase:
            return False
        
        purchase.approval_status = "APPROVED"
        purchase.approved_by = approved_by
        purchase.approved_date = approved_date
        
        await self.session.commit()
        return True
    
    async def update_receiving_info(self, purchase_id: UUID, received_date: date) -> bool:
        """Update receiving information for a purchase."""
        purchase = await self.get_purchase_by_id(purchase_id)
        if not purchase:
            return False
        
        purchase.received_date = received_date
        await self.session.commit()
        return True
    
    async def generate_po_number(self) -> str:
        """Generate next purchase order number."""
        query = select(func.max(Purchase.purchase_order_number)).where(
            Purchase.purchase_order_number.like("PO-%")
        )
        result = await self.session.execute(query)
        max_po = result.scalar()
        
        if max_po:
            # Extract number from format PO-000001
            try:
                number = int(max_po.split("-")[1]) + 1
            except (IndexError, ValueError):
                number = 1
        else:
            number = 1
        
        return f"PO-{number:06d}"


class PurchaseLineRepository(BaseTransactionLineRepository):
    """Repository for purchase line operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def create_purchase_line(self, line_data: Dict[str, Any]) -> PurchaseLine:
        """Create a new purchase line."""
        line = PurchaseLine(**line_data)
        self.session.add(line)
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def get_purchase_lines(self, purchase_id: UUID) -> List[PurchaseLine]:
        """Get all line items for a purchase."""
        query = select(PurchaseLine).where(
            PurchaseLine.transaction_id == purchase_id
        ).order_by(PurchaseLine.line_number)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_received_quantity(self, line_id: UUID, received_quantity: Decimal) -> bool:
        """Update received quantity for a line item."""
        line = await self.get_by_id(line_id)
        if not line:
            return False
        
        line.received_quantity = received_quantity
        await self.session.commit()
        return True
    
    async def update_inspection_status(self, line_id: UUID, inspection_status: str, quality_rating: Optional[str] = None) -> bool:
        """Update inspection status for a line item."""
        line = await self.get_by_id(line_id)
        if not line:
            return False
        
        line.inspection_status = inspection_status
        if quality_rating:
            line.quality_rating = quality_rating
        
        await self.session.commit()
        return True
    
    async def get_items_to_receive(self, location_id: Optional[str] = None, limit: int = 100) -> List[PurchaseLine]:
        """Get line items that need to be received."""
        query = select(PurchaseLine).join(Purchase).where(
            and_(
                Purchase.approval_status == "APPROVED",
                PurchaseLine.received_quantity < PurchaseLine.quantity
            )
        )
        
        if location_id:
            query = query.where(Purchase.location_id == location_id)
        
        query = query.order_by(desc(Purchase.transaction_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_inspection_required_items(self, limit: int = 100) -> List[PurchaseLine]:
        """Get line items that require inspection."""
        query = select(PurchaseLine).join(Purchase).where(
            and_(
                PurchaseLine.inspection_required == True,
                PurchaseLine.inspection_status.in_(["PENDING", None])
            )
        )
        
        query = query.order_by(desc(Purchase.transaction_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()