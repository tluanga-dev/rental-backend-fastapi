import pytest
import pytest_asyncio
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta

from app.modules.suppliers.service import SupplierService
from app.modules.suppliers.models import Supplier, SupplierType, SupplierTier, SupplierStatus, PaymentTerms
from app.modules.suppliers.schemas import SupplierCreate, SupplierUpdate, SupplierResponse
from app.core.errors import ValidationError, NotFoundError, ConflictError


@pytest.mark.unit
class TestSupplierService:
    """Test SupplierService functionality."""
    
    @pytest_asyncio.fixture
    async def supplier_service(self, session):
        """Create SupplierService instance."""
        return SupplierService(session)
    
    @pytest_asyncio.fixture
    async def sample_supplier(self, session):
        """Create sample supplier in database."""
        supplier = Supplier(
            supplier_code="SUPP001",
            company_name="Test Supplier Inc",
            supplier_type=SupplierType.MANUFACTURER,
            contact_person="John Manager",
            email="contact@testsupplier.com",
            phone="123-456-7890",
            address_line1="123 Supplier St",
            city="Supplier City",
            state="SC",
            postal_code="12345",
            country="USA",
            payment_terms=PaymentTerms.NET30,
            credit_limit=Decimal("10000.00"),
            supplier_tier=SupplierTier.STANDARD
        )
        session.add(supplier)
        await session.commit()
        await session.refresh(supplier)
        return supplier
    
    async def test_create_supplier_success(self, supplier_service):
        """Test creating supplier successfully."""
        supplier_data = SupplierCreate(
            supplier_code="SUPP002",
            company_name="New Supplier Corp",
            supplier_type=SupplierType.DISTRIBUTOR,
            contact_person="Jane Contact",
            email="info@newsupplier.com",
            phone="987-654-3210",
            address_line1="456 Vendor Ave",
            city="Vendor City",
            state="VC",
            postal_code="67890",
            country="USA",
            payment_terms=PaymentTerms.NET45,
            credit_limit=Decimal("15000.00"),
            supplier_tier=SupplierTier.PREMIUM
        )
        
        result = await supplier_service.create_supplier(supplier_data)
        
        assert isinstance(result, SupplierResponse)
        assert result.supplier_code == "SUPP002"
        assert result.company_name == "New Supplier Corp"
        assert result.supplier_type == SupplierType.DISTRIBUTOR.value
        assert result.contact_person == "Jane Contact"
        assert result.email == "info@newsupplier.com"
        assert result.payment_terms == PaymentTerms.NET45.value
        assert result.credit_limit == Decimal("15000.00")
        assert result.supplier_tier == SupplierTier.PREMIUM.value
        assert result.status == SupplierStatus.ACTIVE.value
        assert result.is_active is True
        assert result.quality_rating == 0.0
        assert result.delivery_rating == 0.0
        assert result.total_orders == 0
        assert result.total_spend == 0.0
    
    async def test_create_supplier_duplicate_code(self, supplier_service, sample_supplier):
        """Test creating supplier with duplicate code."""
        supplier_data = SupplierCreate(
            supplier_code="SUPP001",  # Same as sample_supplier
            company_name="Duplicate Supplier",
            supplier_type=SupplierType.WHOLESALER,
            email="duplicate@example.com"
        )
        
        with pytest.raises(ConflictError, match="Supplier with code 'SUPP001' already exists"):
            await supplier_service.create_supplier(supplier_data)
    
    async def test_get_supplier_success(self, supplier_service, sample_supplier):
        """Test getting supplier by ID successfully."""
        result = await supplier_service.get_supplier(sample_supplier.id)
        
        assert isinstance(result, SupplierResponse)
        assert result.id == sample_supplier.id
        assert result.supplier_code == sample_supplier.supplier_code
        assert result.company_name == sample_supplier.company_name
        assert result.supplier_type == sample_supplier.supplier_type
    
    async def test_get_supplier_not_found(self, supplier_service):
        """Test getting non-existent supplier."""
        result = await supplier_service.get_supplier(uuid4())
        assert result is None
    
    async def test_get_supplier_by_code_success(self, supplier_service, sample_supplier):
        """Test getting supplier by code successfully."""
        result = await supplier_service.get_supplier_by_code(sample_supplier.supplier_code)
        
        assert isinstance(result, SupplierResponse)
        assert result.supplier_code == sample_supplier.supplier_code
        assert result.company_name == sample_supplier.company_name
    
    async def test_get_supplier_by_code_not_found(self, supplier_service):
        """Test getting supplier by non-existent code."""
        result = await supplier_service.get_supplier_by_code("NONEXISTENT")
        assert result is None
    
    async def test_update_supplier_success(self, supplier_service, sample_supplier):
        """Test updating supplier successfully."""
        update_data = SupplierUpdate(
            company_name="Updated Supplier Corp",
            contact_person="Updated Contact",
            email="updated@supplier.com",
            phone="111-222-3333",
            city="Updated City",
            credit_limit=Decimal("20000.00"),
            supplier_tier=SupplierTier.PREMIUM
        )
        
        result = await supplier_service.update_supplier(sample_supplier.id, update_data)
        
        assert isinstance(result, SupplierResponse)
        assert result.company_name == "Updated Supplier Corp"
        assert result.contact_person == "Updated Contact"
        assert result.email == "updated@supplier.com"
        assert result.phone == "111-222-3333"
        assert result.city == "Updated City"
        assert result.credit_limit == Decimal("20000.00")
        assert result.supplier_tier == SupplierTier.PREMIUM.value
        # Unchanged fields should remain the same
        assert result.supplier_code == sample_supplier.supplier_code
        assert result.state == sample_supplier.state
    
    async def test_update_supplier_not_found(self, supplier_service):
        """Test updating non-existent supplier."""
        update_data = SupplierUpdate(company_name="Updated")
        
        with pytest.raises(NotFoundError, match="Supplier not found"):
            await supplier_service.update_supplier(uuid4(), update_data)
    
    async def test_delete_supplier_success(self, supplier_service, sample_supplier):
        """Test deleting supplier successfully."""
        result = await supplier_service.delete_supplier(sample_supplier.id)
        
        assert result is True
        
        # Verify supplier is soft deleted
        deleted_supplier = await supplier_service.get_supplier(sample_supplier.id)
        assert deleted_supplier is None
    
    async def test_delete_supplier_not_found(self, supplier_service):
        """Test deleting non-existent supplier."""
        result = await supplier_service.delete_supplier(uuid4())
        assert result is False
    
    async def test_list_suppliers_success(self, supplier_service, sample_supplier):
        """Test listing suppliers successfully."""
        result = await supplier_service.list_suppliers()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == sample_supplier.id
        assert result[0].supplier_code == sample_supplier.supplier_code
    
    async def test_list_suppliers_with_filters(self, supplier_service, sample_supplier):
        """Test listing suppliers with filters."""
        # Test filter by supplier type
        result = await supplier_service.list_suppliers(supplier_type=SupplierType.MANUFACTURER)
        assert len(result) == 1
        assert result[0].supplier_type == SupplierType.MANUFACTURER.value
        
        # Test filter by supplier type that doesn't exist
        result = await supplier_service.list_suppliers(supplier_type=SupplierType.RETAILER)
        assert len(result) == 0
        
        # Test filter by status
        result = await supplier_service.list_suppliers(status=SupplierStatus.ACTIVE)
        assert len(result) == 1
        assert result[0].status == SupplierStatus.ACTIVE.value
        
        # Test filter by status that doesn't exist
        result = await supplier_service.list_suppliers(status=SupplierStatus.SUSPENDED)
        assert len(result) == 0
    
    async def test_list_suppliers_pagination(self, supplier_service, sample_supplier):
        """Test listing suppliers with pagination."""
        result = await supplier_service.list_suppliers(skip=0, limit=10)
        assert isinstance(result, list)
        assert len(result) <= 10
        
        # Test skip
        result = await supplier_service.list_suppliers(skip=1, limit=10)
        assert len(result) == 0  # Only one supplier exists
    
    async def test_search_suppliers_success(self, supplier_service, sample_supplier):
        """Test searching suppliers successfully."""
        # Search by company name
        result = await supplier_service.search_suppliers("Test Supplier")
        assert len(result) == 1
        assert result[0].company_name == "Test Supplier Inc"
        
        # Search by supplier code
        result = await supplier_service.search_suppliers("SUPP001")
        assert len(result) == 1
        assert result[0].supplier_code == "SUPP001"
        
        # Search by email
        result = await supplier_service.search_suppliers("contact@testsupplier.com")
        assert len(result) == 1
        assert result[0].email == "contact@testsupplier.com"
        
        # Search by contact person
        result = await supplier_service.search_suppliers("John Manager")
        assert len(result) == 1
        assert result[0].contact_person == "John Manager"
    
    async def test_search_suppliers_no_results(self, supplier_service, sample_supplier):
        """Test searching suppliers with no results."""
        result = await supplier_service.search_suppliers("nonexistent")
        assert len(result) == 0
    
    async def test_count_suppliers_success(self, supplier_service, sample_supplier):
        """Test counting suppliers successfully."""
        count = await supplier_service.count_suppliers()
        assert count == 1
        
        # Test count with filters
        count = await supplier_service.count_suppliers(supplier_type=SupplierType.MANUFACTURER)
        assert count == 1
        
        count = await supplier_service.count_suppliers(supplier_type=SupplierType.RETAILER)
        assert count == 0
        
        count = await supplier_service.count_suppliers(status=SupplierStatus.ACTIVE)
        assert count == 1
        
        count = await supplier_service.count_suppliers(status=SupplierStatus.SUSPENDED)
        assert count == 0
    
    async def test_update_supplier_status_success(self, supplier_service, sample_supplier):
        """Test updating supplier status successfully."""
        from app.modules.suppliers.schemas import SupplierStatusUpdate
        
        status_update = SupplierStatusUpdate(
            status=SupplierStatus.SUSPENDED,
            notes="Quality issues reported"
        )
        
        result = await supplier_service.update_supplier_status(sample_supplier.id, status_update)
        
        assert isinstance(result, SupplierResponse)
        assert result.status == SupplierStatus.SUSPENDED.value
        assert result.notes == "Quality issues reported"
    
    async def test_update_supplier_status_not_found(self, supplier_service):
        """Test updating status of non-existent supplier."""
        from app.modules.suppliers.schemas import SupplierStatusUpdate
        
        status_update = SupplierStatusUpdate(status=SupplierStatus.SUSPENDED)
        
        with pytest.raises(NotFoundError, match="Supplier not found"):
            await supplier_service.update_supplier_status(uuid4(), status_update)
    
    async def test_get_supplier_statistics_success(self, supplier_service, sample_supplier):
        """Test getting supplier statistics successfully."""
        stats = await supplier_service.get_supplier_statistics()
        
        assert isinstance(stats, dict)
        assert "total_suppliers" in stats
        assert "active_suppliers" in stats
        assert "inactive_suppliers" in stats
        assert "inventory_suppliers" in stats
        assert "service_suppliers" in stats
        assert "approved_suppliers" in stats
        assert "pending_suppliers" in stats
        assert "recent_suppliers" in stats
        
        assert stats["total_suppliers"] == 1
        assert stats["active_suppliers"] == 1
        assert stats["inactive_suppliers"] == 0
        assert len(stats["recent_suppliers"]) == 1
    
    async def test_supplier_business_methods(self, supplier_service, sample_supplier):
        """Test supplier business logic methods."""
        # Test supplier properties that would be computed
        supplier_response = await supplier_service.get_supplier(sample_supplier.id)
        
        # Test basic properties
        assert supplier_response.id == sample_supplier.id
        assert supplier_response.supplier_code == sample_supplier.supplier_code
        assert supplier_response.status == SupplierStatus.ACTIVE.value
        assert supplier_response.is_active is True
        
        # Test performance metrics (should be 0 for new supplier)
        assert supplier_response.quality_rating == 0.0
        assert supplier_response.delivery_rating == 0.0
        assert supplier_response.total_orders == 0
        assert supplier_response.total_spend == 0.0
        assert supplier_response.average_delivery_days == 0
    
    async def test_supplier_contract_dates(self, supplier_service):
        """Test supplier with contract dates."""
        supplier_data = SupplierCreate(
            supplier_code="SUPP003",
            company_name="Contract Supplier",
            supplier_type=SupplierType.DISTRIBUTOR,
            email="contract@supplier.com",
            contract_start_date=datetime.utcnow(),
            contract_end_date=datetime.utcnow() + timedelta(days=365)
        )
        
        result = await supplier_service.create_supplier(supplier_data)
        
        assert isinstance(result, SupplierResponse)
        assert result.contract_start_date is not None
        assert result.contract_end_date is not None
        assert result.contract_end_date > result.contract_start_date
    
    async def test_supplier_validation_edge_cases(self, supplier_service):
        """Test supplier validation edge cases."""
        # Test minimum required fields
        supplier_data = SupplierCreate(
            supplier_code="SUPP004",
            company_name="Minimal Supplier",
            supplier_type=SupplierType.MANUFACTURER
        )
        
        result = await supplier_service.create_supplier(supplier_data)
        
        assert isinstance(result, SupplierResponse)
        assert result.supplier_code == "SUPP004"
        assert result.company_name == "Minimal Supplier"
        assert result.supplier_type == SupplierType.MANUFACTURER.value
        assert result.status == SupplierStatus.ACTIVE.value
        assert result.supplier_tier == SupplierTier.STANDARD.value
        assert result.payment_terms == PaymentTerms.NET30.value
        assert result.credit_limit == Decimal("0.00")
    
    async def test_supplier_type_filtering(self, supplier_service, sample_supplier):
        """Test filtering suppliers by type."""
        # Create suppliers of different types
        supplier_data_2 = SupplierCreate(
            supplier_code="SUPP005",
            company_name="Service Supplier",
            supplier_type=SupplierType.SERVICE,
            email="service@supplier.com"
        )
        
        await supplier_service.create_supplier(supplier_data_2)
        
        # Test filtering by MANUFACTURER
        result = await supplier_service.list_suppliers(supplier_type=SupplierType.MANUFACTURER)
        assert len(result) == 1
        assert result[0].supplier_type == SupplierType.MANUFACTURER.value
        
        # Test filtering by SERVICE
        result = await supplier_service.list_suppliers(supplier_type=SupplierType.SERVICE)
        assert len(result) == 1
        assert result[0].supplier_type == SupplierType.SERVICE.value
        
        # Test no filter (should return all)
        result = await supplier_service.list_suppliers()
        assert len(result) == 2
    
    async def test_supplier_tier_upgrade(self, supplier_service, sample_supplier):
        """Test upgrading supplier tier."""
        update_data = SupplierUpdate(
            supplier_tier=SupplierTier.PREMIUM,
            credit_limit=Decimal("50000.00")
        )
        
        result = await supplier_service.update_supplier(sample_supplier.id, update_data)
        
        assert result.supplier_tier == SupplierTier.PREMIUM.value
        assert result.credit_limit == Decimal("50000.00")
    
    async def test_supplier_contact_info_update(self, supplier_service, sample_supplier):
        """Test updating supplier contact information."""
        update_data = SupplierUpdate(
            contact_person="New Contact Person",
            email="newcontact@supplier.com",
            phone="999-888-7777",
            mobile="555-444-3333"
        )
        
        result = await supplier_service.update_supplier(sample_supplier.id, update_data)
        
        assert result.contact_person == "New Contact Person"
        assert result.email == "newcontact@supplier.com"
        assert result.phone == "999-888-7777"
        assert result.mobile == "555-444-3333"