from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.master_data.item_master.models import Item, ItemStatus
from app.modules.master_data.locations.models import Location
from app.modules.inventory.models import (
    InventoryUnit, StockLevel, StockMovement, InventoryUnitStatus, InventoryUnitCondition,
    MovementType, ReferenceType
)
from app.modules.inventory.repository import (
    ItemRepository, InventoryUnitRepository, StockLevelRepository, StockMovementRepository
)
from app.modules.master_data.locations.repository import LocationRepository
from app.modules.master_data.item_master.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemListResponse, ItemWithInventoryResponse,
    SKUGenerationRequest, SKUGenerationResponse, SKUBulkGenerationResponse
)
from app.modules.inventory.schemas import (
    InventoryUnitCreate, InventoryUnitUpdate, InventoryUnitResponse,
    StockLevelCreate, StockLevelUpdate, StockLevelResponse,
    StockAdjustment, StockReservation, StockReservationRelease,
    InventoryReport, StockMovementResponse, StockMovementHistoryRequest,
    StockMovementSummaryResponse, ItemInventoryOverview, ItemInventoryDetailed,
    UnitsByStatus, LocationStockInfo, InventoryUnitDetail, RecentMovement,
    ItemInventoryOverviewParams
)
from app.shared.utils.sku_generator import SKUGenerator


