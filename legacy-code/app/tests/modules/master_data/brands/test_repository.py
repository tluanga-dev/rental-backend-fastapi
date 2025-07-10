import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master_data.brands.repository import BrandRepository
from app.modules.master_data.brands.models import Brand


class TestBrandRepository:
    """Tests for BrandRepository."""
    
    @pytest.fixture
    async def repository(self, test_session: AsyncSession):
        """Create repository instance."""
        return BrandRepository(test_session)
    
    @pytest.fixture
    async def sample_brand_data(self):
        """Sample brand data for testing."""
        return {
            "name": "Test Brand",
            "code": "TST",
            "description": "Test brand description",
            "created_by": "test_user",
            "updated_by": "test_user"
        }
    
    @pytest.fixture
    async def sample_brands(self, repository: BrandRepository):
        """Create sample brands for testing."""
        brands = []
        for i in range(5):
            brand_data = {
                "name": f"Brand {i}",
                "code": f"B{i}",
                "description": f"Description {i}",
                "created_by": "test_user",
                "updated_by": "test_user",
                "is_active": i % 2 == 0  # Alternate active/inactive
            }
            brand = await repository.create(brand_data)
            brands.append(brand)
        return brands
    
    async def test_create_brand(self, repository: BrandRepository, sample_brand_data: dict):
        """Test creating a brand."""
        brand = await repository.create(sample_brand_data)
        
        assert brand.id is not None
        assert brand.name == sample_brand_data["name"]
        assert brand.code == sample_brand_data["code"]
        assert brand.description == sample_brand_data["description"]
        assert brand.created_by == sample_brand_data["created_by"]
        assert brand.updated_by == sample_brand_data["updated_by"]
        assert brand.is_active is True
        assert brand.created_at is not None
    
    async def test_create_brand_minimal(self, repository: BrandRepository):
        """Test creating a brand with minimal data."""
        brand_data = {"name": "Minimal Brand"}
        brand = await repository.create(brand_data)
        
        assert brand.id is not None
        assert brand.name == "Minimal Brand"
        assert brand.code is None
        assert brand.description is None
        assert brand.is_active is True
    
    async def test_get_by_id(self, repository: BrandRepository, sample_brand_data: dict):
        """Test getting a brand by ID."""
        created_brand = await repository.create(sample_brand_data)
        
        retrieved_brand = await repository.get_by_id(created_brand.id)
        
        assert retrieved_brand is not None
        assert retrieved_brand.id == created_brand.id
        assert retrieved_brand.name == created_brand.name
        assert retrieved_brand.code == created_brand.code
    
    async def test_get_by_id_not_found(self, repository: BrandRepository):
        """Test getting a brand by non-existent ID."""
        non_existent_id = uuid4()
        brand = await repository.get_by_id(non_existent_id)
        
        assert brand is None
    
    async def test_get_by_name(self, repository: BrandRepository, sample_brand_data: dict):
        """Test getting a brand by name."""
        created_brand = await repository.create(sample_brand_data)
        
        retrieved_brand = await repository.get_by_name(sample_brand_data["name"])
        
        assert retrieved_brand is not None
        assert retrieved_brand.id == created_brand.id
        assert retrieved_brand.name == sample_brand_data["name"]
    
    async def test_get_by_name_not_found(self, repository: BrandRepository):
        """Test getting a brand by non-existent name."""
        brand = await repository.get_by_name("Non-existent Brand")
        
        assert brand is None
    
    async def test_get_by_code(self, repository: BrandRepository, sample_brand_data: dict):
        """Test getting a brand by code."""
        created_brand = await repository.create(sample_brand_data)
        
        retrieved_brand = await repository.get_by_code(sample_brand_data["code"])
        
        assert retrieved_brand is not None
        assert retrieved_brand.id == created_brand.id
        assert retrieved_brand.code == sample_brand_data["code"]
    
    async def test_get_by_code_not_found(self, repository: BrandRepository):
        """Test getting a brand by non-existent code."""
        brand = await repository.get_by_code("XXX")
        
        assert brand is None
    
    async def test_list_brands(self, repository: BrandRepository, sample_brands: list):
        """Test listing brands."""
        brands = await repository.list(limit=10)
        
        assert len(brands) == len(sample_brands)
        # Check ordering (should be by name by default)
        for i in range(len(brands) - 1):
            assert brands[i].name <= brands[i + 1].name
    
    async def test_list_brands_with_pagination(self, repository: BrandRepository, sample_brands: list):
        """Test listing brands with pagination."""
        # Get first 2 brands
        brands_page1 = await repository.list(skip=0, limit=2)
        assert len(brands_page1) == 2
        
        # Get next 2 brands
        brands_page2 = await repository.list(skip=2, limit=2)
        assert len(brands_page2) == 2
        
        # Ensure different results
        assert brands_page1[0].id != brands_page2[0].id
    
    async def test_list_brands_active_only(self, repository: BrandRepository, sample_brands: list):
        """Test listing only active brands."""
        active_brands = await repository.list(include_inactive=False)
        
        # Should only get active brands (even indices from sample_brands)
        expected_count = len([b for b in sample_brands if b.is_active])
        assert len(active_brands) == expected_count
        
        for brand in active_brands:
            assert brand.is_active is True
    
    async def test_list_brands_with_filters(self, repository: BrandRepository, sample_brands: list):
        """Test listing brands with filters."""
        # Filter by name
        filters = {"name": "Brand 1"}
        brands = await repository.list(filters=filters)
        
        assert len(brands) == 1
        assert brands[0].name == "Brand 1"
    
    async def test_list_brands_with_search(self, repository: BrandRepository, sample_brands: list):
        """Test listing brands with search."""
        filters = {"search": "Brand"}
        brands = await repository.list(filters=filters)
        
        # Should find all brands as they all contain "Brand"
        assert len(brands) == len(sample_brands)
    
    async def test_list_brands_with_sorting(self, repository: BrandRepository, sample_brands: list):
        """Test listing brands with sorting."""
        # Sort by name descending
        brands = await repository.list(sort_by="name", sort_order="desc")
        
        # Check descending order
        for i in range(len(brands) - 1):
            assert brands[i].name >= brands[i + 1].name
    
    async def test_get_paginated(self, repository: BrandRepository, sample_brands: list):
        """Test getting paginated brands."""
        page_result = await repository.get_paginated(page=1, page_size=2)
        
        assert len(page_result.items) == 2
        assert page_result.page_info.page == 1
        assert page_result.page_info.page_size == 2
        assert page_result.page_info.total_items == len(sample_brands)
        assert page_result.page_info.total_pages == 3  # 5 items / 2 per page = 3 pages
        assert page_result.page_info.has_next is True
        assert page_result.page_info.has_previous is False
    
    async def test_update_brand(self, repository: BrandRepository, sample_brand_data: dict):
        """Test updating a brand."""
        created_brand = await repository.create(sample_brand_data)
        
        update_data = {
            "name": "Updated Brand",
            "code": "UPD",
            "description": "Updated description",
            "updated_by": "updater"
        }
        
        updated_brand = await repository.update(created_brand.id, update_data)
        
        assert updated_brand is not None
        assert updated_brand.id == created_brand.id
        assert updated_brand.name == "Updated Brand"
        assert updated_brand.code == "UPD"
        assert updated_brand.description == "Updated description"
        assert updated_brand.updated_by == "updater"
        assert updated_brand.updated_at is not None
    
    async def test_update_brand_not_found(self, repository: BrandRepository):
        """Test updating a non-existent brand."""
        non_existent_id = uuid4()
        update_data = {"name": "Updated Brand"}
        
        updated_brand = await repository.update(non_existent_id, update_data)
        
        assert updated_brand is None
    
    async def test_delete_brand(self, repository: BrandRepository, sample_brand_data: dict):
        """Test soft deleting a brand."""
        created_brand = await repository.create(sample_brand_data)
        
        success = await repository.delete(created_brand.id)
        
        assert success is True
        
        # Check that brand is marked as inactive
        retrieved_brand = await repository.get_by_id(created_brand.id)
        assert retrieved_brand.is_active is False
    
    async def test_delete_brand_not_found(self, repository: BrandRepository):
        """Test deleting a non-existent brand."""
        non_existent_id = uuid4()
        
        success = await repository.delete(non_existent_id)
        
        assert success is False
    
    async def test_count_brands(self, repository: BrandRepository, sample_brands: list):
        """Test counting brands."""
        count = await repository.count()
        
        # Should count only active brands by default
        expected_count = len([b for b in sample_brands if b.is_active])
        assert count == expected_count
    
    async def test_count_brands_with_filters(self, repository: BrandRepository, sample_brands: list):
        """Test counting brands with filters."""
        filters = {"name": "Brand 1"}
        count = await repository.count(filters=filters)
        
        assert count == 1
    
    async def test_count_brands_include_inactive(self, repository: BrandRepository, sample_brands: list):
        """Test counting brands including inactive ones."""
        count = await repository.count(include_inactive=True)
        
        assert count == len(sample_brands)
    
    async def test_exists_by_name(self, repository: BrandRepository, sample_brand_data: dict):
        """Test checking if brand exists by name."""
        created_brand = await repository.create(sample_brand_data)
        
        exists = await repository.exists_by_name(sample_brand_data["name"])
        assert exists is True
        
        exists = await repository.exists_by_name("Non-existent Brand")
        assert exists is False
    
    async def test_exists_by_name_exclude_id(self, repository: BrandRepository, sample_brand_data: dict):
        """Test checking if brand exists by name excluding specific ID."""
        created_brand = await repository.create(sample_brand_data)
        
        # Should not exist when excluding the created brand's ID
        exists = await repository.exists_by_name(
            sample_brand_data["name"], 
            exclude_id=created_brand.id
        )
        assert exists is False
        
        # Should exist when not excluding
        exists = await repository.exists_by_name(sample_brand_data["name"])
        assert exists is True
    
    async def test_exists_by_code(self, repository: BrandRepository, sample_brand_data: dict):
        """Test checking if brand exists by code."""
        created_brand = await repository.create(sample_brand_data)
        
        exists = await repository.exists_by_code(sample_brand_data["code"])
        assert exists is True
        
        exists = await repository.exists_by_code("XXX")
        assert exists is False
    
    async def test_exists_by_code_exclude_id(self, repository: BrandRepository, sample_brand_data: dict):
        """Test checking if brand exists by code excluding specific ID."""
        created_brand = await repository.create(sample_brand_data)
        
        # Should not exist when excluding the created brand's ID
        exists = await repository.exists_by_code(
            sample_brand_data["code"], 
            exclude_id=created_brand.id
        )
        assert exists is False
        
        # Should exist when not excluding
        exists = await repository.exists_by_code(sample_brand_data["code"])
        assert exists is True
    
    async def test_search_brands(self, repository: BrandRepository, sample_brands: list):
        """Test searching brands."""
        results = await repository.search("Brand", limit=3)
        
        assert len(results) <= 3
        for brand in results:
            assert "Brand" in brand.name or "Brand" in (brand.code or "") or "Brand" in (brand.description or "")
    
    async def test_get_active_brands(self, repository: BrandRepository, sample_brands: list):
        """Test getting active brands."""
        active_brands = await repository.get_active_brands()
        
        expected_count = len([b for b in sample_brands if b.is_active])
        assert len(active_brands) == expected_count
        
        for brand in active_brands:
            assert brand.is_active is True
    
    async def test_get_inactive_brands(self, repository: BrandRepository, sample_brands: list):
        """Test getting inactive brands."""
        inactive_brands = await repository.get_inactive_brands()
        
        expected_count = len([b for b in sample_brands if not b.is_active])
        assert len(inactive_brands) == expected_count
        
        for brand in inactive_brands:
            assert brand.is_active is False
    
    async def test_bulk_activate(self, repository: BrandRepository, sample_brands: list):
        """Test bulk activating brands."""
        # Get IDs of inactive brands
        inactive_ids = [b.id for b in sample_brands if not b.is_active]
        
        count = await repository.bulk_activate(inactive_ids)
        
        assert count == len(inactive_ids)
        
        # Check that brands are now active
        for brand_id in inactive_ids:
            brand = await repository.get_by_id(brand_id)
            assert brand.is_active is True
    
    async def test_bulk_deactivate(self, repository: BrandRepository, sample_brands: list):
        """Test bulk deactivating brands."""
        # Get IDs of active brands
        active_ids = [b.id for b in sample_brands if b.is_active]
        
        count = await repository.bulk_deactivate(active_ids)
        
        assert count == len(active_ids)
        
        # Check that brands are now inactive
        for brand_id in active_ids:
            brand = await repository.get_by_id(brand_id)
            assert brand.is_active is False
    
    async def test_get_statistics(self, repository: BrandRepository, sample_brands: list):
        """Test getting brand statistics."""
        stats = await repository.get_statistics()
        
        assert stats["total_brands"] == len(sample_brands)
        assert stats["active_brands"] == len([b for b in sample_brands if b.is_active])
        assert stats["inactive_brands"] == len([b for b in sample_brands if not b.is_active])
        assert stats["brands_with_items"] == 0  # No items in test
        assert stats["brands_without_items"] == len(sample_brands)
    
    async def test_get_most_used_brands(self, repository: BrandRepository, sample_brands: list):
        """Test getting most used brands."""
        most_used = await repository.get_most_used_brands(limit=3)
        
        # Should return empty list since no items relationship is available
        assert isinstance(most_used, list)
        assert len(most_used) == 0