from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import SupplierRepository
from .models import Supplier, SupplierType, SupplierStatus
from .schemas import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierStatusUpdate
)
from app.core.errors import ValidationError, NotFoundError, ConflictError


class SupplierService:
    """Supplier service."""
    
    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.repository = SupplierRepository(session)
    
    async def create_supplier(self, supplier_data: SupplierCreate) -> SupplierResponse:
        """Create a new supplier."""
        # Check if supplier code already exists
        existing_supplier = await self.repository.get_by_code(supplier_data.supplier_code)
        if existing_supplier:
            raise ConflictError(f"Supplier with code '{supplier_data.supplier_code}' already exists")
        
        # Create supplier
        supplier_dict = supplier_data.model_dump()
        supplier = await self.repository.create(supplier_dict)
        
        return SupplierResponse.model_validate(supplier)
    
    async def get_supplier(self, supplier_id: UUID) -> Optional[SupplierResponse]:
        """Get supplier by ID."""
        supplier = await self.repository.get_by_id(supplier_id)
        if not supplier:
            return None
        
        return SupplierResponse.model_validate(supplier)
    
    async def get_supplier_by_code(self, supplier_code: str) -> Optional[SupplierResponse]:
        """Get supplier by code."""
        supplier = await self.repository.get_by_code(supplier_code)
        if not supplier:
            return None
        
        return SupplierResponse.model_validate(supplier)
    
    async def update_supplier(self, supplier_id: UUID, update_data: SupplierUpdate) -> SupplierResponse:
        """Update supplier information."""
        supplier = await self.repository.get_by_id(supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found")
        
        # Update supplier
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_supplier = await self.repository.update(supplier_id, update_dict)
        
        return SupplierResponse.model_validate(updated_supplier)
    
    async def delete_supplier(self, supplier_id: UUID) -> bool:
        """Delete supplier."""
        return await self.repository.delete(supplier_id)
    
    async def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_type: Optional[SupplierType] = None,
        status: Optional[SupplierStatus] = None,
        active_only: bool = True
    ) -> List[SupplierResponse]:
        """List suppliers with filtering."""
        suppliers = await self.repository.get_all(
            skip=skip,
            limit=limit,
            supplier_type=supplier_type,
            status=status,
            active_only=active_only
        )
        
        return [SupplierResponse.model_validate(supplier) for supplier in suppliers]
    
    async def search_suppliers(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[SupplierResponse]:
        """Search suppliers."""
        suppliers = await self.repository.search(
            search_term=search_term,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [SupplierResponse.model_validate(supplier) for supplier in suppliers]
    
    async def count_suppliers(
        self,
        supplier_type: Optional[SupplierType] = None,
        status: Optional[SupplierStatus] = None,
        active_only: bool = True
    ) -> int:
        """Count suppliers with filtering."""
        return await self.repository.count_all(
            supplier_type=supplier_type,
            status=status,
            active_only=active_only
        )
    
    async def update_supplier_status(self, supplier_id: UUID, status_update: SupplierStatusUpdate) -> SupplierResponse:
        """Update supplier status."""
        supplier = await self.repository.get_by_id(supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found")
        
        update_dict = {
            "status": status_update.status,
            "notes": status_update.notes
        }
        
        updated_supplier = await self.repository.update(supplier_id, update_dict)
        return SupplierResponse.model_validate(updated_supplier)
    
    async def get_supplier_statistics(self) -> Dict[str, Any]:
        """Get supplier statistics."""
        # Get basic counts
        total_suppliers = await self.repository.count_all(active_only=False)
        active_suppliers = await self.repository.count_all(active_only=True)
        
        # Get suppliers by type
        inventory_suppliers = await self.repository.count_all(
            supplier_type=SupplierType.INVENTORY, active_only=True
        )
        service_suppliers = await self.repository.count_all(
            supplier_type=SupplierType.SERVICE, active_only=True
        )
        
        # Get suppliers by status
        approved_suppliers = await self.repository.count_all(
            status=SupplierStatus.APPROVED, active_only=True
        )
        pending_suppliers = await self.repository.count_all(
            status=SupplierStatus.PENDING, active_only=True
        )
        
        # Get recent suppliers
        recent_suppliers = await self.repository.get_all(skip=0, limit=10, active_only=True)
        
        return {
            "total_suppliers": total_suppliers,
            "active_suppliers": active_suppliers,
            "inactive_suppliers": total_suppliers - active_suppliers,
            "inventory_suppliers": inventory_suppliers,
            "service_suppliers": service_suppliers,
            "approved_suppliers": approved_suppliers,
            "pending_suppliers": pending_suppliers,
            "suppliers_by_country": {},
            "suppliers_by_rating": {},
            "top_suppliers_by_orders": [],
            "top_suppliers_by_value": [],
            "recent_suppliers": [SupplierResponse.model_validate(supplier) for supplier in recent_suppliers]
        }