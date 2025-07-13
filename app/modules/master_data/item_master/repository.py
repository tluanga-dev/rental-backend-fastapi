from typing import Optional, List
from uuid import UUID
from sqlalchemy import and_, or_, func, select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master_data.item_master.models import Item, ItemStatus
from app.modules.master_data.item_master.schemas import ItemCreate, ItemUpdate


class ItemMasterRepository:
    """Repository for Item operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, item_data: ItemCreate, sku: str) -> Item:
        """Create a new item with SKU."""
        item = Item(
            sku=sku,
            item_name=item_data.item_name,
            item_status=item_data.item_status,
            is_rentable=item_data.is_rentable,
            is_saleable=item_data.is_saleable
        )
        
        # Set optional fields
        if item_data.brand_id:
            item.brand_id = item_data.brand_id
        if item_data.category_id:
            item.category_id = item_data.category_id
        # Set required field
        item.unit_of_measurement_id = item_data.unit_of_measurement_id
        if item_data.rental_rate_per_period:
            item.rental_rate_per_period = item_data.rental_rate_per_period
        if item_data.rental_period:
            item.rental_period = item_data.rental_period
        if item_data.sale_price:
            item.sale_price = item_data.sale_price
        if item_data.purchase_price is not None:
            item.purchase_price = item_data.purchase_price
        if item_data.security_deposit:
            item.security_deposit = item_data.security_deposit
        if item_data.description:
            item.description = item_data.description
        if item_data.specifications:
            item.specifications = item_data.specifications
        if item_data.model_number:
            item.model_number = item_data.model_number
        if item_data.serial_number_required:
            item.serial_number_required = item_data.serial_number_required
        if item_data.warranty_period_days:
            item.warranty_period_days = item_data.warranty_period_days
        if item_data.reorder_level:
            item.reorder_level = item_data.reorder_level
        if item_data.reorder_quantity:
            item.reorder_quantity = item_data.reorder_quantity
        
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item
    
    async def get_by_id(self, item_id: UUID) -> Optional[Item]:
        """Get item by ID."""
        query = select(Item).where(Item.id == item_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    
    async def get_by_sku(self, sku: str) -> Optional[Item]:
        """Get item by SKU."""
        query = select(Item).where(Item.sku == sku)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def exists_by_sku(self, sku: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if an item with the given SKU exists."""
        query = select(func.count()).select_from(Item).where(Item.sku == sku)
        
        if exclude_id:
            query = query.where(Item.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        return count > 0
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        item_status: Optional[ItemStatus] = None,
        brand_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        active_only: bool = True,
        # Date filters
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None
    ) -> List[Item]:
        """Get all items with essential filtering."""
        query = select(Item)
        
        # Apply essential filters only
        conditions = []
        if active_only:
            conditions.append(Item.is_active == True)
        if item_status:
            conditions.append(Item.item_status == item_status.value)
        if brand_id:
            conditions.append(Item.brand_id == brand_id)
        if category_id:
            conditions.append(Item.category_id == category_id)
        
        # Date range filters
        if created_after:
            from datetime import datetime
            created_after_dt = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
            conditions.append(Item.created_at >= created_after_dt)
        if created_before:
            from datetime import datetime
            created_before_dt = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
            conditions.append(Item.created_at <= created_before_dt)
        if updated_after:
            from datetime import datetime
            updated_after_dt = datetime.fromisoformat(updated_after.replace('Z', '+00:00'))
            conditions.append(Item.updated_at >= updated_after_dt)
        if updated_before:
            from datetime import datetime
            updated_before_dt = datetime.fromisoformat(updated_before.replace('Z', '+00:00'))
            conditions.append(Item.updated_at <= updated_before_dt)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(asc(Item.item_name)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_all(
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
        query = select(func.count(Item.id))
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(Item.is_active == True)
        if item_status:
            conditions.append(Item.item_status == item_status.value)
        if brand_id:
            conditions.append(Item.brand_id == brand_id)
        if category_id:
            conditions.append(Item.category_id == category_id)
        if is_rentable is not None:
            conditions.append(Item.is_rentable == is_rentable)
        if is_saleable is not None:
            conditions.append(Item.is_saleable == is_saleable)
        
        # Apply search
        if search:
            search_condition = or_(
                Item.item_name.ilike(f"%{search}%"),
                Item.sku.ilike(f"%{search}%"),
                Item.description.ilike(f"%{search}%")
            )
            conditions.append(search_condition)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def search(
        self, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[Item]:
        """Search items by name or code."""
        query = select(Item).where(
            or_(
                Item.item_name.ilike(f"%{search_term}%"),
                Item.sku.ilike(f"%{search_term}%"),
                Item.description.ilike(f"%{search_term}%")
            )
        )
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, item_id: UUID, item_data: ItemUpdate) -> Optional[Item]:
        """Update an item."""
        query = select(Item).where(Item.id == item_id)
        result = await self.session.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        # Update fields
        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        await self.session.commit()
        await self.session.refresh(item)
        return item
    
    async def delete(self, item_id: UUID) -> bool:
        """Soft delete an item."""
        query = select(Item).where(Item.id == item_id)
        result = await self.session.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        item.is_active = False
        await self.session.commit()
        return True
    
    async def get_rental_items(self, active_only: bool = True) -> List[Item]:
        """Get all rental items."""
        query = select(Item).where(Item.is_rentable == True)
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_sale_items(self, active_only: bool = True) -> List[Item]:
        """Get all sale items."""
        query = select(Item).where(Item.is_saleable == True)
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_items_by_category(self, category_id: UUID, active_only: bool = True) -> List[Item]:
        """Get all items in a specific category."""
        query = select(Item).where(Item.category_id == category_id)
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_items_by_brand(self, brand_id: UUID, active_only: bool = True) -> List[Item]:
        """Get all items for a specific brand."""
        query = select(Item).where(Item.brand_id == brand_id)
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_low_stock_items(self, active_only: bool = True) -> List[Item]:
        """Get items that need reordering based on reorder level."""
        # This would need to be enhanced with actual stock level logic
        query = select(Item).where(
            and_(
                Item.reorder_level != "0",
                Item.reorder_level.isnot(None)
            )
        )
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name))
        
        result = await self.session.execute(query)
        return result.scalars().all()