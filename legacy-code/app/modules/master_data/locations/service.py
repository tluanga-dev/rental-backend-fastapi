from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import LocationRepository
from .models import Location
from .schemas import LocationCreate, LocationUpdate, LocationResponse
from app.core.errors import ValidationError, NotFoundError, ConflictError


class LocationService:
    """Location service."""
    
    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.repository = LocationRepository(session)
    
    async def create_location(self, location_data: LocationCreate) -> LocationResponse:
        """Create a new location."""
        # Check if location code already exists
        existing_location = await self.repository.get_by_code(location_data.location_code)
        if existing_location:
            raise ConflictError(f"Location with code '{location_data.location_code}' already exists")
        
        # Create location
        location_dict = location_data.model_dump()
        location = await self.repository.create(location_dict)
        
        return LocationResponse.model_validate(location)
    
    async def get_location(self, location_id: UUID) -> Optional[LocationResponse]:
        """Get location by ID."""
        location = await self.repository.get_by_id(location_id)
        if not location:
            return None
        
        return LocationResponse.model_validate(location)
    
    async def get_location_by_code(self, location_code: str) -> Optional[LocationResponse]:
        """Get location by code."""
        location = await self.repository.get_by_code(location_code)
        if not location:
            return None
        
        return LocationResponse.model_validate(location)
    
    async def update_location(self, location_id: UUID, update_data: LocationUpdate) -> LocationResponse:
        """Update location information."""
        location = await self.repository.get_by_id(location_id)
        if not location:
            raise NotFoundError("Location not found")
        
        # Update location
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_location = await self.repository.update(location_id, update_dict)
        
        return LocationResponse.model_validate(updated_location)
    
    async def delete_location(self, location_id: UUID) -> bool:
        """Delete location."""
        return await self.repository.delete(location_id)
    
    async def list_locations(
        self,
        skip: int = 0,
        limit: int = 100,
        location_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[LocationResponse]:
        """List locations with filtering."""
        locations = await self.repository.get_all(
            skip=skip,
            limit=limit,
            location_type=location_type,
            active_only=active_only
        )
        
        return [LocationResponse.model_validate(location) for location in locations]
    
    async def search_locations(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[LocationResponse]:
        """Search locations."""
        locations = await self.repository.search(
            search_term=search_term,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [LocationResponse.model_validate(location) for location in locations]
    
    async def count_locations(
        self,
        location_type: Optional[str] = None,
        active_only: bool = True
    ) -> int:
        """Count locations with filtering."""
        return await self.repository.count_all(
            location_type=location_type,
            active_only=active_only
        )