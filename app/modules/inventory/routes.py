from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.inventory.service import InventoryService
from app.modules.inventory.models import ItemType, ItemStatus, InventoryUnitStatus, InventoryUnitCondition
from app.modules.inventory.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemListResponse,
    InventoryUnitCreate, InventoryUnitUpdate, InventoryUnitResponse, InventoryUnitListResponse,
    InventoryUnitStatusUpdate,
    StockLevelCreate, StockLevelUpdate, StockLevelResponse, StockLevelListResponse,
    StockAdjustment, StockReservation, StockReservationRelease,
    InventoryReport, ItemWithInventoryResponse
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(prefix="/inventory", tags=["inventory"])


def get_inventory_service(session: AsyncSession = Depends(get_session)) -> InventoryService:
    """Get inventory service instance."""
    return InventoryService(session)


# Item endpoints
@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new item."""
    try:
        return await service.create_item(item_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get item by ID."""
    try:
        return await service.get_item(item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/items/code/{item_code}", response_model=ItemResponse)
async def get_item_by_code(
    item_code: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get item by code."""
    try:
        return await service.get_item_by_code(item_code)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/items", response_model=List[ItemListResponse])
async def get_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_type: Optional[ItemType] = None,
    item_status: Optional[ItemStatus] = None,
    brand_id: Optional[UUID] = None,
    category_id: Optional[UUID] = None,
    active_only: bool = Query(True),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all items with optional filtering."""
    return await service.get_items(
        skip=skip,
        limit=limit,
        item_type=item_type,
        item_status=item_status,
        brand_id=brand_id,
        category_id=category_id,
        active_only=active_only
    )


@router.get("/items/search/{search_term}", response_model=List[ItemListResponse])
async def search_items(
    search_term: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    service: InventoryService = Depends(get_inventory_service)
):
    """Search items by name or code."""
    return await service.search_items(
        search_term=search_term,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: UUID,
    item_data: ItemUpdate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update an item."""
    try:
        return await service.update_item(item_id, item_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Delete an item."""
    try:
        success = await service.delete_item(item_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/items/rental", response_model=List[ItemListResponse])
async def get_rental_items(
    active_only: bool = Query(True),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all rental items."""
    return await service.get_rental_items(active_only=active_only)


@router.get("/items/sale", response_model=List[ItemListResponse])
async def get_sale_items(
    active_only: bool = Query(True),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all sale items."""
    return await service.get_sale_items(active_only=active_only)


# Inventory Unit endpoints
@router.post("/units", response_model=InventoryUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_unit(
    unit_data: InventoryUnitCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new inventory unit."""
    try:
        return await service.create_inventory_unit(unit_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/units/{unit_id}", response_model=InventoryUnitResponse)
async def get_inventory_unit(
    unit_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get inventory unit by ID."""
    try:
        return await service.get_inventory_unit(unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/units", response_model=List[InventoryUnitResponse])
async def get_inventory_units(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    status: Optional[InventoryUnitStatus] = None,
    condition: Optional[InventoryUnitCondition] = None,
    active_only: bool = Query(True),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all inventory units with optional filtering."""
    return await service.get_inventory_units(
        skip=skip,
        limit=limit,
        item_id=item_id,
        location_id=location_id,
        status=status,
        condition=condition,
        active_only=active_only
    )


@router.get("/units/available", response_model=List[InventoryUnitResponse])
async def get_available_units(
    item_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get available inventory units."""
    return await service.get_available_units(
        item_id=item_id,
        location_id=location_id
    )


@router.put("/units/{unit_id}", response_model=InventoryUnitResponse)
async def update_inventory_unit(
    unit_id: UUID,
    unit_data: InventoryUnitUpdate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update an inventory unit."""
    try:
        return await service.update_inventory_unit(unit_id, unit_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/units/{unit_id}/status", response_model=InventoryUnitResponse)
async def update_unit_status(
    unit_id: UUID,
    status_data: InventoryUnitStatusUpdate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update inventory unit status."""
    try:
        return await service.update_unit_status(
            unit_id=unit_id,
            status=status_data.status,
            condition=status_data.condition
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/units/{unit_id}/rent", response_model=InventoryUnitResponse)
async def rent_out_unit(
    unit_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Rent out an inventory unit."""
    try:
        return await service.rent_out_unit(unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/units/{unit_id}/return", response_model=InventoryUnitResponse)
async def return_unit_from_rent(
    unit_id: UUID,
    condition: Optional[InventoryUnitCondition] = None,
    service: InventoryService = Depends(get_inventory_service)
):
    """Return unit from rental."""
    try:
        return await service.return_unit_from_rent(unit_id, condition)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/units/{unit_id}/sell", response_model=InventoryUnitResponse)
async def sell_unit(
    unit_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Sell an inventory unit."""
    try:
        return await service.sell_unit(unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# Stock Level endpoints
@router.post("/stock", response_model=StockLevelResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_level(
    stock_data: StockLevelCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new stock level."""
    try:
        return await service.create_stock_level(stock_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/stock/{stock_id}", response_model=StockLevelResponse)
async def get_stock_level(
    stock_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock level by ID."""
    try:
        return await service.get_stock_level(stock_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stock", response_model=List[StockLevelResponse])
async def get_stock_levels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    active_only: bool = Query(True),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all stock levels with optional filtering."""
    return await service.get_stock_levels(
        skip=skip,
        limit=limit,
        item_id=item_id,
        location_id=location_id,
        active_only=active_only
    )


@router.put("/stock/{stock_id}", response_model=StockLevelResponse)
async def update_stock_level(
    stock_id: UUID,
    stock_data: StockLevelUpdate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update a stock level."""
    try:
        return await service.update_stock_level(stock_id, stock_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/stock/{stock_id}/adjust", response_model=StockLevelResponse)
async def adjust_stock(
    stock_id: UUID,
    adjustment_data: StockAdjustment,
    service: InventoryService = Depends(get_inventory_service)
):
    """Adjust stock quantity."""
    try:
        return await service.adjust_stock(stock_id, adjustment_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/stock/{stock_id}/reserve", response_model=StockLevelResponse)
async def reserve_stock(
    stock_id: UUID,
    reservation_data: StockReservation,
    service: InventoryService = Depends(get_inventory_service)
):
    """Reserve stock quantity."""
    try:
        return await service.reserve_stock(stock_id, reservation_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/stock/{stock_id}/release", response_model=StockLevelResponse)
async def release_stock_reservation(
    stock_id: UUID,
    release_data: StockReservationRelease,
    service: InventoryService = Depends(get_inventory_service)
):
    """Release stock reservation."""
    try:
        return await service.release_stock_reservation(stock_id, release_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/stock/low", response_model=List[StockLevelResponse])
async def get_low_stock_items(
    service: InventoryService = Depends(get_inventory_service)
):
    """Get items with low stock."""
    return await service.get_low_stock_items()


# Reporting endpoints
@router.get("/report", response_model=InventoryReport)
async def get_inventory_report(
    service: InventoryService = Depends(get_inventory_service)
):
    """Get comprehensive inventory report."""
    return await service.get_inventory_report()