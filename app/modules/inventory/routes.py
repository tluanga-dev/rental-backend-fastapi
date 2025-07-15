from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.inventory.service import InventoryService
from app.modules.master_data.item_master.models import ItemStatus
from app.modules.inventory.models import InventoryUnitStatus, InventoryUnitCondition, MovementType, ReferenceType
from app.modules.master_data.item_master.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemListResponse, ItemWithInventoryResponse,
    SKUGenerationRequest, SKUGenerationResponse, SKUBulkGenerationResponse
)
from app.modules.inventory.schemas import (
    InventoryUnitCreate, InventoryUnitUpdate, InventoryUnitResponse, InventoryUnitListResponse,
    InventoryUnitStatusUpdate,
    StockLevelCreate, StockLevelUpdate, StockLevelResponse, StockLevelListResponse,
    StockAdjustment, StockReservation, StockReservationRelease,
    InventoryReport, StockMovementResponse, StockMovementHistoryRequest,
    StockMovementSummaryResponse
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(tags=["inventory"])


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


# SKU-specific endpoints
@router.get("/items/sku/{sku}", response_model=ItemResponse)
async def get_item_by_sku(
    sku: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get item by SKU."""
    try:
        return await service.get_item_by_sku(sku)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/skus/generate", response_model=SKUGenerationResponse)
async def generate_sku_preview(
    request: SKUGenerationRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Generate a preview of what SKU would be created for the given brand/category."""
    return await service.generate_sku_preview(request)


# SKU validation endpoint removed - custom SKUs are no longer supported


@router.post("/skus/bulk-generate", response_model=SKUBulkGenerationResponse)
async def bulk_generate_skus(
    service: InventoryService = Depends(get_inventory_service)
):
    """Generate SKUs for all existing items that don't have them."""
    return await service.bulk_generate_skus()


# Stock Query endpoints for initial stock integration
@router.get("/items/{item_id}/stock", response_model=List[StockLevelResponse])
async def get_item_stock_levels(
    item_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all stock levels for a specific item across all locations."""
    try:
        return await service.get_stock_levels(item_id=item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/items/{item_id}/units", response_model=List[InventoryUnitResponse])
async def get_item_inventory_units(
    item_id: UUID,
    location_id: Optional[UUID] = None,
    status: Optional[InventoryUnitStatus] = None,
    condition: Optional[InventoryUnitCondition] = None,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all inventory units for a specific item with optional filtering."""
    try:
        return await service.get_inventory_units(
            item_id=item_id,
            location_id=location_id,
            status=status,
            condition=condition
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/items/{item_id}/stock-summary")
async def get_item_stock_summary(
    item_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get comprehensive stock summary for an item."""
    try:
        # Get all stock levels for the item
        stock_levels = await service.get_stock_levels(item_id=item_id)
        
        # Get all inventory units for the item
        inventory_units = await service.get_inventory_units(item_id=item_id)
        
        # Calculate summary statistics
        total_on_hand = sum(int(stock.quantity_on_hand) for stock in stock_levels)
        total_available = sum(int(stock.quantity_available) for stock in stock_levels)
        total_reserved = sum(int(stock.quantity_reserved) for stock in stock_levels)
        
        # Count units by status
        units_by_status = {}
        for unit in inventory_units:
            status_key = unit.status.value
            units_by_status[status_key] = units_by_status.get(status_key, 0) + 1
        
        # Count units by location
        units_by_location = {}
        for unit in inventory_units:
            loc_key = str(unit.location_id)
            units_by_location[loc_key] = units_by_location.get(loc_key, 0) + 1
        
        return {
            "item_id": str(item_id),
            "total_stock_levels": len(stock_levels),
            "total_inventory_units": len(inventory_units),
            "aggregate_quantities": {
                "on_hand": total_on_hand,
                "available": total_available,
                "reserved": total_reserved
            },
            "units_by_status": units_by_status,
            "units_by_location": units_by_location,
            "stock_levels": stock_levels,
            "has_initial_stock": len(inventory_units) > 0
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/locations/{location_id}/stock", response_model=List[StockLevelResponse])
async def get_location_stock_levels(
    location_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all stock levels at a specific location."""
    try:
        return await service.get_stock_levels(location_id=location_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Stock Movement Endpoints

@router.get("/stock/{stock_level_id}/movements", response_model=List[StockMovementResponse])
async def get_stock_level_movements(
    stock_level_id: UUID,
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of records to return"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock movements for a specific stock level."""
    try:
        return await service.get_stock_movements_by_stock_level(
            stock_level_id=stock_level_id,
            skip=skip,
            limit=limit
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/items/{item_id}/movements", response_model=List[StockMovementResponse])
async def get_item_movements(
    item_id: UUID,
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of records to return"),
    movement_type: Optional[MovementType] = Query(default=None, description="Filter by movement type"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock movements for a specific item."""
    try:
        return await service.get_stock_movements_by_item(
            item_id=item_id,
            skip=skip,
            limit=limit,
            movement_type=movement_type
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/movements/reference/{reference_type}/{reference_id}", response_model=List[StockMovementResponse])
async def get_movements_by_reference(
    reference_type: ReferenceType,
    reference_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock movements by reference."""
    try:
        return await service.get_stock_movements_by_reference(
            reference_type=reference_type,
            reference_id=reference_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/movements/range", response_model=List[StockMovementResponse])
async def get_movements_by_date_range(
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    item_id: Optional[UUID] = Query(default=None, description="Filter by item ID"),
    location_id: Optional[UUID] = Query(default=None, description="Filter by location ID"),
    movement_type: Optional[MovementType] = Query(default=None, description="Filter by movement type"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock movements within a date range."""
    try:
        return await service.get_stock_movements_by_date_range(
            start_date=start_date,
            end_date=end_date,
            item_id=item_id,
            location_id=location_id,
            movement_type=movement_type
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/items/{item_id}/movements/summary", response_model=StockMovementSummaryResponse)
async def get_item_movement_summary(
    item_id: UUID,
    start_date: Optional[datetime] = Query(default=None, description="Start date for summary"),
    end_date: Optional[datetime] = Query(default=None, description="End date for summary"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get movement summary for an item."""
    try:
        return await service.get_stock_movement_summary(
            item_id=item_id,
            start_date=start_date,
            end_date=end_date
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/stock/{stock_level_id}/movements/manual", response_model=StockMovementResponse)
async def create_manual_stock_movement(
    stock_level_id: UUID,
    movement_type: MovementType = Query(..., description="Type of movement"),
    quantity_change: Decimal = Query(..., description="Quantity change (+/-)"),
    reason: str = Query(..., description="Reason for movement"),
    notes: Optional[str] = Query(default=None, description="Additional notes"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a manual stock movement."""
    try:
        return await service.create_manual_stock_movement(
            stock_level_id=stock_level_id,
            movement_type=movement_type,
            quantity_change=quantity_change,
            reason=reason,
            notes=notes
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/stock/{stock_level_id}/rent-out", response_model=StockMovementResponse)
async def rent_out_stock(
    stock_level_id: UUID,
    quantity: Decimal = Query(..., ge=0, description="Quantity to rent out"),
    transaction_id: str = Query(..., description="Transaction ID"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Move stock from available to on rent."""
    try:
        return await service.rent_out_stock(
            stock_level_id=stock_level_id,
            quantity=quantity,
            transaction_id=transaction_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/stock/{stock_level_id}/return-from-rent", response_model=StockMovementResponse)
async def return_from_rent(
    stock_level_id: UUID,
    quantity: Decimal = Query(..., ge=0, description="Quantity to return"),
    transaction_id: str = Query(..., description="Transaction ID"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Move stock from on rent back to available."""
    try:
        return await service.return_from_rent(
            stock_level_id=stock_level_id,
            quantity=quantity,
            transaction_id=transaction_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))