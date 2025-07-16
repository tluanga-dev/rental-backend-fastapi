from typing import List, Optional, Dict, Any
from uuid import UUID

from .repository import CompanyRepository
from .models import Company
from .schemas import (
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanySummary,
    CompanyList, CompanyFilter, CompanySort, CompanyActiveStatus
)
from app.core.errors import (
    NotFoundError, ConflictError, ValidationError,
    BusinessRuleError
)


class CompanyService:
    """Service layer for company business logic."""
    
    def __init__(self, repository: CompanyRepository):
        """Initialize service with repository."""
        self.repository = repository
    
    async def create_company(
        self,
        company_data: CompanyCreate,
        created_by: Optional[str] = None
    ) -> CompanyResponse:
        """Create a new company.
        
        Args:
            company_data: Company creation data
            created_by: User creating the company
            
        Returns:
            Created company response
            
        Raises:
            ConflictError: If company name, GST or registration number already exists
            ValidationError: If company data is invalid
        """
        # Check if company name already exists
        if await self.repository.exists_by_name(company_data.company_name):
            raise ConflictError(f"Company with name '{company_data.company_name}' already exists")
        
        # Check if GST number already exists
        if company_data.gst_no and await self.repository.exists_by_gst_no(company_data.gst_no):
            raise ConflictError(f"Company with GST number '{company_data.gst_no}' already exists")
        
        # Check if registration number already exists
        if company_data.registration_number and await self.repository.exists_by_registration_number(company_data.registration_number):
            raise ConflictError(f"Company with registration number '{company_data.registration_number}' already exists")
        
        # Prepare company data
        create_data = company_data.model_dump()
        create_data.update({
            "created_by": created_by,
            "updated_by": created_by
        })
        
        # Create company
        company = await self.repository.create(create_data)
        
        # Convert to response
        return CompanyResponse.model_validate(company)
    
    async def get_company(self, company_id: UUID) -> CompanyResponse:
        """Get company by ID.
        
        Args:
            company_id: Company UUID
            
        Returns:
            Company response
            
        Raises:
            NotFoundError: If company not found
        """
        company = await self.repository.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company with id {company_id} not found")
        
        return CompanyResponse.model_validate(company)
    
    async def get_active_company(self) -> CompanyResponse:
        """Get the active company.
        
        Returns:
            Active company response
            
        Raises:
            NotFoundError: If no active company found
        """
        company = await self.repository.get_active_company()
        if not company:
            raise NotFoundError("No active company found")
        
        return CompanyResponse.model_validate(company)
    
    async def update_company(
        self,
        company_id: UUID,
        company_data: CompanyUpdate,
        updated_by: Optional[str] = None
    ) -> CompanyResponse:
        """Update an existing company.
        
        Args:
            company_id: Company UUID
            company_data: Company update data
            updated_by: User updating the company
            
        Returns:
            Updated company response
            
        Raises:
            NotFoundError: If company not found
            ConflictError: If name, GST or registration number already exists
            ValidationError: If update data is invalid
        """
        # Get existing company
        existing_company = await self.repository.get_by_id(company_id)
        if not existing_company:
            raise NotFoundError(f"Company with id {company_id} not found")
        
        # Prepare update data
        update_data = {}
        
        # Check name uniqueness if provided
        if company_data.company_name is not None and company_data.company_name != existing_company.company_name:
            if await self.repository.exists_by_name(company_data.company_name, exclude_id=company_id):
                raise ConflictError(f"Company with name '{company_data.company_name}' already exists")
            update_data["company_name"] = company_data.company_name
        
        # Check GST number uniqueness if provided
        if company_data.gst_no is not None and company_data.gst_no != existing_company.gst_no:
            if company_data.gst_no and await self.repository.exists_by_gst_no(company_data.gst_no, exclude_id=company_id):
                raise ConflictError(f"Company with GST number '{company_data.gst_no}' already exists")
            update_data["gst_no"] = company_data.gst_no
        
        # Check registration number uniqueness if provided
        if company_data.registration_number is not None and company_data.registration_number != existing_company.registration_number:
            if company_data.registration_number and await self.repository.exists_by_registration_number(company_data.registration_number, exclude_id=company_id):
                raise ConflictError(f"Company with registration number '{company_data.registration_number}' already exists")
            update_data["registration_number"] = company_data.registration_number
        
        # Add other fields if provided
        if company_data.address is not None:
            update_data["address"] = company_data.address
        if company_data.email is not None:
            update_data["email"] = company_data.email
        if company_data.phone is not None:
            update_data["phone"] = company_data.phone
        if company_data.is_active is not None:
            update_data["is_active"] = company_data.is_active
        
        # Add updated_by
        update_data["updated_by"] = updated_by
        
        # Update company
        company = await self.repository.update(company_id, update_data)
        if not company:
            raise NotFoundError(f"Failed to update company with id {company_id}")
        
        return CompanyResponse.model_validate(company)
    
    async def delete_company(self, company_id: UUID) -> bool:
        """Soft delete a company.
        
        Args:
            company_id: Company UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If company not found
            BusinessRuleError: If company cannot be deleted
        """
        company = await self.repository.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company with id {company_id} not found")
        
        # Check if this is the only active company
        total_active = await self.repository.count(include_inactive=False)
        if total_active == 1 and company.is_active:
            raise BusinessRuleError("Cannot delete the only active company")
        
        success = await self.repository.delete(company_id)
        if not success:
            raise BusinessRuleError(f"Failed to delete company with id {company_id}")
        
        return True
    
    async def activate_company(self, company_id: UUID) -> CompanyResponse:
        """Activate a company (and deactivate all others).
        
        Args:
            company_id: Company UUID to activate
            
        Returns:
            Activated company response
            
        Raises:
            NotFoundError: If company not found
        """
        company = await self.repository.activate(company_id)
        if not company:
            raise NotFoundError(f"Company with id {company_id} not found")
        
        return CompanyResponse.model_validate(company)
    
    async def list_companies(
        self,
        page: int = 1,
        page_size: int = 20,
        filter_params: Optional[CompanyFilter] = None,
        sort_params: Optional[CompanySort] = None,
        include_inactive: bool = False
    ) -> CompanyList:
        """List companies with pagination, filtering and sorting.
        
        Args:
            page: Page number (1-based)
            page_size: Items per page
            filter_params: Filtering parameters
            sort_params: Sorting parameters
            include_inactive: Include inactive companies
            
        Returns:
            Paginated company list
        """
        # Convert filter parameters to dict
        filters = filter_params.model_dump(exclude_none=True) if filter_params else {}
        
        # Get sorting parameters
        sort_by = sort_params.field if sort_params else "company_name"
        sort_order = sort_params.direction if sort_params else "asc"
        
        # Get paginated companies
        companies = await self.repository.get_paginated(
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            include_inactive=include_inactive
        )
        
        # Get total count
        total = await self.repository.count(
            filters=filters,
            include_inactive=include_inactive
        )
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        # Convert to summaries
        items = [CompanySummary.model_validate(company) for company in companies]
        
        return CompanyList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
    
    async def search_companies(
        self,
        search_term: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[CompanySummary]:
        """Search companies by name, email, GST or registration number.
        
        Args:
            search_term: Search term
            limit: Maximum results to return
            include_inactive: Include inactive companies
            
        Returns:
            List of company summaries
        """
        companies = await self.repository.search(
            search_term=search_term,
            limit=limit,
            include_inactive=include_inactive
        )
        
        return [CompanySummary.model_validate(company) for company in companies]