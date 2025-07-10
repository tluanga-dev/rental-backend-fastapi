from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, validator
from datetime import datetime
from uuid import UUID


class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    parent_category_id: Optional[UUID] = Field(None, description="Parent category ID")
    display_order: int = Field(0, ge=0, description="Display order within parent")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    display_order: Optional[int] = Field(None, ge=0, description="Display order within parent")
    is_active: Optional[bool] = Field(None, description="Category active status")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Category name cannot be empty')
            return v.strip()
        return v


class CategoryMove(BaseModel):
    """Schema for moving a category to a new parent."""
    
    new_parent_id: Optional[UUID] = Field(None, description="New parent category ID (None for root)")
    new_display_order: int = Field(0, ge=0, description="Display order in new parent")


class CategoryResponse(CategoryBase):
    """Schema for category response with all fields."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Category unique identifier")
    category_path: str = Field(..., description="Full category path")
    category_level: int = Field(..., ge=1, description="Category hierarchy level")
    is_leaf: bool = Field(..., description="True if category has no children")
    is_active: bool = Field(True, description="Category active status")
    created_at: datetime = Field(..., description="Category creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Category last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the category")
    updated_by: Optional[str] = Field(None, description="User who last updated the category")
    
    # Computed fields
    child_count: int = Field(0, description="Number of direct children")
    item_count: int = Field(0, description="Number of items in this category")
    can_have_items: bool = Field(True, description="Whether category can have items")
    can_have_children: bool = Field(True, description="Whether category can have children")
    can_delete: bool = Field(False, description="Whether category can be deleted")
    is_root: bool = Field(False, description="Whether this is a root category")
    has_children: bool = Field(False, description="Whether category has children")
    has_items: bool = Field(False, description="Whether category has items")
    breadcrumb: List[str] = Field(default_factory=list, description="Breadcrumb trail")
    full_name: str = Field(..., description="Full category name with path")


class CategorySummary(BaseModel):
    """Schema for category summary with minimal fields."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Category unique identifier")
    name: str = Field(..., description="Category name")
    category_path: str = Field(..., description="Full category path")
    category_level: int = Field(..., description="Category hierarchy level")
    parent_category_id: Optional[UUID] = Field(None, description="Parent category ID")
    display_order: int = Field(0, description="Display order within parent")
    is_leaf: bool = Field(..., description="True if category has no children")
    is_active: bool = Field(True, description="Category active status")
    child_count: int = Field(0, description="Number of direct children")
    item_count: int = Field(0, description="Number of items in this category")


class CategoryTree(BaseModel):
    """Schema for hierarchical category tree."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Category unique identifier")
    name: str = Field(..., description="Category name")
    category_path: str = Field(..., description="Full category path")
    category_level: int = Field(..., description="Category hierarchy level")
    parent_category_id: Optional[UUID] = Field(None, description="Parent category ID")
    display_order: int = Field(0, description="Display order within parent")
    is_leaf: bool = Field(..., description="True if category has no children")
    is_active: bool = Field(True, description="Category active status")
    child_count: int = Field(0, description="Number of direct children")
    item_count: int = Field(0, description="Number of items in this category")
    children: List["CategoryTree"] = Field(default_factory=list, description="Child categories")


class CategoryList(BaseModel):
    """Schema for paginated category list response."""
    
    items: List[CategorySummary] = Field(..., description="List of category summaries")
    total: int = Field(..., description="Total number of categories")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class CategoryFilter(BaseModel):
    """Schema for category filtering and search."""
    
    name: Optional[str] = Field(None, description="Filter by category name (partial match)")
    parent_id: Optional[UUID] = Field(None, description="Filter by parent category ID")
    level: Optional[int] = Field(None, ge=1, description="Filter by category level")
    is_leaf: Optional[bool] = Field(None, description="Filter by leaf status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, description="Search in name and path")
    path_contains: Optional[str] = Field(None, description="Filter by path containing text")
    has_items: Optional[bool] = Field(None, description="Filter by whether category has items")
    has_children: Optional[bool] = Field(None, description="Filter by whether category has children")
    
    @validator('name', 'search', 'path_contains')
    def validate_string_filters(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CategorySort(BaseModel):
    """Schema for category sorting options."""
    
    field: str = Field('name', description="Field to sort by")
    direction: str = Field('asc', description="Sort direction (asc/desc)")
    
    @validator('field')
    def validate_field(cls, v):
        allowed_fields = [
            'name', 'category_path', 'category_level', 'display_order',
            'created_at', 'updated_at', 'is_active'
        ]
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {", ".join(allowed_fields)}')
        return v
    
    @validator('direction')
    def validate_direction(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('Sort direction must be "asc" or "desc"')
        return v.lower()


class CategoryStats(BaseModel):
    """Schema for category statistics."""
    
    total_categories: int = Field(..., description="Total number of categories")
    active_categories: int = Field(..., description="Number of active categories")
    inactive_categories: int = Field(..., description="Number of inactive categories")
    root_categories: int = Field(..., description="Number of root categories")
    leaf_categories: int = Field(..., description="Number of leaf categories")
    categories_with_items: int = Field(..., description="Number of categories with items")
    categories_without_items: int = Field(..., description="Number of categories without items")
    max_depth: int = Field(..., description="Maximum category depth")
    avg_children_per_category: float = Field(..., description="Average number of children per category")
    most_used_categories: List[Dict[str, Any]] = Field(..., description="Top categories by item count")
    
    @validator('most_used_categories')
    def validate_most_used_categories(cls, v):
        """Validate the structure of most_used_categories."""
        for category in v:
            if not isinstance(category, dict) or 'name' not in category or 'item_count' not in category:
                raise ValueError('Each category in most_used_categories must have name and item_count')
        return v


class CategoryBulkOperation(BaseModel):
    """Schema for bulk category operations."""
    
    category_ids: List[UUID] = Field(..., min_items=1, description="List of category IDs")
    operation: str = Field(..., description="Operation to perform (activate/deactivate/delete)")
    
    @validator('operation')
    def validate_operation(cls, v):
        if v not in ['activate', 'deactivate', 'delete']:
            raise ValueError('Operation must be "activate", "deactivate", or "delete"')
        return v


class CategoryBulkResult(BaseModel):
    """Schema for bulk operation results."""
    
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(..., description="List of errors for failed operations")
    
    @validator('errors')
    def validate_errors(cls, v):
        """Validate the structure of errors."""
        for error in v:
            if not isinstance(error, dict) or 'category_id' not in error or 'error' not in error:
                raise ValueError('Each error must have category_id and error fields')
        return v


class CategoryExport(BaseModel):
    """Schema for category export data."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    parent_category_id: Optional[UUID]
    category_path: str
    category_level: int
    display_order: int
    is_leaf: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]
    child_count: int = Field(0, description="Number of direct children")
    item_count: int = Field(0, description="Number of items in this category")


