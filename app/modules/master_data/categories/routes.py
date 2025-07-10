from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from .service import CategoryService
from .schemas import (
    CategoryCreate, CategoryUpdate, CategoryMove, CategoryResponse, 
    CategorySummary, CategoryTree, CategoryList, CategoryFilter, 
    CategorySort, CategoryStats, CategoryBulkOperation, CategoryBulkResult,
    CategoryExport, CategoryImport, CategoryImportResult, CategoryHierarchy,
    CategoryValidation
)
from app.shared.dependencies import get_category_service
from app.core.errors import (
    NotFoundError, ConflictError, ValidationError,
    BusinessRuleError
)


router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Create a new category."""
    try:
        return await service.create_category(category_data, created_by=current_user_id)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    service: CategoryService = Depends(get_category_service)
):
    """Get a category by ID."""
    try:
        return await service.get_category(category_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/by-path/{path:path}", response_model=CategoryResponse)
async def get_category_by_path(
    path: str,
    service: CategoryService = Depends(get_category_service)
):
    """Get a category by path."""
    try:
        return await service.get_category_by_path(path)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=CategoryList)
async def list_categories(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category ID"),
    level: Optional[int] = Query(None, ge=1, description="Filter by category level"),
    is_leaf: Optional[bool] = Query(None, description="Filter by leaf status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and path"),
    path_contains: Optional[str] = Query(None, description="Filter by path containing text"),
    has_items: Optional[bool] = Query(None, description="Filter by whether category has items"),
    has_children: Optional[bool] = Query(None, description="Filter by whether category has children"),
    sort_field: str = Query("name", description="Field to sort by"),
    sort_direction: str = Query("asc", description="Sort direction (asc/desc)"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    service: CategoryService = Depends(get_category_service)
):
    """List categories with pagination, filtering, and sorting."""
    # Create filter object
    filters = CategoryFilter(
        name=name,
        parent_id=parent_id,
        level=level,
        is_leaf=is_leaf,
        is_active=is_active,
        search=search,
        path_contains=path_contains,
        has_items=has_items,
        has_children=has_children
    )
    
    # Create sort object
    sort_options = CategorySort(
        field=sort_field,
        direction=sort_direction
    )
    
    try:
        return await service.list_categories(
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


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Update an existing category."""
    try:
        return await service.update_category(
            category_id=category_id,
            category_data=category_data,
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


@router.post("/{category_id}/move", response_model=CategoryResponse)
async def move_category(
    category_id: UUID,
    move_data: CategoryMove,
    service: CategoryService = Depends(get_category_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Move category to a new parent."""
    try:
        return await service.move_category(
            category_id=category_id,
            move_data=move_data,
            updated_by=current_user_id
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


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    service: CategoryService = Depends(get_category_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Delete (deactivate) a category."""
    try:
        success = await service.delete_category(category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
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


@router.get("/tree/", response_model=List[CategoryTree])
async def get_category_tree(
    root_id: Optional[UUID] = Query(None, description="Root category ID (None for full tree)"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    service: CategoryService = Depends(get_category_service)
):
    """Get hierarchical category tree."""
    return await service.get_category_tree(
        root_id=root_id,
        include_inactive=include_inactive
    )


@router.get("/{category_id}/hierarchy", response_model=CategoryHierarchy)
async def get_category_hierarchy(
    category_id: UUID,
    service: CategoryService = Depends(get_category_service)
):
    """Get category hierarchy information."""
    try:
        return await service.get_category_hierarchy(category_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/search/", response_model=List[CategorySummary])
async def search_categories(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    service: CategoryService = Depends(get_category_service)
):
    """Search categories by name or path."""
    return await service.search_categories(
        search_term=q,
        limit=limit,
        include_inactive=include_inactive
    )


@router.get("/roots/", response_model=List[CategorySummary])
async def get_root_categories(
    service: CategoryService = Depends(get_category_service)
):
    """Get all root categories."""
    return await service.get_root_categories()


@router.get("/leaves/", response_model=List[CategorySummary])
async def get_leaf_categories(
    service: CategoryService = Depends(get_category_service)
):
    """Get all leaf categories."""
    return await service.get_leaf_categories()


@router.get("/{parent_id}/children", response_model=List[CategorySummary])
async def get_category_children(
    parent_id: UUID,
    service: CategoryService = Depends(get_category_service)
):
    """Get direct children of a category."""
    try:
        return await service.get_category_children(parent_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/stats/", response_model=CategoryStats)
async def get_category_statistics(
    service: CategoryService = Depends(get_category_service)
):
    """Get category statistics."""
    return await service.get_category_statistics()


@router.post("/bulk-operation", response_model=CategoryBulkResult)
async def bulk_category_operation(
    operation: CategoryBulkOperation,
    service: CategoryService = Depends(get_category_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Perform bulk operations on categories."""
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


@router.get("/export/", response_model=List[CategoryExport])
async def export_categories(
    include_inactive: bool = Query(False, description="Include inactive categories"),
    service: CategoryService = Depends(get_category_service)
):
    """Export categories data."""
    return await service.export_categories(include_inactive=include_inactive)


@router.post("/import/", response_model=CategoryImportResult)
async def import_categories(
    categories_data: List[CategoryImport],
    service: CategoryService = Depends(get_category_service),
    current_user_id: Optional[str] = None  # TODO: Get from auth context
):
    """Import categories data."""
    try:
        return await service.import_categories(
            import_data=categories_data,
            created_by=current_user_id
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{category_id}/validate/{operation}", response_model=CategoryValidation)
async def validate_category_operation(
    category_id: UUID,
    operation: str,
    service: CategoryService = Depends(get_category_service)
):
    """Validate category operation."""
    return await service.validate_category_operation(
        category_id=category_id,
        operation=operation
    )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for categories module."""
    return JSONResponse(
        content={
            "status": "healthy",
            "module": "categories",
            "timestamp": "2025-01-09T00:00:00Z"
        }
    )