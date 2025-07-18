from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy import and_, or_, func, select, update, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.modules.master_data.item_master.models import Item, ItemStatus
from app.modules.inventory.models import (
    InventoryUnit, StockLevel, StockMovement, InventoryUnitStatus, InventoryUnitCondition,
    MovementType, ReferenceType
)
from app.modules.master_data.item_master.schemas import ItemCreate, ItemUpdate
from app.modules.inventory.schemas import (
    InventoryUnitCreate, InventoryUnitUpdate, StockLevelCreate, StockLevelUpdate
)


class ItemRepository:
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
        if item_data.unit_of_measurement_id:
            item.unit_of_measurement_id = item_data.unit_of_measurement_id
        if item_data.supplier_id:
            item.supplier_id = item_data.supplier_id
        if item_data.rental_rate_per_period:
            item.rental_rate_per_period = item_data.rental_rate_per_period
        if item_data.rental_period:
            item.rental_period = item_data.rental_period
        if item_data.sale_price:
            item.sale_price = item_data.sale_price
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
        active_only: bool = True
    ) -> List[Item]:
        """Get all items with optional filtering."""
        query = select(Item)
        
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
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(asc(Item.item_name)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_all(
        self,
        item_status: Optional[ItemStatus] = None,
        brand_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> int:
        """Count all items with optional filtering."""
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
    
    async def get_items_by_brand(self, brand_id: UUID, active_only: bool = True) -> List[Item]:
        """Get items by brand."""
        query = select(Item).where(Item.brand_id == brand_id)
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_items_by_category(self, category_id: UUID, active_only: bool = True) -> List[Item]:
        """Get items by category."""
        query = select(Item).where(Item.category_id == category_id)
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name))
        
        result = await self.session.execute(query)
        return result.scalars().all()


