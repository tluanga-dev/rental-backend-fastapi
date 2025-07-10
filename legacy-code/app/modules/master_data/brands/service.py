from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from .repository import BrandRepository
from .models import Brand
from .schemas import (
    BrandCreate, BrandUpdate, BrandResponse, BrandSummary, 
    BrandList, BrandFilter, BrandSort, BrandStats,
    BrandBulkOperation, BrandBulkResult, BrandExport,
    BrandImport, BrandImportResult
)
from app.shared.pagination import Page
from app.core.errors import (
    NotFoundError, ConflictError, ValidationError, 
    BusinessRuleError
)


class BrandService:
    """Service layer for brand business logic."""
    
    def __init__(self, repository: BrandRepository):
        """Initialize service with repository."""
        self.repository = repository
    
    async def create_brand(
        self,
        brand_data: BrandCreate,
        created_by: Optional[str] = None
    ) -> BrandResponse:
        """Create a new brand.
        
        Args:
            brand_data: Brand creation data
            created_by: User creating the brand
            
        Returns:
            Created brand response
            
        Raises:
            ConflictError: If brand name or code already exists
            ValidationError: If brand data is invalid
        """
        # Check if brand name already exists
        if await self.repository.exists_by_name(brand_data.name):
            raise ConflictError(f"Brand with name '{brand_data.name}' already exists")
        
        # Check if brand code already exists
        if brand_data.code and await self.repository.exists_by_code(brand_data.code):
            raise ConflictError(f"Brand with code '{brand_data.code}' already exists")
        
        # Prepare brand data
        create_data = brand_data.model_dump()
        create_data.update({
            "created_by": created_by,
            "updated_by": created_by
        })
        
        # Create brand
        brand = await self.repository.create(create_data)
        
        # Convert to response
        return await self._to_response(brand)
    
    async def get_brand(self, brand_id: UUID) -> BrandResponse:
        """Get brand by ID.
        
        Args:
            brand_id: Brand UUID
            
        Returns:
            Brand response
            
        Raises:
            NotFoundError: If brand not found
        """
        brand = await self.repository.get_by_id(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with id {brand_id} not found")
        
        return await self._to_response(brand)
    
    async def get_brand_by_name(self, name: str) -> BrandResponse:
        """Get brand by name.
        
        Args:
            name: Brand name
            
        Returns:
            Brand response
            
        Raises:
            NotFoundError: If brand not found
        """
        brand = await self.repository.get_by_name(name)
        if not brand:
            raise NotFoundError(f"Brand with name '{name}' not found")
        
        return await self._to_response(brand)
    
    async def get_brand_by_code(self, code: str) -> BrandResponse:
        """Get brand by code.
        
        Args:
            code: Brand code
            
        Returns:
            Brand response
            
        Raises:
            NotFoundError: If brand not found
        """
        brand = await self.repository.get_by_code(code)
        if not brand:
            raise NotFoundError(f"Brand with code '{code}' not found")
        
        return await self._to_response(brand)
    
    async def update_brand(
        self,
        brand_id: UUID,
        brand_data: BrandUpdate,
        updated_by: Optional[str] = None
    ) -> BrandResponse:
        """Update an existing brand.
        
        Args:
            brand_id: Brand UUID
            brand_data: Brand update data
            updated_by: User updating the brand
            
        Returns:
            Updated brand response
            
        Raises:
            NotFoundError: If brand not found
            ConflictError: If name or code already exists
            ValidationError: If update data is invalid
        """
        # Get existing brand
        existing_brand = await self.repository.get_by_id(brand_id)
        if not existing_brand:
            raise NotFoundError(f"Brand with id {brand_id} not found")
        
        # Prepare update data
        update_data = {}
        
        # Check name uniqueness if provided
        if brand_data.name is not None and brand_data.name != existing_brand.name:
            if await self.repository.exists_by_name(brand_data.name, exclude_id=brand_id):
                raise ConflictError(f"Brand with name '{brand_data.name}' already exists")
            update_data["name"] = brand_data.name
        
        # Check code uniqueness if provided
        if brand_data.code is not None and brand_data.code != existing_brand.code:
            if brand_data.code and await self.repository.exists_by_code(brand_data.code, exclude_id=brand_id):
                raise ConflictError(f"Brand with code '{brand_data.code}' already exists")
            update_data["code"] = brand_data.code
        
        # Update other fields
        if brand_data.description is not None:
            update_data["description"] = brand_data.description
        
        if brand_data.is_active is not None:
            update_data["is_active"] = brand_data.is_active
        
        # Add updated_by
        update_data["updated_by"] = updated_by
        
        # Update brand
        updated_brand = await self.repository.update(brand_id, update_data)
        if not updated_brand:
            raise NotFoundError(f"Brand with id {brand_id} not found")
        
        return await self._to_response(updated_brand)
    
    async def delete_brand(self, brand_id: UUID) -> bool:
        """Soft delete a brand.
        
        Args:
            brand_id: Brand UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If brand not found
            BusinessRuleError: If brand has associated items
        """
        brand = await self.repository.get_by_id(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with id {brand_id} not found")
        
        # Check if brand can be deleted
        if not brand.can_delete():
            raise BusinessRuleError("Cannot delete brand with associated items")
        
        return await self.repository.delete(brand_id)
    
    async def list_brands(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[BrandFilter] = None,
        sort: Optional[BrandSort] = None,
        include_inactive: bool = False
    ) -> BrandList:
        """List brands with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Items per page
            filters: Filter criteria
            sort: Sort options
            include_inactive: Include inactive brands
            
        Returns:
            Paginated brand list
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
        
        # Get paginated brands
        page_result = await self.repository.get_paginated(
            page=page,
            page_size=page_size,
            filters=filter_dict,
            sort_by=sort_by,
            sort_order=sort_order,
            include_inactive=include_inactive
        )
        
        # Convert to summaries
        brand_summaries = []
        for brand in page_result.items:
            summary = BrandSummary.model_validate(brand)
            brand_summaries.append(summary)
        
        # Return list response
        return BrandList(
            items=brand_summaries,
            total=page_result.page_info.total_items,
            page=page_result.page_info.page,
            page_size=page_result.page_info.page_size,
            total_pages=page_result.page_info.total_pages,
            has_next=page_result.page_info.has_next,
            has_previous=page_result.page_info.has_previous
        )
    
    async def search_brands(
        self,
        search_term: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[BrandSummary]:
        """Search brands by name, code, or description.
        
        Args:
            search_term: Search term
            limit: Maximum results
            include_inactive: Include inactive brands
            
        Returns:
            List of brand summaries
        """
        brands = await self.repository.search(
            search_term=search_term,
            limit=limit,
            include_inactive=include_inactive
        )
        
        return [BrandSummary.model_validate(brand) for brand in brands]
    
    async def get_active_brands(self) -> List[BrandSummary]:
        """Get all active brands.
        
        Returns:
            List of active brand summaries
        """
        brands = await self.repository.get_active_brands()
        return [BrandSummary.model_validate(brand) for brand in brands]
    
    async def get_brand_statistics(self) -> BrandStats:
        """Get brand statistics.
        
        Returns:
            Brand statistics
        """
        stats = await self.repository.get_statistics()
        most_used = await self.repository.get_most_used_brands()
        
        return BrandStats(
            total_brands=stats["total_brands"],
            active_brands=stats["active_brands"],
            inactive_brands=stats["inactive_brands"],
            brands_with_items=stats["brands_with_items"],
            brands_without_items=stats["brands_without_items"],
            most_used_brands=most_used
        )
    
    async def bulk_operation(
        self,
        operation: BrandBulkOperation,
        updated_by: Optional[str] = None
    ) -> BrandBulkResult:
        """Perform bulk operations on brands.
        
        Args:
            operation: Bulk operation data
            updated_by: User performing the operation
            
        Returns:
            Bulk operation result
        """
        success_count = 0
        errors = []
        
        for brand_id in operation.brand_ids:
            try:
                if operation.operation == "activate":
                    count = await self.repository.bulk_activate([brand_id])
                    success_count += count
                elif operation.operation == "deactivate":
                    count = await self.repository.bulk_deactivate([brand_id])
                    success_count += count
            except Exception as e:
                errors.append({
                    "brand_id": str(brand_id),
                    "error": str(e)
                })
        
        return BrandBulkResult(
            success_count=success_count,
            failure_count=len(errors),
            errors=errors
        )
    
    async def export_brands(
        self,
        include_inactive: bool = False
    ) -> List[BrandExport]:
        """Export brands data.
        
        Args:
            include_inactive: Include inactive brands
            
        Returns:
            List of brand export data
        """
        brands = await self.repository.list(
            skip=0,
            limit=10000,  # Large limit for export
            include_inactive=include_inactive
        )
        
        export_data = []
        for brand in brands:
            export_item = BrandExport.model_validate(brand)
            # Add item count (when available)
            export_item.item_count = len(brand.items) if brand.items else 0
            export_data.append(export_item)
        
        return export_data
    
    async def import_brands(
        self,
        import_data: List[BrandImport],
        created_by: Optional[str] = None
    ) -> BrandImportResult:
        """Import brands data.
        
        Args:
            import_data: List of brand import data
            created_by: User importing the data
            
        Returns:
            Import operation result
        """
        total_processed = len(import_data)
        successful_imports = 0
        failed_imports = 0
        skipped_imports = 0
        errors = []
        
        for row, brand_data in enumerate(import_data, 1):
            try:
                # Check if brand already exists
                if await self.repository.exists_by_name(brand_data.name):
                    skipped_imports += 1
                    continue
                
                if brand_data.code and await self.repository.exists_by_code(brand_data.code):
                    skipped_imports += 1
                    continue
                
                # Create brand
                create_data = brand_data.model_dump()
                create_data.update({
                    "created_by": created_by,
                    "updated_by": created_by
                })
                
                await self.repository.create(create_data)
                successful_imports += 1
                
            except Exception as e:
                failed_imports += 1
                errors.append({
                    "row": row,
                    "error": str(e)
                })
        
        return BrandImportResult(
            total_processed=total_processed,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            skipped_imports=skipped_imports,
            errors=errors
        )
    
    async def activate_brand(self, brand_id: UUID) -> BrandResponse:
        """Activate a brand.
        
        Args:
            brand_id: Brand UUID
            
        Returns:
            Updated brand response
        """
        brand = await self.repository.get_by_id(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with id {brand_id} not found")
        
        if brand.is_active:
            return await self._to_response(brand)
        
        updated_brand = await self.repository.update(brand_id, {"is_active": True})
        return await self._to_response(updated_brand)
    
    async def deactivate_brand(self, brand_id: UUID) -> BrandResponse:
        """Deactivate a brand.
        
        Args:
            brand_id: Brand UUID
            
        Returns:
            Updated brand response
        """
        brand = await self.repository.get_by_id(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with id {brand_id} not found")
        
        if not brand.is_active:
            return await self._to_response(brand)
        
        updated_brand = await self.repository.update(brand_id, {"is_active": False})
        return await self._to_response(updated_brand)
    
    async def _to_response(self, brand: Brand) -> BrandResponse:
        """Convert brand model to response schema.
        
        Args:
            brand: Brand model
            
        Returns:
            Brand response schema
        """
        # Convert to dict and add computed fields
        brand_dict = {
            "id": brand.id,
            "name": brand.name,
            "code": brand.code,
            "description": brand.description,
            "is_active": brand.is_active,
            "created_at": brand.created_at,
            "updated_at": brand.updated_at,
            "created_by": brand.created_by,
            "updated_by": brand.updated_by,
            "display_name": brand.display_name,
            "has_items": brand.has_items
        }
        
        return BrandResponse(**brand_dict)