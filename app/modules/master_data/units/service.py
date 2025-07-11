from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from .repository import UnitOfMeasurementRepository
from .models import UnitOfMeasurement
from .schemas import (
    UnitOfMeasurementCreate, UnitOfMeasurementUpdate, UnitOfMeasurementResponse, 
    UnitOfMeasurementSummary, UnitOfMeasurementList, UnitOfMeasurementFilter, 
    UnitOfMeasurementSort, UnitOfMeasurementStats, UnitOfMeasurementBulkOperation, 
    UnitOfMeasurementBulkResult, UnitOfMeasurementExport, UnitOfMeasurementImport, 
    UnitOfMeasurementImportResult
)
from app.core.errors import (
    NotFoundError, ConflictError, ValidationError, 
    BusinessRuleError
)


class UnitOfMeasurementService:
    """Service layer for unit of measurement business logic."""
    
    def __init__(self, repository: UnitOfMeasurementRepository):
        """Initialize service with repository."""
        self.repository = repository
    
    async def create_unit(
        self,
        unit_data: UnitOfMeasurementCreate,
        created_by: Optional[str] = None
    ) -> UnitOfMeasurementResponse:
        """Create a new unit of measurement.
        
        Args:
            unit_data: Unit creation data
            created_by: User creating the unit
            
        Returns:
            Created unit response
            
        Raises:
            ConflictError: If unit name or abbreviation already exists
            ValidationError: If unit data is invalid
        """
        # Check if unit name already exists
        if await self.repository.exists_by_name(unit_data.name):
            raise ConflictError(f"Unit with name '{unit_data.name}' already exists")
        
        # Check if unit abbreviation already exists
        if unit_data.abbreviation and await self.repository.exists_by_abbreviation(unit_data.abbreviation):
            raise ConflictError(f"Unit with abbreviation '{unit_data.abbreviation}' already exists")
        
        # Prepare unit data
        create_data = unit_data.model_dump()
        create_data.update({
            "created_by": created_by,
            "updated_by": created_by
        })
        
        # Create unit
        unit = await self.repository.create(create_data)
        
        # Convert to response
        return await self._to_response(unit)
    
    async def get_unit(self, unit_id: UUID) -> UnitOfMeasurementResponse:
        """Get unit of measurement by ID.
        
        Args:
            unit_id: Unit UUID
            
        Returns:
            Unit response
            
        Raises:
            NotFoundError: If unit not found
        """
        unit = await self.repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit with id {unit_id} not found")
        
        return await self._to_response(unit)
    
    async def get_unit_by_name(self, name: str) -> UnitOfMeasurementResponse:
        """Get unit of measurement by name.
        
        Args:
            name: Unit name
            
        Returns:
            Unit response
            
        Raises:
            NotFoundError: If unit not found
        """
        unit = await self.repository.get_by_name(name)
        if not unit:
            raise NotFoundError(f"Unit with name '{name}' not found")
        
        return await self._to_response(unit)
    
    async def get_unit_by_abbreviation(self, abbreviation: str) -> UnitOfMeasurementResponse:
        """Get unit of measurement by abbreviation.
        
        Args:
            abbreviation: Unit abbreviation
            
        Returns:
            Unit response
            
        Raises:
            NotFoundError: If unit not found
        """
        unit = await self.repository.get_by_abbreviation(abbreviation)
        if not unit:
            raise NotFoundError(f"Unit with abbreviation '{abbreviation}' not found")
        
        return await self._to_response(unit)
    
    async def update_unit(
        self,
        unit_id: UUID,
        unit_data: UnitOfMeasurementUpdate,
        updated_by: Optional[str] = None
    ) -> UnitOfMeasurementResponse:
        """Update an existing unit of measurement.
        
        Args:
            unit_id: Unit UUID
            unit_data: Unit update data
            updated_by: User updating the unit
            
        Returns:
            Updated unit response
            
        Raises:
            NotFoundError: If unit not found
            ConflictError: If name or abbreviation already exists
            ValidationError: If update data is invalid
        """
        # Get existing unit
        existing_unit = await self.repository.get_by_id(unit_id)
        if not existing_unit:
            raise NotFoundError(f"Unit with id {unit_id} not found")
        
        # Prepare update data
        update_data = {}
        
        # Check name uniqueness if provided
        if unit_data.name is not None and unit_data.name != existing_unit.name:
            if await self.repository.exists_by_name(unit_data.name, exclude_id=unit_id):
                raise ConflictError(f"Unit with name '{unit_data.name}' already exists")
            update_data["name"] = unit_data.name
        
        # Check abbreviation uniqueness if provided
        if unit_data.abbreviation is not None and unit_data.abbreviation != existing_unit.abbreviation:
            if unit_data.abbreviation and await self.repository.exists_by_abbreviation(unit_data.abbreviation, exclude_id=unit_id):
                raise ConflictError(f"Unit with abbreviation '{unit_data.abbreviation}' already exists")
            update_data["abbreviation"] = unit_data.abbreviation
        
        # Update other fields
        if unit_data.description is not None:
            update_data["description"] = unit_data.description
        
        if unit_data.is_active is not None:
            update_data["is_active"] = unit_data.is_active
        
        # Add updated_by
        update_data["updated_by"] = updated_by
        
        # Update unit
        updated_unit = await self.repository.update(unit_id, update_data)
        if not updated_unit:
            raise NotFoundError(f"Unit with id {unit_id} not found")
        
        return await self._to_response(updated_unit)
    
    async def delete_unit(self, unit_id: UUID) -> bool:
        """Soft delete a unit of measurement.
        
        Args:
            unit_id: Unit UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If unit not found
            BusinessRuleError: If unit has associated items
        """
        unit = await self.repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit with id {unit_id} not found")
        
        # Check if unit can be deleted
        if not unit.can_delete():
            raise BusinessRuleError("Cannot delete unit with associated items")
        
        return await self.repository.delete(unit_id)
    
    async def list_units(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[UnitOfMeasurementFilter] = None,
        sort: Optional[UnitOfMeasurementSort] = None,
        include_inactive: bool = False
    ) -> UnitOfMeasurementList:
        """List units of measurement with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Items per page
            filters: Filter criteria
            sort: Sort options
            include_inactive: Include inactive units
            
        Returns:
            Paginated unit list
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
        
        # Get total count
        total_count = await self.repository.count(
            filters=filter_dict,
            include_inactive=include_inactive
        )
        
        # Get paginated units
        units_list = await self.repository.get_paginated(
            page=page,
            page_size=page_size,
            filters=filter_dict,
            sort_by=sort_by,
            sort_order=sort_order,
            include_inactive=include_inactive
        )
        
        # Convert to summaries
        unit_summaries = []
        for unit in units_list:
            summary = UnitOfMeasurementSummary.model_validate(unit)
            unit_summaries.append(summary)
        
        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size
        
        return UnitOfMeasurementList(
            items=unit_summaries,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    async def search_units(
        self,
        search_term: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[UnitOfMeasurementSummary]:
        """Search units of measurement by name, abbreviation, or description.
        
        Args:
            search_term: Search term
            limit: Maximum results
            include_inactive: Include inactive units
            
        Returns:
            List of unit summaries
        """
        units = await self.repository.search(
            search_term=search_term,
            limit=limit,
            include_inactive=include_inactive
        )
        
        return [UnitOfMeasurementSummary.model_validate(unit) for unit in units]
    
    async def get_active_units(self) -> List[UnitOfMeasurementSummary]:
        """Get all active units of measurement.
        
        Returns:
            List of active unit summaries
        """
        units = await self.repository.get_active_units()
        return [UnitOfMeasurementSummary.model_validate(unit) for unit in units]
    
    async def get_unit_statistics(self) -> UnitOfMeasurementStats:
        """Get unit of measurement statistics.
        
        Returns:
            Unit statistics
        """
        stats = await self.repository.get_statistics()
        most_used = await self.repository.get_most_used_units()
        
        return UnitOfMeasurementStats(
            total_units=stats["total_units"],
            active_units=stats["active_units"],
            inactive_units=stats["inactive_units"],
            units_with_items=stats["units_with_items"],
            units_without_items=stats["units_without_items"],
            most_used_units=most_used
        )
    
    async def bulk_operation(
        self,
        operation: UnitOfMeasurementBulkOperation,
        updated_by: Optional[str] = None
    ) -> UnitOfMeasurementBulkResult:
        """Perform bulk operations on units of measurement.
        
        Args:
            operation: Bulk operation data
            updated_by: User performing the operation
            
        Returns:
            Bulk operation result
        """
        success_count = 0
        errors = []
        
        for unit_id in operation.unit_ids:
            try:
                if operation.operation == "activate":
                    count = await self.repository.bulk_activate([unit_id])
                    success_count += count
                elif operation.operation == "deactivate":
                    count = await self.repository.bulk_deactivate([unit_id])
                    success_count += count
            except Exception as e:
                errors.append({
                    "unit_id": str(unit_id),
                    "error": str(e)
                })
        
        return UnitOfMeasurementBulkResult(
            success_count=success_count,
            failure_count=len(errors),
            errors=errors
        )
    
    async def export_units(
        self,
        include_inactive: bool = False
    ) -> List[UnitOfMeasurementExport]:
        """Export units of measurement data.
        
        Args:
            include_inactive: Include inactive units
            
        Returns:
            List of unit export data
        """
        units = await self.repository.list(
            skip=0,
            limit=10000,  # Large limit for export
            include_inactive=include_inactive
        )
        
        export_data = []
        for unit in units:
            export_item = UnitOfMeasurementExport.model_validate(unit)
            # Add item count (when available)
            export_item.item_count = unit.item_count
            export_data.append(export_item)
        
        return export_data
    
    async def import_units(
        self,
        import_data: List[UnitOfMeasurementImport],
        created_by: Optional[str] = None
    ) -> UnitOfMeasurementImportResult:
        """Import units of measurement data.
        
        Args:
            import_data: List of unit import data
            created_by: User importing the data
            
        Returns:
            Import operation result
        """
        total_processed = len(import_data)
        successful_imports = 0
        failed_imports = 0
        skipped_imports = 0
        errors = []
        
        for row, unit_data in enumerate(import_data, 1):
            try:
                # Check if unit already exists
                if await self.repository.exists_by_name(unit_data.name):
                    skipped_imports += 1
                    continue
                
                if unit_data.abbreviation and await self.repository.exists_by_abbreviation(unit_data.abbreviation):
                    skipped_imports += 1
                    continue
                
                # Create unit
                create_data = unit_data.model_dump()
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
        
        return UnitOfMeasurementImportResult(
            total_processed=total_processed,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            skipped_imports=skipped_imports,
            errors=errors
        )
    
    async def activate_unit(self, unit_id: UUID) -> UnitOfMeasurementResponse:
        """Activate a unit of measurement.
        
        Args:
            unit_id: Unit UUID
            
        Returns:
            Updated unit response
        """
        unit = await self.repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit with id {unit_id} not found")
        
        if unit.is_active:
            return await self._to_response(unit)
        
        updated_unit = await self.repository.update(unit_id, {"is_active": True})
        return await self._to_response(updated_unit)
    
    async def deactivate_unit(self, unit_id: UUID) -> UnitOfMeasurementResponse:
        """Deactivate a unit of measurement.
        
        Args:
            unit_id: Unit UUID
            
        Returns:
            Updated unit response
        """
        unit = await self.repository.get_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit with id {unit_id} not found")
        
        if not unit.is_active:
            return await self._to_response(unit)
        
        updated_unit = await self.repository.update(unit_id, {"is_active": False})
        return await self._to_response(updated_unit)
    
    async def _to_response(self, unit: UnitOfMeasurement) -> UnitOfMeasurementResponse:
        """Convert unit model to response schema.
        
        Args:
            unit: Unit model
            
        Returns:
            Unit response schema
        """
        # Convert to dict and add computed fields
        unit_dict = {
            "id": unit.id,
            "name": unit.name,
            "abbreviation": unit.abbreviation,
            "description": unit.description,
            "is_active": unit.is_active,
            "created_at": unit.created_at,
            "updated_at": unit.updated_at,
            "created_by": unit.created_by,
            "updated_by": unit.updated_by,
            "display_name": unit.display_name,
            "item_count": unit.item_count
        }
        
        return UnitOfMeasurementResponse(**unit_dict)