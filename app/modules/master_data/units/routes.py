from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from .service import UnitOfMeasurementService
from .schemas import (
    UnitOfMeasurementCreate, UnitOfMeasurementUpdate, UnitOfMeasurementResponse, 
    UnitOfMeasurementSummary, UnitOfMeasurementList, UnitOfMeasurementFilter, 
    UnitOfMeasurementSort, UnitOfMeasurementStats, UnitOfMeasurementBulkOperation, 
    UnitOfMeasurementBulkResult, UnitOfMeasurementExport, UnitOfMeasurementImport, 
    UnitOfMeasurementImportResult
)
from app.shared.dependencies import get_unit_of_measurement_service
from app.core.errors import (
    NotFoundError, ConflictError, ValidationError,
    BusinessRuleError
)


router = APIRouter(tags=["units-of-measurement"])


@router.post("/", response_model=UnitOfMeasurementResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_of_measurement(
    unit_data: UnitOfMeasurementCreate,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Create a new unit of measurement."""
    try:
        return await service.create_unit(unit_data, created_by=current_user_id)
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


@router.get("/{unit_id}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement(
    unit_id: UUID,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get a unit of measurement by ID."""
    try:
        return await service.get_unit(unit_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/by-name/{unit_name}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement_by_name(
    unit_name: str,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get a unit of measurement by name."""
    try:
        return await service.get_unit_by_name(unit_name)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/by-abbreviation/{unit_abbreviation}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement_by_abbreviation(
    unit_abbreviation: str,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get a unit of measurement by abbreviation."""
    try:
        return await service.get_unit_by_abbreviation(unit_abbreviation)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=UnitOfMeasurementList)
async def list_units_of_measurement(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    abbreviation: Optional[str] = Query(None, description="Filter by abbreviation (partial match)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and abbreviation"),
    sort_field: str = Query("name", description="Field to sort by"),
    sort_direction: str = Query("asc", description="Sort direction (asc/desc)"),
    include_inactive: bool = Query(False, description="Include inactive units"),
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """List units of measurement with pagination, filtering, and sorting."""
    # Create filter object
    filters = UnitOfMeasurementFilter(
        name=name,
        abbreviation=abbreviation,
        is_active=is_active,
        search=search
    )
    
    # Create sort object
    sort_options = UnitOfMeasurementSort(
        field=sort_field,
        direction=sort_direction
    )
    
    try:
        return await service.list_units(
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


@router.put("/{unit_id}", response_model=UnitOfMeasurementResponse)
async def update_unit_of_measurement(
    unit_id: UUID,
    unit_data: UnitOfMeasurementUpdate,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Update an existing unit of measurement."""
    try:
        return await service.update_unit(
            unit_id=unit_id,
            unit_data=unit_data,
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


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit_of_measurement(
    unit_id: UUID,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Delete (deactivate) a unit of measurement."""
    try:
        success = await service.delete_unit(unit_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unit with id {unit_id} not found"
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


@router.get("/search/", response_model=List[UnitOfMeasurementSummary])
async def search_units_of_measurement(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    include_inactive: bool = Query(False, description="Include inactive units"),
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Search units of measurement by name, abbreviation, or description."""
    return await service.search_units(
        search_term=q,
        limit=limit,
        include_inactive=include_inactive
    )


@router.get("/active/", response_model=List[UnitOfMeasurementSummary])
async def get_active_units_of_measurement(
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get all active units of measurement."""
    return await service.get_active_units()


@router.get("/stats/", response_model=UnitOfMeasurementStats)
async def get_unit_of_measurement_statistics(
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get unit of measurement statistics."""
    return await service.get_unit_statistics()


@router.post("/{unit_id}/activate", response_model=UnitOfMeasurementResponse)
async def activate_unit_of_measurement(
    unit_id: UUID,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Activate a unit of measurement."""
    try:
        return await service.activate_unit(unit_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{unit_id}/deactivate", response_model=UnitOfMeasurementResponse)
async def deactivate_unit_of_measurement(
    unit_id: UUID,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Deactivate a unit of measurement."""
    try:
        return await service.deactivate_unit(unit_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/bulk-operation", response_model=UnitOfMeasurementBulkResult)
async def bulk_unit_of_measurement_operation(
    operation: UnitOfMeasurementBulkOperation,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Perform bulk operations on units of measurement."""
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


@router.get("/export/", response_model=List[UnitOfMeasurementExport])
async def export_units_of_measurement(
    include_inactive: bool = Query(False, description="Include inactive units"),
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Export units of measurement data."""
    return await service.export_units(include_inactive=include_inactive)


@router.post("/import/", response_model=UnitOfMeasurementImportResult)
async def import_units_of_measurement(
    units_data: List[UnitOfMeasurementImport],
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Import units of measurement data."""
    try:
        return await service.import_units(
            import_data=units_data,
            created_by=current_user_id
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for units of measurement module."""
    return JSONResponse(
        content={
            "status": "healthy",
            "module": "units-of-measurement",
            "timestamp": "2025-01-09T00:00:00Z"
        }
    )