class InventoryService:
    """Service for inventory management operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.item_repository = ItemRepository(session)
        self.inventory_unit_repository = InventoryUnitRepository(session)
        self.stock_level_repository = StockLevelRepository(session)
        self.stock_movement_repository = StockMovementRepository(session)
        self.location_repository = LocationRepository(session)
        self.sku_generator = SKUGenerator(session)
    
    # Item operations
    async def create_item(self, item_data: ItemCreate) -> ItemResponse:
        """Create a new item with automatic SKU generation."""
        # Check if item code already exists
        existing_item = await self.item_repository.get_by_code(item_data.item_code)
        if existing_item:
            raise ConflictError(f"Item with code '{item_data.item_code}' already exists")
        
        # Generate SKU automatically using new format
        sku = await self.sku_generator.generate_sku(
            category_id=item_data.category_id,
            item_name=item_data.item_name,
            item_type=item_data.item_type.value
        )
        
        # Validate item type and pricing
        self._validate_item_pricing(item_data)
        
        # Create item with generated SKU
        item = await self.item_repository.create(item_data, sku)
        return ItemResponse.model_validate(item)
    
    async def get_item(self, item_id: UUID) -> ItemResponse:
        """Get item by ID."""
        item = await self.item_repository.get_by_id(item_id)
        if not item:
            raise NotFoundError(f"Item with ID {item_id} not found")
        
        return ItemResponse.model_validate(item)
    
    async def get_item_by_code(self, item_code: str) -> ItemResponse:
        """Get item by code."""
        item = await self.item_repository.get_by_code(item_code)
        if not item:
            raise NotFoundError(f"Item with code '{item_code}' not found")
        
        return ItemResponse.model_validate(item)
    
    async def get_items(
        self, 
        skip: int = 0, 
        limit: int = 100,
        item_status: Optional[ItemStatus] = None,
        brand_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> List[ItemListResponse]:
        """Get all items with optional filtering."""
        items = await self.item_repository.get_all(
            skip=skip,
            limit=limit,
            item_status=item_status,
            brand_id=brand_id,
            category_id=category_id,
            active_only=active_only
        )
        
        return [ItemListResponse.model_validate(item) for item in items]
    
    async def search_items(
        self, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[ItemListResponse]:
        """Search items by name or code."""
        items = await self.item_repository.search(
            search_term=search_term,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [ItemListResponse.model_validate(item) for item in items]
    
    async def update_item(self, item_id: UUID, item_data: ItemUpdate) -> ItemResponse:
        """Update an item."""
        # Check if item exists
        existing_item = await self.item_repository.get_by_id(item_id)
        if not existing_item:
            raise NotFoundError(f"Item with ID {item_id} not found")
        
        # Validate pricing if relevant fields are being updated
        if any(field in item_data.model_dump(exclude_unset=True) for field in [
            'rental_rate_per_period', 'rental_period', 'sale_price'
        ]):
            self._validate_item_pricing_update(existing_item, item_data)
        
        # Update item
        item = await self.item_repository.update(item_id, item_data)
        return ItemResponse.model_validate(item)
    
    async def delete_item(self, item_id: UUID) -> bool:
        """Delete an item."""
        # Check if item has inventory units
        units = await self.inventory_unit_repository.get_units_by_item(item_id)
        if units:
            raise ValidationError("Cannot delete item with existing inventory units")
        
        return await self.item_repository.delete(item_id)
    
    async def get_rental_items(self, active_only: bool = True) -> List[ItemListResponse]:
        """Get all rental items."""
        items = await self.item_repository.get_rental_items(active_only=active_only)
        return [ItemListResponse.model_validate(item) for item in items]
    
    async def get_sale_items(self, active_only: bool = True) -> List[ItemListResponse]:
        """Get all sale items."""
        items = await self.item_repository.get_sale_items(active_only=active_only)
        return [ItemListResponse.model_validate(item) for item in items]
    
    # Inventory Unit operations
    async def create_inventory_unit(self, unit_data: InventoryUnitCreate) -> InventoryUnitResponse:
        """Create a new inventory unit."""
        # Check if unit code already exists
        existing_unit = await self.inventory_unit_repository.get_by_code(unit_data.unit_code)
        if existing_unit:
            raise ConflictError(f"Inventory unit with code '{unit_data.unit_code}' already exists")
        
        # Verify item exists
        item = await self.item_repository.get_by_id(unit_data.item_id)
        if not item:
            raise NotFoundError(f"Item with ID {unit_data.item_id} not found")
        
        # Validate serial number requirement
        if item.serial_number_required and not unit_data.serial_number:
            raise ValidationError("Serial number is required for this item")
        
        # Create inventory unit
        unit = await self.inventory_unit_repository.create(unit_data)
        
        # Update stock levels
        await self._update_stock_levels_for_unit_creation(unit)
        
        return InventoryUnitResponse.model_validate(unit)
    
    async def get_inventory_unit(self, unit_id: UUID) -> InventoryUnitResponse:
        """Get inventory unit by ID."""
        unit = await self.inventory_unit_repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Inventory unit with ID {unit_id} not found")
        
        return InventoryUnitResponse.model_validate(unit)
    
    async def get_inventory_units(
        self, 
        skip: int = 0, 
        limit: int = 100,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[InventoryUnitStatus] = None,
        condition: Optional[InventoryUnitCondition] = None,
        active_only: bool = True
    ) -> List[InventoryUnitResponse]:
        """Get all inventory units with optional filtering."""
        units = await self.inventory_unit_repository.get_all(
            skip=skip,
            limit=limit,
            item_id=item_id,
            location_id=location_id,
            status=status,
            condition=condition,
            active_only=active_only
        )
        
        return [InventoryUnitResponse.model_validate(unit) for unit in units]
    
    async def get_available_units(
        self, 
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None
    ) -> List[InventoryUnitResponse]:
        """Get available inventory units."""
        units = await self.inventory_unit_repository.get_available_units(
            item_id=item_id,
            location_id=location_id
        )
        
        return [InventoryUnitResponse.model_validate(unit) for unit in units]
    
    async def update_inventory_unit(self, unit_id: UUID, unit_data: InventoryUnitUpdate) -> InventoryUnitResponse:
        """Update an inventory unit."""
        # Check if unit exists
        existing_unit = await self.inventory_unit_repository.get_by_id(unit_id)
        if not existing_unit:
            raise NotFoundError(f"Inventory unit with ID {unit_id} not found")
        
        # Update unit
        unit = await self.inventory_unit_repository.update(unit_id, unit_data)
        return InventoryUnitResponse.model_validate(unit)
    
    async def update_unit_status(
        self, 
        unit_id: UUID, 
        status: InventoryUnitStatus,
        condition: Optional[InventoryUnitCondition] = None
    ) -> InventoryUnitResponse:
        """Update inventory unit status."""
        unit = await self.inventory_unit_repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Inventory unit with ID {unit_id} not found")
        
        # Validate status transition
        self._validate_status_transition(unit.status, status)
        
        # Update status
        unit.status = status.value
        if condition:
            unit.condition = condition.value
        
        await self.session.commit()
        await self.session.refresh(unit)
        
        return InventoryUnitResponse.model_validate(unit)
    
    async def rent_out_unit(self, unit_id: UUID) -> InventoryUnitResponse:
        """Rent out an inventory unit."""
        unit = await self.inventory_unit_repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Inventory unit with ID {unit_id} not found")
        
        if not unit.is_available():
            raise ValidationError("Unit is not available for rental")
        
        unit.rent_out()
        await self.session.commit()
        await self.session.refresh(unit)
        
        return InventoryUnitResponse.model_validate(unit)
    
    async def return_unit_from_rent(
        self, 
        unit_id: UUID, 
        condition: Optional[InventoryUnitCondition] = None
    ) -> InventoryUnitResponse:
        """Return unit from rental."""
        unit = await self.inventory_unit_repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Inventory unit with ID {unit_id} not found")
        
        if not unit.is_rented():
            raise ValidationError("Unit is not currently rented")
        
        unit.return_from_rent(condition)
        await self.session.commit()
        await self.session.refresh(unit)
        
        return InventoryUnitResponse.model_validate(unit)
    
    async def sell_unit(self, unit_id: UUID) -> InventoryUnitResponse:
        """Sell an inventory unit."""
        unit = await self.inventory_unit_repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Inventory unit with ID {unit_id} not found")
        
        if not unit.is_available():
            raise ValidationError("Unit is not available for sale")
        
        unit.mark_as_sold()
        await self.session.commit()
        await self.session.refresh(unit)
        
        return InventoryUnitResponse.model_validate(unit)
    
    # Stock Level operations
    async def create_stock_level(self, stock_data: StockLevelCreate) -> StockLevelResponse:
        """Create a new stock level."""
        # Check if stock level already exists for this item/location
        existing_stock = await self.stock_level_repository.get_by_item_location(
            stock_data.item_id, stock_data.location_id
        )
        if existing_stock:
            raise ConflictError(f"Stock level already exists for item {stock_data.item_id} at location {stock_data.location_id}")
        
        # Create stock level
        stock_level = await self.stock_level_repository.create(stock_data)
        return StockLevelResponse.model_validate(stock_level)
    
    async def get_stock_level(self, stock_id: UUID) -> StockLevelResponse:
        """Get stock level by ID."""
        stock_level = await self.stock_level_repository.get_by_id(stock_id)
        if not stock_level:
            raise NotFoundError(f"Stock level with ID {stock_id} not found")
        
        return StockLevelResponse.model_validate(stock_level)
    
    async def get_stock_levels(
        self, 
        skip: int = 0, 
        limit: int = 100,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> List[StockLevelResponse]:
        """Get all stock levels with optional filtering."""
        stock_levels = await self.stock_level_repository.get_all(
            skip=skip,
            limit=limit,
            item_id=item_id,
            location_id=location_id,
            active_only=active_only
        )
        
        return [StockLevelResponse.model_validate(stock) for stock in stock_levels]
    
    async def update_stock_level(self, stock_id: UUID, stock_data: StockLevelUpdate) -> StockLevelResponse:
        """Update a stock level."""
        # Check if stock level exists
        existing_stock = await self.stock_level_repository.get_by_id(stock_id)
        if not existing_stock:
            raise NotFoundError(f"Stock level with ID {stock_id} not found")
        
        # Update stock level
        stock_level = await self.stock_level_repository.update(stock_id, stock_data)
        return StockLevelResponse.model_validate(stock_level)
    
    async def adjust_stock(self, stock_id: UUID, adjustment_data: StockAdjustment) -> StockLevelResponse:
        """Adjust stock quantity."""
        stock_level = await self.stock_level_repository.get_by_id(stock_id)
        if not stock_level:
            raise NotFoundError(f"Stock level with ID {stock_id} not found")
        
        stock_level.adjust_quantity(adjustment_data.adjustment)
        await self.session.commit()
        await self.session.refresh(stock_level)
        
        return StockLevelResponse.model_validate(stock_level)
    
    async def reserve_stock(self, stock_id: UUID, reservation_data: StockReservation) -> StockLevelResponse:
        """Reserve stock quantity."""
        stock_level = await self.stock_level_repository.get_by_id(stock_id)
        if not stock_level:
            raise NotFoundError(f"Stock level with ID {stock_id} not found")
        
        stock_level.reserve_quantity(reservation_data.quantity)
        await self.session.commit()
        await self.session.refresh(stock_level)
        
        return StockLevelResponse.model_validate(stock_level)
    
    async def release_stock_reservation(self, stock_id: UUID, release_data: StockReservationRelease) -> StockLevelResponse:
        """Release stock reservation."""
        stock_level = await self.stock_level_repository.get_by_id(stock_id)
        if not stock_level:
            raise NotFoundError(f"Stock level with ID {stock_id} not found")
        
        stock_level.release_reservation(release_data.quantity)
        await self.session.commit()
        await self.session.refresh(stock_level)
        
        return StockLevelResponse.model_validate(stock_level)
    
    async def get_low_stock_items(self) -> List[StockLevelResponse]:
        """Get items with low stock."""
        low_stock_items = await self.stock_level_repository.get_low_stock_items()
        return [StockLevelResponse.model_validate(stock) for stock in low_stock_items]
    
    # Reporting operations
    async def get_inventory_report(self) -> InventoryReport:
        """Get comprehensive inventory report."""
        # Get all items
        items = await self.item_repository.get_all(active_only=True)
        
        # Get inventory counts
        total_items = len(items)
        total_active_items = len([item for item in items if item.is_active])
        
        # Get all inventory units
        all_units = await self.inventory_unit_repository.get_all(active_only=True)
        total_inventory_units = len(all_units)
        total_available_units = len([unit for unit in all_units if unit.is_available()])
        total_rented_units = len([unit for unit in all_units if unit.is_rented()])
        
        # Get items needing reorder
        low_stock_items = await self.stock_level_repository.get_low_stock_items()
        items_needing_reorder = []
        for stock_level in low_stock_items:
            item = await self.item_repository.get_by_id(UUID(stock_level.item_id))
            if item:
                items_needing_reorder.append(ItemListResponse.model_validate(item))
        
        # Convert items to response format
        item_responses = [ItemWithInventoryResponse.model_validate(item) for item in items]
        
        return InventoryReport(
            items=item_responses,
            total_items=total_items,
            total_active_items=total_active_items,
            total_inventory_units=total_inventory_units,
            total_available_units=total_available_units,
            total_rented_units=total_rented_units,
            items_needing_reorder=items_needing_reorder
        )
    
    # Helper methods
    def _validate_item_pricing(self, item_data: ItemCreate):
        """Validate item pricing based on boolean fields."""
        if item_data.is_rentable:
            if not item_data.rental_rate_per_period:
                raise ValidationError("Rental rate per period is required for rentable items")
        
        if item_data.is_saleable:
            if not item_data.sale_price:
                raise ValidationError("Sale price is required for saleable items")
    
    def _validate_item_pricing_update(self, existing_item: Item, item_data: ItemUpdate):
        """Validate item pricing for updates."""
        # Get effective boolean fields after update
        is_rentable = item_data.is_rentable if item_data.is_rentable is not None else existing_item.is_rentable
        is_saleable = item_data.is_saleable if item_data.is_saleable is not None else existing_item.is_saleable
        
        # Get effective pricing after update
        rental_price = item_data.rental_rate_per_period if item_data.rental_rate_per_period is not None else existing_item.rental_rate_per_period
        sale_price = item_data.sale_price if item_data.sale_price is not None else existing_item.sale_price
        
        if is_rentable:
            if not rental_price:
                raise ValidationError("Rental price per day is required for rentable items")
        
        if is_saleable:
            if not sale_price:
                raise ValidationError("Sale price is required for saleable items")
    
    def _validate_status_transition(self, current_status: str, new_status: InventoryUnitStatus):
        """Validate inventory unit status transitions."""
        valid_transitions = {
            InventoryUnitStatus.AVAILABLE.value: [
                InventoryUnitStatus.RENTED.value,
                InventoryUnitStatus.SOLD.value,
                InventoryUnitStatus.MAINTENANCE.value,
                InventoryUnitStatus.DAMAGED.value,
                InventoryUnitStatus.RETIRED.value
            ],
            InventoryUnitStatus.RENTED.value: [
                InventoryUnitStatus.AVAILABLE.value,
                InventoryUnitStatus.MAINTENANCE.value,
                InventoryUnitStatus.DAMAGED.value
            ],
            InventoryUnitStatus.SOLD.value: [],  # No transitions from sold
            InventoryUnitStatus.MAINTENANCE.value: [
                InventoryUnitStatus.AVAILABLE.value,
                InventoryUnitStatus.DAMAGED.value,
                InventoryUnitStatus.RETIRED.value
            ],
            InventoryUnitStatus.DAMAGED.value: [
                InventoryUnitStatus.MAINTENANCE.value,
                InventoryUnitStatus.RETIRED.value
            ],
            InventoryUnitStatus.RETIRED.value: []  # No transitions from retired
        }
        
        if new_status.value not in valid_transitions.get(current_status, []):
            raise ValidationError(f"Invalid status transition from {current_status} to {new_status.value}")
    
    # SKU-specific operations
    async def get_item_by_sku(self, sku: str) -> ItemResponse:
        """Get item by SKU."""
        item = await self.item_repository.get_by_sku(sku)
        if not item:
            raise NotFoundError(f"Item with SKU '{sku}' not found")
        return ItemResponse.model_validate(item)
    
    async def generate_sku_preview(self, request: SKUGenerationRequest) -> SKUGenerationResponse:
        """Generate a preview of what SKU would be created."""
        sku = await self.sku_generator.preview_sku(
            category_id=request.category_id,
            item_name=request.item_name,
            item_type=request.item_type
        )
        
        # Extract components for response
        parts = sku.split('-')
        if len(parts) == 5:
            category_code, subcategory_code, product_code, attributes_code, sequence = parts
            sequence_number = int(sequence)
        else:
            category_code = "MISC"
            subcategory_code = "ITEM"
            sequence_number = 1
        
        return SKUGenerationResponse(
            sku=sku,
            category_code=category_code,
            subcategory_code=subcategory_code,
            product_code=parts[2] if len(parts) > 2 else "PROD",
            attributes_code=parts[3] if len(parts) > 3 else "R",
            sequence_number=sequence_number
        )
    
    
    async def bulk_generate_skus(self) -> SKUBulkGenerationResponse:
        """Generate SKUs for all existing items that don't have them."""
        result = await self.sku_generator.bulk_generate_skus_for_existing_items()
        return SKUBulkGenerationResponse(**result)
    
    async def _update_stock_levels_for_unit_creation(self, unit: InventoryUnit):
        """Update stock levels when a new inventory unit is created."""
        # Get or create stock level for the item/location
        stock_level = await self.stock_level_repository.get_by_item_location(
            UUID(unit.item_id), UUID(unit.location_id)
        )
        
        if stock_level:
            # Increment quantity
            current_quantity = int(stock_level.quantity_on_hand)
            new_quantity = current_quantity + 1
            stock_level.quantity_on_hand = str(new_quantity)
            
            # Update available quantity if the unit is available
            if unit.is_available():
                stock_level.quantity_available = str(int(stock_level.quantity_available) + 1)
            
            await self.session.commit()
        else:
            # Create new stock level
            stock_data = StockLevelCreate(
                item_id=UUID(unit.item_id),
                location_id=UUID(unit.location_id),
                quantity_on_hand="1",
                quantity_available="1" if unit.is_available() else "0"
            )
            await self.stock_level_repository.create(stock_data)
    
    # Helper methods for initial stock creation
    async def get_default_location(self) -> Location:
        """Get the default location for inventory operations."""
        # Try to get the first active location
        locations = await self.location_repository.get_all(skip=0, limit=1, active_only=True)
        
        if locations:
            return locations[0]
        
        # If no locations exist, create a default one
        from app.modules.master_data.locations.schemas import LocationCreate
        default_location_data = LocationCreate(
            location_code="DEFAULT",
            location_name="Default Warehouse",
            location_type="WAREHOUSE",
            address_line1="Main Storage Facility",
            city="Default City",
            state="N/A",
            postal_code="00000",
            country="USA",
            description="Default location for initial inventory"
        )
        
        return await self.location_repository.create(default_location_data)
    
    def generate_unit_code(self, item_sku: str, sequence: int) -> str:
        """Generate a unique unit code for an inventory unit."""
        return f"{item_sku}-U{sequence:03d}"
    
    async def create_initial_stock(
        self, 
        item_id: UUID, 
        item_sku: str, 
        purchase_price: Optional[Decimal], 
        quantity: int,
        location_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create initial stock for a new item.
        
        Args:
            item_id: The item's UUID
            item_sku: The item's SKU for unit code generation
            purchase_price: Purchase price for inventory units
            quantity: Number of units to create
            location_id: Location ID (uses default if None)
            
        Returns:
            Dictionary with creation summary
        """
        # Business rule validation
        validation_result = await self._validate_initial_stock_business_rules(
            item_id, item_sku, purchase_price, quantity, location_id
        )
        if not validation_result["valid"]:
            return {"created": False, "reason": validation_result["reason"]}
        
        try:
            # Get location
            if location_id:
                location = await self.location_repository.get_by_id(location_id)
                if not location:
                    raise NotFoundError(f"Location with ID {location_id} not found")
            else:
                location = await self.get_default_location()
            
            # Check if stock level already exists
            existing_stock = await self.stock_level_repository.get_by_item_location(
                item_id, location.id
            )
            if existing_stock:
                raise ConflictError(f"Stock level already exists for item {item_id} at location {location.id}")
            
            # Create stock level first
            stock_data = StockLevelCreate(
                item_id=item_id,
                location_id=location.id,
                quantity_on_hand=quantity,
                quantity_available=quantity,
                quantity_on_rent=Decimal("0")
            )
            
            stock_level = await self.stock_level_repository.create(stock_data)
            
            # Create individual inventory units
            created_units = []
            for i in range(1, quantity + 1):
                unit_code = self.generate_unit_code(item_sku, i)
                
                unit_data = InventoryUnitCreate(
                    item_id=item_id,
                    location_id=location.id,
                    unit_code=unit_code,
                    status=InventoryUnitStatus.AVAILABLE,
                    condition=InventoryUnitCondition.NEW,
                    purchase_price=purchase_price or Decimal("0.00"),
                    purchase_date=datetime.utcnow()
                )
                
                unit = await self.inventory_unit_repository.create(unit_data)
                created_units.append(unit.unit_code)
            
            return {
                "created": True,
                "stock_level_id": str(stock_level.id),
                "location_id": str(location.id),
                "location_name": location.location_name,
                "total_quantity": quantity,
                "unit_codes": created_units,
                "purchase_price": str(purchase_price) if purchase_price else "0.00"
            }
            
        except Exception as e:
            # Roll back the transaction on error
            await self.session.rollback()
            raise e
    
    async def _validate_initial_stock_business_rules(
        self, 
        item_id: UUID, 
        item_sku: str, 
        purchase_price: Optional[Decimal], 
        quantity: int,
        location_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Validate business rules for initial stock creation.
        
        Args:
            item_id: The item's UUID
            item_sku: The item's SKU
            purchase_price: Purchase price for inventory units
            quantity: Number of units to create
            location_id: Location ID (optional)
            
        Returns:
            Dictionary with validation result: {"valid": bool, "reason": str}
        """
        # Rule 1: Quantity must be positive
        if quantity <= 0:
            return {"valid": False, "reason": "Quantity must be greater than 0"}
        
        # Rule 2: Quantity must be reasonable (max 10,000 units per initial creation)
        if quantity > 10000:
            return {"valid": False, "reason": "Initial stock quantity cannot exceed 10,000 units"}
        
        # Rule 3: Item must exist and be active
        try:
            item = await self.item_repository.get_by_id(item_id)
            if not item:
                return {"valid": False, "reason": f"Item with ID {item_id} not found"}
            
            if not item.is_active:
                return {"valid": False, "reason": "Cannot create stock for inactive items"}
                
        except Exception as e:
            return {"valid": False, "reason": f"Error validating item: {str(e)}"}
        
        # Rule 4: SKU must be valid and match the item
        if not item_sku or not item_sku.strip():
            return {"valid": False, "reason": "Item SKU cannot be empty"}
        
        if len(item_sku) > 50:
            return {"valid": False, "reason": "Item SKU cannot exceed 50 characters"}
        
        if item.sku != item_sku:
            return {"valid": False, "reason": f"SKU mismatch: expected {item.sku}, got {item_sku}"}
        
        # Rule 5: Purchase price validation
        if purchase_price is not None:
            if purchase_price < 0:
                return {"valid": False, "reason": "Purchase price cannot be negative"}
            
            if purchase_price > Decimal("999999.99"):
                return {"valid": False, "reason": "Purchase price cannot exceed $999,999.99"}
        
        # Rule 6: No existing stock should exist for this item (this is initial stock)
        try:
            existing_stock_levels = await self.stock_level_repository.get_all(
                item_id=item_id, skip=0, limit=1, active_only=True
            )
            if existing_stock_levels:
                return {
                    "valid": False, 
                    "reason": f"Item {item_id} already has existing stock levels. Use stock adjustment instead."
                }
            
            existing_inventory_units = await self.inventory_unit_repository.get_units_by_item(item_id)
            if existing_inventory_units:
                return {
                    "valid": False, 
                    "reason": f"Item {item_id} already has existing inventory units. Use stock adjustment instead."
                }
                
        except Exception as e:
            return {"valid": False, "reason": f"Error checking existing stock: {str(e)}"}
        
        # Rule 7: Location validation (if provided)
        if location_id:
            try:
                location = await self.location_repository.get_by_id(location_id)
                if not location:
                    return {"valid": False, "reason": f"Location with ID {location_id} not found"}
                
                if not location.is_active:
                    return {"valid": False, "reason": "Cannot create stock at inactive location"}
                    
            except Exception as e:
                return {"valid": False, "reason": f"Error validating location: {str(e)}"}
        
        # Rule 8: Unique unit code validation (ensure no conflicts)
        try:
            for i in range(1, min(quantity + 1, 6)):  # Check first 5 unit codes for conflicts
                test_unit_code = self.generate_unit_code(item_sku, i)
                existing_unit = await self.inventory_unit_repository.get_by_code(test_unit_code)
                if existing_unit:
                    return {
                        "valid": False, 
                        "reason": f"Unit code conflict: {test_unit_code} already exists"
                    }
        except Exception as e:
            return {"valid": False, "reason": f"Error validating unit codes: {str(e)}"}
        
        return {"valid": True, "reason": "All business rules passed"}
    
    # Return processing methods
    async def adjust_stock_level(
        self,
        item_id: UUID,
        location_id: UUID,
        quantity_change: Decimal,
        transaction_type: str,
        reference_id: str,
        notes: Optional[str] = None
    ) -> StockLevelResponse:
        """
        Adjust stock level for return processing.
        
        Args:
            item_id: Item to adjust
            location_id: Location of the adjustment
            quantity_change: Change in quantity (positive for additions, negative for reductions)
            transaction_type: Type of transaction causing adjustment
            reference_id: Reference transaction ID
            notes: Optional notes about the adjustment
            
        Returns:
            Updated stock level
        """
        # Get current stock level
        stock_level = await self.stock_level_repository.get_by_item_location(
            item_id=item_id,
            location_id=location_id
        )
        
        quantity_before = Decimal("0")
        
        if not stock_level:
            if quantity_change < 0:
                raise ValidationError("Cannot remove from non-existent stock")
            
            # Create new stock level for positive adjustments
            stock_data = StockLevelCreate(
                item_id=item_id,
                location_id=location_id,
                quantity_on_hand=quantity_change,
                quantity_available=quantity_change
            )
            
            stock_level = await self.stock_level_repository.create(stock_data)
            quantity_before = Decimal("0")
        else:
            # Update existing stock
            quantity_before = stock_level.quantity_on_hand
            stock_level.adjust_quantity(quantity_change)
            
            await self.session.commit()
            await self.session.refresh(stock_level)
        
        quantity_after = stock_level.quantity_on_hand
        
        # Determine movement type based on transaction type
        movement_type = self._map_transaction_to_movement_type(transaction_type)
        
        # Create stock movement record
        await self._create_stock_movement_record(
            stock_level_id=stock_level.id,
            movement_type=movement_type,
            quantity_change=quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reference_type=ReferenceType.TRANSACTION,
            reference_id=reference_id,
            reason=f"{transaction_type} - {notes or 'Stock adjustment'}",
            notes=notes
        )
        
        return StockLevelResponse.model_validate(stock_level)
    
    async def update_inventory_unit_status(
        self,
        unit_id: UUID,
        status: str,
        condition: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """
        Update inventory unit status and condition for rental returns.
        
        Args:
            unit_id: Inventory unit to update
            status: New status (AVAILABLE, REQUIRES_INSPECTION, etc.)
            condition: New condition if applicable
            notes: Optional notes about the update
        """
        unit = await self.inventory_unit_repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Inventory unit {unit_id} not found")
        
        # Update status
        if status in [s.value for s in InventoryUnitStatus]:
            unit.status = status
        else:
            raise ValidationError(f"Invalid status: {status}")
        
        # Update condition if provided
        if condition and condition in [c.value for c in InventoryUnitCondition]:
            unit.condition = condition
        
        # Add notes if provided
        if notes:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            status_note = f"\n[{timestamp}] Status updated to {status}: {notes}"
            unit.notes = (unit.notes or "") + status_note
        
        await self.session.commit()
    
    async def update_stock_condition(
        self,
        item_id: UUID,
        location_id: UUID,
        quantity: Decimal,
        condition: str,
        status: str
    ) -> None:
        """
        Update stock condition for items without individual unit tracking.
        
        Args:
            item_id: Item to update
            location_id: Location of the stock
            quantity: Quantity with the specified condition
            condition: Item condition
            status: Stock status
        """
        # For items without unit tracking, we would update stock level metadata
        # This is a simplified implementation - in practice, you might have
        # a separate table for tracking stock by condition
        
        stock_level = await self.stock_level_repository.get_by_item_location(
            item_id=item_id,
            location_id=location_id
        )
        
        if not stock_level:
            raise NotFoundError(f"Stock level not found for item {item_id} at location {location_id}")
        
        # Add condition tracking to notes (simplified approach)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        condition_note = f"\n[{timestamp}] {quantity} units in {condition} condition, status: {status}"
        stock_level.notes = (stock_level.notes or "") + condition_note
        
        await self.session.commit()
    
    async def _create_stock_movement_record(
        self,
        stock_level_id: UUID,
        movement_type: str,
        quantity_change: Decimal,
        quantity_before: Decimal,
        quantity_after: Decimal,
        reference_type: ReferenceType,
        reference_id: str,
        reason: str,
        notes: Optional[str] = None,
        transaction_line_id: Optional[UUID] = None,
        created_by: Optional[str] = None
    ) -> StockMovement:
        """
        Create a stock movement record for audit trail.
        
        Args:
            stock_level_id: ID of the stock level being modified
            movement_type: Type of movement (from MovementType enum)
            quantity_change: Amount of change (+/-)
            quantity_before: Quantity before the movement
            quantity_after: Quantity after the movement
            reference_type: Type of reference (from ReferenceType enum)
            reference_id: External reference ID
            reason: Human-readable reason for the movement
            notes: Additional notes
            transaction_line_id: Optional transaction line reference
            created_by: User who created the movement
        
        Returns:
            The created stock movement record
        """
        # Get stock level to extract item_id and location_id
        stock_level = await self.stock_level_repository.get_by_id(stock_level_id)
        if not stock_level:
            raise NotFoundError(f"Stock level with ID {stock_level_id} not found")
        
        # Create movement data
        movement_data = {
            "stock_level_id": stock_level_id,
            "item_id": stock_level.item_id,
            "location_id": stock_level.location_id,
            "movement_type": movement_type,
            "reference_type": reference_type.value,
            "reference_id": reference_id,
            "quantity_change": quantity_change,
            "quantity_before": quantity_before,
            "quantity_after": quantity_after,
            "reason": reason,
            "notes": notes,
            "transaction_line_id": transaction_line_id,
            "created_by": created_by
        }
        
        # Create the movement record
        movement = await self.stock_movement_repository.create(movement_data)
        
        # Log the movement for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Stock movement created: {movement_type} - "
            f"Stock Level: {stock_level_id}, "
            f"Change: {quantity_change}, "
            f"Before: {quantity_before}, After: {quantity_after}, "
            f"Reference: {reference_type.value}:{reference_id}"
        )
        
        return movement
    
    def _map_transaction_to_movement_type(self, transaction_type: str) -> str:
        """Map transaction type to movement type."""
        mapping = {
            "RENTAL_OUT": MovementType.RENTAL_OUT.value,
            "RENTAL_RETURN": MovementType.RENTAL_RETURN.value,
            "SALE": MovementType.SALE.value,
            "PURCHASE": MovementType.PURCHASE.value,
            "ADJUSTMENT": MovementType.ADJUSTMENT_POSITIVE.value,
            "DAMAGE": MovementType.DAMAGE_LOSS.value,
            "TRANSFER_IN": MovementType.TRANSFER_IN.value,
            "TRANSFER_OUT": MovementType.TRANSFER_OUT.value,
        }
        return mapping.get(transaction_type, MovementType.SYSTEM_CORRECTION.value)
    
    # Stock Movement operations
    async def get_stock_movements_by_stock_level(
        self,
        stock_level_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockMovementResponse]:
        """Get stock movements for a specific stock level."""
        movements = await self.stock_movement_repository.get_by_stock_level(
            stock_level_id=stock_level_id,
            skip=skip,
            limit=limit
        )
        return [StockMovementResponse.model_validate(movement) for movement in movements]
    
    async def get_stock_movements_by_item(
        self,
        item_id: UUID,
        skip: int = 0,
        limit: int = 100,
        movement_type: Optional[MovementType] = None
    ) -> List[StockMovementResponse]:
        """Get stock movements for a specific item."""
        movements = await self.stock_movement_repository.get_by_item(
            item_id=item_id,
            skip=skip,
            limit=limit,
            movement_type=movement_type
        )
        return [StockMovementResponse.model_validate(movement) for movement in movements]
    
    async def get_stock_movements_by_reference(
        self,
        reference_type: ReferenceType,
        reference_id: str
    ) -> List[StockMovementResponse]:
        """Get stock movements by reference."""
        movements = await self.stock_movement_repository.get_by_reference(
            reference_type=reference_type,
            reference_id=reference_id
        )
        return [StockMovementResponse.model_validate(movement) for movement in movements]
    
    async def get_stock_movements_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        movement_type: Optional[MovementType] = None
    ) -> List[StockMovementResponse]:
        """Get stock movements within a date range."""
        movements = await self.stock_movement_repository.get_movements_by_date_range(
            start_date=start_date,
            end_date=end_date,
            item_id=item_id,
            location_id=location_id,
            movement_type=movement_type
        )
        return [StockMovementResponse.model_validate(movement) for movement in movements]
    
    async def get_stock_movement_summary(
        self,
        item_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> StockMovementSummaryResponse:
        """Get movement summary for an item."""
        summary = await self.stock_movement_repository.get_movement_summary(
            item_id=item_id,
            start_date=start_date,
            end_date=end_date
        )
        return StockMovementSummaryResponse.model_validate(summary)
    
    async def create_manual_stock_movement(
        self,
        stock_level_id: UUID,
        movement_type: MovementType,
        quantity_change: Decimal,
        reason: str,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> StockMovementResponse:
        """Create a manual stock movement record."""
        # Get current stock level
        stock_level = await self.stock_level_repository.get_by_id(stock_level_id)
        if not stock_level:
            raise NotFoundError(f"Stock level with ID {stock_level_id} not found")
        
        quantity_before = stock_level.quantity_on_hand
        
        # Update stock level
        stock_level.adjust_quantity(quantity_change, updated_by=created_by)
        await self.session.commit()
        await self.session.refresh(stock_level)
        
        quantity_after = stock_level.quantity_on_hand
        
        # Create movement record
        movement = await self._create_stock_movement_record(
            stock_level_id=stock_level_id,
            movement_type=movement_type.value,
            quantity_change=quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reference_type=ReferenceType.MANUAL_ADJUSTMENT,
            reference_id=f"MANUAL_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            reason=reason,
            notes=notes,
            created_by=created_by
        )
        
        return StockMovementResponse.model_validate(movement)
    
    async def rent_out_stock(
        self,
        stock_level_id: UUID,
        quantity: Decimal,
        transaction_id: str,
        updated_by: Optional[str] = None
    ) -> StockMovementResponse:
        """Move stock from available to on rent."""
        # Get current stock level
        stock_level = await self.stock_level_repository.get_by_id(stock_level_id)
        if not stock_level:
            raise NotFoundError(f"Stock level with ID {stock_level_id} not found")
        
        quantity_before = stock_level.quantity_available
        
        # Move quantity from available to on rent
        stock_level.rent_out_quantity(quantity, updated_by=updated_by)
        await self.session.commit()
        await self.session.refresh(stock_level)
        
        # Create movement record
        movement = await self._create_stock_movement_record(
            stock_level_id=stock_level_id,
            movement_type=MovementType.RENTAL_OUT.value,
            quantity_change=-quantity,  # Negative because it's leaving available
            quantity_before=quantity_before,
            quantity_after=stock_level.quantity_available,
            reference_type=ReferenceType.TRANSACTION,
            reference_id=transaction_id,
            reason=f"Rented out {quantity} units",
            created_by=updated_by
        )
        
        return StockMovementResponse.model_validate(movement)
    
    async def return_from_rent(
        self,
        stock_level_id: UUID,
        quantity: Decimal,
        transaction_id: str,
        updated_by: Optional[str] = None
    ) -> StockMovementResponse:
        """Move stock from on rent back to available."""
        # Get current stock level
        stock_level = await self.stock_level_repository.get_by_id(stock_level_id)
        if not stock_level:
            raise NotFoundError(f"Stock level with ID {stock_level_id} not found")
        
        quantity_before = stock_level.quantity_available
        
        # Move quantity from on rent to available
        stock_level.return_from_rent(quantity, updated_by=updated_by)
        await self.session.commit()
        await self.session.refresh(stock_level)
        
        # Create movement record
        movement = await self._create_stock_movement_record(
            stock_level_id=stock_level_id,
            movement_type=MovementType.RENTAL_RETURN.value,
            quantity_change=quantity,  # Positive because it's returning to available
            quantity_before=quantity_before,
            quantity_after=stock_level.quantity_available,
            reference_type=ReferenceType.TRANSACTION,
            reference_id=transaction_id,
            reason=f"Returned {quantity} units from rent",
            created_by=updated_by
        )
        
        return StockMovementResponse.model_validate(movement)
    
    # Item Inventory Overview and Detailed operations
    async def get_items_inventory_overview(
        self,
        params: ItemInventoryOverviewParams
    ) -> List[ItemInventoryOverview]:
        """Get inventory overview for multiple items - optimized for table display."""
        from sqlalchemy import select, func, case, and_, or_
        from sqlalchemy.orm import selectinload
        
        # Base query for items
        query = select(Item).options(
            selectinload(Item.brand),
            selectinload(Item.category),
            selectinload(Item.inventory_units),
            selectinload(Item.stock_levels)
        )
        
        # Apply filters
        filters = []
        if params.item_status:
            filters.append(Item.item_status == params.item_status.value)
        if params.brand_id:
            filters.append(Item.brand_id == params.brand_id)
        if params.category_id:
            filters.append(Item.category_id == params.category_id)
        if params.is_rentable is not None:
            filters.append(Item.is_rentable == params.is_rentable)
        if params.is_saleable is not None:
            filters.append(Item.is_saleable == params.is_saleable)
        if params.search:
            search_term = f"%{params.search}%"
            filters.append(
                or_(
                    Item.item_name.ilike(search_term),
                    Item.sku.ilike(search_term)
                )
            )
        
        # Always filter active items
        filters.append(Item.is_active == True)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Execute query
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        # Build overview list
        overview_list = []
        for item in items:
            # Calculate units by status
            units_by_status = UnitsByStatus()
            for unit in item.inventory_units:
                if unit.is_active:
                    status = unit.status.lower()
                    if hasattr(units_by_status, status):
                        setattr(units_by_status, status, getattr(units_by_status, status) + 1)
            
            # Calculate stock totals
            total_on_hand = Decimal("0")
            total_available = Decimal("0")
            total_on_rent = Decimal("0")
            
            for stock_level in item.stock_levels:
                if stock_level.is_active:
                    total_on_hand += stock_level.quantity_on_hand
                    total_available += stock_level.quantity_available
                    total_on_rent += stock_level.quantity_on_rent
            
            # Determine stock status
            if units_by_status.available == 0 and total_available == 0:
                stock_status = "OUT_OF_STOCK"
            elif item.is_low_stock():
                stock_status = "LOW_STOCK"
            else:
                stock_status = "IN_STOCK"
            
            overview = ItemInventoryOverview(
                id=item.id,
                sku=item.sku,
                item_name=item.item_name,
                item_status=item.item_status,
                brand_name=item.brand.name if item.brand else None,
                category_name=item.category.name if item.category else None,
                rental_rate_per_period=item.rental_rate_per_period,
                sale_price=item.sale_price,
                is_rentable=item.is_rentable,
                is_saleable=item.is_saleable,
                total_units=len([u for u in item.inventory_units if u.is_active]),
                units_by_status=units_by_status,
                total_quantity_on_hand=total_on_hand,
                total_quantity_available=total_available,
                total_quantity_on_rent=total_on_rent,
                stock_status=stock_status,
                reorder_point=item.reorder_point,
                is_low_stock=item.is_low_stock(),
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            overview_list.append(overview)
        
        # Apply stock status filter if specified
        if params.stock_status:
            overview_list = [o for o in overview_list if o.stock_status == params.stock_status]
        
        # Sort results
        sort_key = params.sort_by
        reverse = params.sort_order == "desc"
        
        if sort_key == "item_name":
            overview_list.sort(key=lambda x: x.item_name, reverse=reverse)
        elif sort_key == "sku":
            overview_list.sort(key=lambda x: x.sku, reverse=reverse)
        elif sort_key == "created_at":
            overview_list.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_key == "total_units":
            overview_list.sort(key=lambda x: x.total_units, reverse=reverse)
        elif sort_key == "stock_status":
            # Define sort order for stock status
            status_order = {"OUT_OF_STOCK": 0, "LOW_STOCK": 1, "IN_STOCK": 2}
            overview_list.sort(
                key=lambda x: status_order.get(x.stock_status, 3),
                reverse=reverse
            )
        
        # Apply pagination
        start = params.skip
        end = params.skip + params.limit
        return overview_list[start:end]
    
    async def get_item_inventory_detailed(self, item_id: UUID) -> ItemInventoryDetailed:
        """Get detailed inventory information for a single item."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Get item with all relationships
        query = select(Item).options(
            selectinload(Item.brand),
            selectinload(Item.category),
            selectinload(Item.unit_of_measurement),
            selectinload(Item.inventory_units),
            selectinload(Item.stock_levels),
            selectinload(Item.stock_movements)
        ).where(Item.id == item_id)
        
        result = await self.session.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            raise NotFoundError(f"Item with ID {item_id} not found")
        
        # Build units by status
        units_by_status = UnitsByStatus()
        inventory_unit_details = []
        
        # Get location data for units
        location_ids = set()
        for unit in item.inventory_units:
            if unit.is_active:
                location_ids.add(unit.location_id)
        
        # Fetch locations
        locations_map = {}
        if location_ids:
            loc_query = select(Location).where(Location.id.in_(location_ids))
            loc_result = await self.session.execute(loc_query)
            locations = loc_result.scalars().all()
            locations_map = {loc.id: loc.location_name for loc in locations}
        
        # Process inventory units
        for unit in item.inventory_units:
            if unit.is_active:
                status = unit.status.lower()
                if hasattr(units_by_status, status):
                    setattr(units_by_status, status, getattr(units_by_status, status) + 1)
                
                unit_detail = InventoryUnitDetail(
                    id=unit.id,
                    unit_code=unit.unit_code,
                    serial_number=unit.serial_number,
                    status=unit.status,
                    condition=unit.condition,
                    location_id=unit.location_id,
                    location_name=locations_map.get(unit.location_id, "Unknown"),
                    purchase_date=unit.purchase_date,
                    purchase_price=unit.purchase_price,
                    warranty_expiry=unit.warranty_expiry,
                    last_maintenance_date=unit.last_maintenance_date,
                    next_maintenance_date=unit.next_maintenance_date,
                    notes=unit.notes,
                    created_at=unit.created_at,
                    updated_at=unit.updated_at
                )
                inventory_unit_details.append(unit_detail)
        
        # Process stock levels by location
        stock_by_location = []
        total_on_hand = Decimal("0")
        total_available = Decimal("0")
        total_on_rent = Decimal("0")
        
        for stock_level in item.stock_levels:
            if stock_level.is_active:
                total_on_hand += stock_level.quantity_on_hand
                total_available += stock_level.quantity_available
                total_on_rent += stock_level.quantity_on_rent
                
                location_stock = LocationStockInfo(
                    location_id=stock_level.location_id,
                    location_name=locations_map.get(stock_level.location_id, "Unknown"),
                    quantity_on_hand=stock_level.quantity_on_hand,
                    quantity_available=stock_level.quantity_available,
                    quantity_on_rent=stock_level.quantity_on_rent
                )
                stock_by_location.append(location_stock)
        
        # Get recent movements (last 10)
        recent_movements = []
        if item.stock_movements:
            # Sort by created_at descending and take first 10
            sorted_movements = sorted(
                item.stock_movements,
                key=lambda x: x.created_at,
                reverse=True
            )[:10]
            
            # Get user names if needed
            user_ids = set()
            for movement in sorted_movements:
                if movement.created_by:
                    user_ids.add(movement.created_by)
            
            # For now, we'll use user IDs as names
            # In a real implementation, you'd fetch user names from the users tables
            
            for movement in sorted_movements:
                recent_movement = RecentMovement(
                    id=movement.id,
                    movement_type=movement.movement_type,
                    quantity_change=movement.quantity_change,
                    reason=movement.reason,
                    reference_type=movement.reference_type,
                    reference_id=movement.reference_id,
                    location_name=locations_map.get(movement.location_id, "Unknown"),
                    created_at=movement.created_at,
                    created_by_name=str(movement.created_by) if movement.created_by else None
                )
                recent_movements.append(recent_movement)
        
        # Determine stock status
        if units_by_status.available == 0 and total_available == 0:
            stock_status = "OUT_OF_STOCK"
        elif item.is_low_stock():
            stock_status = "LOW_STOCK"
        else:
            stock_status = "IN_STOCK"
        
        # Build detailed response
        detailed = ItemInventoryDetailed(
            id=item.id,
            sku=item.sku,
            item_name=item.item_name,
            item_status=item.item_status,
            brand_id=item.brand_id,
            brand_name=item.brand.name if item.brand else None,
            category_id=item.category_id,
            category_name=item.category.name if item.category else None,
            unit_of_measurement_id=item.unit_of_measurement_id,
            unit_of_measurement_name=item.unit_of_measurement.name if item.unit_of_measurement else "Unknown",
            description=item.description,
            specifications=item.specifications,
            model_number=item.model_number,
            serial_number_required=item.serial_number_required,
            warranty_period_days=item.warranty_period_days,
            rental_rate_per_period=item.rental_rate_per_period,
            rental_period=item.rental_period,
            sale_price=item.sale_price,
            purchase_price=item.purchase_price,
            security_deposit=item.security_deposit,
            is_rentable=item.is_rentable,
            is_saleable=item.is_saleable,
            total_units=len([u for u in item.inventory_units if u.is_active]),
            units_by_status=units_by_status,
            inventory_units=inventory_unit_details,
            stock_by_location=stock_by_location,
            total_quantity_on_hand=total_on_hand,
            total_quantity_available=total_available,
            total_quantity_on_rent=total_on_rent,
            reorder_point=item.reorder_point,
            stock_status=stock_status,
            is_low_stock=item.is_low_stock(),
            recent_movements=recent_movements,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
            created_by=item.created_by,
            updated_by=item.updated_by
        )
        
        return detailed