class InventoryUnitRepository:
    """Repository for InventoryUnit operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, unit_data: InventoryUnitCreate) -> InventoryUnit:
        """Create a new inventory unit."""
        unit = InventoryUnit(
            item_id=str(unit_data.item_id),
            location_id=str(unit_data.location_id),
            unit_code=unit_data.unit_code,
            serial_number=unit_data.serial_number,
            status=unit_data.status,
            condition=unit_data.condition,
            purchase_price=unit_data.purchase_price
        )
        
        if unit_data.purchase_date:
            unit.purchase_date = unit_data.purchase_date
        if unit_data.warranty_expiry:
            unit.warranty_expiry = unit_data.warranty_expiry
        if unit_data.notes:
            unit.notes = unit_data.notes
        
        self.session.add(unit)
        await self.session.commit()
        await self.session.refresh(unit)
        return unit
    
    async def get_by_id(self, unit_id: UUID) -> Optional[InventoryUnit]:
        """Get inventory unit by ID."""
        query = select(InventoryUnit).where(InventoryUnit.id == unit_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_code(self, unit_code: str) -> Optional[InventoryUnit]:
        """Get inventory unit by code."""
        query = select(InventoryUnit).where(InventoryUnit.unit_code == unit_code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[InventoryUnitStatus] = None,
        condition: Optional[InventoryUnitCondition] = None,
        active_only: bool = True
    ) -> List[InventoryUnit]:
        """Get all inventory units with optional filtering."""
        query = select(InventoryUnit)
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(InventoryUnit.is_active == True)
        if item_id:
            conditions.append(InventoryUnit.item_id == str(item_id))
        if location_id:
            conditions.append(InventoryUnit.location_id == str(location_id))
        if status:
            conditions.append(InventoryUnit.status == status.value)
        if condition:
            conditions.append(InventoryUnit.condition == condition.value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(asc(InventoryUnit.unit_code)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_all(
        self,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[InventoryUnitStatus] = None,
        condition: Optional[InventoryUnitCondition] = None,
        active_only: bool = True
    ) -> int:
        """Count all inventory units with optional filtering."""
        query = select(func.count(InventoryUnit.id))
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(InventoryUnit.is_active == True)
        if item_id:
            conditions.append(InventoryUnit.item_id == str(item_id))
        if location_id:
            conditions.append(InventoryUnit.location_id == str(location_id))
        if status:
            conditions.append(InventoryUnit.status == status.value)
        if condition:
            conditions.append(InventoryUnit.condition == condition.value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def get_available_units(
        self, 
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None
    ) -> List[InventoryUnit]:
        """Get available inventory units."""
        query = select(InventoryUnit).where(
            and_(
                InventoryUnit.status == InventoryUnitStatus.AVAILABLE.value,
                InventoryUnit.is_active == True
            )
        )
        
        if item_id:
            query = query.where(InventoryUnit.item_id == str(item_id))
        if location_id:
            query = query.where(InventoryUnit.location_id == str(location_id))
        
        query = query.order_by(asc(InventoryUnit.unit_code))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rented_units(
        self, 
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None
    ) -> List[InventoryUnit]:
        """Get rented inventory units."""
        query = select(InventoryUnit).where(
            and_(
                InventoryUnit.status == InventoryUnitStatus.RENTED.value,
                InventoryUnit.is_active == True
            )
        )
        
        if item_id:
            query = query.where(InventoryUnit.item_id == str(item_id))
        if location_id:
            query = query.where(InventoryUnit.location_id == str(location_id))
        
        query = query.order_by(asc(InventoryUnit.unit_code))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_units_by_item(self, item_id: UUID, active_only: bool = True) -> List[InventoryUnit]:
        """Get inventory units by item."""
        query = select(InventoryUnit).where(InventoryUnit.item_id == str(item_id))
        
        if active_only:
            query = query.where(InventoryUnit.is_active == True)
        
        query = query.order_by(asc(InventoryUnit.unit_code))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_units_by_location(self, location_id: UUID, active_only: bool = True) -> List[InventoryUnit]:
        """Get inventory units by location."""
        query = select(InventoryUnit).where(InventoryUnit.location_id == str(location_id))
        
        if active_only:
            query = query.where(InventoryUnit.is_active == True)
        
        query = query.order_by(asc(InventoryUnit.unit_code))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_by_serial(self, serial_number: str, active_only: bool = True) -> List[InventoryUnit]:
        """Search inventory units by serial number."""
        query = select(InventoryUnit).where(
            InventoryUnit.serial_number.ilike(f"%{serial_number}%")
        )
        
        if active_only:
            query = query.where(InventoryUnit.is_active == True)
        
        query = query.order_by(asc(InventoryUnit.unit_code))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, unit_id: UUID, unit_data: InventoryUnitUpdate) -> Optional[InventoryUnit]:
        """Update an inventory unit."""
        query = select(InventoryUnit).where(InventoryUnit.id == unit_id)
        result = await self.session.execute(query)
        unit = result.scalar_one_or_none()
        
        if not unit:
            return None
        
        # Update fields
        update_data = unit_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(unit, field, value)
        
        await self.session.commit()
        await self.session.refresh(unit)
        return unit
    
    async def delete(self, unit_id: UUID) -> bool:
        """Soft delete an inventory unit."""
        query = select(InventoryUnit).where(InventoryUnit.id == unit_id)
        result = await self.session.execute(query)
        unit = result.scalar_one_or_none()
        
        if not unit:
            return False
        
        unit.is_active = False
        await self.session.commit()
        return True


class StockLevelRepository:
    """Repository for StockLevel operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, stock_data: StockLevelCreate) -> StockLevel:
        """Create a new stock level."""
        stock_level = StockLevel(
            item_id=str(stock_data.item_id),
            location_id=str(stock_data.location_id),
            quantity_on_hand=stock_data.quantity_on_hand
        )
        
        if stock_data.quantity_available:
            stock_level.quantity_available = stock_data.quantity_available
        if stock_data.quantity_on_rent:
            stock_level.quantity_on_rent = stock_data.quantity_on_rent
        
        self.session.add(stock_level)
        await self.session.commit()
        await self.session.refresh(stock_level)
        return stock_level
    
    async def get_by_id(self, stock_id: UUID) -> Optional[StockLevel]:
        """Get stock level by ID."""
        query = select(StockLevel).where(StockLevel.id == stock_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_item_location(self, item_id: UUID, location_id: UUID) -> Optional[StockLevel]:
        """Get stock level by item and location."""
        query = select(StockLevel).where(
            and_(
                StockLevel.item_id == str(item_id),
                StockLevel.location_id == str(location_id)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> List[StockLevel]:
        """Get all stock levels with optional filtering."""
        query = select(StockLevel)
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(StockLevel.is_active == True)
        if item_id:
            conditions.append(StockLevel.item_id == str(item_id))
        if location_id:
            conditions.append(StockLevel.location_id == str(location_id))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(asc(StockLevel.item_id)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_stock_levels_by_item(self, item_id: UUID, active_only: bool = True) -> List[StockLevel]:
        """Get stock levels by item."""
        query = select(StockLevel).where(StockLevel.item_id == str(item_id))
        
        if active_only:
            query = query.where(StockLevel.is_active == True)
        
        query = query.order_by(asc(StockLevel.location_id))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_stock_levels_by_location(self, location_id: UUID, active_only: bool = True) -> List[StockLevel]:
        """Get stock levels by location."""
        query = select(StockLevel).where(StockLevel.location_id == str(location_id))
        
        if active_only:
            query = query.where(StockLevel.is_active == True)
        
        query = query.order_by(asc(StockLevel.item_id))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_low_stock_items(self, active_only: bool = True) -> List[StockLevel]:
        """Get items with low stock (below configurable threshold)."""
        # Since reorder_point was removed, return empty list for now
        # This method can be enhanced later with configurable thresholds
        return []
    
    async def update(self, stock_id: UUID, stock_data: StockLevelUpdate) -> Optional[StockLevel]:
        """Update a stock level."""
        query = select(StockLevel).where(StockLevel.id == stock_id)
        result = await self.session.execute(query)
        stock_level = result.scalar_one_or_none()
        
        if not stock_level:
            return None
        
        # Update fields
        update_data = stock_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(stock_level, field, value)
        
        await self.session.commit()
        await self.session.refresh(stock_level)
        return stock_level
    
    async def delete(self, stock_id: UUID) -> bool:
        """Soft delete a stock level."""
        query = select(StockLevel).where(StockLevel.id == stock_id)
        result = await self.session.execute(query)
        stock_level = result.scalar_one_or_none()
        
        if not stock_level:
            return False
        
        stock_level.is_active = False
        await self.session.commit()
        return True


class StockMovementRepository:
    """Repository for StockMovement operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, movement_data: dict) -> StockMovement:
        """Create a new stock movement record."""
        movement = StockMovement(**movement_data)
        self.session.add(movement)
        await self.session.commit()
        await self.session.refresh(movement)
        return movement
    
    async def get_by_id(self, movement_id: UUID) -> Optional[StockMovement]:
        """Get stock movement by ID."""
        query = select(StockMovement).where(StockMovement.id == movement_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_stock_level(
        self,
        stock_level_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[StockMovement]:
        """Get stock movements for a specific stock level."""
        query = select(StockMovement).where(StockMovement.stock_level_id == stock_level_id)
        
        if active_only:
            query = query.where(StockMovement.is_active == True)
        
        query = query.order_by(desc(StockMovement.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_item(
        self,
        item_id: UUID,
        skip: int = 0,
        limit: int = 100,
        movement_type: Optional[MovementType] = None,
        active_only: bool = True
    ) -> List[StockMovement]:
        """Get stock movements for a specific item."""
        query = select(StockMovement).where(StockMovement.item_id == item_id)
        
        if movement_type:
            query = query.where(StockMovement.movement_type == movement_type.value)
        
        if active_only:
            query = query.where(StockMovement.is_active == True)
        
        query = query.order_by(desc(StockMovement.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_reference(
        self,
        reference_type: ReferenceType,
        reference_id: str,
        active_only: bool = True
    ) -> List[StockMovement]:
        """Get stock movements by reference."""
        query = select(StockMovement).where(
            and_(
                StockMovement.reference_type == reference_type.value,
                StockMovement.reference_id == reference_id
            )
        )
        
        if active_only:
            query = query.where(StockMovement.is_active == True)
        
        query = query.order_by(desc(StockMovement.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_movements_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        movement_type: Optional[MovementType] = None,
        active_only: bool = True
    ) -> List[StockMovement]:
        """Get stock movements within a date range with optional filters."""
        query = select(StockMovement).where(
            and_(
                StockMovement.created_at >= start_date,
                StockMovement.created_at <= end_date
            )
        )
        
        if item_id:
            query = query.where(StockMovement.item_id == item_id)
        
        if location_id:
            query = query.where(StockMovement.location_id == location_id)
        
        if movement_type:
            query = query.where(StockMovement.movement_type == movement_type.value)
        
        if active_only:
            query = query.where(StockMovement.is_active == True)
        
        query = query.order_by(desc(StockMovement.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_movement_summary(
        self,
        item_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get movement summary for an item."""
        query = select(StockMovement).where(StockMovement.item_id == item_id)
        
        if start_date:
            query = query.where(StockMovement.created_at >= start_date)
        
        if end_date:
            query = query.where(StockMovement.created_at <= end_date)
        
        query = query.where(StockMovement.is_active == True)
        
        result = await self.session.execute(query)
        movements = result.scalars().all()
        
        summary = {
            "total_movements": len(movements),
            "total_increases": sum(m.quantity_change for m in movements if m.quantity_change > 0),
            "total_decreases": abs(sum(m.quantity_change for m in movements if m.quantity_change < 0)),
            "net_change": sum(m.quantity_change for m in movements),
            "movement_types": {}
        }
        
        # Count by movement type
        for movement in movements:
            movement_type = movement.movement_type
            if movement_type not in summary["movement_types"]:
                summary["movement_types"][movement_type] = {
                    "count": 0,
                    "total_quantity": Decimal("0")
                }
            summary["movement_types"][movement_type]["count"] += 1
            summary["movement_types"][movement_type]["total_quantity"] += movement.quantity_change
        
        return summary