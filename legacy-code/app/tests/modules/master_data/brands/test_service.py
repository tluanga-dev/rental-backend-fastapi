import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.modules.master_data.brands.service import BrandService
from app.modules.master_data.brands.repository import BrandRepository
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.brands.schemas import (
    BrandCreate, BrandUpdate, BrandFilter, BrandSort,
    BrandBulkOperation, BrandImport
)
from app.core.errors import NotFoundError, ConflictError, ValidationError, BusinessRuleError


class TestBrandService:
    """Tests for BrandService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock(spec=BrandRepository)
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create service instance with mock repository."""
        return BrandService(mock_repository)
    
    @pytest.fixture
    def sample_brand(self):
        """Create sample brand for testing."""
        return Brand(
            id=uuid4(),
            name="Test Brand",
            code="TST",
            description="Test description",
            is_active=True,
            created_by="test_user",
            updated_by="test_user"
        )
    
    @pytest.fixture
    def sample_brand_create(self):
        """Create sample brand create schema."""
        return BrandCreate(
            name="Test Brand",
            code="TST",
            description="Test description"
        )
    
    async def test_create_brand_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand_create: BrandCreate, sample_brand: Brand):
        """Test successful brand creation."""
        mock_repository.exists_by_name.return_value = False
        mock_repository.exists_by_code.return_value = False
        mock_repository.create.return_value = sample_brand
        
        result = await service.create_brand(sample_brand_create, created_by="test_user")
        
        assert result.name == sample_brand.name
        assert result.code == sample_brand.code
        assert result.description == sample_brand.description
        
        mock_repository.exists_by_name.assert_called_once_with("Test Brand")
        mock_repository.exists_by_code.assert_called_once_with("TST")
        mock_repository.create.assert_called_once()
    
    async def test_create_brand_name_conflict(self, service: BrandService, mock_repository: AsyncMock, sample_brand_create: BrandCreate):
        """Test brand creation with name conflict."""
        mock_repository.exists_by_name.return_value = True
        
        with pytest.raises(ConflictError, match="Brand with name 'Test Brand' already exists"):
            await service.create_brand(sample_brand_create)
    
    async def test_create_brand_code_conflict(self, service: BrandService, mock_repository: AsyncMock, sample_brand_create: BrandCreate):
        """Test brand creation with code conflict."""
        mock_repository.exists_by_name.return_value = False
        mock_repository.exists_by_code.return_value = True
        
        with pytest.raises(ConflictError, match="Brand with code 'TST' already exists"):
            await service.create_brand(sample_brand_create)
    
    async def test_get_brand_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand retrieval."""
        mock_repository.get_by_id.return_value = sample_brand
        
        result = await service.get_brand(sample_brand.id)
        
        assert result.id == sample_brand.id
        assert result.name == sample_brand.name
        mock_repository.get_by_id.assert_called_once_with(sample_brand.id)
    
    async def test_get_brand_not_found(self, service: BrandService, mock_repository: AsyncMock):
        """Test brand retrieval when not found."""
        brand_id = uuid4()
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match=f"Brand with id {brand_id} not found"):
            await service.get_brand(brand_id)
    
    async def test_get_brand_by_name_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand retrieval by name."""
        mock_repository.get_by_name.return_value = sample_brand
        
        result = await service.get_brand_by_name("Test Brand")
        
        assert result.name == sample_brand.name
        mock_repository.get_by_name.assert_called_once_with("Test Brand")
    
    async def test_get_brand_by_name_not_found(self, service: BrandService, mock_repository: AsyncMock):
        """Test brand retrieval by name when not found."""
        mock_repository.get_by_name.return_value = None
        
        with pytest.raises(NotFoundError, match="Brand with name 'Test Brand' not found"):
            await service.get_brand_by_name("Test Brand")
    
    async def test_get_brand_by_code_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand retrieval by code."""
        mock_repository.get_by_code.return_value = sample_brand
        
        result = await service.get_brand_by_code("TST")
        
        assert result.code == sample_brand.code
        mock_repository.get_by_code.assert_called_once_with("TST")
    
    async def test_get_brand_by_code_not_found(self, service: BrandService, mock_repository: AsyncMock):
        """Test brand retrieval by code when not found."""
        mock_repository.get_by_code.return_value = None
        
        with pytest.raises(NotFoundError, match="Brand with code 'TST' not found"):
            await service.get_brand_by_code("TST")
    
    async def test_update_brand_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand update."""
        update_data = BrandUpdate(name="Updated Brand", code="UPD")
        updated_brand = Brand(
            id=sample_brand.id,
            name="Updated Brand",
            code="UPD",
            description=sample_brand.description,
            is_active=True
        )
        
        mock_repository.get_by_id.return_value = sample_brand
        mock_repository.exists_by_name.return_value = False
        mock_repository.exists_by_code.return_value = False
        mock_repository.update.return_value = updated_brand
        
        result = await service.update_brand(sample_brand.id, update_data, updated_by="test_user")
        
        assert result.name == "Updated Brand"
        assert result.code == "UPD"
        mock_repository.update.assert_called_once()
    
    async def test_update_brand_not_found(self, service: BrandService, mock_repository: AsyncMock):
        """Test brand update when brand not found."""
        brand_id = uuid4()
        update_data = BrandUpdate(name="Updated Brand")
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match=f"Brand with id {brand_id} not found"):
            await service.update_brand(brand_id, update_data)
    
    async def test_update_brand_name_conflict(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test brand update with name conflict."""
        update_data = BrandUpdate(name="Existing Brand")
        mock_repository.get_by_id.return_value = sample_brand
        mock_repository.exists_by_name.return_value = True
        
        with pytest.raises(ConflictError, match="Brand with name 'Existing Brand' already exists"):
            await service.update_brand(sample_brand.id, update_data)
    
    async def test_update_brand_code_conflict(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test brand update with code conflict."""
        update_data = BrandUpdate(code="EXI")
        mock_repository.get_by_id.return_value = sample_brand
        mock_repository.exists_by_code.return_value = True
        
        with pytest.raises(ConflictError, match="Brand with code 'EXI' already exists"):
            await service.update_brand(sample_brand.id, update_data)
    
    async def test_delete_brand_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand deletion."""
        mock_repository.get_by_id.return_value = sample_brand
        mock_repository.delete.return_value = True
        
        result = await service.delete_brand(sample_brand.id)
        
        assert result is True
        mock_repository.delete.assert_called_once_with(sample_brand.id)
    
    async def test_delete_brand_not_found(self, service: BrandService, mock_repository: AsyncMock):
        """Test brand deletion when not found."""
        brand_id = uuid4()
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match=f"Brand with id {brand_id} not found"):
            await service.delete_brand(brand_id)
    
    async def test_delete_brand_cannot_delete(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test brand deletion when cannot delete."""
        # Mock brand that cannot be deleted
        sample_brand.can_delete = MagicMock(return_value=False)
        mock_repository.get_by_id.return_value = sample_brand
        
        with pytest.raises(BusinessRuleError, match="Cannot delete brand with associated items"):
            await service.delete_brand(sample_brand.id)
    
    async def test_list_brands_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand listing."""
        from app.shared.pagination import Page, PageInfo
        
        # Mock paginated response
        page_info = PageInfo(
            page=1,
            page_size=20,
            total_items=1,
            total_pages=1,
            has_next=False,
            has_previous=False
        )
        page_result = Page(items=[sample_brand], page_info=page_info)
        mock_repository.get_paginated.return_value = page_result
        
        result = await service.list_brands(page=1, page_size=20)
        
        assert len(result.items) == 1
        assert result.items[0].name == sample_brand.name
        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 20
    
    async def test_list_brands_with_filters(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test brand listing with filters."""
        from app.shared.pagination import Page, PageInfo
        
        filters = BrandFilter(name="Test", is_active=True)
        sort_options = BrandSort(field="name", direction="asc")
        
        page_info = PageInfo(
            page=1,
            page_size=20,
            total_items=1,
            total_pages=1,
            has_next=False,
            has_previous=False
        )
        page_result = Page(items=[sample_brand], page_info=page_info)
        mock_repository.get_paginated.return_value = page_result
        
        result = await service.list_brands(
            page=1,
            page_size=20,
            filters=filters,
            sort=sort_options
        )
        
        assert len(result.items) == 1
        mock_repository.get_paginated.assert_called_once()
    
    async def test_search_brands_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand search."""
        mock_repository.search.return_value = [sample_brand]
        
        result = await service.search_brands("Test", limit=10)
        
        assert len(result) == 1
        assert result[0].name == sample_brand.name
        mock_repository.search.assert_called_once_with(
            search_term="Test",
            limit=10,
            include_inactive=False
        )
    
    async def test_get_active_brands_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test getting active brands."""
        mock_repository.get_active_brands.return_value = [sample_brand]
        
        result = await service.get_active_brands()
        
        assert len(result) == 1
        assert result[0].name == sample_brand.name
        mock_repository.get_active_brands.assert_called_once()
    
    async def test_get_brand_statistics_success(self, service: BrandService, mock_repository: AsyncMock):
        """Test getting brand statistics."""
        mock_stats = {
            "total_brands": 10,
            "active_brands": 8,
            "inactive_brands": 2,
            "brands_with_items": 5,
            "brands_without_items": 5
        }
        mock_most_used = []
        
        mock_repository.get_statistics.return_value = mock_stats
        mock_repository.get_most_used_brands.return_value = mock_most_used
        
        result = await service.get_brand_statistics()
        
        assert result.total_brands == 10
        assert result.active_brands == 8
        assert result.inactive_brands == 2
        assert result.brands_with_items == 5
        assert result.brands_without_items == 5
        assert result.most_used_brands == []
    
    async def test_bulk_operation_activate(self, service: BrandService, mock_repository: AsyncMock):
        """Test bulk activation operation."""
        brand_ids = [uuid4(), uuid4()]
        operation = BrandBulkOperation(brand_ids=brand_ids, operation="activate")
        
        mock_repository.bulk_activate.return_value = 2
        
        result = await service.bulk_operation(operation)
        
        assert result.success_count == 2
        assert result.failure_count == 0
        assert len(result.errors) == 0
    
    async def test_bulk_operation_deactivate(self, service: BrandService, mock_repository: AsyncMock):
        """Test bulk deactivation operation."""
        brand_ids = [uuid4(), uuid4()]
        operation = BrandBulkOperation(brand_ids=brand_ids, operation="deactivate")
        
        mock_repository.bulk_deactivate.return_value = 2
        
        result = await service.bulk_operation(operation)
        
        assert result.success_count == 2
        assert result.failure_count == 0
        assert len(result.errors) == 0
    
    async def test_bulk_operation_with_errors(self, service: BrandService, mock_repository: AsyncMock):
        """Test bulk operation with errors."""
        brand_ids = [uuid4(), uuid4()]
        operation = BrandBulkOperation(brand_ids=brand_ids, operation="activate")
        
        # Mock to raise exception for second brand
        mock_repository.bulk_activate.side_effect = [1, Exception("Database error")]
        
        result = await service.bulk_operation(operation)
        
        assert result.success_count == 1
        assert result.failure_count == 1
        assert len(result.errors) == 1
        assert "Database error" in result.errors[0]["error"]
    
    async def test_export_brands_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand export."""
        mock_repository.list.return_value = [sample_brand]
        
        result = await service.export_brands()
        
        assert len(result) == 1
        assert result[0].name == sample_brand.name
        mock_repository.list.assert_called_once_with(
            skip=0,
            limit=10000,
            include_inactive=False
        )
    
    async def test_import_brands_success(self, service: BrandService, mock_repository: AsyncMock):
        """Test successful brand import."""
        import_data = [
            BrandImport(name="Brand 1", code="B1"),
            BrandImport(name="Brand 2", code="B2")
        ]
        
        mock_repository.exists_by_name.return_value = False
        mock_repository.exists_by_code.return_value = False
        mock_repository.create.return_value = MagicMock()
        
        result = await service.import_brands(import_data)
        
        assert result.total_processed == 2
        assert result.successful_imports == 2
        assert result.failed_imports == 0
        assert result.skipped_imports == 0
        assert len(result.errors) == 0
    
    async def test_import_brands_with_duplicates(self, service: BrandService, mock_repository: AsyncMock):
        """Test brand import with duplicate names."""
        import_data = [
            BrandImport(name="Brand 1", code="B1"),
            BrandImport(name="Brand 1", code="B2")  # Duplicate name
        ]
        
        # First brand doesn't exist, second one does
        mock_repository.exists_by_name.side_effect = [False, True]
        mock_repository.exists_by_code.return_value = False
        mock_repository.create.return_value = MagicMock()
        
        result = await service.import_brands(import_data)
        
        assert result.total_processed == 2
        assert result.successful_imports == 1
        assert result.failed_imports == 0
        assert result.skipped_imports == 1
        assert len(result.errors) == 0
    
    async def test_import_brands_with_errors(self, service: BrandService, mock_repository: AsyncMock):
        """Test brand import with errors."""
        import_data = [
            BrandImport(name="Brand 1", code="B1"),
            BrandImport(name="Brand 2", code="B2")
        ]
        
        mock_repository.exists_by_name.return_value = False
        mock_repository.exists_by_code.return_value = False
        mock_repository.create.side_effect = [MagicMock(), Exception("Database error")]
        
        result = await service.import_brands(import_data)
        
        assert result.total_processed == 2
        assert result.successful_imports == 1
        assert result.failed_imports == 1
        assert result.skipped_imports == 0
        assert len(result.errors) == 1
        assert "Database error" in result.errors[0]["error"]
    
    async def test_activate_brand_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand activation."""
        # Set brand as inactive
        sample_brand.is_active = False
        activated_brand = Brand(
            id=sample_brand.id,
            name=sample_brand.name,
            code=sample_brand.code,
            description=sample_brand.description,
            is_active=True
        )
        
        mock_repository.get_by_id.return_value = sample_brand
        mock_repository.update.return_value = activated_brand
        
        result = await service.activate_brand(sample_brand.id)
        
        assert result.is_active is True
        mock_repository.update.assert_called_once_with(sample_brand.id, {"is_active": True})
    
    async def test_activate_brand_already_active(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test activating already active brand."""
        mock_repository.get_by_id.return_value = sample_brand
        
        result = await service.activate_brand(sample_brand.id)
        
        assert result.is_active is True
        # Should not call update since already active
        mock_repository.update.assert_not_called()
    
    async def test_deactivate_brand_success(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test successful brand deactivation."""
        deactivated_brand = Brand(
            id=sample_brand.id,
            name=sample_brand.name,
            code=sample_brand.code,
            description=sample_brand.description,
            is_active=False
        )
        
        mock_repository.get_by_id.return_value = sample_brand
        mock_repository.update.return_value = deactivated_brand
        
        result = await service.deactivate_brand(sample_brand.id)
        
        assert result.is_active is False
        mock_repository.update.assert_called_once_with(sample_brand.id, {"is_active": False})
    
    async def test_deactivate_brand_already_inactive(self, service: BrandService, mock_repository: AsyncMock, sample_brand: Brand):
        """Test deactivating already inactive brand."""
        sample_brand.is_active = False
        mock_repository.get_by_id.return_value = sample_brand
        
        result = await service.deactivate_brand(sample_brand.id)
        
        assert result.is_active is False
        # Should not call update since already inactive
        mock_repository.update.assert_not_called()