from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy import and_, or_, func, select, asc, case, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
        
        # Set reorder_point (mandatory field)
        item.reorder_point = item_data.reorder_point
        
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item
    
    async def get_by_id(self, item_id: UUID) -> Optional[Item]:
        """Get item by ID."""
        query = select(Item).where(Item.id == item_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id_with_relations(self, item_id: UUID) -> Optional[Item]:
        """Get item by ID with relationships loaded."""
        query = (
            select(Item)
            .options(
                selectinload(Item.brand),
                selectinload(Item.category),
                selectinload(Item.unit_of_measurement),
                selectinload(Item.inventory_units),
                selectinload(Item.stock_levels)
            )
            .where(Item.id == item_id)
        )
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
    
    async def get_all_with_relations(
        self, 
        skip: int = 0, 
        limit: int = 100,
        item_status: Optional[ItemStatus] = None,
        brand_ids: Optional[List[UUID]] = None,
        category_ids: Optional[List[UUID]] = None,
        active_only: bool = True,
        # Additional filters
        is_rentable: Optional[bool] = None,
        is_saleable: Optional[bool] = None,
        min_rental_rate: Optional[Decimal] = None,
        max_rental_rate: Optional[Decimal] = None,
        min_sale_price: Optional[Decimal] = None,
        max_sale_price: Optional[Decimal] = None,
        has_stock: Optional[bool] = None,
        search_term: Optional[str] = None,
        # Date filters
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all items with relationship data and inventory aggregation."""
        from app.modules.master_data.brands.models import Brand
        from app.modules.master_data.categories.models import Category
        from app.modules.master_data.units.models import UnitOfMeasurement
        from app.modules.inventory.models import InventoryUnit, InventoryUnitStatus
        
        # Build base query with JOINs for relationship data
        query = (
            select(
                Item,
                Brand.name.label("brand_name"),
                Brand.code.label("brand_code"),
                Brand.description.label("brand_description"),
                Category.name.label("category_name"),
                Category.category_path,
                Category.category_level.label("category_level"),
                UnitOfMeasurement.name.label("unit_name"),
                UnitOfMeasurement.abbreviation,
                func.count(InventoryUnit.id).label("total_units"),
                func.sum(
                    case(
                        (InventoryUnit.status == InventoryUnitStatus.AVAILABLE.value, 1),
                        else_=0
                    )
                ).label("available_units"),
                func.sum(
                    case(
                        (InventoryUnit.status == InventoryUnitStatus.RENTED.value, 1),
                        else_=0
                    )
                ).label("rented_units")
            )
            .outerjoin(Brand, Item.brand_id == Brand.id)
            .outerjoin(Category, Item.category_id == Category.id)
            .outerjoin(UnitOfMeasurement, Item.unit_of_measurement_id == UnitOfMeasurement.id)
            .outerjoin(InventoryUnit, Item.id == InventoryUnit.item_id)
            .group_by(Item.id, Brand.id, Category.id, UnitOfMeasurement.id)
        )
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(Item.is_active == True)
        if item_status:
            conditions.append(Item.item_status == item_status.value)
        if brand_ids:
            conditions.append(Item.brand_id.in_(brand_ids))
        if category_ids:
            conditions.append(Item.category_id.in_(category_ids))
        if is_rentable is not None:
            conditions.append(Item.is_rentable == is_rentable)
        if is_saleable is not None:
            conditions.append(Item.is_saleable == is_saleable)
        if min_rental_rate:
            conditions.append(Item.rental_rate_per_period >= min_rental_rate)
        if max_rental_rate:
            conditions.append(Item.rental_rate_per_period <= max_rental_rate)
        if min_sale_price:
            conditions.append(Item.sale_price >= min_sale_price)
        if max_sale_price:
            conditions.append(Item.sale_price <= max_sale_price)
        
        # Search functionality enhanced
        if search_term:
            search_condition = or_(
                Item.item_name.ilike(f"%{search_term}%"),
                Item.sku.ilike(f"%{search_term}%"),
                Item.description.ilike(f"%{search_term}%"),
                Item.model_number.ilike(f"%{search_term}%"),
                Item.specifications.ilike(f"%{search_term}%"),
                Brand.name.ilike(f"%{search_term}%"),
                Category.name.ilike(f"%{search_term}%")
            )
            conditions.append(search_condition)
        
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
        
        # Apply stock filter after grouping
        if has_stock is not None:
            if has_stock:
                query = query.having(func.count(InventoryUnit.id) > 0)
            else:
                query = query.having(func.count(InventoryUnit.id) == 0)
        
        query = query.order_by(asc(Item.item_name)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        # Convert to list of dictionaries with all data
        items_data = []
        for row in rows:
            item = row[0]  # Item object
            item_dict = {
                # Basic item fields
                "id": item.id,
                "sku": item.sku,
                "item_name": item.item_name,
                "item_status": item.item_status,
                "brand_id": item.brand_id,
                "category_id": item.category_id,
                "unit_of_measurement_id": item.unit_of_measurement_id,
                "rental_rate_per_period": item.rental_rate_per_period,
                "rental_period": item.rental_period,
                "sale_price": item.sale_price,
                "purchase_price": item.purchase_price,
                "security_deposit": item.security_deposit,
                "description": item.description,
                "specifications": item.specifications,
                "model_number": item.model_number,
                "serial_number_required": item.serial_number_required,
                "warranty_period_days": item.warranty_period_days,
                "reorder_point": item.reorder_point,
                "is_rentable": item.is_rentable,
                "is_saleable": item.is_saleable,
                "is_active": item.is_active,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                # Relationship data
                "brand_name": row[1],
                "brand_code": row[2],
                "brand_description": row[3],
                "category_name": row[4],
                "category_path": row[5],
                "category_level": row[6],
                "unit_name": row[7],
                "unit_abbreviation": row[8],
                # Inventory summary
                "total_units": row[9] or 0,
                "available_units": row[10] or 0,
                "rented_units": row[11] or 0,
            }
            items_data.append(item_dict)
        
        return items_data
    
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
    
    async def get_low_stock_items_legacy(self, active_only: bool = True) -> List[Item]:
        """Legacy method - use get_low_stock_items instead."""
        query = select(Item).where(
            and_(
                Item.reorder_point > 0,
                Item.is_active == True
            )
        )
        
        if active_only:
            query = query.where(Item.is_active == True)
        
        query = query.order_by(asc(Item.item_name))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_all_with_nested_relations(
        self, 
        skip: int = 0, 
        limit: int = 100,
        item_status: Optional[ItemStatus] = None,
        brand_ids: Optional[List[UUID]] = None,
        category_ids: Optional[List[UUID]] = None,
        active_only: bool = True,
        # Additional filters
        is_rentable: Optional[bool] = None,
        is_saleable: Optional[bool] = None,
        min_rental_rate: Optional[Decimal] = None,
        max_rental_rate: Optional[Decimal] = None,
        min_sale_price: Optional[Decimal] = None,
        max_sale_price: Optional[Decimal] = None,
        has_stock: Optional[bool] = None,
        search_term: Optional[str] = None,
        # Date filters
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None
    ) -> List[Item]:
        """Get all items with eagerly loaded relationships for nested response."""
        from app.modules.master_data.brands.models import Brand
        from app.modules.master_data.categories.models import Category
        from app.modules.master_data.units.models import UnitOfMeasurement
        
        # Build query with eager loading
        query = (
            select(Item)
            .options(
                selectinload(Item.brand),
                selectinload(Item.category),
                selectinload(Item.unit_of_measurement)
            )
        )
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(Item.is_active == True)
        if item_status:
            conditions.append(Item.item_status == item_status.value)
        if brand_ids:
            conditions.append(Item.brand_id.in_(brand_ids))
        if category_ids:
            conditions.append(Item.category_id.in_(category_ids))
        if is_rentable is not None:
            conditions.append(Item.is_rentable == is_rentable)
        if is_saleable is not None:
            conditions.append(Item.is_saleable == is_saleable)
        if min_rental_rate:
            conditions.append(Item.rental_rate_per_period >= min_rental_rate)
        if max_rental_rate:
            conditions.append(Item.rental_rate_per_period <= max_rental_rate)
        if min_sale_price:
            conditions.append(Item.sale_price >= min_sale_price)
        if max_sale_price:
            conditions.append(Item.sale_price <= max_sale_price)
        
        # Search functionality
        if search_term:
            # Need to join for search in related tables
            query = query.outerjoin(Brand, Item.brand_id == Brand.id)
            query = query.outerjoin(Category, Item.category_id == Category.id)
            
            search_condition = or_(
                Item.item_name.ilike(f"%{search_term}%"),
                Item.sku.ilike(f"%{search_term}%"),
                Item.description.ilike(f"%{search_term}%"),
                Item.model_number.ilike(f"%{search_term}%"),
                Item.specifications.ilike(f"%{search_term}%"),
                Brand.name.ilike(f"%{search_term}%"),
                Category.name.ilike(f"%{search_term}%")
            )
            conditions.append(search_condition)
        
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
        return result.scalars().unique().all()
    
    async def get_low_stock_items(
        self, 
        location_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Item]:
        """
        Get items with stock levels at or below their reorder point.
        Uses efficient JOIN with StockLevel table.
        """
        from app.modules.inventory.models import StockLevel
        
        # Build query with JOIN between items and stock_levels
        query = select(Item).join(
            StockLevel, Item.id == StockLevel.item_id
        ).where(
            and_(
                Item.is_active == True,
                Item.reorder_point > 0,  # Only include items with configured reorder points
                func.cast(StockLevel.quantity_available, Integer) <= Item.reorder_point
            )
        )
        
        # Add location filter if specified
        if location_id:
            query = query.where(StockLevel.location_id == location_id)
        
        # Add pagination
        query = query.order_by(
            # Order by urgency: out of stock first, then by how far below reorder point
            asc(func.cast(StockLevel.quantity_available, Integer)),
            asc(Item.item_name)
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().unique().all()
    
    async def get_stock_alerts_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for stock alerts.
        """
        from app.modules.inventory.models import StockLevel
        
        # Count items that are out of stock
        out_of_stock_query = select(func.count(Item.id.distinct())).select_from(
            Item.__table__.join(StockLevel.__table__, Item.id == StockLevel.item_id)
        ).where(
            and_(
                Item.is_active == True,
                func.cast(StockLevel.quantity_available, Integer) == 0
            )
        )
        
        # Count items that are low stock (at or below reorder point, but not zero)
        low_stock_query = select(func.count(Item.id.distinct())).select_from(
            Item.__table__.join(StockLevel.__table__, Item.id == StockLevel.item_id)
        ).where(
            and_(
                Item.is_active == True,
                Item.reorder_point > 0,
                func.cast(StockLevel.quantity_available, Integer) > 0,
                func.cast(StockLevel.quantity_available, Integer) <= Item.reorder_point
            )
        )
        
        # Count total active items
        total_items_query = select(func.count(Item.id)).where(Item.is_active == True)
        
        # Average reorder point
        avg_reorder_point_query = select(func.avg(Item.reorder_point)).where(
            and_(Item.is_active == True, Item.reorder_point > 0)
        )
        
        # Execute all queries
        out_of_stock_result = await self.session.execute(out_of_stock_query)
        low_stock_result = await self.session.execute(low_stock_query)
        total_items_result = await self.session.execute(total_items_query)
        avg_reorder_result = await self.session.execute(avg_reorder_point_query)
        
        return {
            "out_of_stock": out_of_stock_result.scalar() or 0,
            "low_stock": low_stock_result.scalar() or 0,
            "total_items": total_items_result.scalar() or 0,
            "avg_reorder_point": float(avg_reorder_result.scalar() or 0)
        }