from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from .models import Location
from app.shared.repository import BaseRepository


class LocationRepository(BaseRepository[Location]):
    """Repository for location operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Location, session)
    
    async def get_by_code(self, location_code: str) -> Optional[Location]:
        """Get location by code."""
        query = select(Location).where(Location.location_code == location_code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_type(self, location_type: str, active_only: bool = True) -> List[Location]:
        """Get locations by type."""
        query = select(Location).where(Location.location_type == location_type)
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        query = query.order_by(Location.location_name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_manager(self, manager_user_id: UUID, active_only: bool = True) -> List[Location]:
        """Get locations by manager."""
        query = select(Location).where(Location.manager_user_id == manager_user_id)
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        query = query.order_by(Location.location_name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_city(self, city: str, active_only: bool = True) -> List[Location]:
        """Get locations by city."""
        query = select(Location).where(Location.city.ilike(f"%{city}%"))
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        query = query.order_by(Location.location_name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_state(self, state: str, active_only: bool = True) -> List[Location]:
        """Get locations by state."""
        query = select(Location).where(Location.state.ilike(f"%{state}%"))
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        query = query.order_by(Location.location_name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_country(self, country: str, active_only: bool = True) -> List[Location]:
        """Get locations by country."""
        query = select(Location).where(Location.country.ilike(f"%{country}%"))
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        query = query.order_by(Location.location_name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Location]:
        """Search locations by name, code, or address."""
        search_conditions = [
            Location.location_name.ilike(f"%{search_term}%"),
            Location.location_code.ilike(f"%{search_term}%"),
            Location.address_line1.ilike(f"%{search_term}%"),
            Location.city.ilike(f"%{search_term}%"),
            Location.state.ilike(f"%{search_term}%"),
            Location.country.ilike(f"%{search_term}%")
        ]
        
        query = select(Location).where(or_(*search_conditions))
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        query = query.order_by(Location.location_name).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        location_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Location]:
        """Get all locations with filtering."""
        query = select(Location)
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        if location_type:
            query = query.where(Location.location_type == location_type)
        
        query = query.order_by(Location.location_name).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_all(
        self,
        location_type: Optional[str] = None,
        active_only: bool = True
    ) -> int:
        """Count locations with filtering."""
        query = select(func.count(Location.id))
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        if location_type:
            query = query.where(Location.location_type == location_type)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def exists_by_code(self, location_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if location exists by code."""
        query = select(func.count(Location.id)).where(Location.location_code == location_code)
        
        if exclude_id:
            query = query.where(Location.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar() > 0
    
    async def get_statistics(self):
        """Get location statistics."""
        # Total and active counts
        total_count = await self.session.execute(select(func.count(Location.id)))
        active_count = await self.session.execute(
            select(func.count(Location.id)).where(Location.is_active == True)
        )
        
        # Count by type
        type_counts = await self.session.execute(
            select(Location.location_type, func.count(Location.id))
            .where(Location.is_active == True)
            .group_by(Location.location_type)
        )
        
        # Count by country
        country_counts = await self.session.execute(
            select(Location.country, func.count(Location.id))
            .where(Location.is_active == True)
            .group_by(Location.country)
            .order_by(func.count(Location.id).desc())
            .limit(10)
        )
        
        # Count by state
        state_counts = await self.session.execute(
            select(Location.state, func.count(Location.id))
            .where(Location.is_active == True)
            .group_by(Location.state)
            .order_by(func.count(Location.id).desc())
            .limit(10)
        )
        
        return {
            "total_locations": total_count.scalar(),
            "active_locations": active_count.scalar(),
            "locations_by_type": dict(type_counts.fetchall()),
            "locations_by_country": dict(country_counts.fetchall()),
            "locations_by_state": dict(state_counts.fetchall())
        }