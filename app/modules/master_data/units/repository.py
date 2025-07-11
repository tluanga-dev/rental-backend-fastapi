from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import UnitOfMeasurement


class UnitOfMeasurementRepository:
    """Repository for unit of measurement data access operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, unit_data: dict) -> UnitOfMeasurement:
        """Create a new unit of measurement."""
        unit = UnitOfMeasurement(**unit_data)
        self.session.add(unit)
        await self.session.commit()
        await self.session.refresh(unit)
        return unit
    
    async def get_by_id(self, unit_id: UUID) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by ID."""
        query = select(UnitOfMeasurement).where(UnitOfMeasurement.id == unit_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by name."""
        query = select(UnitOfMeasurement).where(UnitOfMeasurement.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_abbreviation(self, abbreviation: str) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by abbreviation."""
        query = select(UnitOfMeasurement).where(UnitOfMeasurement.abbreviation == abbreviation)
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
    ) -> List[UnitOfMeasurement]:
        """List units of measurement with optional filters and sorting."""
        query = select(UnitOfMeasurement)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(UnitOfMeasurement.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(UnitOfMeasurement, sort_by)))
        else:
            query = query.order_by(asc(getattr(UnitOfMeasurement, sort_by)))
        
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
    ) -> List[UnitOfMeasurement]:
        """Get paginated units of measurement."""
        query = select(UnitOfMeasurement)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(UnitOfMeasurement.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(UnitOfMeasurement, sort_by)))
        else:
            query = query.order_by(asc(getattr(UnitOfMeasurement, sort_by)))
        
        # Calculate pagination
        skip = (page - 1) * page_size
        limit = page_size
        
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update(self, unit_id: UUID, update_data: dict) -> Optional[UnitOfMeasurement]:
        """Update existing unit of measurement."""
        unit = await self.get_by_id(unit_id)
        if not unit:
            return None
        
        # Update fields using the model's update method
        unit.update_details(**update_data)
        
        await self.session.commit()
        await self.session.refresh(unit)
        
        return unit
    
    async def delete(self, unit_id: UUID) -> bool:
        """Soft delete unit of measurement by setting is_active to False."""
        unit = await self.get_by_id(unit_id)
        if not unit:
            return False
        
        unit.is_active = False
        await self.session.commit()
        
        return True
    
    async def hard_delete(self, unit_id: UUID) -> bool:
        """Hard delete unit of measurement from database."""
        unit = await self.get_by_id(unit_id)
        if not unit:
            return False
        
        # Check if unit can be deleted
        if not unit.can_delete():
            return False
        
        await self.session.delete(unit)
        await self.session.commit()
        
        return True
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_inactive: bool = False
    ) -> int:
        """Count units of measurement matching filters."""
        query = select(func.count()).select_from(UnitOfMeasurement)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(UnitOfMeasurement.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a unit of measurement with the given name exists."""
        query = select(func.count()).select_from(UnitOfMeasurement).where(
            UnitOfMeasurement.name == name
        )
        
        if exclude_id:
            query = query.where(UnitOfMeasurement.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_abbreviation(self, abbreviation: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a unit of measurement with the given abbreviation exists."""
        query = select(func.count()).select_from(UnitOfMeasurement).where(
            UnitOfMeasurement.abbreviation == abbreviation
        )
        
        if exclude_id:
            query = query.where(UnitOfMeasurement.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def search(
        self,
        search_term: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[UnitOfMeasurement]:
        """Search units of measurement by name, abbreviation, or description."""
        search_pattern = f"%{search_term}%"
        
        query = select(UnitOfMeasurement).where(
            or_(
                UnitOfMeasurement.name.ilike(search_pattern),
                UnitOfMeasurement.abbreviation.ilike(search_pattern),
                UnitOfMeasurement.description.ilike(search_pattern)
            )
        )
        
        if not include_inactive:
            query = query.where(UnitOfMeasurement.is_active == True)
        
        query = query.order_by(UnitOfMeasurement.name).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_active_units(self) -> List[UnitOfMeasurement]:
        """Get all active units of measurement."""
        query = select(UnitOfMeasurement).where(UnitOfMeasurement.is_active == True).order_by(UnitOfMeasurement.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_inactive_units(self) -> List[UnitOfMeasurement]:
        """Get all inactive units of measurement."""
        query = select(UnitOfMeasurement).where(UnitOfMeasurement.is_active == False).order_by(UnitOfMeasurement.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_units_with_items(self) -> List[UnitOfMeasurement]:
        """Get units of measurement that have associated items."""
        # This will be implemented when items relationship is fully available
        query = select(UnitOfMeasurement).where(
            UnitOfMeasurement.is_active == True
        ).order_by(UnitOfMeasurement.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_units_without_items(self) -> List[UnitOfMeasurement]:
        """Get units of measurement that have no associated items."""
        # This will be implemented when items relationship is fully available
        query = select(UnitOfMeasurement).where(
            UnitOfMeasurement.is_active == True
        ).order_by(UnitOfMeasurement.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def bulk_activate(self, unit_ids: List[UUID]) -> int:
        """Activate multiple units of measurement."""
        query = select(UnitOfMeasurement).where(UnitOfMeasurement.id.in_(unit_ids))
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        count = 0
        for unit in units:
            if not unit.is_active:
                unit.is_active = True
                count += 1
        
        await self.session.commit()
        return count
    
    async def bulk_deactivate(self, unit_ids: List[UUID]) -> int:
        """Deactivate multiple units of measurement."""
        query = select(UnitOfMeasurement).where(UnitOfMeasurement.id.in_(unit_ids))
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        count = 0
        for unit in units:
            if unit.is_active:
                unit.is_active = False
                count += 1
        
        await self.session.commit()
        return count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get unit of measurement statistics."""
        # Count all units
        total_query = select(func.count()).select_from(UnitOfMeasurement)
        total_result = await self.session.execute(total_query)
        total_units = total_result.scalar_one()
        
        # Count active units
        active_query = select(func.count()).select_from(UnitOfMeasurement).where(UnitOfMeasurement.is_active == True)
        active_result = await self.session.execute(active_query)
        active_units = active_result.scalar_one()
        
        # Count units with items (when items relationship is available)
        units_with_items = 0  # Temporary until items relationship is available
        
        return {
            "total_units": total_units,
            "active_units": active_units,
            "inactive_units": total_units - active_units,
            "units_with_items": units_with_items,
            "units_without_items": total_units - units_with_items
        }
    
    async def get_most_used_units(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get units of measurement with most items."""
        # This will be implemented when items relationship is fully available
        # For now, return empty list
        return []
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        for key, value in filters.items():
            if value is None:
                continue
            
            if key == "name":
                query = query.where(UnitOfMeasurement.name.ilike(f"%{value}%"))
            elif key == "abbreviation":
                query = query.where(UnitOfMeasurement.abbreviation.ilike(f"%{value}%"))
            elif key == "description":
                query = query.where(UnitOfMeasurement.description.ilike(f"%{value}%"))
            elif key == "is_active":
                query = query.where(UnitOfMeasurement.is_active == value)
            elif key == "search":
                search_pattern = f"%{value}%"
                query = query.where(
                    or_(
                        UnitOfMeasurement.name.ilike(search_pattern),
                        UnitOfMeasurement.abbreviation.ilike(search_pattern),
                        UnitOfMeasurement.description.ilike(search_pattern)
                    )
                )
            elif key == "created_after":
                query = query.where(UnitOfMeasurement.created_at >= value)
            elif key == "created_before":
                query = query.where(UnitOfMeasurement.created_at <= value)
            elif key == "updated_after":
                query = query.where(UnitOfMeasurement.updated_at >= value)
            elif key == "updated_before":
                query = query.where(UnitOfMeasurement.updated_at <= value)
            elif key == "created_by":
                query = query.where(UnitOfMeasurement.created_by == value)
            elif key == "updated_by":
                query = query.where(UnitOfMeasurement.updated_by == value)
        
        return query