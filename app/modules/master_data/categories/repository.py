from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy import select, func, or_, and_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from .models import Category, CategoryPath
# from app.shared.pagination import Page


class CategoryRepository:
    """Repository for category data access operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, category_data: dict) -> Category:
        """Create a new category."""
        category = Category(**category_data)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Get category by ID."""
        query = select(Category).where(Category.id == category_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_name_and_parent(
        self, 
        name: str, 
        parent_id: Optional[UUID] = None
    ) -> Optional[Category]:
        """Get category by name and parent ID."""
        query = select(Category).where(
            and_(
                Category.name == name,
                Category.parent_category_id == parent_id
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_path(self, path: str) -> Optional[Category]:
        """Get category by full path."""
        query = select(Category).where(Category.category_path == path)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_root_categories(self) -> List[Category]:
        """Get all root categories."""
        query = select(Category).where(
            and_(
                Category.category_level == 1,
                Category.parent_category_id.is_(None),
                Category.is_active == True
            )
        ).order_by(Category.display_order, Category.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_children(self, parent_id: UUID) -> List[Category]:
        """Get direct children of a category."""
        query = select(Category).where(
            and_(
                Category.parent_category_id == parent_id,
                Category.is_active == True
            )
        ).order_by(Category.display_order, Category.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_descendants(self, category_id: UUID) -> List[Category]:
        """Get all descendants of a category."""
        parent_category = await self.get_by_id(category_id)
        if not parent_category:
            return []
        
        query = select(Category).where(
            and_(
                Category.category_path.like(f"{parent_category.category_path}/%"),
                Category.is_active == True
            )
        ).order_by(Category.category_path)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_ancestors(self, category_id: UUID) -> List[Category]:
        """Get all ancestors of a category."""
        category = await self.get_by_id(category_id)
        if not category or category.is_root():
            return []
        
        path_segments = category.get_path_segments()
        ancestors = []
        
        # Build paths for each ancestor
        for i in range(len(path_segments) - 1):
            ancestor_path = "/".join(path_segments[:i + 1])
            ancestor = await self.get_by_path(ancestor_path)
            if ancestor:
                ancestors.append(ancestor)
        
        return ancestors
    
    async def get_siblings(self, category_id: UUID) -> List[Category]:
        """Get sibling categories."""
        category = await self.get_by_id(category_id)
        if not category:
            return []
        
        query = select(Category).where(
            and_(
                Category.parent_category_id == category.parent_category_id,
                Category.id != category_id,
                Category.is_active == True
            )
        ).order_by(Category.display_order, Category.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_tree(self, root_id: Optional[UUID] = None) -> List[Category]:
        """Get hierarchical tree of categories."""
        if root_id:
            # Get tree starting from specific root
            root_category = await self.get_by_id(root_id)
            if not root_category:
                return []
            
            query = select(Category).where(
                and_(
                    or_(
                        Category.id == root_id,
                        Category.category_path.like(f"{root_category.category_path}/%")
                    ),
                    Category.is_active == True
                )
            ).order_by(Category.category_path)
        else:
            # Get full tree
            query = select(Category).where(
                Category.is_active == True
            ).order_by(Category.category_path)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        include_inactive: bool = False
    ) -> List[Category]:
        """List categories with optional filters and sorting."""
        query = select(Category)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Category.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(Category, sort_by)))
        else:
            query = query.order_by(asc(getattr(Category, sort_by)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        include_inactive: bool = False
    ) -> List[Category]:
        """Get paginated categories."""
        query = select(Category)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Category.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(Category, sort_by)))
        else:
            query = query.order_by(asc(getattr(Category, sort_by)))
        
        # Calculate pagination
        skip = (page - 1) * page_size
        limit = page_size
        
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update(self, category_id: UUID, update_data: dict) -> Optional[Category]:
        """Update existing category."""
        category = await self.get_by_id(category_id)
        if not category:
            return None
        
        # Update fields using the model's update method
        if 'name' in update_data or 'display_order' in update_data:
            category.update_info(
                name=update_data.get('name'),
                display_order=update_data.get('display_order'),
                updated_by=update_data.get('updated_by')
            )
        
        # Handle other fields
        if 'is_active' in update_data:
            category.is_active = update_data['is_active']
        
        if 'category_path' in update_data:
            category.update_path(
                update_data['category_path'],
                updated_by=update_data.get('updated_by')
            )
        
        if 'is_leaf' in update_data:
            if update_data['is_leaf']:
                category.mark_as_leaf(updated_by=update_data.get('updated_by'))
            else:
                category.mark_as_parent(updated_by=update_data.get('updated_by'))
        
        await self.session.commit()
        await self.session.refresh(category)
        
        return category
    
    async def move_category(
        self,
        category_id: UUID,
        new_parent_id: Optional[UUID],
        updated_by: Optional[str] = None
    ) -> Optional[Category]:
        """Move category to a new parent."""
        category = await self.get_by_id(category_id)
        if not category:
            return None
        
        # Get new parent if specified
        new_parent = None
        if new_parent_id:
            new_parent = await self.get_by_id(new_parent_id)
            if not new_parent:
                raise ValueError(f"New parent category {new_parent_id} not found")
        
        # Calculate new level and path
        if new_parent:
            new_level = new_parent.category_level + 1
            new_path = f"{new_parent.category_path}/{category.name}"
        else:
            new_level = 1
            new_path = category.name
        
        # Update category
        category.move_to_parent(
            new_parent_id=new_parent_id,
            new_level=new_level,
            new_path=new_path,
            updated_by=updated_by
        )
        
        # Update all descendants
        await self._update_descendant_paths(category)
        
        await self.session.commit()
        await self.session.refresh(category)
        
        return category
    
    async def delete(self, category_id: UUID) -> bool:
        """Soft delete category by setting is_active to False."""
        category = await self.get_by_id(category_id)
        if not category:
            return False
        
        category.is_active = False
        await self.session.commit()
        
        return True
    
    async def hard_delete(self, category_id: UUID) -> bool:
        """Hard delete category from database."""
        category = await self.get_by_id(category_id)
        if not category:
            return False
        
        # Check if category can be deleted
        if not category.can_delete():
            return False
        
        await self.session.delete(category)
        await self.session.commit()
        
        return True
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_inactive: bool = False
    ) -> int:
        """Count categories matching filters."""
        query = select(func.count()).select_from(Category)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Category.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_filters(query, filters)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def exists_by_name_and_parent(
        self, 
        name: str, 
        parent_id: Optional[UUID] = None,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if a category with the given name exists under the same parent."""
        query = select(func.count()).select_from(Category).where(
            and_(
                Category.name == name,
                Category.parent_category_id == parent_id
            )
        )
        
        if exclude_id:
            query = query.where(Category.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_path(self, path: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a category with the given path exists."""
        query = select(func.count()).select_from(Category).where(
            Category.category_path == path
        )
        
        if exclude_id:
            query = query.where(Category.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def search(
        self,
        search_term: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[Category]:
        """Search categories by name or path."""
        search_pattern = f"%{search_term}%"
        
        query = select(Category).where(
            or_(
                Category.name.ilike(search_pattern),
                Category.category_path.ilike(search_pattern)
            )
        )
        
        if not include_inactive:
            query = query.where(Category.is_active == True)
        
        query = query.order_by(Category.category_path).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_leaf_categories(self) -> List[Category]:
        """Get all leaf categories (categories with no children)."""
        query = select(Category).where(
            and_(
                Category.is_leaf == True,
                Category.is_active == True
            )
        ).order_by(Category.category_path)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_categories_by_level(self, level: int) -> List[Category]:
        """Get all categories at a specific level."""
        query = select(Category).where(
            and_(
                Category.category_level == level,
                Category.is_active == True
            )
        ).order_by(Category.category_path)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_categories_with_items(self) -> List[Category]:
        """Get categories that have items."""
        query = select(Category).where(
            and_(
                Category.items.any(),
                Category.is_active == True
            )
        ).order_by(Category.category_path)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_categories_without_items(self) -> List[Category]:
        """Get categories that have no items."""
        query = select(Category).where(
            and_(
                ~Category.items.any(),
                Category.is_active == True
            )
        ).order_by(Category.category_path)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def bulk_activate(self, category_ids: List[UUID]) -> int:
        """Activate multiple categories."""
        query = select(Category).where(Category.id.in_(category_ids))
        result = await self.session.execute(query)
        categories = result.scalars().all()
        
        count = 0
        for category in categories:
            if not category.is_active:
                category.is_active = True
                count += 1
        
        await self.session.commit()
        return count
    
    async def bulk_deactivate(self, category_ids: List[UUID]) -> int:
        """Deactivate multiple categories."""
        query = select(Category).where(Category.id.in_(category_ids))
        result = await self.session.execute(query)
        categories = result.scalars().all()
        
        count = 0
        for category in categories:
            if category.is_active:
                category.is_active = False
                count += 1
        
        await self.session.commit()
        return count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get category statistics."""
        # Count all categories
        total_query = select(func.count()).select_from(Category)
        total_result = await self.session.execute(total_query)
        total_categories = total_result.scalar_one()
        
        # Count active categories
        active_query = select(func.count()).select_from(Category).where(Category.is_active == True)
        active_result = await self.session.execute(active_query)
        active_categories = active_result.scalar_one()
        
        # Count root categories
        root_query = select(func.count()).select_from(Category).where(
            and_(Category.category_level == 1, Category.is_active == True)
        )
        root_result = await self.session.execute(root_query)
        root_categories = root_result.scalar_one()
        
        # Count leaf categories
        leaf_query = select(func.count()).select_from(Category).where(
            and_(Category.is_leaf == True, Category.is_active == True)
        )
        leaf_result = await self.session.execute(leaf_query)
        leaf_categories = leaf_result.scalar_one()
        
        # Get max depth
        max_depth_query = select(func.max(Category.category_level)).select_from(Category).where(
            Category.is_active == True
        )
        max_depth_result = await self.session.execute(max_depth_query)
        max_depth = max_depth_result.scalar_one() or 0
        
        # Count categories with items
        try:
            with_items_query = select(func.count()).select_from(Category).where(
                and_(Category.items.any(), Category.is_active == True)
            )
            with_items_result = await self.session.execute(with_items_query)
            categories_with_items = with_items_result.scalar_one()
        except:
            categories_with_items = 0
        
        # Calculate average children per category
        avg_children = 0
        if total_categories > 0:
            parent_categories = total_categories - root_categories
            if parent_categories > 0:
                avg_children = (total_categories - root_categories) / parent_categories
        
        return {
            "total_categories": total_categories,
            "active_categories": active_categories,
            "inactive_categories": total_categories - active_categories,
            "root_categories": root_categories,
            "leaf_categories": leaf_categories,
            "categories_with_items": categories_with_items,
            "categories_without_items": total_categories - categories_with_items,
            "max_depth": max_depth,
            "avg_children_per_category": avg_children
        }
    
    async def get_most_used_categories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get categories with most items."""
        # This will be implemented when items relationship is fully available
        # For now, return empty list
        return []
    
    async def update_display_orders(
        self, 
        category_orders: List[Tuple[UUID, int]]
    ) -> List[Category]:
        """Update display orders for multiple categories."""
        updated_categories = []
        
        for category_id, new_order in category_orders:
            category = await self.get_by_id(category_id)
            if category:
                category.display_order = new_order
                updated_categories.append(category)
        
        await self.session.commit()
        
        for category in updated_categories:
            await self.session.refresh(category)
        
        return updated_categories
    
    async def _update_descendant_paths(self, parent_category: Category):
        """Update paths for all descendants when parent is moved."""
        descendants = await self.get_descendants(parent_category.id)
        
        for descendant in descendants:
            # Calculate new path
            old_path_segments = descendant.get_path_segments()
            parent_path_segments = parent_category.get_path_segments()
            
            # Replace the parent part of the path
            descendant_relative_segments = old_path_segments[len(parent_path_segments):]
            new_path_segments = parent_path_segments + descendant_relative_segments
            new_path = "/".join(new_path_segments)
            
            # Update descendant
            descendant.category_path = new_path
            descendant.category_level = len(new_path_segments)
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        for key, value in filters.items():
            if value is None:
                continue
            
            if key == "name":
                query = query.where(Category.name.ilike(f"%{value}%"))
            elif key == "parent_id":
                query = query.where(Category.parent_category_id == value)
            elif key == "level":
                query = query.where(Category.category_level == value)
            elif key == "is_leaf":
                query = query.where(Category.is_leaf == value)
            elif key == "is_active":
                query = query.where(Category.is_active == value)
            elif key == "search":
                search_pattern = f"%{value}%"
                query = query.where(
                    or_(
                        Category.name.ilike(search_pattern),
                        Category.category_path.ilike(search_pattern)
                    )
                )
            elif key == "path_contains":
                query = query.where(Category.category_path.ilike(f"%{value}%"))
            elif key == "has_items":
                if value:
                    query = query.where(Category.items.any())
                else:
                    query = query.where(~Category.items.any())
            elif key == "has_children":
                if value:
                    query = query.where(Category.is_leaf == False)
                else:
                    query = query.where(Category.is_leaf == True)
            elif key == "created_after":
                query = query.where(Category.created_at >= value)
            elif key == "created_before":
                query = query.where(Category.created_at <= value)
            elif key == "updated_after":
                query = query.where(Category.updated_at >= value)
            elif key == "updated_before":
                query = query.where(Category.updated_at <= value)
            elif key == "created_by":
                query = query.where(Category.created_by == value)
            elif key == "updated_by":
                query = query.where(Category.updated_by == value)
        
        return query