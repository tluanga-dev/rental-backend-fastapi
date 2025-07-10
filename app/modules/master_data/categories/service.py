from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from .repository import CategoryRepository
from .models import Category, CategoryPath
from .schemas import (
    CategoryCreate, CategoryUpdate, CategoryMove, CategoryResponse, 
    CategorySummary, CategoryTree, CategoryList, CategoryFilter, 
    CategorySort, CategoryStats, CategoryBulkOperation, CategoryBulkResult,
    CategoryExport, CategoryImport, CategoryImportResult, CategoryHierarchy,
    CategoryValidation
)
from app.shared.pagination import Page
from app.core.errors import (
    NotFoundError, ConflictError, ValidationError, 
    BusinessRuleError
)


class CategoryService:
    """Service layer for category business logic."""
    
    def __init__(self, repository: CategoryRepository):
        """Initialize service with repository."""
        self.repository = repository
    
    async def create_category(
        self,
        category_data: CategoryCreate,
        created_by: Optional[str] = None
    ) -> CategoryResponse:
        """Create a new category.
        
        Args:
            category_data: Category creation data
            created_by: User creating the category
            
        Returns:
            Created category response
            
        Raises:
            ConflictError: If category name already exists under same parent
            ValidationError: If category data is invalid
            NotFoundError: If parent category not found
        """
        # Check if parent exists
        parent_category = None
        if category_data.parent_category_id:
            parent_category = await self.repository.get_by_id(category_data.parent_category_id)
            if not parent_category:
                raise NotFoundError(f"Parent category with id {category_data.parent_category_id} not found")
        
        # Check for duplicate name under same parent
        if await self.repository.exists_by_name_and_parent(
            category_data.name, 
            category_data.parent_category_id
        ):
            parent_name = parent_category.name if parent_category else "root"
            raise ConflictError(f"Category with name '{category_data.name}' already exists under '{parent_name}'")
        
        # Calculate hierarchy details
        if parent_category:
            category_level = parent_category.category_level + 1
            category_path = f"{parent_category.category_path}/{category_data.name}"
            
            # Update parent to mark as non-leaf
            if parent_category.is_leaf:
                await self.repository.update(
                    parent_category.id,
                    {"is_leaf": False, "updated_by": created_by}
                )
        else:
            category_level = 1
            category_path = category_data.name
        
        # Prepare category data
        create_data = category_data.model_dump()
        create_data.update({
            "category_level": category_level,
            "category_path": category_path,
            "is_leaf": True,  # New categories are always leaf initially
            "created_by": created_by,
            "updated_by": created_by
        })
        
        # Create category
        category = await self.repository.create(create_data)
        
        # Convert to response
        return await self._to_response(category)
    
    async def get_category(self, category_id: UUID) -> CategoryResponse:
        """Get category by ID.
        
        Args:
            category_id: Category UUID
            
        Returns:
            Category response
            
        Raises:
            NotFoundError: If category not found
        """
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category with id {category_id} not found")
        
        return await self._to_response(category)
    
    async def get_category_by_path(self, path: str) -> CategoryResponse:
        """Get category by path.
        
        Args:
            path: Category path
            
        Returns:
            Category response
            
        Raises:
            NotFoundError: If category not found
        """
        category = await self.repository.get_by_path(path)
        if not category:
            raise NotFoundError(f"Category with path '{path}' not found")
        
        return await self._to_response(category)
    
    async def update_category(
        self,
        category_id: UUID,
        category_data: CategoryUpdate,
        updated_by: Optional[str] = None
    ) -> CategoryResponse:
        """Update an existing category.
        
        Args:
            category_id: Category UUID
            category_data: Category update data
            updated_by: User updating the category
            
        Returns:
            Updated category response
            
        Raises:
            NotFoundError: If category not found
            ConflictError: If name already exists under same parent
            ValidationError: If update data is invalid
        """
        # Get existing category
        existing_category = await self.repository.get_by_id(category_id)
        if not existing_category:
            raise NotFoundError(f"Category with id {category_id} not found")
        
        # Prepare update data
        update_data = {"updated_by": updated_by}
        path_update_needed = False
        
        # Check name uniqueness if provided
        if category_data.name is not None and category_data.name != existing_category.name:
            if await self.repository.exists_by_name_and_parent(
                category_data.name, 
                existing_category.parent_category_id,
                exclude_id=category_id
            ):
                raise ConflictError(f"Category with name '{category_data.name}' already exists under same parent")
            
            update_data["name"] = category_data.name
            path_update_needed = True
        
        # Update display order
        if category_data.display_order is not None:
            update_data["display_order"] = category_data.display_order
        
        # Update active status
        if category_data.is_active is not None:
            update_data["is_active"] = category_data.is_active
        
        # Update path if name changed
        if path_update_needed:
            parent_path = existing_category.get_parent_path()
            if parent_path:
                new_path = f"{parent_path}/{category_data.name}"
            else:
                new_path = category_data.name
            
            update_data["category_path"] = new_path
        
        # Update category
        updated_category = await self.repository.update(category_id, update_data)
        if not updated_category:
            raise NotFoundError(f"Category with id {category_id} not found")
        
        # Update descendant paths if name changed
        if path_update_needed:
            await self._update_descendant_paths_after_rename(updated_category)
        
        return await self._to_response(updated_category)
    
    async def move_category(
        self,
        category_id: UUID,
        move_data: CategoryMove,
        updated_by: Optional[str] = None
    ) -> CategoryResponse:
        """Move category to a new parent.
        
        Args:
            category_id: Category UUID
            move_data: Move operation data
            updated_by: User performing the move
            
        Returns:
            Updated category response
            
        Raises:
            NotFoundError: If category or new parent not found
            BusinessRuleError: If move would create cycle
        """
        # Get existing category
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category with id {category_id} not found")
        
        # Validate move operation
        await self._validate_move_operation(category, move_data.new_parent_id)
        
        # Update old parent if needed
        if category.parent_category_id:
            await self._update_parent_leaf_status(category.parent_category_id)
        
        # Move category
        moved_category = await self.repository.move_category(
            category_id=category_id,
            new_parent_id=move_data.new_parent_id,
            updated_by=updated_by
        )
        
        # Update display order
        if move_data.new_display_order != moved_category.display_order:
            await self.repository.update(
                category_id,
                {"display_order": move_data.new_display_order, "updated_by": updated_by}
            )
        
        # Update new parent if needed
        if move_data.new_parent_id:
            await self._update_parent_leaf_status(move_data.new_parent_id)
        
        return await self._to_response(moved_category)
    
    async def delete_category(self, category_id: UUID) -> bool:
        """Soft delete a category.
        
        Args:
            category_id: Category UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If category not found
            BusinessRuleError: If category has children or items
        """
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category with id {category_id} not found")
        
        # Check if category can be deleted
        if not category.can_delete():
            raise BusinessRuleError("Cannot delete category with children or items")
        
        success = await self.repository.delete(category_id)
        
        # Update parent leaf status if needed
        if success and category.parent_category_id:
            await self._update_parent_leaf_status(category.parent_category_id)
        
        return success
    
    async def get_category_tree(
        self,
        root_id: Optional[UUID] = None,
        include_inactive: bool = False
    ) -> List[CategoryTree]:
        """Get hierarchical category tree.
        
        Args:
            root_id: Root category ID (None for full tree)
            include_inactive: Include inactive categories
            
        Returns:
            List of category trees
        """
        # Get all categories in tree
        categories = await self.repository.get_tree(root_id)
        
        if not include_inactive:
            categories = [cat for cat in categories if cat.is_active]
        
        # Build tree structure
        category_dict = {cat.id: cat for cat in categories}
        tree_nodes = {}
        
        # Create tree nodes
        for category in categories:
            tree_node = CategoryTree(
                id=category.id,
                name=category.name,
                category_path=category.category_path,
                category_level=category.category_level,
                parent_category_id=category.parent_category_id,
                display_order=category.display_order,
                is_leaf=category.is_leaf,
                is_active=category.is_active,
                child_count=category.child_count,
                item_count=category.item_count,
                children=[]
            )
            tree_nodes[category.id] = tree_node
        
        # Build parent-child relationships
        root_nodes = []
        for category in categories:
            tree_node = tree_nodes[category.id]
            
            if category.parent_category_id and category.parent_category_id in tree_nodes:
                parent_node = tree_nodes[category.parent_category_id]
                parent_node.children.append(tree_node)
            else:
                root_nodes.append(tree_node)
        
        # Sort children by display order and name
        def sort_children(node):
            node.children.sort(key=lambda x: (x.display_order, x.name))
            for child in node.children:
                sort_children(child)
        
        for root in root_nodes:
            sort_children(root)
        
        # Sort root nodes
        root_nodes.sort(key=lambda x: (x.display_order, x.name))
        
        return root_nodes
    
    async def get_category_hierarchy(self, category_id: UUID) -> CategoryHierarchy:
        """Get category hierarchy information.
        
        Args:
            category_id: Category UUID
            
        Returns:
            Category hierarchy information
            
        Raises:
            NotFoundError: If category not found
        """
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category with id {category_id} not found")
        
        # Get ancestors
        ancestors = await self.repository.get_ancestors(category_id)
        ancestor_summaries = [await self._to_summary(cat) for cat in ancestors]
        
        # Get descendants
        descendants = await self.repository.get_descendants(category_id)
        descendant_summaries = [await self._to_summary(cat) for cat in descendants]
        
        # Get siblings
        siblings = await self.repository.get_siblings(category_id)
        sibling_summaries = [await self._to_summary(cat) for cat in siblings]
        
        # Build path to root
        path_to_root = ancestor_summaries + [await self._to_summary(category)]
        
        return CategoryHierarchy(
            category_id=category_id,
            ancestors=ancestor_summaries,
            descendants=descendant_summaries,
            siblings=sibling_summaries,
            depth=category.category_level,
            path_to_root=path_to_root
        )
    
    async def list_categories(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[CategoryFilter] = None,
        sort: Optional[CategorySort] = None,
        include_inactive: bool = False
    ) -> CategoryList:
        """List categories with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Items per page
            filters: Filter criteria
            sort: Sort options
            include_inactive: Include inactive categories
            
        Returns:
            Paginated category list
        """
        # Convert filters to dict
        filter_dict = {}
        if filters:
            filter_data = filters.model_dump(exclude_none=True)
            for key, value in filter_data.items():
                if value is not None:
                    filter_dict[key] = value
        
        # Set sort options
        sort_by = sort.field if sort else "name"
        sort_order = sort.direction if sort else "asc"
        
        # Get paginated categories
        page_result = await self.repository.get_paginated(
            page=page,
            page_size=page_size,
            filters=filter_dict,
            sort_by=sort_by,
            sort_order=sort_order,
            include_inactive=include_inactive
        )
        
        # Convert to summaries
        category_summaries = []
        for category in page_result.items:
            summary = await self._to_summary(category)
            category_summaries.append(summary)
        
        # Return list response
        return CategoryList(
            items=category_summaries,
            total=page_result.page_info.total_items,
            page=page_result.page_info.page,
            page_size=page_result.page_info.page_size,
            total_pages=page_result.page_info.total_pages,
            has_next=page_result.page_info.has_next,
            has_previous=page_result.page_info.has_previous
        )
    
    async def search_categories(
        self,
        search_term: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[CategorySummary]:
        """Search categories by name or path.
        
        Args:
            search_term: Search term
            limit: Maximum results
            include_inactive: Include inactive categories
            
        Returns:
            List of category summaries
        """
        categories = await self.repository.search(
            search_term=search_term,
            limit=limit,
            include_inactive=include_inactive
        )
        
        return [await self._to_summary(cat) for cat in categories]
    
    async def get_root_categories(self) -> List[CategorySummary]:
        """Get all root categories.
        
        Returns:
            List of root category summaries
        """
        categories = await self.repository.get_root_categories()
        return [await self._to_summary(cat) for cat in categories]
    
    async def get_leaf_categories(self) -> List[CategorySummary]:
        """Get all leaf categories.
        
        Returns:
            List of leaf category summaries
        """
        categories = await self.repository.get_leaf_categories()
        return [await self._to_summary(cat) for cat in categories]
    
    async def get_category_children(self, parent_id: UUID) -> List[CategorySummary]:
        """Get direct children of a category.
        
        Args:
            parent_id: Parent category ID
            
        Returns:
            List of child category summaries
            
        Raises:
            NotFoundError: If parent category not found
        """
        parent = await self.repository.get_by_id(parent_id)
        if not parent:
            raise NotFoundError(f"Parent category with id {parent_id} not found")
        
        children = await self.repository.get_children(parent_id)
        return [await self._to_summary(cat) for cat in children]
    
    async def get_category_statistics(self) -> CategoryStats:
        """Get category statistics.
        
        Returns:
            Category statistics
        """
        stats = await self.repository.get_statistics()
        most_used = await self.repository.get_most_used_categories()
        
        return CategoryStats(
            total_categories=stats["total_categories"],
            active_categories=stats["active_categories"],
            inactive_categories=stats["inactive_categories"],
            root_categories=stats["root_categories"],
            leaf_categories=stats["leaf_categories"],
            categories_with_items=stats["categories_with_items"],
            categories_without_items=stats["categories_without_items"],
            max_depth=stats["max_depth"],
            avg_children_per_category=stats["avg_children_per_category"],
            most_used_categories=most_used
        )
    
    async def bulk_operation(
        self,
        operation: CategoryBulkOperation,
        updated_by: Optional[str] = None
    ) -> CategoryBulkResult:
        """Perform bulk operations on categories.
        
        Args:
            operation: Bulk operation data
            updated_by: User performing the operation
            
        Returns:
            Bulk operation result
        """
        success_count = 0
        errors = []
        
        for category_id in operation.category_ids:
            try:
                if operation.operation == "activate":
                    count = await self.repository.bulk_activate([category_id])
                    success_count += count
                elif operation.operation == "deactivate":
                    count = await self.repository.bulk_deactivate([category_id])
                    success_count += count
                elif operation.operation == "delete":
                    category = await self.repository.get_by_id(category_id)
                    if category and category.can_delete():
                        await self.repository.delete(category_id)
                        success_count += 1
                    else:
                        errors.append({
                            "category_id": str(category_id),
                            "error": "Cannot delete category with children or items"
                        })
            except Exception as e:
                errors.append({
                    "category_id": str(category_id),
                    "error": str(e)
                })
        
        return CategoryBulkResult(
            success_count=success_count,
            failure_count=len(errors),
            errors=errors
        )
    
    async def export_categories(
        self,
        include_inactive: bool = False
    ) -> List[CategoryExport]:
        """Export categories data.
        
        Args:
            include_inactive: Include inactive categories
            
        Returns:
            List of category export data
        """
        categories = await self.repository.list(
            skip=0,
            limit=10000,  # Large limit for export
            include_inactive=include_inactive
        )
        
        export_data = []
        for category in categories:
            export_item = CategoryExport(
                id=category.id,
                name=category.name,
                parent_category_id=category.parent_category_id,
                category_path=category.category_path,
                category_level=category.category_level,
                display_order=category.display_order,
                is_leaf=category.is_leaf,
                is_active=category.is_active,
                created_at=category.created_at,
                updated_at=category.updated_at,
                created_by=category.created_by,
                updated_by=category.updated_by,
                child_count=category.child_count,
                item_count=category.item_count
            )
            export_data.append(export_item)
        
        return export_data
    
    async def import_categories(
        self,
        import_data: List[CategoryImport],
        created_by: Optional[str] = None
    ) -> CategoryImportResult:
        """Import categories data.
        
        Args:
            import_data: List of category import data
            created_by: User importing the data
            
        Returns:
            Import operation result
        """
        total_processed = len(import_data)
        successful_imports = 0
        failed_imports = 0
        skipped_imports = 0
        errors = []
        
        for row, category_data in enumerate(import_data, 1):
            try:
                # Find parent category if specified
                parent_id = None
                if category_data.parent_category_path:
                    parent_category = await self.repository.get_by_path(
                        category_data.parent_category_path
                    )
                    if parent_category:
                        parent_id = parent_category.id
                    else:
                        errors.append({
                            "row": row,
                            "error": f"Parent category '{category_data.parent_category_path}' not found"
                        })
                        failed_imports += 1
                        continue
                
                # Check if category already exists
                if await self.repository.exists_by_name_and_parent(
                    category_data.name, parent_id
                ):
                    skipped_imports += 1
                    continue
                
                # Create category
                create_request = CategoryCreate(
                    name=category_data.name,
                    parent_category_id=parent_id,
                    display_order=category_data.display_order
                )
                
                await self.create_category(create_request, created_by=created_by)
                successful_imports += 1
                
            except Exception as e:
                failed_imports += 1
                errors.append({
                    "row": row,
                    "error": str(e)
                })
        
        return CategoryImportResult(
            total_processed=total_processed,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            skipped_imports=skipped_imports,
            errors=errors
        )
    
    async def validate_category_operation(
        self,
        category_id: UUID,
        operation: str,
        data: Optional[Dict[str, Any]] = None
    ) -> CategoryValidation:
        """Validate category operation.
        
        Args:
            category_id: Category ID
            operation: Operation type (create/update/delete/move)
            data: Operation data
            
        Returns:
            Validation result
        """
        category = await self.repository.get_by_id(category_id)
        
        errors = []
        warnings = []
        can_create = True
        can_update = True
        can_delete = True
        can_move = True
        
        if operation == "delete":
            if category:
                if not category.can_delete():
                    can_delete = False
                    errors.append("Cannot delete category with children or items")
            else:
                can_delete = False
                errors.append("Category not found")
        
        elif operation == "move":
            if category and data and "new_parent_id" in data:
                try:
                    await self._validate_move_operation(category, data["new_parent_id"])
                except Exception as e:
                    can_move = False
                    errors.append(str(e))
        
        return CategoryValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            can_create=can_create,
            can_update=can_update,
            can_delete=can_delete,
            can_move=can_move
        )
    
    async def _validate_move_operation(
        self,
        category: Category,
        new_parent_id: Optional[UUID]
    ):
        """Validate move operation to prevent cycles."""
        if new_parent_id is None:
            return  # Moving to root is always valid
        
        # Check if new parent exists
        new_parent = await self.repository.get_by_id(new_parent_id)
        if not new_parent:
            raise NotFoundError(f"New parent category {new_parent_id} not found")
        
        # Check for cycle - new parent cannot be a descendant of current category
        if new_parent.is_descendant_of(category.category_path):
            raise BusinessRuleError("Cannot move category to its own descendant")
        
        # Check if moving to same parent
        if new_parent_id == category.parent_category_id:
            raise BusinessRuleError("Category is already under this parent")
    
    async def _update_parent_leaf_status(self, parent_id: UUID):
        """Update parent category leaf status based on children."""
        parent = await self.repository.get_by_id(parent_id)
        if not parent:
            return
        
        children = await self.repository.get_children(parent_id)
        active_children = [child for child in children if child.is_active]
        
        should_be_leaf = len(active_children) == 0
        
        if parent.is_leaf != should_be_leaf:
            await self.repository.update(
                parent_id,
                {"is_leaf": should_be_leaf}
            )
    
    async def _update_descendant_paths_after_rename(self, category: Category):
        """Update descendant paths after category rename."""
        descendants = await self.repository.get_descendants(category.id)
        
        for descendant in descendants:
            # Calculate new path
            old_segments = descendant.get_path_segments()
            category_segments = category.get_path_segments()
            
            # Replace the category part of the path
            descendant_relative_segments = old_segments[len(category_segments):]
            new_path_segments = category_segments + descendant_relative_segments
            new_path = "/".join(new_path_segments)
            
            # Update descendant
            await self.repository.update(
                descendant.id,
                {"category_path": new_path}
            )
    
    async def _to_response(self, category: Category) -> CategoryResponse:
        """Convert category model to response schema."""
        return CategoryResponse(
            id=category.id,
            name=category.name,
            parent_category_id=category.parent_category_id,
            category_path=category.category_path,
            category_level=category.category_level,
            display_order=category.display_order,
            is_leaf=category.is_leaf,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
            created_by=category.created_by,
            updated_by=category.updated_by,
            child_count=category.child_count,
            item_count=category.item_count,
            can_have_items=category.can_have_items(),
            can_have_children=category.can_have_children(),
            can_delete=category.can_delete(),
            is_root=category.is_root(),
            has_children=category.has_children,
            has_items=category.has_items,
            breadcrumb=category.get_breadcrumb(),
            full_name=category.full_name
        )
    
    async def _to_summary(self, category: Category) -> CategorySummary:
        """Convert category model to summary schema."""
        return CategorySummary(
            id=category.id,
            name=category.name,
            category_path=category.category_path,
            category_level=category.category_level,
            parent_category_id=category.parent_category_id,
            display_order=category.display_order,
            is_leaf=category.is_leaf,
            is_active=category.is_active,
            child_count=category.child_count,
            item_count=category.item_count
        )