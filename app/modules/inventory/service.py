from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.master_data.item_master.models import Item, ItemStatus
from app.modules.master_data.locations.models import Location
from app.modules.inventory.models import (
    InventoryUnit, StockLevel, InventoryUnitStatus, InventoryUnitCondition
)
from app.modules.inventory.repository import (
    ItemRepository, InventoryUnitRepository, StockLevelRepository
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
    InventoryReport
)
from app.shared.utils.sku_generator import SKUGenerator


class InventoryService:
    """Service for inventory management operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.item_repository = ItemRepository(session)
        self.inventory_unit_repository = InventoryUnitRepository(session)
        self.stock_level_repository = StockLevelRepository(session)
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
                quantity_on_hand=str(quantity),
                quantity_available=str(quantity),
                quantity_reserved="0",
                quantity_on_order="0",
                minimum_level="0",
                maximum_level="0",
                reorder_point="0"
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