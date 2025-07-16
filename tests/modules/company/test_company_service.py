import pytest
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.service import CompanyService
from app.modules.company.schemas import (
    CompanyCreate, CompanyUpdate, CompanyFilter, CompanySort
)
from app.core.errors import NotFoundError, ConflictError, BusinessRuleError


@pytest.mark.asyncio
class TestCompanyService:
    """Test cases for company service."""
    
    async def test_create_company(self, company_service: CompanyService):
        """Test creating a new company."""
        # Arrange
        company_data = CompanyCreate(
            company_name="New Test Company",
            address="New Address",
            email="new@company.com",
            phone="+91-1111111111",
            gst_no="12ABCDE3456F7G8",
            registration_number="NEWREG123"
        )
        
        # Act
        company = await company_service.create_company(
            company_data=company_data,
            created_by="test_user"
        )
        
        # Assert
        assert company.id is not None
        assert company.company_name == "New Test Company"
        assert company.email == "new@company.com"
        assert company.gst_no == "12ABCDE3456F7G8"
        assert company.registration_number == "NEWREG123"
        assert company.is_active is True
        assert company.created_by == "test_user"
    
    async def test_create_company_duplicate_name(
        self, company_service: CompanyService, test_company
    ):
        """Test creating a company with duplicate name."""
        # Arrange
        company_data = CompanyCreate(
            company_name=test_company.company_name,  # Use existing name
            email="different@company.com"
        )
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await company_service.create_company(company_data)
        
        assert "already exists" in str(exc_info.value)
    
    async def test_create_company_duplicate_gst(
        self, company_service: CompanyService, test_company
    ):
        """Test creating a company with duplicate GST number."""
        # Arrange
        company_data = CompanyCreate(
            company_name="Different Company",
            gst_no=test_company.gst_no  # Use existing GST
        )
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await company_service.create_company(company_data)
        
        assert "GST number" in str(exc_info.value)
    
    async def test_get_company(self, company_service: CompanyService, test_company):
        """Test getting a company by ID."""
        # Act
        company = await company_service.get_company(test_company.id)
        
        # Assert
        assert company.id == test_company.id
        assert company.company_name == test_company.company_name
        assert company.email == test_company.email
    
    async def test_get_company_not_found(self, company_service: CompanyService):
        """Test getting a non-existent company."""
        # Arrange
        fake_id = UUID("00000000-0000-0000-0000-000000000000")
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await company_service.get_company(fake_id)
    
    async def test_get_active_company(
        self, company_service: CompanyService, test_company
    ):
        """Test getting the active company."""
        # Act
        company = await company_service.get_active_company()
        
        # Assert
        assert company.id == test_company.id
        assert company.is_active is True
    
    async def test_update_company(self, company_service: CompanyService, test_company):
        """Test updating a company."""
        # Arrange
        update_data = CompanyUpdate(
            company_name="Updated Company Name",
            email="updated@company.com",
            phone="+91-2222222222"
        )
        
        # Act
        updated_company = await company_service.update_company(
            company_id=test_company.id,
            company_data=update_data,
            updated_by="test_updater"
        )
        
        # Assert
        assert updated_company.company_name == "Updated Company Name"
        assert updated_company.email == "updated@company.com"
        assert updated_company.phone == "+91-2222222222"
        assert updated_company.updated_by == "test_updater"
        # Unchanged fields
        assert updated_company.gst_no == test_company.gst_no
        assert updated_company.registration_number == test_company.registration_number
    
    async def test_update_company_duplicate_name(
        self, company_service: CompanyService, test_company, test_company_2
    ):
        """Test updating a company with duplicate name."""
        # Arrange
        update_data = CompanyUpdate(
            company_name=test_company_2.company_name  # Use another company's name
        )
        
        # Act & Assert
        with pytest.raises(ConflictError) as exc_info:
            await company_service.update_company(
                company_id=test_company.id,
                company_data=update_data
            )
        
        assert "already exists" in str(exc_info.value)
    
    async def test_delete_company(
        self, company_service: CompanyService, test_company, test_company_2
    ):
        """Test soft deleting a company."""
        # Ensure test_company_2 is active
        await company_service.activate_company(test_company_2.id)
        
        # Act
        success = await company_service.delete_company(test_company.id)
        
        # Assert
        assert success is True
        
        # Verify company is soft deleted
        deleted_company = await company_service.repository.get_by_id(test_company.id)
        assert deleted_company.is_active is False
    
    async def test_delete_only_active_company(
        self, company_service: CompanyService, test_company
    ):
        """Test deleting the only active company."""
        # Deactivate all other companies
        await company_service.activate_company(test_company.id)
        
        # Act & Assert
        with pytest.raises(BusinessRuleError) as exc_info:
            await company_service.delete_company(test_company.id)
        
        assert "Cannot delete the only active company" in str(exc_info.value)
    
    async def test_activate_company(
        self, company_service: CompanyService, test_company, test_company_2
    ):
        """Test activating a company."""
        # Act
        activated = await company_service.activate_company(test_company_2.id)
        
        # Assert
        assert activated.id == test_company_2.id
        assert activated.is_active is True
        
        # Verify first company is deactivated
        first_company = await company_service.repository.get_by_id(test_company.id)
        assert first_company.is_active is False
    
    async def test_list_companies(
        self, company_service: CompanyService, test_company, test_company_2
    ):
        """Test listing companies with pagination."""
        # Act
        result = await company_service.list_companies(
            page=1,
            page_size=10,
            include_inactive=True
        )
        
        # Assert
        assert result.total >= 2
        assert len(result.items) >= 2
        assert result.page == 1
        assert result.has_next is False
        assert result.has_previous is False
    
    async def test_list_companies_with_filter(
        self, company_service: CompanyService, test_company, test_company_2
    ):
        """Test listing companies with filters."""
        # Arrange
        filter_params = CompanyFilter(
            company_name="Test Company Pvt"  # Partial match
        )
        
        # Act
        result = await company_service.list_companies(
            page=1,
            page_size=10,
            filter_params=filter_params
        )
        
        # Assert
        assert result.total >= 1
        assert any(
            "Test Company Pvt" in item.company_name 
            for item in result.items
        )
    
    async def test_list_companies_with_sort(
        self, company_service: CompanyService, test_company, test_company_2
    ):
        """Test listing companies with sorting."""
        # Arrange
        sort_params = CompanySort(
            field="company_name",
            direction="desc"
        )
        
        # Act
        result = await company_service.list_companies(
            page=1,
            page_size=10,
            sort_params=sort_params,
            include_inactive=True
        )
        
        # Assert
        assert len(result.items) >= 2
        # Verify descending order
        if len(result.items) >= 2:
            assert result.items[0].company_name >= result.items[1].company_name
    
    async def test_search_companies(
        self, company_service: CompanyService, test_company, test_company_2
    ):
        """Test searching companies."""
        # Act
        results = await company_service.search_companies(
            search_term="Test",
            limit=10,
            include_inactive=True
        )
        
        # Assert
        assert len(results) >= 2
        assert all("Test" in company.company_name for company in results)
    
    async def test_search_companies_by_gst(
        self, company_service: CompanyService, test_company
    ):
        """Test searching companies by GST number."""
        # Act
        results = await company_service.search_companies(
            search_term=test_company.gst_no[:5],  # Partial GST
            limit=10
        )
        
        # Assert
        assert len(results) >= 1
        assert any(
            company.id == test_company.id 
            for company in results
        )