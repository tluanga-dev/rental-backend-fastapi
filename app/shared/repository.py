from typing import Generic, TypeVar, Optional, List, Dict, Any, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.db.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common database operations."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_data)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get record by ID."""
        result = await self.session.get(self.model, id)
        return result
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        **filters
    ) -> List[ModelType]:
        """Get all records with optional filtering."""
        query = select(self.model)
        
        if active_only:
            query = query.where(self.model.is_active == True)
        
        # Apply additional filters
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, id: UUID, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update a record."""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        
        for key, value in obj_data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        db_obj.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: UUID) -> bool:
        """Soft delete a record."""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False
        
        db_obj.is_active = False
        db_obj.deleted_at = datetime.utcnow()
        await self.session.commit()
        return True
    
    async def hard_delete(self, id: UUID) -> bool:
        """Hard delete a record."""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False
        
        await self.session.delete(db_obj)
        await self.session.commit()
        return True
    
    async def count_all(self, active_only: bool = True, **filters) -> int:
        """Count all records with optional filtering."""
        query = select(func.count(self.model.id))
        
        if active_only:
            query = query.where(self.model.is_active == True)
        
        # Apply additional filters
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def exists(self, id: UUID) -> bool:
        """Check if record exists."""
        query = select(func.count(self.model.id)).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar() > 0
    
    async def bulk_create(self, objs_data: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records."""
        db_objs = [self.model(**obj_data) for obj_data in objs_data]
        self.session.add_all(db_objs)
        await self.session.commit()
        
        # Refresh all objects
        for db_obj in db_objs:
            await self.session.refresh(db_obj)
        
        return db_objs
    
    async def bulk_update(
        self,
        updates: List[Dict[str, Any]],
        key_field: str = "id"
    ) -> int:
        """Bulk update records."""
        if not updates:
            return 0
        
        stmt = update(self.model)
        
        # Execute bulk update
        for update_data in updates:
            key_value = update_data.pop(key_field)
            update_data['updated_at'] = datetime.utcnow()
            
            await self.session.execute(
                stmt.where(getattr(self.model, key_field) == key_value).values(**update_data)
            )
        
        await self.session.commit()
        return len(updates)
    
    async def bulk_delete(self, ids: List[UUID]) -> int:
        """Bulk soft delete records."""
        if not ids:
            return 0
        
        stmt = update(self.model).where(
            self.model.id.in_(ids)
        ).values(
            is_active=False,
            deleted_at=datetime.utcnow()
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_hard_delete(self, ids: List[UUID]) -> int:
        """Bulk hard delete records."""
        if not ids:
            return 0
        
        stmt = delete(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
    
    async def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """Get record by specific field."""
        if not hasattr(self.model, field_name):
            return None
        
        query = select(self.model).where(getattr(self.model, field_name) == value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_fields(self, **filters) -> Optional[ModelType]:
        """Get record by multiple fields."""
        query = select(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[ModelType]:
        """Search records by multiple fields."""
        from sqlalchemy import or_
        
        query = select(self.model)
        
        # Create search conditions
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                if hasattr(field_attr.type, 'python_type') and field_attr.type.python_type == str:
                    search_conditions.append(field_attr.ilike(f"%{search_term}%"))
        
        if search_conditions:
            query = query.where(or_(*search_conditions))
        
        if active_only:
            query = query.where(self.model.is_active == True)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_with_relationships(
        self,
        id: UUID,
        relationships: List[str]
    ) -> Optional[ModelType]:
        """Get record with eagerly loaded relationships."""
        query = select(self.model).where(self.model.id == id)
        
        for rel in relationships:
            if hasattr(self.model, rel):
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        active_only: bool = True,
        **filters
    ) -> Dict[str, Any]:
        """Get paginated results."""
        skip = (page - 1) * page_size
        
        # Get total count
        total = await self.count_all(active_only=active_only, **filters)
        
        # Get items
        items = await self.get_all(
            skip=skip,
            limit=page_size,
            active_only=active_only,
            **filters
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }