import pytest
import pytest_asyncio
from uuid import uuid4
from decimal import Decimal

from app.modules.customers.service import CustomerService
from app.modules.customers.models import Customer, CustomerType, CustomerStatus, BlacklistStatus, CreditRating
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.errors import ValidationError, NotFoundError, ConflictError


@pytest.mark.unit
class TestCustomerService:
    """Test CustomerService functionality."""
    
    @pytest_asyncio.fixture
    async def customer_service(self, session):
        """Create CustomerService instance."""
        return CustomerService(session)
    
    @pytest_asyncio.fixture
    async def sample_customer(self, session):
        """Create sample customer in database."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            address_line1="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        )
        session.add(customer)
        await session.commit()
        await session.refresh(customer)
        return customer
    
    async def test_create_customer_individual_success(self, customer_service):
        """Test creating individual customer successfully."""
        customer_data = CustomerCreate(
            customer_code="CUST002",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="9876543210",
            address_line1="456 Oak Ave",
            city="Los Angeles",
            state="CA",
            postal_code="90210",
            country="USA"
        )
        
        result = await customer_service.create_customer(customer_data)
        
        assert isinstance(result, CustomerResponse)
        assert result.customer_code == "CUST002"
        assert result.customer_type == CustomerType.INDIVIDUAL.value
        assert result.first_name == "Jane"
        assert result.last_name == "Smith"
        assert result.email == "jane.smith@example.com"
        assert result.customer_status == CustomerStatus.ACTIVE.value
        assert result.blacklist_status == BlacklistStatus.CLEAR.value
        assert result.credit_rating == CreditRating.GOOD.value
        assert result.is_active is True
    
    async def test_create_customer_business_success(self, customer_service):
        """Test creating business customer successfully."""
        customer_data = CustomerCreate(
            customer_code="CUST003",
            customer_type=CustomerType.BUSINESS,
            company_name="Acme Corp",
            email="info@acmecorp.com",
            phone="5555555555",
            address_line1="789 Business Blvd",
            city="Chicago",
            state="IL",
            postal_code="60601",
            country="USA",
            tax_number="12-3456789"
        )
        
        result = await customer_service.create_customer(customer_data)
        
        assert isinstance(result, CustomerResponse)
        assert result.customer_code == "CUST003"
        assert result.customer_type == CustomerType.BUSINESS.value
        assert result.business_name == "Acme Corp"
        assert result.email == "info@acmecorp.com"
        assert result.tax_number == "12-3456789"
    
    async def test_create_customer_duplicate_code(self, customer_service, sample_customer):
        """Test creating customer with duplicate code."""
        customer_data = CustomerCreate(
            customer_code="CUST001",  # Same as sample_customer
            customer_type=CustomerType.INDIVIDUAL,
            first_name="Duplicate",
            last_name="Customer",
            email="duplicate@example.com"
        )
        
        with pytest.raises(ConflictError, match="Customer with code 'CUST001' already exists"):
            await customer_service.create_customer(customer_data)
    
    async def test_get_customer_success(self, customer_service, sample_customer):
        """Test getting customer by ID successfully."""
        result = await customer_service.get_customer(sample_customer.id)
        
        assert isinstance(result, CustomerResponse)
        assert result.id == sample_customer.id
        assert result.customer_code == sample_customer.customer_code
        assert result.first_name == sample_customer.first_name
        assert result.last_name == sample_customer.last_name
    
    async def test_get_customer_not_found(self, customer_service):
        """Test getting non-existent customer."""
        result = await customer_service.get_customer(uuid4())
        assert result is None
    
    async def test_get_customer_by_code_success(self, customer_service, sample_customer):
        """Test getting customer by code successfully."""
        result = await customer_service.get_customer_by_code(sample_customer.customer_code)
        
        assert isinstance(result, CustomerResponse)
        assert result.customer_code == sample_customer.customer_code
        assert result.first_name == sample_customer.first_name
    
    async def test_get_customer_by_code_not_found(self, customer_service):
        """Test getting customer by non-existent code."""
        result = await customer_service.get_customer_by_code("NONEXISTENT")
        assert result is None
    
    async def test_update_customer_success(self, customer_service, sample_customer):
        """Test updating customer successfully."""
        update_data = CustomerUpdate(
            first_name="Updated",
            last_name="Name",
            email="updated@example.com",
            phone="9999999999",
            city="Updated City"
        )
        
        result = await customer_service.update_customer(sample_customer.id, update_data)
        
        assert isinstance(result, CustomerResponse)
        assert result.first_name == "Updated"
        assert result.last_name == "Name"
        assert result.email == "updated@example.com"
        assert result.phone == "9999999999"
        assert result.city == "Updated City"
        # Unchanged fields should remain the same
        assert result.customer_code == sample_customer.customer_code
        assert result.state == sample_customer.state
    
    async def test_update_customer_not_found(self, customer_service):
        """Test updating non-existent customer."""
        update_data = CustomerUpdate(first_name="Updated")
        
        with pytest.raises(NotFoundError, match="Customer not found"):
            await customer_service.update_customer(uuid4(), update_data)
    
    async def test_delete_customer_success(self, customer_service, sample_customer):
        """Test deleting customer successfully."""
        result = await customer_service.delete_customer(sample_customer.id)
        
        assert result is True
        
        # Verify customer is soft deleted
        deleted_customer = await customer_service.get_customer(sample_customer.id)
        assert deleted_customer is None
    
    async def test_delete_customer_not_found(self, customer_service):
        """Test deleting non-existent customer."""
        result = await customer_service.delete_customer(uuid4())
        assert result is False
    
    async def test_list_customers_success(self, customer_service, sample_customer):
        """Test listing customers successfully."""
        result = await customer_service.list_customers()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == sample_customer.id
        assert result[0].customer_code == sample_customer.customer_code
    
    async def test_list_customers_with_filters(self, customer_service, sample_customer):
        """Test listing customers with filters."""
        # Test filter by customer type
        result = await customer_service.list_customers(customer_type=CustomerType.INDIVIDUAL)
        assert len(result) == 1
        assert result[0].customer_type == CustomerType.INDIVIDUAL.value
        
        # Test filter by customer type that doesn't exist
        result = await customer_service.list_customers(customer_type=CustomerType.BUSINESS)
        assert len(result) == 0
    
    async def test_list_customers_pagination(self, customer_service, sample_customer):
        """Test listing customers with pagination."""
        result = await customer_service.list_customers(skip=0, limit=10)
        assert isinstance(result, list)
        assert len(result) <= 10
        
        # Test skip
        result = await customer_service.list_customers(skip=1, limit=10)
        assert len(result) == 0  # Only one customer exists
    
    async def test_search_customers_success(self, customer_service, sample_customer):
        """Test searching customers successfully."""
        # Search by first name
        result = await customer_service.search_customers("John")
        assert len(result) == 1
        assert result[0].first_name == "John"
        
        # Search by last name
        result = await customer_service.search_customers("Doe")
        assert len(result) == 1
        assert result[0].last_name == "Doe"
        
        # Search by email
        result = await customer_service.search_customers("john.doe@example.com")
        assert len(result) == 1
        assert result[0].email == "john.doe@example.com"
        
        # Search by customer code
        result = await customer_service.search_customers("CUST001")
        assert len(result) == 1
        assert result[0].customer_code == "CUST001"
    
    async def test_search_customers_no_results(self, customer_service, sample_customer):
        """Test searching customers with no results."""
        result = await customer_service.search_customers("nonexistent")
        assert len(result) == 0
    
    async def test_count_customers_success(self, customer_service, sample_customer):
        """Test counting customers successfully."""
        count = await customer_service.count_customers()
        assert count == 1
        
        # Test count with filter
        count = await customer_service.count_customers(customer_type=CustomerType.INDIVIDUAL)
        assert count == 1
        
        count = await customer_service.count_customers(customer_type=CustomerType.BUSINESS)
        assert count == 0
    
    async def test_update_customer_status_success(self, customer_service, sample_customer):
        """Test updating customer status successfully."""
        from app.modules.customers.schemas import CustomerStatusUpdate
        
        status_update = CustomerStatusUpdate(
            status=CustomerStatus.INACTIVE,
            notes="Customer requested deactivation"
        )
        
        result = await customer_service.update_customer_status(sample_customer.id, status_update)
        
        assert isinstance(result, CustomerResponse)
        assert result.customer_status == CustomerStatus.INACTIVE.value
        assert result.notes == "Customer requested deactivation"
    
    async def test_update_customer_status_not_found(self, customer_service):
        """Test updating status of non-existent customer."""
        from app.modules.customers.schemas import CustomerStatusUpdate
        
        status_update = CustomerStatusUpdate(status=CustomerStatus.INACTIVE)
        
        with pytest.raises(NotFoundError, match="Customer not found"):
            await customer_service.update_customer_status(uuid4(), status_update)
    
    async def test_update_blacklist_status_success(self, customer_service, sample_customer):
        """Test updating blacklist status successfully."""
        from app.modules.customers.schemas import CustomerBlacklistUpdate
        
        blacklist_update = CustomerBlacklistUpdate(
            blacklist_status=BlacklistStatus.BLACKLISTED,
            blacklist_reason="Fraudulent activity",
            notes="Customer attempted fraud"
        )
        
        result = await customer_service.update_blacklist_status(sample_customer.id, blacklist_update)
        
        assert isinstance(result, CustomerResponse)
        assert result.blacklist_status == BlacklistStatus.BLACKLISTED.value
        assert result.blacklist_reason == "Fraudulent activity"
        assert result.notes == "Customer attempted fraud"
    
    async def test_update_credit_info_success(self, customer_service, sample_customer):
        """Test updating credit information successfully."""
        from app.modules.customers.schemas import CustomerCreditUpdate
        
        credit_update = CustomerCreditUpdate(
            credit_limit=Decimal("5000.00"),
            credit_rating=CreditRating.EXCELLENT,
            payment_terms="NET15",
            notes="Excellent payment history"
        )
        
        result = await customer_service.update_credit_info(sample_customer.id, credit_update)
        
        assert isinstance(result, CustomerResponse)
        assert result.credit_limit == Decimal("5000.00")
        assert result.credit_rating == CreditRating.EXCELLENT.value
        assert result.payment_terms == "NET15"
        assert result.notes == "Excellent payment history"
    
    async def test_get_customer_statistics_success(self, customer_service, sample_customer):
        """Test getting customer statistics successfully."""
        stats = await customer_service.get_customer_statistics()
        
        assert isinstance(stats, dict)
        assert "total_customers" in stats
        assert "active_customers" in stats
        assert "inactive_customers" in stats
        assert "individual_customers" in stats
        assert "business_customers" in stats
        assert "recent_customers" in stats
        
        assert stats["total_customers"] == 1
        assert stats["active_customers"] == 1
        assert stats["inactive_customers"] == 0
        assert stats["individual_customers"] == 1
        assert stats["business_customers"] == 0
        assert len(stats["recent_customers"]) == 1
    
    async def test_customer_data_validation(self, customer_service):
        """Test customer data validation."""
        # Test invalid customer type
        customer_data = CustomerCreate(
            customer_code="CUST999",
            customer_type="INVALID_TYPE",  # Invalid type
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        
        with pytest.raises(ValidationError):
            await customer_service.create_customer(customer_data)
    
    async def test_business_customer_validation(self, customer_service):
        """Test business customer specific validation."""
        # Business customer should have company_name
        customer_data = CustomerCreate(
            customer_code="CUST999",
            customer_type=CustomerType.BUSINESS,
            # Missing company_name
            email="business@example.com"
        )
        
        # This should be validated at the schema level
        with pytest.raises(ValidationError):
            await customer_service.create_customer(customer_data)