class CategoryImport(BaseModel):
    """Schema for category import data."""
    
    name: str = Field(..., min_length=1, max_length=100)
    parent_category_path: Optional[str] = Field(None, description="Parent category path")
    display_order: int = Field(0, ge=0)
    is_active: bool = Field(True)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()
    
    @validator('parent_category_path')
    def validate_parent_path(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CategoryImportResult(BaseModel):
    """Schema for category import results."""
    
    total_processed: int = Field(..., description="Total number of categories processed")
    successful_imports: int = Field(..., description="Number of successful imports")
    failed_imports: int = Field(..., description="Number of failed imports")
    skipped_imports: int = Field(..., description="Number of skipped imports (duplicates)")
    errors: List[Dict[str, Any]] = Field(..., description="List of import errors")
    
    @validator('errors')
    def validate_errors(cls, v):
        """Validate the structure of errors."""
        for error in v:
            if not isinstance(error, dict) or 'row' not in error or 'error' not in error:
                raise ValueError('Each error must have row and error fields')
        return v


class CategoryPath(BaseModel):
    """Schema for category path operations."""
    
    path: str = Field(..., description="Category path")
    segments: List[str] = Field(..., description="Path segments")
    level: int = Field(..., ge=1, description="Path depth level")
    is_root: bool = Field(..., description="Whether this is a root path")
    parent_path: Optional[str] = Field(None, description="Parent path")
    
    @validator('path')
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Category path cannot be empty')
        return v.strip()
    
    @validator('segments')
    def validate_segments(cls, v):
        if not v:
            raise ValueError('Path segments cannot be empty')
        for segment in v:
            if not segment or not segment.strip():
                raise ValueError('Path segments cannot contain empty values')
        return v


class CategoryHierarchy(BaseModel):
    """Schema for category hierarchy operations."""
    
    category_id: UUID = Field(..., description="Category ID")
    ancestors: List[CategorySummary] = Field(..., description="Ancestor categories")
    descendants: List[CategorySummary] = Field(..., description="Descendant categories")
    siblings: List[CategorySummary] = Field(..., description="Sibling categories")
    depth: int = Field(..., ge=1, description="Category depth in hierarchy")
    path_to_root: List[CategorySummary] = Field(..., description="Path from category to root")


class CategoryValidation(BaseModel):
    """Schema for category validation results."""
    
    is_valid: bool = Field(..., description="Whether category is valid")
    errors: List[str] = Field(..., description="List of validation errors")
    warnings: List[str] = Field(..., description="List of validation warnings")
    can_create: bool = Field(..., description="Whether category can be created")
    can_update: bool = Field(..., description="Whether category can be updated")
    can_delete: bool = Field(..., description="Whether category can be deleted")
    can_move: bool = Field(..., description="Whether category can be moved")


# Enable forward references for recursive models
CategoryTree.model_rebuild()