from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Company


class CompanyRepository:
    """Repository for company data access operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, company_data: dict) -> Company:
        """Create a new company."""
        company = Company(**company_data)
        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
        return company
    
    async def get_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID."""
        query = select(Company).where(Company.id == company_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, company_name: str) -> Optional[Company]:
        """Get company by name."""
        query = select(Company).where(Company.company_name == company_name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_gst_no(self, gst_no: str) -> Optional[Company]:
        """Get company by GST number."""
        query = select(Company).where(Company.gst_no == gst_no)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_registration_number(self, registration_number: str) -> Optional[Company]:
        """Get company by registration number."""
        query = select(Company).where(Company.registration_number == registration_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_company(self) -> Optional[Company]:
        """Get the active company (for single company mode)."""
        query = select(Company).where(Company.is_active == True).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "company_name",
        sort_order: str = "asc",
        include_inactive: bool = False
    ) -> List[Company]:
        """List companies with optional filters and sorting."""
        query = select(Company)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Company.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(Company, sort_by)))
        else:
            query = query.order_by(asc(getattr(Company, sort_by)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "company_name",
        sort_order: str = "asc",
        include_inactive: bool = False
    ) -> List[Company]:
        """Get paginated companies."""
        query = select(Company)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Company.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(Company, sort_by)))
        else:
            query = query.order_by(asc(getattr(Company, sort_by)))
        
        # Calculate pagination
        skip = (page - 1) * page_size
        limit = page_size
        
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update(self, company_id: UUID, update_data: dict) -> Optional[Company]:
        """Update existing company."""
        company = await self.get_by_id(company_id)
        if not company:
            return None
        
        # Update fields using the model's update method
        company.update_info(**update_data)
        
        await self.session.commit()
        await self.session.refresh(company)
        
        return company
    
    async def delete(self, company_id: UUID) -> bool:
        """Soft delete company by setting is_active to False."""
        company = await self.get_by_id(company_id)
        if not company:
            return False
        
        company.is_active = False
        await self.session.commit()
        
        return True
    
    async def activate(self, company_id: UUID) -> Optional[Company]:
        """Activate a company and deactivate all others (single company mode)."""
        # First deactivate all companies
        all_companies_query = select(Company)
        result = await self.session.execute(all_companies_query)
        all_companies = result.scalars().all()
        
        for comp in all_companies:
            comp.is_active = False
        
        # Then activate the specified company
        company = await self.get_by_id(company_id)
        if not company:
            return None
        
        company.is_active = True
        await self.session.commit()
        await self.session.refresh(company)
        
        return company
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_inactive: bool = False
    ) -> int:
        """Count companies matching filters."""
        query = select(func.count()).select_from(Company)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Company.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def exists_by_name(self, company_name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a company with the given name exists."""
        query = select(func.count()).select_from(Company).where(
            Company.company_name == company_name
        )
        
        if exclude_id:
            query = query.where(Company.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_gst_no(self, gst_no: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a company with the given GST number exists."""
        query = select(func.count()).select_from(Company).where(
            Company.gst_no == gst_no
        )
        
        if exclude_id:
            query = query.where(Company.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_registration_number(self, registration_number: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a company with the given registration number exists."""
        query = select(func.count()).select_from(Company).where(
            Company.registration_number == registration_number
        )
        
        if exclude_id:
            query = query.where(Company.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def search(
        self,
        search_term: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[Company]:
        """Search companies by name, email, GST or registration number."""
        search_pattern = f"%{search_term}%"
        
        query = select(Company).where(
            or_(
                Company.company_name.ilike(search_pattern),
                Company.email.ilike(search_pattern),
                Company.gst_no.ilike(search_pattern),
                Company.registration_number.ilike(search_pattern)
            )
        )
        
        if not include_inactive:
            query = query.where(Company.is_active == True)
        
        query = query.order_by(Company.company_name).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        for key, value in filters.items():
            if value is None:
                continue
            
            if key == "company_name":
                query = query.where(Company.company_name.ilike(f"%{value}%"))
            elif key == "email":
                query = query.where(Company.email.ilike(f"%{value}%"))
            elif key == "phone":
                query = query.where(Company.phone.ilike(f"%{value}%"))
            elif key == "gst_no":
                query = query.where(Company.gst_no.ilike(f"%{value}%"))
            elif key == "registration_number":
                query = query.where(Company.registration_number.ilike(f"%{value}%"))
            elif key == "address":
                query = query.where(Company.address.ilike(f"%{value}%"))
            elif key == "is_active":
                query = query.where(Company.is_active == value)
            elif key == "search":
                search_pattern = f"%{value}%"
                query = query.where(
                    or_(
                        Company.company_name.ilike(search_pattern),
                        Company.email.ilike(search_pattern),
                        Company.gst_no.ilike(search_pattern),
                        Company.registration_number.ilike(search_pattern)
                    )
                )
            elif key == "created_after":
                query = query.where(Company.created_at >= value)
            elif key == "created_before":
                query = query.where(Company.created_at <= value)
            elif key == "updated_after":
                query = query.where(Company.updated_at >= value)
            elif key == "updated_before":
                query = query.where(Company.updated_at <= value)
            elif key == "created_by":
                query = query.where(Company.created_by == value)
            elif key == "updated_by":
                query = query.where(Company.updated_by == value)
        
        return query