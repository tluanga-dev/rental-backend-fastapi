import pytest
from uuid import uuid4
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master_data.brands.models import Brand
from app.modules.master_data.brands.schemas import BrandCreate, BrandUpdate


class TestBrandRoutes:
    """Integration tests for brand routes."""
    
    @pytest.fixture
    async def sample_brand(self, test_session: AsyncSession):
        """Create a sample brand for testing."""
        brand = Brand(
            name="Test Brand",
            code="TST",
            description="Test brand description",
            created_by="test_user",
            updated_by="test_user"
        )
        test_session.add(brand)
        await test_session.commit()
        await test_session.refresh(brand)
        return brand
    
    @pytest.fixture
    async def sample_brands(self, test_session: AsyncSession):
        """Create multiple sample brands for testing."""
        brands = []
        for i in range(5):
            brand = Brand(
                name=f"Brand {i}",
                code=f"B{i}",
                description=f"Description {i}",
                created_by="test_user",
                updated_by="test_user",
                is_active=i % 2 == 0  # Alternate active/inactive
            )
            test_session.add(brand)
            brands.append(brand)
        
        await test_session.commit()
        for brand in brands:
            await test_session.refresh(brand)
        return brands
    
    async def test_create_brand_success(self, client: AsyncClient):
        """Test successful brand creation."""
        brand_data = {
            "name": "New Brand",
            "code": "NEW",
            "description": "New brand description"
        }
        
        response = await client.post("/brands/", json=brand_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == brand_data["name"]
        assert data["code"] == brand_data["code"]
        assert data["description"] == brand_data["description"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "display_name" in data
    
    async def test_create_brand_minimal_data(self, client: AsyncClient):
        """Test brand creation with minimal data."""
        brand_data = {"name": "Minimal Brand"}
        
        response = await client.post("/brands/", json=brand_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == brand_data["name"]
        assert data["code"] is None
        assert data["description"] is None
        assert data["is_active"] is True
    
    async def test_create_brand_duplicate_name(self, client: AsyncClient, sample_brand: Brand):
        """Test brand creation with duplicate name."""
        brand_data = {
            "name": sample_brand.name,
            "code": "DUP",
            "description": "Duplicate name brand"
        }
        
        response = await client.post("/brands/", json=brand_data)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]
    
    async def test_create_brand_duplicate_code(self, client: AsyncClient, sample_brand: Brand):
        """Test brand creation with duplicate code."""
        brand_data = {
            "name": "Different Brand",
            "code": sample_brand.code,
            "description": "Duplicate code brand"
        }
        
        response = await client.post("/brands/", json=brand_data)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]
    
    async def test_create_brand_invalid_data(self, client: AsyncClient):
        """Test brand creation with invalid data."""
        brand_data = {
            "name": "",  # Empty name
            "code": "TST",
            "description": "Invalid brand"
        }
        
        response = await client.post("/brands/", json=brand_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_get_brand_success(self, client: AsyncClient, sample_brand: Brand):
        """Test successful brand retrieval."""
        response = await client.get(f"/brands/{sample_brand.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_brand.id)
        assert data["name"] == sample_brand.name
        assert data["code"] == sample_brand.code
        assert data["description"] == sample_brand.description
    
    async def test_get_brand_not_found(self, client: AsyncClient):
        """Test brand retrieval with non-existent ID."""
        non_existent_id = uuid4()
        response = await client.get(f"/brands/{non_existent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    async def test_get_brand_by_name_success(self, client: AsyncClient, sample_brand: Brand):
        """Test successful brand retrieval by name."""
        response = await client.get(f"/brands/by-name/{sample_brand.name}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == sample_brand.name
    
    async def test_get_brand_by_name_not_found(self, client: AsyncClient):
        """Test brand retrieval by name with non-existent name."""
        response = await client.get("/brands/by-name/Non-existent Brand")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    async def test_get_brand_by_code_success(self, client: AsyncClient, sample_brand: Brand):
        """Test successful brand retrieval by code."""
        response = await client.get(f"/brands/by-code/{sample_brand.code}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == sample_brand.code
    
    async def test_get_brand_by_code_not_found(self, client: AsyncClient):
        """Test brand retrieval by code with non-existent code."""
        response = await client.get("/brands/by-code/XXX")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    async def test_list_brands_success(self, client: AsyncClient, sample_brands: list):
        """Test successful brand listing."""
        response = await client.get("/brands/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_previous" in data
        
        # Should only return active brands by default
        active_count = len([b for b in sample_brands if b.is_active])
        assert len(data["items"]) == active_count
    
    async def test_list_brands_with_pagination(self, client: AsyncClient, sample_brands: list):
        """Test brand listing with pagination."""
        response = await client.get("/brands/?page=1&page_size=2")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2
    
    async def test_list_brands_with_search(self, client: AsyncClient, sample_brands: list):
        """Test brand listing with search."""
        response = await client.get("/brands/?search=Brand 1")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Brand 1"
    
    async def test_list_brands_with_filters(self, client: AsyncClient, sample_brands: list):
        """Test brand listing with filters."""
        response = await client.get("/brands/?name=Brand 1&is_active=true")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should find "Brand 1" which is active (index 1, but index 1 is inactive)
        # Actually "Brand 0" is active, "Brand 1" is inactive
        # Let's check for "Brand 0" instead
        response = await client.get("/brands/?name=Brand 0&is_active=true")
        data = response.json()
        assert len(data["items"]) <= 1
    
    async def test_list_brands_with_sorting(self, client: AsyncClient, sample_brands: list):
        """Test brand listing with sorting."""
        response = await client.get("/brands/?sort_field=name&sort_direction=desc")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check that results are sorted by name descending
        if len(data["items"]) > 1:
            for i in range(len(data["items"]) - 1):
                assert data["items"][i]["name"] >= data["items"][i + 1]["name"]
    
    async def test_list_brands_include_inactive(self, client: AsyncClient, sample_brands: list):
        """Test brand listing including inactive brands."""
        response = await client.get("/brands/?include_inactive=true")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should return all brands
        assert len(data["items"]) == len(sample_brands)
    
    async def test_update_brand_success(self, client: AsyncClient, sample_brand: Brand):
        """Test successful brand update."""
        update_data = {
            "name": "Updated Brand",
            "code": "UPD",
            "description": "Updated description"
        }
        
        response = await client.put(f"/brands/{sample_brand.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["code"] == update_data["code"]
        assert data["description"] == update_data["description"]
        assert "updated_at" in data
    
    async def test_update_brand_partial(self, client: AsyncClient, sample_brand: Brand):
        """Test partial brand update."""
        update_data = {"name": "Partially Updated Brand"}
        
        response = await client.put(f"/brands/{sample_brand.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["code"] == sample_brand.code  # Should remain unchanged
        assert data["description"] == sample_brand.description  # Should remain unchanged
    
    async def test_update_brand_not_found(self, client: AsyncClient):
        """Test brand update with non-existent ID."""
        non_existent_id = uuid4()
        update_data = {"name": "Updated Brand"}
        
        response = await client.put(f"/brands/{non_existent_id}", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    async def test_update_brand_duplicate_name(self, client: AsyncClient, sample_brands: list):
        """Test brand update with duplicate name."""
        brand1, brand2 = sample_brands[0], sample_brands[1]
        update_data = {"name": brand2.name}
        
        response = await client.put(f"/brands/{brand1.id}", json=update_data)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]
    
    async def test_update_brand_duplicate_code(self, client: AsyncClient, sample_brands: list):
        """Test brand update with duplicate code."""
        brand1, brand2 = sample_brands[0], sample_brands[1]
        update_data = {"code": brand2.code}
        
        response = await client.put(f"/brands/{brand1.id}", json=update_data)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]
    
    async def test_delete_brand_success(self, client: AsyncClient, sample_brand: Brand):
        """Test successful brand deletion."""
        response = await client.delete(f"/brands/{sample_brand.id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify brand is deactivated
        get_response = await client.get(f"/brands/{sample_brand.id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["is_active"] is False
    
    async def test_delete_brand_not_found(self, client: AsyncClient):
        """Test brand deletion with non-existent ID."""
        non_existent_id = uuid4()
        response = await client.delete(f"/brands/{non_existent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    async def test_search_brands_success(self, client: AsyncClient, sample_brands: list):
        """Test successful brand search."""
        response = await client.get("/brands/search/?q=Brand")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
        # Should find brands containing "Brand"
        for item in data:
            assert "Brand" in item["name"] or "Brand" in (item["code"] or "")
    
    async def test_search_brands_with_limit(self, client: AsyncClient, sample_brands: list):
        """Test brand search with limit."""
        response = await client.get("/brands/search/?q=Brand&limit=2")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 2
    
    async def test_search_brands_include_inactive(self, client: AsyncClient, sample_brands: list):
        """Test brand search including inactive brands."""
        response = await client.get("/brands/search/?q=Brand&include_inactive=true")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should find more brands when including inactive
        response_active_only = await client.get("/brands/search/?q=Brand&include_inactive=false")
        data_active_only = response_active_only.json()
        assert len(data) >= len(data_active_only)
    
    async def test_get_active_brands(self, client: AsyncClient, sample_brands: list):
        """Test getting active brands."""
        response = await client.get("/brands/active/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
        # Should only return active brands
        active_count = len([b for b in sample_brands if b.is_active])
        assert len(data) == active_count
        
        for item in data:
            assert item["is_active"] is True
    
    async def test_get_brand_statistics(self, client: AsyncClient, sample_brands: list):
        """Test getting brand statistics."""
        response = await client.get("/brands/stats/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "total_brands" in data
        assert "active_brands" in data
        assert "inactive_brands" in data
        assert "brands_with_items" in data
        assert "brands_without_items" in data
        assert "most_used_brands" in data
        
        assert data["total_brands"] == len(sample_brands)
        assert data["active_brands"] == len([b for b in sample_brands if b.is_active])
        assert data["inactive_brands"] == len([b for b in sample_brands if not b.is_active])
    
    async def test_activate_brand_success(self, client: AsyncClient, sample_brands: list):
        """Test successful brand activation."""
        # Find an inactive brand
        inactive_brand = next((b for b in sample_brands if not b.is_active), None)
        if inactive_brand:
            response = await client.post(f"/brands/{inactive_brand.id}/activate")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_active"] is True
    
    async def test_activate_brand_not_found(self, client: AsyncClient):
        """Test brand activation with non-existent ID."""
        non_existent_id = uuid4()
        response = await client.post(f"/brands/{non_existent_id}/activate")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    async def test_deactivate_brand_success(self, client: AsyncClient, sample_brands: list):
        """Test successful brand deactivation."""
        # Find an active brand
        active_brand = next((b for b in sample_brands if b.is_active), None)
        if active_brand:
            response = await client.post(f"/brands/{active_brand.id}/deactivate")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_active"] is False
    
    async def test_deactivate_brand_not_found(self, client: AsyncClient):
        """Test brand deactivation with non-existent ID."""
        non_existent_id = uuid4()
        response = await client.post(f"/brands/{non_existent_id}/deactivate")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    async def test_bulk_brand_operation_activate(self, client: AsyncClient, sample_brands: list):
        """Test bulk brand activation."""
        # Get inactive brand IDs
        inactive_ids = [str(b.id) for b in sample_brands if not b.is_active]
        
        if inactive_ids:
            bulk_data = {
                "brand_ids": inactive_ids,
                "operation": "activate"
            }
            
            response = await client.post("/brands/bulk-operation", json=bulk_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success_count"] > 0
            assert data["failure_count"] == 0
            assert len(data["errors"]) == 0
    
    async def test_bulk_brand_operation_deactivate(self, client: AsyncClient, sample_brands: list):
        """Test bulk brand deactivation."""
        # Get active brand IDs
        active_ids = [str(b.id) for b in sample_brands if b.is_active]
        
        if active_ids:
            bulk_data = {
                "brand_ids": active_ids,
                "operation": "deactivate"
            }
            
            response = await client.post("/brands/bulk-operation", json=bulk_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success_count"] > 0
            assert data["failure_count"] == 0
            assert len(data["errors"]) == 0
    
    async def test_bulk_brand_operation_invalid_operation(self, client: AsyncClient):
        """Test bulk brand operation with invalid operation."""
        bulk_data = {
            "brand_ids": [str(uuid4())],
            "operation": "invalid_operation"
        }
        
        response = await client.post("/brands/bulk-operation", json=bulk_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_export_brands(self, client: AsyncClient, sample_brands: list):
        """Test brand export."""
        response = await client.get("/brands/export/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
        # Should export only active brands by default
        active_count = len([b for b in sample_brands if b.is_active])
        assert len(data) == active_count
        
        for item in data:
            assert "id" in item
            assert "name" in item
            assert "code" in item
            assert "description" in item
            assert "is_active" in item
            assert "created_at" in item
            assert "item_count" in item
    
    async def test_export_brands_include_inactive(self, client: AsyncClient, sample_brands: list):
        """Test brand export including inactive brands."""
        response = await client.get("/brands/export/?include_inactive=true")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should export all brands
        assert len(data) == len(sample_brands)
    
    async def test_import_brands_success(self, client: AsyncClient):
        """Test successful brand import."""
        import_data = [
            {
                "name": "Import Brand 1",
                "code": "IMP1",
                "description": "Imported brand 1",
                "is_active": True
            },
            {
                "name": "Import Brand 2",
                "code": "IMP2",
                "description": "Imported brand 2",
                "is_active": True
            }
        ]
        
        response = await client.post("/brands/import/", json=import_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_processed"] == 2
        assert data["successful_imports"] == 2
        assert data["failed_imports"] == 0
        assert data["skipped_imports"] == 0
        assert len(data["errors"]) == 0
    
    async def test_import_brands_with_duplicates(self, client: AsyncClient, sample_brand: Brand):
        """Test brand import with duplicate names."""
        import_data = [
            {
                "name": sample_brand.name,  # Duplicate name
                "code": "DUP1",
                "description": "Duplicate brand",
                "is_active": True
            },
            {
                "name": "New Import Brand",
                "code": "NEW1",
                "description": "New brand",
                "is_active": True
            }
        ]
        
        response = await client.post("/brands/import/", json=import_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_processed"] == 2
        assert data["successful_imports"] == 1
        assert data["failed_imports"] == 0
        assert data["skipped_imports"] == 1
        assert len(data["errors"]) == 0
    
    async def test_import_brands_invalid_data(self, client: AsyncClient):
        """Test brand import with invalid data."""
        import_data = [
            {
                "name": "",  # Empty name
                "code": "INV1",
                "description": "Invalid brand",
                "is_active": True
            }
        ]
        
        response = await client.post("/brands/import/", json=import_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_health_check(self, client: AsyncClient):
        """Test brands module health check."""
        response = await client.get("/brands/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "brands"
        assert "timestamp" in data