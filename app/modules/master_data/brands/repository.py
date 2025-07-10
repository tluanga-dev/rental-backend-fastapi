from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Brand
# from app.shared.pagination import Page


class BrandRepository:
    """Repository for brand data access operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, brand_data: dict) -> Brand:
        """Create a new brand."""
        brand = Brand(**brand_data)
        self.session.add(brand)
        await self.session.commit()
        await self.session.refresh(brand)
        return brand
    
    async def get_by_id(self, brand_id: UUID) -> Optional[Brand]:
        """Get brand by ID."""
        query = select(Brand).where(Brand.id == brand_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Brand]:
        """Get brand by name."""
        query = select(Brand).where(Brand.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> Optional[Brand]:
        """Get brand by code."""
        query = select(Brand).where(Brand.code == code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        include_inactive: bool = False
    ) -> List[Brand]:
        """List brands with optional filters and sorting."""
        query = select(Brand)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Brand.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(Brand, sort_by)))
        else:
            query = query.order_by(asc(getattr(Brand, sort_by)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        include_inactive: bool = False
    ) -> List[Brand]:
        """Get paginated brands."""
        query = select(Brand)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Brand.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(Brand, sort_by)))
        else:
            query = query.order_by(asc(getattr(Brand, sort_by)))
        
        # Calculate pagination
        skip = (page - 1) * page_size
        limit = page_size
        
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update(self, brand_id: UUID, update_data: dict) -> Optional[Brand]:
        """Update existing brand."""
        brand = await self.get_by_id(brand_id)
        if not brand:
            return None
        
        # Update fields using the model's update method
        brand.update_info(**update_data)
        
        await self.session.commit()
        await self.session.refresh(brand)
        
        return brand
    
    async def delete(self, brand_id: UUID) -> bool:
        """Soft delete brand by setting is_active to False."""
        brand = await self.get_by_id(brand_id)
        if not brand:
            return False
        
        brand.is_active = False
        await self.session.commit()
        
        return True
    
    async def hard_delete(self, brand_id: UUID) -> bool:
        """Hard delete brand from database."""
        brand = await self.get_by_id(brand_id)
        if not brand:
            return False
        
        # Check if brand can be deleted
        if not brand.can_delete():
            return False
        
        await self.session.delete(brand)
        await self.session.commit()
        
        return True
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_inactive: bool = False
    ) -> int:
        """Count brands matching filters."""
        query = select(func.count()).select_from(Brand)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Brand.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a brand with the given name exists."""
        query = select(func.count()).select_from(Brand).where(
            Brand.name == name
        )
        
        if exclude_id:
            query = query.where(Brand.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_code(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a brand with the given code exists."""
        query = select(func.count()).select_from(Brand).where(
            Brand.code == code
        )
        
        if exclude_id:
            query = query.where(Brand.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def search(
        self,
        search_term: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[Brand]:
        """Search brands by name, code, or description."""
        search_pattern = f"%{search_term}%"
        
        query = select(Brand).where(
            or_(
                Brand.name.ilike(search_pattern),
                Brand.code.ilike(search_pattern),
                Brand.description.ilike(search_pattern)
            )
        )
        
        if not include_inactive:
            query = query.where(Brand.is_active == True)
        
        query = query.order_by(Brand.name).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_active_brands(self) -> List[Brand]:
        """Get all active brands."""
        query = select(Brand).where(Brand.is_active == True).order_by(Brand.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_inactive_brands(self) -> List[Brand]:
        """Get all inactive brands."""
        query = select(Brand).where(Brand.is_active == False).order_by(Brand.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_brands_with_items(self) -> List[Brand]:
        """Get brands that have associated items."""
        query = select(Brand).options(selectinload(Brand.items)).where(
            Brand.items.any()
        ).order_by(Brand.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_brands_without_items(self) -> List[Brand]:
        """Get brands that have no associated items."""
        query = select(Brand).where(
            ~Brand.items.any()
        ).order_by(Brand.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def bulk_activate(self, brand_ids: List[UUID]) -> int:
        """Activate multiple brands."""
        query = select(Brand).where(Brand.id.in_(brand_ids))
        result = await self.session.execute(query)
        brands = result.scalars().all()
        
        count = 0
        for brand in brands:
            if not brand.is_active:
                brand.is_active = True
                count += 1
        
        await self.session.commit()
        return count
    
    async def bulk_deactivate(self, brand_ids: List[UUID]) -> int:
        """Deactivate multiple brands."""
        query = select(Brand).where(Brand.id.in_(brand_ids))
        result = await self.session.execute(query)
        brands = result.scalars().all()
        
        count = 0
        for brand in brands:
            if brand.is_active:
                brand.is_active = False
                count += 1
        
        await self.session.commit()
        return count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get brand statistics."""
        # Count all brands
        total_query = select(func.count()).select_from(Brand)
        total_result = await self.session.execute(total_query)
        total_brands = total_result.scalar_one()
        
        # Count active brands
        active_query = select(func.count()).select_from(Brand).where(Brand.is_active == True)
        active_result = await self.session.execute(active_query)
        active_brands = active_result.scalar_one()
        
        # Count brands with items (when items relationship is available)
        with_items_query = select(func.count()).select_from(Brand).where(
            Brand.items.any()
        )
        try:
            with_items_result = await self.session.execute(with_items_query)
            brands_with_items = with_items_result.scalar_one()
        except:
            # If items relationship is not available yet, set to 0
            brands_with_items = 0
        
        return {
            "total_brands": total_brands,
            "active_brands": active_brands,
            "inactive_brands": total_brands - active_brands,
            "brands_with_items": brands_with_items,
            "brands_without_items": total_brands - brands_with_items
        }
    
    async def get_most_used_brands(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get brands with most items."""
        # This will be implemented when items relationship is fully available
        # For now, return empty list
        return []
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        for key, value in filters.items():
            if value is None:
                continue
            
            if key == "name":
                query = query.where(Brand.name.ilike(f"%{value}%"))
            elif key == "code":
                query = query.where(Brand.code.ilike(f"%{value}%"))
            elif key == "description":
                query = query.where(Brand.description.ilike(f"%{value}%"))
            elif key == "is_active":
                query = query.where(Brand.is_active == value)
            elif key == "search":
                search_pattern = f"%{value}%"
                query = query.where(
                    or_(
                        Brand.name.ilike(search_pattern),
                        Brand.code.ilike(search_pattern),
                        Brand.description.ilike(search_pattern)
                    )
                )
            elif key == "created_after":
                query = query.where(Brand.created_at >= value)
            elif key == "created_before":
                query = query.where(Brand.created_at <= value)
            elif key == "updated_after":
                query = query.where(Brand.updated_at >= value)
            elif key == "updated_before":
                query = query.where(Brand.updated_at <= value)
            elif key == "created_by":
                query = query.where(Brand.created_by == value)
            elif key == "updated_by":
                query = query.where(Brand.updated_by == value)
        
        return query