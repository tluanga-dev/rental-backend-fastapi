from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from .service import BrandService
from .schemas import (
    BrandCreate, BrandUpdate, BrandResponse, BrandSummary,
    BrandList, BrandFilter, BrandSort, BrandStats,
    BrandBulkOperation, BrandBulkResult, BrandExport,
    BrandImport, BrandImportResult
)
from app.shared.dependencies import get_brand_service
from app.core.errors import (
    NotFoundError, ConflictError, ValidationError,
    BusinessRuleError
)


router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_data: BrandCreate,
    service: BrandService = Depends(get_brand_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Create a new brand."""
    try:
        return await service.create_brand(brand_data, created_by=current_user_id)
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


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    service: BrandService = Depends(get_brand_service)
):
    """Get a brand by ID."""
    try:
        return await service.get_brand(brand_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/by-name/{brand_name}", response_model=BrandResponse)
async def get_brand_by_name(
    brand_name: str,
    service: BrandService = Depends(get_brand_service)
):
    """Get a brand by name."""
    try:
        return await service.get_brand_by_name(brand_name)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/by-code/{brand_code}", response_model=BrandResponse)
async def get_brand_by_code(
    brand_code: str,
    service: BrandService = Depends(get_brand_service)
):
    """Get a brand by code."""
    try:
        return await service.get_brand_by_code(brand_code.upper())
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=BrandList)
async def list_brands(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    code: Optional[str] = Query(None, description="Filter by code (partial match)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and code"),
    sort_field: str = Query("name", description="Field to sort by"),
    sort_direction: str = Query("asc", description="Sort direction (asc/desc)"),
    include_inactive: bool = Query(False, description="Include inactive brands"),
    service: BrandService = Depends(get_brand_service)
):
    """List brands with pagination, filtering, and sorting."""
    # Create filter object
    filters = BrandFilter(
        name=name,
        code=code,
        is_active=is_active,
        search=search
    )
    
    # Create sort object
    sort_options = BrandSort(
        field=sort_field,
        direction=sort_direction
    )
    
    try:
        return await service.list_brands(
            page=page,
            page_size=page_size,
            filters=filters,
            sort=sort_options,
            include_inactive=include_inactive
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    brand_data: BrandUpdate,
    service: BrandService = Depends(get_brand_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Update an existing brand."""
    try:
        return await service.update_brand(
            brand_id=brand_id,
            brand_data=brand_data,
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


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: UUID,
    service: BrandService = Depends(get_brand_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Delete (deactivate) a brand."""
    try:
        success = await service.delete_brand(brand_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand with id {brand_id} not found"
            )
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


@router.get("/search/", response_model=List[BrandSummary])
async def search_brands(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    include_inactive: bool = Query(False, description="Include inactive brands"),
    service: BrandService = Depends(get_brand_service)
):
    """Search brands by name, code, or description."""
    return await service.search_brands(
        search_term=q,
        limit=limit,
        include_inactive=include_inactive
    )


@router.get("/active/", response_model=List[BrandSummary])
async def get_active_brands(
    service: BrandService = Depends(get_brand_service)
):
    """Get all active brands."""
    return await service.get_active_brands()


@router.get("/stats/", response_model=BrandStats)
async def get_brand_statistics(
    service: BrandService = Depends(get_brand_service)
):
    """Get brand statistics."""
    return await service.get_brand_statistics()


@router.post("/{brand_id}/activate", response_model=BrandResponse)
async def activate_brand(
    brand_id: UUID,
    service: BrandService = Depends(get_brand_service)
):
    """Activate a brand."""
    try:
        return await service.activate_brand(brand_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{brand_id}/deactivate", response_model=BrandResponse)
async def deactivate_brand(
    brand_id: UUID,
    service: BrandService = Depends(get_brand_service)
):
    """Deactivate a brand."""
    try:
        return await service.deactivate_brand(brand_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/bulk-operation", response_model=BrandBulkResult)
async def bulk_brand_operation(
    operation: BrandBulkOperation,
    service: BrandService = Depends(get_brand_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Perform bulk operations on brands."""
    try:
        return await service.bulk_operation(
            operation=operation,
            updated_by=current_user_id
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/export/", response_model=List[BrandExport])
async def export_brands(
    include_inactive: bool = Query(False, description="Include inactive brands"),
    service: BrandService = Depends(get_brand_service)
):
    """Export brands data."""
    return await service.export_brands(include_inactive=include_inactive)


@router.post("/import/", response_model=BrandImportResult)
async def import_brands(
    brands_data: List[BrandImport],
    service: BrandService = Depends(get_brand_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Import brands data."""
    try:
        return await service.import_brands(
            import_data=brands_data,
            created_by=current_user_id
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for brands module."""
    return JSONResponse(
        content={
            "status": "healthy",
            "module": "brands",
            "timestamp": "2025-01-09T00:00:00Z"
        }
    )