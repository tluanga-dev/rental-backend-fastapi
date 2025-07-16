import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.models import Company
from app.modules.company.service import CompanyService
from app.modules.company.repository import CompanyRepository
from app.modules.company.schemas import CompanyCreate


@pytest_asyncio.fixture
async def company_repository(db_session: AsyncSession) -> CompanyRepository:
    """Create company repository instance."""
    return CompanyRepository(db_session)


@pytest_asyncio.fixture
async def company_service(company_repository: CompanyRepository) -> CompanyService:
    """Create company service instance."""
    return CompanyService(company_repository)


@pytest_asyncio.fixture
async def test_company(company_service: CompanyService) -> Company:
    """Create a test company."""
    company_data = CompanyCreate(
        company_name="Test Company Pvt Ltd",
        address="123 Test Street, Test City, Test State 12345",
        email="test@testcompany.com",
        phone="+91-1234567890",
        gst_no="29ABCDE1234F1Z5",
        registration_number="REG123456789"
    )
    
    company_response = await company_service.create_company(
        company_data=company_data,
        created_by="test_user"
    )
    
    # Get the actual company model from the response
    company = await company_service.repository.get_by_id(company_response.id)
    return company


@pytest_asyncio.fixture
async def test_company_2(company_service: CompanyService) -> Company:
    """Create a second test company."""
    company_data = CompanyCreate(
        company_name="Another Test Company LLC",
        address="456 Another Street, Another City, Another State 67890",
        email="info@anothercompany.com",
        phone="+91-9876543210",
        gst_no="27FGHIJ5678K2M6",
        registration_number="REG987654321"
    )
    
    company_response = await company_service.create_company(
        company_data=company_data,
        created_by="test_user"
    )
    
    # Get the actual company model from the response
    company = await company_service.repository.get_by_id(company_response.id)
    return company


@pytest.fixture
def company_create_data() -> dict:
    """Sample company creation data."""
    return {
        "company_name": "Sample Company Inc",
        "address": "789 Sample Road, Sample City, Sample State 54321",
        "email": "contact@samplecompany.com",
        "phone": "+91-5555555555",
        "gst_no": "33PQRST9012L3N7",
        "registration_number": "REG555555555"
    }


@pytest.fixture
def company_update_data() -> dict:
    """Sample company update data."""
    return {
        "company_name": "Updated Company Inc",
        "address": "999 Updated Street, Updated City, Updated State 99999",
        "email": "updated@updatedcompany.com",
        "phone": "+91-9999999999"
    }