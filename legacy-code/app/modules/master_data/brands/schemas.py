from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, validator
from datetime import datetime
from uuid import UUID


class BrandBase(BaseModel):
    """Base brand schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Brand name")
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="Unique brand code")
    description: Optional[str] = Field(None, max_length=1000, description="Brand description")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Brand name cannot be empty')
        return v.strip()
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Brand code cannot be empty if provided')
            
            # Check for valid characters (letters, numbers, hyphens, underscores)
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Brand code must contain only letters, numbers, hyphens, and underscores')
            
            return v.upper().strip()
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class BrandCreate(BrandBase):
    """Schema for creating a new brand."""
    pass


class BrandUpdate(BaseModel):
    """Schema for updating an existing brand."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Brand name")
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="Unique brand code")
    description: Optional[str] = Field(None, max_length=1000, description="Brand description")
    is_active: Optional[bool] = Field(None, description="Brand active status")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Brand name cannot be empty')
            return v.strip()
        return v
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Brand code cannot be empty if provided')
            
            # Check for valid characters (letters, numbers, hyphens, underscores)
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Brand code must contain only letters, numbers, hyphens, and underscores')
            
            return v.upper().strip()
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class BrandResponse(BrandBase):
    """Schema for brand response with all fields."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Brand unique identifier")
    is_active: bool = Field(True, description="Brand active status")
    created_at: datetime = Field(..., description="Brand creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Brand last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the brand")
    updated_by: Optional[str] = Field(None, description="User who last updated the brand")
    display_name: str = Field(..., description="Brand display name (computed)")
    has_items: bool = Field(False, description="Whether brand has associated items")
    
    @validator('display_name', pre=True, always=True)
    def compute_display_name(cls, v, values):
        """Compute display name from name and code."""
        name = values.get('name', '')
        code = values.get('code')
        if code:
            return f"{name} ({code})"
        return name


class BrandSummary(BaseModel):
    """Schema for brand summary with minimal fields."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Brand unique identifier")
    name: str = Field(..., description="Brand name")
    code: Optional[str] = Field(None, description="Brand code")
    is_active: bool = Field(True, description="Brand active status")
    display_name: str = Field(..., description="Brand display name")
    
    @validator('display_name', pre=True, always=True)
    def compute_display_name(cls, v, values):
        """Compute display name from name and code."""
        name = values.get('name', '')
        code = values.get('code')
        if code:
            return f"{name} ({code})"
        return name


class BrandList(BaseModel):
    """Schema for paginated brand list response."""
    
    items: list[BrandSummary] = Field(..., description="List of brand summaries")
    total: int = Field(..., description="Total number of brands")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class BrandFilter(BaseModel):
    """Schema for brand filtering and search."""
    
    name: Optional[str] = Field(None, description="Filter by brand name (partial match)")
    code: Optional[str] = Field(None, description="Filter by brand code (partial match)")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, description="Search in name and code")
    
    @validator('name', 'code', 'search')
    def validate_string_filters(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class BrandSort(BaseModel):
    """Schema for brand sorting options."""
    
    field: str = Field('name', description="Field to sort by")
    direction: str = Field('asc', description="Sort direction (asc/desc)")
    
    @validator('field')
    def validate_field(cls, v):
        allowed_fields = ['name', 'code', 'created_at', 'updated_at', 'is_active']
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {", ".join(allowed_fields)}')
        return v
    
    @validator('direction')
    def validate_direction(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('Sort direction must be "asc" or "desc"')
        return v.lower()


class BrandStats(BaseModel):
    """Schema for brand statistics."""
    
    total_brands: int = Field(..., description="Total number of brands")
    active_brands: int = Field(..., description="Number of active brands")
    inactive_brands: int = Field(..., description="Number of inactive brands")
    brands_with_items: int = Field(..., description="Number of brands with associated items")
    brands_without_items: int = Field(..., description="Number of brands without items")
    most_used_brands: list[dict] = Field(..., description="Top brands by item count")
    
    @validator('most_used_brands')
    def validate_most_used_brands(cls, v):
        """Validate the structure of most_used_brands."""
        for brand in v:
            if not isinstance(brand, dict) or 'name' not in brand or 'item_count' not in brand:
                raise ValueError('Each brand in most_used_brands must have name and item_count')
        return v


class BrandBulkOperation(BaseModel):
    """Schema for bulk brand operations."""
    
    brand_ids: list[UUID] = Field(..., min_items=1, description="List of brand IDs")
    operation: str = Field(..., description="Operation to perform (activate/deactivate)")
    
    @validator('operation')
    def validate_operation(cls, v):
        if v not in ['activate', 'deactivate']:
            raise ValueError('Operation must be "activate" or "deactivate"')
        return v


class BrandBulkResult(BaseModel):
    """Schema for bulk operation results."""
    
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")
    errors: list[dict] = Field(..., description="List of errors for failed operations")
    
    @validator('errors')
    def validate_errors(cls, v):
        """Validate the structure of errors."""
        for error in v:
            if not isinstance(error, dict) or 'brand_id' not in error or 'error' not in error:
                raise ValueError('Each error must have brand_id and error fields')
        return v


class BrandExport(BaseModel):
    """Schema for brand export data."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    code: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]
    item_count: int = Field(0, description="Number of items under this brand")


class BrandImport(BaseModel):
    """Schema for brand import data."""
    
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: bool = Field(True)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Brand name cannot be empty')
        return v.strip()
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Brand code cannot be empty if provided')
            
            # Check for valid characters (letters, numbers, hyphens, underscores)
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Brand code must contain only letters, numbers, hyphens, and underscores')
            
            return v.upper().strip()
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class BrandImportResult(BaseModel):
    """Schema for brand import results."""
    
    total_processed: int = Field(..., description="Total number of brands processed")
    successful_imports: int = Field(..., description="Number of successful imports")
    failed_imports: int = Field(..., description="Number of failed imports")
    skipped_imports: int = Field(..., description="Number of skipped imports (duplicates)")
    errors: list[dict] = Field(..., description="List of import errors")
    
    @validator('errors')
    def validate_errors(cls, v):
        """Validate the structure of errors."""
        for error in v:
            if not isinstance(error, dict) or 'row' not in error or 'error' not in error:
                raise ValueError('Each error must have row and error fields')
        return v