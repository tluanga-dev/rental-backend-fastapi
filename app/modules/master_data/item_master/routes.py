from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.master_data.item_master.service import ItemMasterService
from app.modules.master_data.item_master.models import ItemStatus
from app.modules.master_data.item_master.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemListResponse, ItemWithInventoryResponse,
    SKUGenerationRequest, SKUGenerationResponse, SKUBulkGenerationResponse
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(tags=["Items"])


def get_item_master_service(session: AsyncSession = Depends(get_session)) -> ItemMasterService:
    """Get item master service instance."""
    return ItemMasterService(session)


# Item endpoints
@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, 
             summary="Create Item", description="Create a new item with automatic SKU generation")
async def create_item(
    item_data: ItemCreate,
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Create a new item with automatic SKU generation based on category and item details."""
    try:
        return await service.create_item(item_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{item_id}", response_model=ItemResponse,
           summary="Get Item by ID", description="Retrieve a single item by its UUID")
async def get_item(
    item_id: UUID,
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Get item by ID."""
    try:
        return await service.get_item(item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))




@router.get("/sku/{sku}", response_model=ItemResponse)
async def get_item_by_sku(
    sku: str,
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Get item by SKU."""
    try:
        return await service.get_item_by_sku(sku)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=List[ItemListResponse],
           summary="Get Items", 
           description="Get paginated list of items with advanced search and filtering capabilities")
async def get_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Search term for item name, code, or SKU"),
    item_status: Optional[ItemStatus] = Query(None, description="Filter by item status"),
    brand_id: Optional[UUID] = Query(None, description="Filter by brand ID"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    is_rentable: Optional[bool] = Query(None, description="Filter by rentable status"),
    is_saleable: Optional[bool] = Query(None, description="Filter by saleable status"),
    active_only: bool = Query(True, description="Show only active items"),
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Get all items with optional search and filtering. Supports text search across item name, code, SKU, and description. Combine search with filters for precise results."""
    return await service.get_items(
        skip=skip,
        limit=limit,
        search=search,
        item_status=item_status,
        brand_id=brand_id,
        category_id=category_id,
        is_rentable=is_rentable,
        is_saleable=is_saleable,
        active_only=active_only
    )


@router.get("/search/{search_term}", response_model=List[ItemListResponse])
async def search_items(
    search_term: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    active_only: bool = Query(True, description="Show only active items"),
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Search items by name or code."""
    return await service.search_items(
        search_term=search_term,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.put("/{item_id}", response_model=ItemResponse,
           summary="Update Item", description="Update an existing item (partial update supported)")
async def update_item(
    item_id: UUID,
    item_data: ItemUpdate,
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Update an item. All fields are optional - only provided fields will be updated."""
    try:
        return await service.update_item(item_id, item_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT,
              summary="Delete Item", description="Soft delete an item (sets is_active to false)")
async def delete_item(
    item_id: UUID,
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Delete (soft delete) an item."""
    try:
        await service.delete_item(item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/types/rental", response_model=List[ItemListResponse])
async def get_rental_items(
    active_only: bool = Query(True, description="Show only active items"),
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Get all rental items."""
    return await service.get_rental_items(active_only=active_only)


@router.get("/types/sale", response_model=List[ItemListResponse])
async def get_sale_items(
    active_only: bool = Query(True, description="Show only active items"),
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Get all sale items."""
    return await service.get_sale_items(active_only=active_only)


@router.get("/category/{category_id}", response_model=List[ItemListResponse])
async def get_items_by_category(
    category_id: UUID,
    active_only: bool = Query(True, description="Show only active items"),
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Get all items in a specific category."""
    return await service.get_items_by_category(category_id, active_only=active_only)


@router.get("/brand/{brand_id}", response_model=List[ItemListResponse])
async def get_items_by_brand(
    brand_id: UUID,
    active_only: bool = Query(True, description="Show only active items"),
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Get all items for a specific brand."""
    return await service.get_items_by_brand(brand_id, active_only=active_only)


@router.get("/low-stock/", response_model=List[ItemListResponse])
async def get_low_stock_items(
    active_only: bool = Query(True, description="Show only active items"),
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Get items that need reordering based on reorder level."""
    return await service.get_low_stock_items(active_only=active_only)


# SKU-specific endpoints
@router.post("/skus/generate", response_model=SKUGenerationResponse)
async def generate_sku_preview(
    request: SKUGenerationRequest,
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Generate a preview of what SKU would be created for the given category and item details."""
    return await service.generate_sku_preview(request)


@router.post("/skus/bulk-generate", response_model=SKUBulkGenerationResponse)
async def bulk_generate_skus(
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Generate SKUs for all existing items that don't have them."""
    return await service.bulk_generate_skus()


# Count endpoint
@router.get("/count/total")
async def count_items(
    search: Optional[str] = Query(None, description="Search term for item name, code, or SKU"),
    item_status: Optional[ItemStatus] = Query(None, description="Filter by item status"),
    brand_id: Optional[UUID] = Query(None, description="Filter by brand ID"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    is_rentable: Optional[bool] = Query(None, description="Filter by rentable status"),
    is_saleable: Optional[bool] = Query(None, description="Filter by saleable status"),
    active_only: bool = Query(True, description="Count only active items"),
    service: ItemMasterService = Depends(get_item_master_service)
):
    """Count items with optional search and filtering."""
    count = await service.count_items(
        search=search,
        item_status=item_status,
        brand_id=brand_id,
        category_id=category_id,
        is_rentable=is_rentable,
        is_saleable=is_saleable,
        active_only=active_only
    )
    return {"count": count}