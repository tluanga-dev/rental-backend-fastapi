from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from .service import CompanyService
from .schemas import (
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanySummary,
    CompanyList, CompanyFilter, CompanySort, CompanyActiveStatus
)
from app.shared.dependencies import get_company_service
from app.core.errors import (
    NotFoundError, ConflictError, ValidationError,
    BusinessRuleError
)


router = APIRouter(tags=["company"])


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    service: CompanyService = Depends(get_company_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Create a new company."""
    try:
        return await service.create_company(company_data, created_by=current_user_id)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/active", response_model=CompanyResponse)
async def get_active_company(
    service: CompanyService = Depends(get_company_service)
):
    """Get the active company."""
    try:
        return await service.get_active_company()
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    service: CompanyService = Depends(get_company_service)
):
    """Get a company by ID."""
    try:
        return await service.get_company(company_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=CompanyList)
async def list_companies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    company_name: Optional[str] = Query(None, description="Filter by company name (partial match)"),
    email: Optional[str] = Query(None, description="Filter by email (partial match)"),
    gst_no: Optional[str] = Query(None, description="Filter by GST number (partial match)"),
    registration_number: Optional[str] = Query(None, description="Filter by registration number (partial match)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name, email, GST and registration number"),
    sort_field: str = Query("company_name", description="Field to sort by"),
    sort_direction: str = Query("asc", description="Sort direction (asc/desc)"),
    include_inactive: bool = Query(False, description="Include inactive companies"),
    service: CompanyService = Depends(get_company_service)
):
    """List companies with pagination, filtering, and sorting."""
    # Create filter object
    filters = CompanyFilter(
        company_name=company_name,
        email=email,
        gst_no=gst_no,
        registration_number=registration_number,
        is_active=is_active,
        search=search
    )
    
    # Create sort object
    sort_options = CompanySort(
        field=sort_field,
        direction=sort_direction
    )
    
    try:
        return await service.list_companies(
            page=page,
            page_size=page_size,
            filter_params=filters,
            sort_params=sort_options,
            include_inactive=include_inactive
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_data: CompanyUpdate,
    service: CompanyService = Depends(get_company_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Update an existing company."""
    try:
        return await service.update_company(
            company_id=company_id,
            company_data=company_data,
            updated_by=current_user_id
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID,
    service: CompanyService = Depends(get_company_service)
):
    """Soft delete a company."""
    try:
        await service.delete_company(company_id)
        return
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{company_id}/activate", response_model=CompanyResponse)
async def activate_company(
    company_id: UUID,
    service: CompanyService = Depends(get_company_service)
):
    """Activate a company (and deactivate all others)."""
    try:
        return await service.activate_company(company_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/search/", response_model=List[CompanySummary])
async def search_companies(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    include_inactive: bool = Query(False, description="Include inactive companies"),
    service: CompanyService = Depends(get_company_service)
):
    """Search companies by name, email, GST or registration number."""
    return await service.search_companies(
        search_term=q,
        limit=limit,
        include_inactive=include_inactive
    )