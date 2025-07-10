from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from .models import Supplier, SupplierType, SupplierTier, SupplierStatus, PaymentTerms
from app.shared.repository import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    """Repository for supplier operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Supplier, session)
    
    async def get_by_code(self, supplier_code: str) -> Optional[Supplier]:
        """Get supplier by code."""
        query = select(Supplier).where(Supplier.supplier_code == supplier_code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[Supplier]:
        """Get supplier by email."""
        query = select(Supplier).where(Supplier.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_type: Optional[SupplierType] = None,
        status: Optional[SupplierStatus] = None,
        supplier_tier: Optional[SupplierTier] = None,
        payment_terms: Optional[PaymentTerms] = None,
        country: Optional[str] = None,
        active_only: bool = True,
        sort_by: str = "company_name",
        sort_order: str = "asc"
    ) -> List[Supplier]:
        """Get all suppliers with filtering and sorting."""
        query = select(Supplier)
        
        # Apply filters
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        if supplier_type:
            query = query.where(Supplier.supplier_type == supplier_type.value)
        
        if status:
            query = query.where(Supplier.status == status.value)
        
        if supplier_tier:
            query = query.where(Supplier.supplier_tier == supplier_tier.value)
        
        if payment_terms:
            query = query.where(Supplier.payment_terms == payment_terms.value)
        
        if country:
            query = query.where(Supplier.country.ilike(f"%{country}%"))
        
        # Apply sorting
        if hasattr(Supplier, sort_by):
            sort_column = getattr(Supplier, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(asc(Supplier.company_name))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        supplier_type: Optional[SupplierType] = None,
        status: Optional[SupplierStatus] = None,
        active_only: bool = True
    ) -> List[Supplier]:
        """Search suppliers by name, code, or email."""
        query = select(Supplier)
        
        # Search conditions
        search_conditions = [
            Supplier.company_name.ilike(f"%{search_term}%"),
            Supplier.supplier_code.ilike(f"%{search_term}%"),
            Supplier.email.ilike(f"%{search_term}%"),
            Supplier.contact_person.ilike(f"%{search_term}%")
        ]
        
        query = query.where(or_(*search_conditions))
        
        # Apply filters
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        if supplier_type:
            query = query.where(Supplier.supplier_type == supplier_type.value)
        
        if status:
            query = query.where(Supplier.status == status.value)
        
        # Order by relevance (exact matches first)
        query = query.order_by(
            func.case(
                (Supplier.supplier_code.ilike(search_term), 1),
                (Supplier.company_name.ilike(search_term), 2),
                (Supplier.email.ilike(search_term), 3),
                else_=4
            ),
            Supplier.company_name
        )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_all(
        self,
        supplier_type: Optional[SupplierType] = None,
        status: Optional[SupplierStatus] = None,
        supplier_tier: Optional[SupplierTier] = None,
        payment_terms: Optional[PaymentTerms] = None,
        country: Optional[str] = None,
        active_only: bool = True
    ) -> int:
        """Count suppliers with filtering."""
        query = select(func.count(Supplier.id))
        
        # Apply filters
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        if supplier_type:
            query = query.where(Supplier.supplier_type == supplier_type.value)
        
        if status:
            query = query.where(Supplier.status == status.value)
        
        if supplier_tier:
            query = query.where(Supplier.supplier_tier == supplier_tier.value)
        
        if payment_terms:
            query = query.where(Supplier.payment_terms == payment_terms.value)
        
        if country:
            query = query.where(Supplier.country.ilike(f"%{country}%"))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def get_suppliers_by_type(
        self,
        supplier_type: SupplierType,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get suppliers by type."""
        query = select(Supplier).where(Supplier.supplier_type == supplier_type.value)
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(Supplier.company_name)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_suppliers_by_status(
        self,
        status: SupplierStatus,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get suppliers by status."""
        query = select(Supplier).where(Supplier.status == status.value)
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(Supplier.company_name)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_suppliers_by_tier(
        self,
        supplier_tier: SupplierTier,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get suppliers by tier."""
        query = select(Supplier).where(Supplier.supplier_tier == supplier_tier.value)
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(Supplier.company_name)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_suppliers_by_country(
        self,
        country: str,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get suppliers by country."""
        query = select(Supplier).where(Supplier.country.ilike(f"%{country}%"))
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(Supplier.company_name)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_top_suppliers_by_orders(
        self,
        limit: int = 10,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get top suppliers by total orders."""
        query = select(Supplier).where(Supplier.total_orders > 0)
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(desc(Supplier.total_orders)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_top_suppliers_by_spend(
        self,
        limit: int = 10,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get top suppliers by total spend."""
        query = select(Supplier).where(Supplier.total_spend > 0)
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(desc(Supplier.total_spend)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_suppliers_with_expiring_contracts(
        self,
        days: int = 30,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get suppliers with contracts expiring within specified days."""
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        query = select(Supplier).where(
            and_(
                Supplier.contract_end_date.isnot(None),
                Supplier.contract_end_date <= cutoff_date,
                Supplier.contract_end_date >= datetime.utcnow()
            )
        )
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(Supplier.contract_end_date)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_suppliers_with_expiring_insurance(
        self,
        days: int = 30,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get suppliers with insurance expiring within specified days."""
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        query = select(Supplier).where(
            and_(
                Supplier.insurance_expiry.isnot(None),
                Supplier.insurance_expiry <= cutoff_date,
                Supplier.insurance_expiry >= datetime.utcnow()
            )
        )
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(Supplier.insurance_expiry)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get supplier statistics."""
        # Basic counts
        total_count = await self.session.execute(select(func.count(Supplier.id)))
        active_count = await self.session.execute(
            select(func.count(Supplier.id)).where(Supplier.is_active == True)
        )
        
        # Count by type
        type_counts = await self.session.execute(
            select(Supplier.supplier_type, func.count(Supplier.id))
            .where(Supplier.is_active == True)
            .group_by(Supplier.supplier_type)
        )
        
        # Count by status
        status_counts = await self.session.execute(
            select(Supplier.status, func.count(Supplier.id))
            .where(Supplier.is_active == True)
            .group_by(Supplier.status)
        )
        
        # Count by tier
        tier_counts = await self.session.execute(
            select(Supplier.supplier_tier, func.count(Supplier.id))
            .where(Supplier.is_active == True)
            .group_by(Supplier.supplier_tier)
        )
        
        # Count by country
        country_counts = await self.session.execute(
            select(Supplier.country, func.count(Supplier.id))
            .where(and_(Supplier.is_active == True, Supplier.country.isnot(None)))
            .group_by(Supplier.country)
            .order_by(desc(func.count(Supplier.id)))
            .limit(10)
        )
        
        # Average ratings
        avg_ratings = await self.session.execute(
            select(
                func.avg(Supplier.quality_rating),
                func.avg(Supplier.delivery_rating)
            )
            .where(Supplier.is_active == True)
        )
        
        return {
            "total_suppliers": total_count.scalar(),
            "active_suppliers": active_count.scalar(),
            "suppliers_by_type": dict(type_counts.fetchall()),
            "suppliers_by_status": dict(status_counts.fetchall()),
            "suppliers_by_tier": dict(tier_counts.fetchall()),
            "suppliers_by_country": dict(country_counts.fetchall()),
            "average_ratings": avg_ratings.fetchone()
        }
    
    async def get_recent_suppliers(
        self,
        limit: int = 10,
        active_only: bool = True
    ) -> List[Supplier]:
        """Get recently created suppliers."""
        query = select(Supplier)
        
        if active_only:
            query = query.where(Supplier.is_active == True)
        
        query = query.order_by(desc(Supplier.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def bulk_update_status(
        self,
        supplier_ids: List[UUID],
        status: SupplierStatus,
        updated_by: Optional[str] = None
    ) -> int:
        """Bulk update supplier status."""
        from sqlalchemy import update
        
        query = update(Supplier).where(
            Supplier.id.in_(supplier_ids)
        ).values(
            status=status.value,
            updated_by=updated_by,
            updated_at=datetime.utcnow()
        )
        
        result = await self.session.execute(query)
        return result.rowcount
    
    async def bulk_update_tier(
        self,
        supplier_ids: List[UUID],
        supplier_tier: SupplierTier,
        updated_by: Optional[str] = None
    ) -> int:
        """Bulk update supplier tier."""
        from sqlalchemy import update
        
        query = update(Supplier).where(
            Supplier.id.in_(supplier_ids)
        ).values(
            supplier_tier=supplier_tier.value,
            updated_by=updated_by,
            updated_at=datetime.utcnow()
        )
        
        result = await self.session.execute(query)
        return result.rowcount
    
    async def exists_by_code(self, supplier_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if supplier exists by code."""
        query = select(func.count(Supplier.id)).where(Supplier.supplier_code == supplier_code)
        
        if exclude_id:
            query = query.where(Supplier.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar() > 0
    
    async def exists_by_email(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if supplier exists by email."""
        query = select(func.count(Supplier.id)).where(Supplier.email == email)
        
        if exclude_id:
            query = query.where(Supplier.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar() > 0