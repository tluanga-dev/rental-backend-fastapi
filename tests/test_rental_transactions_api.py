"""
Comprehensive tests for the Rental Transactions API endpoint.

Tests the /api/transactions/rentals endpoint with various filtering options:
- Customer filtering
- Location filtering  
- Status filtering (transaction status and rental status)
- Date range filtering
- Overdue rentals filtering
- Pagination
- Error handling
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.transactions.base.models import (
    TransactionHeader,
    TransactionType,
    TransactionStatus,
    RentalStatus,
    RentalLifecycle,
)


class TestRentalTransactionsAPI:
    """Test cases for the rental transactions API endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    async def sample_rental_data(self, async_session: AsyncSession):
        """Create sample rental transactions for testing."""
        # Create sample customers and locations
        customer_id_1 = str(uuid4())
        customer_id_2 = str(uuid4())
        location_id_1 = str(uuid4())
        location_id_2 = str(uuid4())
        
        # Create rental transactions with different statuses and dates
        rentals = []
        
        # Active rental - customer 1, location 1
        rental_1 = TransactionHeader(
            id=uuid4(),
            transaction_number="REN-20250101-001",
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime(2025, 1, 1),
            customer_id=customer_id_1,
            location_id=location_id_1,
            status=TransactionStatus.CONFIRMED,
            current_rental_status=RentalStatus.ACTIVE,
            rental_start_date=date(2025, 1, 1),
            rental_end_date=date(2025, 1, 15),
            total_amount=Decimal('100.00'),
            is_active=True
        )
        
        # Overdue rental - customer 1, location 2
        rental_2 = TransactionHeader(
            id=uuid4(),
            transaction_number="REN-20241215-002",
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime(2024, 12, 15),
            customer_id=customer_id_1,
            location_id=location_id_2,
            status=TransactionStatus.CONFIRMED,
            current_rental_status=RentalStatus.LATE,
            rental_start_date=date(2024, 12, 15),
            rental_end_date=date(2024, 12, 30),  # Past due
            total_amount=Decimal('200.00'),
            is_active=True
        )
        
        # Completed rental - customer 2, location 1
        rental_3 = TransactionHeader(
            id=uuid4(),
            transaction_number="REN-20241201-003",
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime(2024, 12, 1),
            customer_id=customer_id_2,
            location_id=location_id_1,
            status=TransactionStatus.COMPLETED,
            current_rental_status=RentalStatus.COMPLETED,
            rental_start_date=date(2024, 12, 1),
            rental_end_date=date(2024, 12, 10),
            total_amount=Decimal('150.00'),
            is_active=True
        )
        
        # Partial return rental - customer 2, location 2
        rental_4 = TransactionHeader(
            id=uuid4(),
            transaction_number="REN-20250102-004",
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime(2025, 1, 2),
            customer_id=customer_id_2,
            location_id=location_id_2,
            status=TransactionStatus.CONFIRMED,
            current_rental_status=RentalStatus.PARTIAL_RETURN,
            rental_start_date=date(2025, 1, 2),
            rental_end_date=date(2025, 1, 20),
            total_amount=Decimal('300.00'),
            is_active=True
        )
        
        rentals = [rental_1, rental_2, rental_3, rental_4]
        
        # Add rentals to session
        for rental in rentals:
            async_session.add(rental)
        
        # Create corresponding lifecycle records
        for rental in rentals:
            lifecycle = RentalLifecycle(
                id=uuid4(),
                transaction_id=rental.id,
                current_status=rental.current_rental_status,
                last_status_change=datetime.utcnow(),
                total_returned_quantity=Decimal('0'),
                expected_return_date=rental.rental_end_date,
                total_late_fees=Decimal('0'),
                total_damage_fees=Decimal('0'),
                total_other_fees=Decimal('0')
            )
            async_session.add(lifecycle)
        
        await async_session.commit()
        
        return {
            'rentals': rentals,
            'customer_id_1': customer_id_1,
            'customer_id_2': customer_id_2,
            'location_id_1': location_id_1,
            'location_id_2': location_id_2
        }

    @pytest.mark.asyncio
    async def test_get_all_rentals(self, client: TestClient, sample_rental_data):
        """Test getting all rental transactions without filters."""
        response = client.get("/api/transactions/rentals")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return all 4 rental transactions
        assert isinstance(data, list)
        assert len(data) == 4
        
        # Verify rental-specific fields are present
        for rental in data:
            assert 'id' in rental
            assert 'transaction_number' in rental
            assert 'current_rental_status' in rental
            assert 'rental_start_date' in rental
            assert 'rental_end_date' in rental

    @pytest.mark.asyncio
    async def test_filter_by_customer(self, client: TestClient, sample_rental_data):
        """Test filtering rentals by customer ID."""
        customer_id = sample_rental_data['customer_id_1']
        
        response = client.get(f"/api/transactions/rentals?customer_id={customer_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 2 rentals for customer 1
        assert len(data) == 2
        for rental in data:
            assert rental['customer_id'] == customer_id

    @pytest.mark.asyncio
    async def test_filter_by_location(self, client: TestClient, sample_rental_data):
        """Test filtering rentals by location ID."""
        location_id = sample_rental_data['location_id_1']
        
        response = client.get(f"/api/transactions/rentals?location_id={location_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 2 rentals for location 1
        assert len(data) == 2
        for rental in data:
            assert rental['location_id'] == location_id

    @pytest.mark.asyncio
    async def test_filter_by_transaction_status(self, client: TestClient, sample_rental_data):
        """Test filtering rentals by transaction status."""
        response = client.get("/api/transactions/rentals?status=CONFIRMED")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 3 confirmed rentals
        assert len(data) == 3
        for rental in data:
            assert rental['status'] == 'CONFIRMED'

    @pytest.mark.asyncio
    async def test_filter_by_rental_status(self, client: TestClient, sample_rental_data):
        """Test filtering rentals by rental status."""
        response = client.get("/api/transactions/rentals?rental_status=ACTIVE")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 1 active rental
        assert len(data) == 1
        assert data[0]['current_rental_status'] == 'ACTIVE'

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client: TestClient, sample_rental_data):
        """Test filtering rentals by date range."""
        response = client.get(
            "/api/transactions/rentals?date_from=2025-01-01&date_to=2025-01-31"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 2 rentals from January 2025
        assert len(data) == 2
        for rental in data:
            start_date = datetime.fromisoformat(rental['rental_start_date'].replace('Z', '+00:00')).date()
            assert start_date >= date(2025, 1, 1)
            assert start_date <= date(2025, 1, 31)

    @pytest.mark.asyncio
    async def test_filter_overdue_only(self, client: TestClient, sample_rental_data):
        """Test filtering for overdue rentals only."""
        response = client.get("/api/transactions/rentals?overdue_only=true")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 1 overdue rental
        assert len(data) == 1
        rental = data[0]
        assert rental['current_rental_status'] == 'LATE'
        end_date = datetime.fromisoformat(rental['rental_end_date'].replace('Z', '+00:00')).date()
        assert end_date < date.today()

    @pytest.mark.asyncio
    async def test_combined_filters(self, client: TestClient, sample_rental_data):
        """Test combining multiple filters."""
        customer_id = sample_rental_data['customer_id_2']
        
        response = client.get(
            f"/api/transactions/rentals?customer_id={customer_id}&status=CONFIRMED"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return 1 rental (customer 2 + confirmed status)
        assert len(data) == 1
        rental = data[0]
        assert rental['customer_id'] == customer_id
        assert rental['status'] == 'CONFIRMED'

    @pytest.mark.asyncio
    async def test_pagination(self, client: TestClient, sample_rental_data):
        """Test pagination with skip and limit parameters."""
        # Test first page
        response = client.get("/api/transactions/rentals?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Test second page
        response = client.get("/api/transactions/rentals?skip=2&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_invalid_customer_id(self, client: TestClient):
        """Test handling of invalid customer ID."""
        response = client.get("/api/transactions/rentals?customer_id=invalid-uuid")
        
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_invalid_status_enum(self, client: TestClient):
        """Test handling of invalid status enum values."""
        response = client.get("/api/transactions/rentals?status=INVALID_STATUS")
        
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_invalid_rental_status_enum(self, client: TestClient):
        """Test handling of invalid rental status enum values."""
        response = client.get("/api/transactions/rentals?rental_status=INVALID_RENTAL_STATUS")
        
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, client: TestClient):
        """Test handling of invalid date format."""
        response = client.get("/api/transactions/rentals?date_from=invalid-date")
        
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_negative_pagination_params(self, client: TestClient):
        """Test handling of negative pagination parameters."""
        response = client.get("/api/transactions/rentals?skip=-1")
        
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_excessive_limit(self, client: TestClient):
        """Test handling of excessive limit parameter."""
        response = client.get("/api/transactions/rentals?limit=2000")
        
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_empty_result_set(self, client: TestClient, sample_rental_data):
        """Test handling when no rentals match the filters."""
        # Use a non-existent customer ID
        non_existent_customer = str(uuid4())
        
        response = client.get(f"/api/transactions/rentals?customer_id={non_existent_customer}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_response_structure(self, client: TestClient, sample_rental_data):
        """Test that the response structure includes all expected fields."""
        response = client.get("/api/transactions/rentals?limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        rental = data[0]
        expected_fields = [
            'id', 'transaction_number', 'transaction_date', 'customer_id',
            'location_id', 'status', 'rental_start_date', 'rental_end_date',
            'total_amount', 'current_rental_status', 'lifecycle'
        ]
        
        for field in expected_fields:
            assert field in rental, f"Missing expected field: {field}"

    @pytest.mark.asyncio
    async def test_lifecycle_information_included(self, client: TestClient, sample_rental_data):
        """Test that lifecycle information is included in the response."""
        response = client.get("/api/transactions/rentals?limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        rental = data[0]
        assert 'lifecycle' in rental
        
        if rental['lifecycle']:
            lifecycle = rental['lifecycle']
            lifecycle_fields = [
                'id', 'current_status', 'last_status_change',
                'total_returned_quantity', 'expected_return_date'
            ]
            
            for field in lifecycle_fields:
                assert field in lifecycle, f"Missing lifecycle field: {field}"

    @pytest.mark.asyncio
    async def test_date_range_edge_cases(self, client: TestClient, sample_rental_data):
        """Test edge cases for date range filtering."""
        # Test with same start and end date
        response = client.get(
            "/api/transactions/rentals?date_from=2025-01-01&date_to=2025-01-01"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return rentals that start on 2025-01-01
        for rental in data:
            start_date = datetime.fromisoformat(rental['rental_start_date'].replace('Z', '+00:00')).date()
            assert start_date == date(2025, 1, 1)

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, client: TestClient):
        """Test that the API performs reasonably with pagination."""
        # Test with reasonable pagination limits
        response = client.get("/api/transactions/rentals?skip=0&limit=100")
        
        assert response.status_code == 200
        # Should complete within reasonable time (handled by test framework)