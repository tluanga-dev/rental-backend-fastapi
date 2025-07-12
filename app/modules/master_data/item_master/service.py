from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.master_data.item_master.models import Item, ItemStatus
from app.modules.master_data.item_master.repository import ItemMasterRepository
from app.modules.master_data.item_master.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemListResponse, ItemWithInventoryResponse,
    SKUGenerationRequest, SKUGenerationResponse, SKUBulkGenerationResponse
)
from app.shared.utils.sku_generator import SKUGenerator


class ItemMasterService:
    """Service for item master data operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.item_repository = ItemMasterRepository(session)
        self.sku_generator = SKUGenerator(session)
    
    # Item operations
    async def create_item(self, item_data: ItemCreate) -> ItemResponse:
        """Create a new item with automatic SKU generation."""
        # Generate SKU automatically using new format
        sku = await self.sku_generator.generate_sku(
            category_id=item_data.category_id,
            item_name=item_data.item_name,
            is_rentable=item_data.is_rentable,
            is_saleable=item_data.is_saleable
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
    
    
    async def get_item_by_sku(self, sku: str) -> ItemResponse:
        """Get item by SKU."""
        item = await self.item_repository.get_by_sku(sku)
        if not item:
            raise NotFoundError(f"Item with SKU '{sku}' not found")
        return ItemResponse.model_validate(item)
    
    async def get_items(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        item_status: Optional[ItemStatus] = None,
        brand_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        is_rentable: Optional[bool] = None,
        is_saleable: Optional[bool] = None,
        active_only: bool = True
    ) -> List[ItemListResponse]:
        """Get all items with optional search and filtering."""
        items = await self.item_repository.get_all(
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
        
        return [ItemListResponse.model_validate(item) for item in items]
    
    async def count_items(
        self,
        search: Optional[str] = None,
        item_status: Optional[ItemStatus] = None,
        brand_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        is_rentable: Optional[bool] = None,
        is_saleable: Optional[bool] = None,
        active_only: bool = True
    ) -> int:
        """Count all items with optional search and filtering."""
        return await self.item_repository.count_all(
            search=search,
            item_status=item_status,
            brand_id=brand_id,
            category_id=category_id,
            is_rentable=is_rentable,
            is_saleable=is_saleable,
            active_only=active_only
        )
    
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
        # Get existing item
        existing_item = await self.item_repository.get_by_id(item_id)
        if not existing_item:
            raise NotFoundError(f"Item with ID {item_id} not found")
        
        # Validate pricing if boolean fields or pricing is being updated
        if any([
            item_data.is_rentable is not None,
            item_data.is_saleable is not None,
            item_data.rental_price_per_day is not None,
            item_data.sale_price is not None
        ]):
            self._validate_item_pricing_update(existing_item, item_data)
        
        # Update item
        updated_item = await self.item_repository.update(item_id, item_data)
        if not updated_item:
            raise NotFoundError(f"Item with ID {item_id} not found")
        
        return ItemResponse.model_validate(updated_item)
    
    async def delete_item(self, item_id: UUID) -> bool:
        """Delete (soft delete) an item."""
        success = await self.item_repository.delete(item_id)
        if not success:
            raise NotFoundError(f"Item with ID {item_id} not found")
        return success
    
    async def get_rental_items(self, active_only: bool = True) -> List[ItemListResponse]:
        """Get all rental items."""
        items = await self.item_repository.get_rental_items(active_only=active_only)
        return [ItemListResponse.model_validate(item) for item in items]
    
    async def get_sale_items(self, active_only: bool = True) -> List[ItemListResponse]:
        """Get all sale items."""
        items = await self.item_repository.get_sale_items(active_only=active_only)
        return [ItemListResponse.model_validate(item) for item in items]
    
    async def get_items_by_category(self, category_id: UUID, active_only: bool = True) -> List[ItemListResponse]:
        """Get all items in a specific category."""
        items = await self.item_repository.get_items_by_category(category_id, active_only=active_only)
        return [ItemListResponse.model_validate(item) for item in items]
    
    async def get_items_by_brand(self, brand_id: UUID, active_only: bool = True) -> List[ItemListResponse]:
        """Get all items for a specific brand."""
        items = await self.item_repository.get_items_by_brand(brand_id, active_only=active_only)
        return [ItemListResponse.model_validate(item) for item in items]
    
    async def get_low_stock_items(self, active_only: bool = True) -> List[ItemListResponse]:
        """Get items that need reordering based on reorder level."""
        items = await self.item_repository.get_low_stock_items(active_only=active_only)
        return [ItemListResponse.model_validate(item) for item in items]
    
    # SKU-specific operations
    async def generate_sku_preview(self, request: SKUGenerationRequest) -> SKUGenerationResponse:
        """Generate a preview of what SKU would be created."""
        sku = await self.sku_generator.preview_sku(
            category_id=request.category_id,
            item_name=request.item_name,
            is_rentable=request.is_rentable,
            is_saleable=request.is_saleable
        )
        
        # Extract components for response
        parts = sku.split('-')
        if len(parts) == 5:
            category_code, subcategory_code, product_code, attributes_code, sequence = parts
            sequence_number = int(sequence)
        else:
            category_code = "MISC"
            subcategory_code = "ITEM"
            product_code = parts[2] if len(parts) > 2 else "PROD"
            attributes_code = parts[3] if len(parts) > 3 else "R"
            sequence_number = 1
        
        return SKUGenerationResponse(
            sku=sku,
            category_code=category_code,
            subcategory_code=subcategory_code,
            product_code=product_code,
            attributes_code=attributes_code,
            sequence_number=sequence_number
        )
    
    async def bulk_generate_skus(self) -> SKUBulkGenerationResponse:
        """Generate SKUs for all existing items that don't have them."""
        result = await self.sku_generator.bulk_generate_skus_for_existing_items()
        return SKUBulkGenerationResponse(**result)
    
    # Helper methods
    def _validate_item_pricing(self, item_data: ItemCreate):
        """Validate item pricing based on boolean fields."""
        if item_data.is_rentable:
            if not item_data.rental_price_per_day:
                raise ValidationError("Rental price per day is required for rentable items")
        
        if item_data.is_saleable:
            if not item_data.sale_price:
                raise ValidationError("Sale price is required for saleable items")
    
    def _validate_item_pricing_update(self, existing_item: Item, item_data: ItemUpdate):
        """Validate item pricing for updates."""
        # Get effective boolean fields after update
        is_rentable = item_data.is_rentable if item_data.is_rentable is not None else existing_item.is_rentable
        is_saleable = item_data.is_saleable if item_data.is_saleable is not None else existing_item.is_saleable
        
        # Get effective pricing after update
        rental_price = item_data.rental_price_per_day if item_data.rental_price_per_day is not None else existing_item.rental_price_per_day
        sale_price = item_data.sale_price if item_data.sale_price is not None else existing_item.sale_price
        
        if is_rentable:
            if not rental_price:
                raise ValidationError("Rental price per day is required for rentable items")
        
        if is_saleable:
            if not sale_price:
                raise ValidationError("Sale price is required for saleable items")