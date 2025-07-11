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
        
        # Create location - map schema fields to model fields
        location_dict = location_data.model_dump()
        
        # Map schema fields to model fields
        mapped_dict = {
            'location_code': location_dict.get('location_code'),
            'location_name': location_dict.get('location_name'),
            'location_type': location_dict.get('location_type'),
            'address': location_dict.get('address_line1'),
            'city': location_dict.get('city'),
            'state': location_dict.get('state'),
            'country': location_dict.get('country'),
            'postal_code': location_dict.get('postal_code'),
            'contact_number': location_dict.get('phone'),
            'email': location_dict.get('email'),
            'manager_user_id': location_dict.get('manager_user_id'),
        }
        
        # Remove None values
        mapped_dict = {k: v for k, v in mapped_dict.items() if v is not None}
        
        location = await self.repository.create(mapped_dict)
        
        # Map model fields back to response schema format
        response_data = {
            'id': location.id,
            'location_code': location.location_code,
            'location_name': location.location_name,
            'location_type': location.location_type,
            'address_line1': location.address,
            'address_line2': None,
            'city': location.city,
            'state': location.state,
            'postal_code': location.postal_code,
            'country': location.country,
            'phone': location.contact_number,
            'email': location.email,
            'manager_user_id': location.manager_user_id,
            'operating_hours': None,
            'capacity': None,
            'description': None,
            'created_at': location.created_at,
            'updated_at': location.updated_at,
            'is_active': location.is_active if hasattr(location, 'is_active') else True,
        }
        return LocationResponse(**response_data)
    
    async def get_location(self, location_id: UUID) -> Optional[LocationResponse]:
        """Get location by ID."""
        location = await self.repository.get_by_id(location_id)
        if not location:
            return None
        
        # Map model fields to response schema format
        response_data = {
            'id': location.id,
            'location_code': location.location_code,
            'location_name': location.location_name,
            'location_type': location.location_type,
            'address_line1': location.address,
            'address_line2': None,
            'city': location.city,
            'state': location.state,
            'postal_code': location.postal_code,
            'country': location.country,
            'phone': location.contact_number,
            'email': location.email,
            'manager_user_id': location.manager_user_id,
            'operating_hours': None,
            'capacity': None,
            'description': None,
            'created_at': location.created_at,
            'updated_at': location.updated_at,
            'is_active': location.is_active if hasattr(location, 'is_active') else True,
        }
        return LocationResponse(**response_data)
    
    async def get_location_by_code(self, location_code: str) -> Optional[LocationResponse]:
        """Get location by code."""
        location = await self.repository.get_by_code(location_code)
        if not location:
            return None
        
        # Map model fields to response schema format
        response_data = {
            'id': location.id,
            'location_code': location.location_code,
            'location_name': location.location_name,
            'location_type': location.location_type,
            'address_line1': location.address,
            'address_line2': None,
            'city': location.city,
            'state': location.state,
            'postal_code': location.postal_code,
            'country': location.country,
            'phone': location.contact_number,
            'email': location.email,
            'manager_user_id': location.manager_user_id,
            'operating_hours': None,
            'capacity': None,
            'description': None,
            'created_at': location.created_at,
            'updated_at': location.updated_at,
            'is_active': location.is_active if hasattr(location, 'is_active') else True,
        }
        return LocationResponse(**response_data)
    
    async def update_location(self, location_id: UUID, update_data: LocationUpdate) -> LocationResponse:
        """Update location information."""
        location = await self.repository.get_by_id(location_id)
        if not location:
            raise NotFoundError("Location not found")
        
        # Update location
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_location = await self.repository.update(location_id, update_dict)
        
        # Map model fields to response schema format
        response_data = {
            'id': updated_location.id,
            'location_code': updated_location.location_code,
            'location_name': updated_location.location_name,
            'location_type': updated_location.location_type,
            'address_line1': updated_location.address,
            'address_line2': None,
            'city': updated_location.city,
            'state': updated_location.state,
            'postal_code': updated_location.postal_code,
            'country': updated_location.country,
            'phone': updated_location.contact_number,
            'email': updated_location.email,
            'manager_user_id': updated_location.manager_user_id,
            'operating_hours': None,
            'capacity': None,
            'description': None,
            'created_at': updated_location.created_at,
            'updated_at': updated_location.updated_at,
            'is_active': updated_location.is_active if hasattr(updated_location, 'is_active') else True,
        }
        return LocationResponse(**response_data)
    
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
        
        # Map model fields to response schema format
        result = []
        for location in locations:
            response_data = {
                'id': location.id,
                'location_code': location.location_code,
                'location_name': location.location_name,
                'location_type': location.location_type,
                'address_line1': location.address,
                'address_line2': None,
                'city': location.city,
                'state': location.state,
                'postal_code': location.postal_code,
                'country': location.country,
                'phone': location.contact_number,
                'email': location.email,
                'manager_user_id': location.manager_user_id,
                'operating_hours': None,
                'capacity': None,
                'description': None,
                'created_at': location.created_at,
                'updated_at': location.updated_at,
                'is_active': location.is_active if hasattr(location, 'is_active') else True,
            }
            result.append(LocationResponse(**response_data))
        
        return result
    
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
        
        # Map model fields to response schema format
        result = []
        for location in locations:
            response_data = {
                'id': location.id,
                'location_code': location.location_code,
                'location_name': location.location_name,
                'location_type': location.location_type,
                'address_line1': location.address,
                'address_line2': None,
                'city': location.city,
                'state': location.state,
                'postal_code': location.postal_code,
                'country': location.country,
                'phone': location.contact_number,
                'email': location.email,
                'manager_user_id': location.manager_user_id,
                'operating_hours': None,
                'capacity': None,
                'description': None,
                'created_at': location.created_at,
                'updated_at': location.updated_at,
                'is_active': location.is_active if hasattr(location, 'is_active') else True,
            }
            result.append(LocationResponse(**response_data))
        
        return result
    
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