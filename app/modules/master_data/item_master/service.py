from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import time
import logging

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
        self.logger = logging.getLogger(__name__)
    
    # Item operations
    async def create_item(self, item_data: ItemCreate) -> ItemResponse:
        """Create a new item with automatic SKU generation."""
        start_time = time.time()
        self.logger.info(f"Starting item creation for: {item_data.item_name}")
        
        try:
            # Generate SKU automatically using new format
            sku_start = time.time()
            sku = await self.sku_generator.generate_sku(
                category_id=item_data.category_id,
                item_name=item_data.item_name,
                is_rentable=item_data.is_rentable,
                is_saleable=item_data.is_saleable
            )
            sku_time = time.time() - sku_start
            self.logger.info(f"SKU generation completed in {sku_time:.3f}s. SKU: {sku}")
            
            # Validate item type and pricing
            validation_start = time.time()
            self._validate_item_pricing(item_data)
            validation_time = time.time() - validation_start
            self.logger.debug(f"Item validation completed in {validation_time:.3f}s")
            
            # Extract initial stock quantity before creating item
            initial_stock_quantity = item_data.initial_stock_quantity
            item_data_dict = item_data.model_dump()
            # Remove initial_stock_quantity as it's not a model field
            item_data_dict.pop('initial_stock_quantity', None)
            
            # Create ItemCreate without initial_stock_quantity
            from app.modules.master_data.item_master.schemas import ItemCreate as ItemCreateClean
            item_data_clean = ItemCreateClean(**item_data_dict)
            
            # Create item with generated SKU
            db_start = time.time()
            item = await self.item_repository.create(item_data_clean, sku)
            db_time = time.time() - db_start
            self.logger.info(f"Database insertion completed in {db_time:.3f}s")
            
            # Create initial stock if specified
            if initial_stock_quantity and initial_stock_quantity > 0:
                try:
                    # Import inventory service to create initial stock
                    from app.modules.inventory.service import InventoryService
                    
                    inventory_service = InventoryService(self.session)
                    stock_result = await inventory_service.create_initial_stock(
                        item_id=item.id,
                        item_sku=sku,
                        purchase_price=item_data.purchase_price,
                        quantity=initial_stock_quantity
                    )
                    
                    if stock_result.get("created"):
                        self.logger.info(
                            f"Created initial stock: {stock_result['total_quantity']} units "
                            f"at {stock_result['location_name']} for item {item.id}. "
                            f"Unit codes: {', '.join(stock_result['unit_codes'])}"
                        )
                    else:
                        self.logger.warning(
                            f"Failed to create initial stock: {stock_result.get('reason', 'Unknown error')}"
                        )
                except Exception as stock_error:
                    self.logger.error(f"Exception during initial stock creation: {str(stock_error)}")
                    # Don't fail item creation if stock creation fails
            
            total_time = time.time() - start_time
            self.logger.info(f"Item creation completed successfully in {total_time:.3f}s. Item ID: {item.id}")
            
            return ItemResponse.model_validate(item)
            
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"Item creation failed after {total_time:.3f}s: {str(e)}")
            raise
    
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
        category_id: Optional[UUID] = None,
        brand_id: Optional[UUID] = None,
        item_status: Optional[ItemStatus] = None,
        active_only: bool = True,
        # Date filters
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None
    ) -> List[ItemListResponse]:
        """Get all items with essential filtering."""
        items = await self.item_repository.get_all(
            skip=skip,
            limit=limit,
            item_status=item_status,
            brand_id=brand_id,
            category_id=category_id,
            active_only=active_only,
            # Date filters
            created_after=created_after,
            created_before=created_before,
            updated_after=updated_after,
            updated_before=updated_before
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
            item_data.rental_rate_per_period is not None,
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
        rental_rate = item_data.rental_rate_per_period if item_data.rental_rate_per_period is not None else existing_item.rental_rate_per_period
        sale_price = item_data.sale_price if item_data.sale_price is not None else existing_item.sale_price
        
        if is_rentable:
            if not rental_rate:
                raise ValidationError("Rental rate per period is required for rentable items")
        
        if is_saleable:
            if not sale_price:
                raise ValidationError("Sale price is required for saleable items")