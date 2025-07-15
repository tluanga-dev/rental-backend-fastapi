"""
API tests for stock movement tracking endpoints.

This test suite covers:
- Stock movement history API endpoints
- Manual stock movement creation
- Rental stock operations via API
- Error handling and validation
- Pagination and filtering
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi import status

from app.modules.inventory.models import MovementType, ReferenceType
from app.modules.master_data.item_master.models import Item, ItemStatus
from app.modules.master_data.locations.models import Location
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.categories.models import Category
from app.modules.inventory.models import StockLevel


@pytest.fixture
async def setup_test_data(session):
    """Set up test data for API tests."""
    # Create supporting data
    brand = Brand(name="API Test Brand", brand_code="ATB", description="API test brand")
    session.add(brand)
    await session.flush()
    
    category = Category(name="API Test Category", category_code="ATC", description="API test category")
    session.add(category)
    await session.flush()
    
    item = Item(
        sku="API-TST-001",
        item_name="API Test Item",
        item_status=ItemStatus.ACTIVE,
        is_rentable=True,
        is_saleable=True,
        brand_id=brand.id,
        category_id=category.id,
        rental_rate_per_period=Decimal("15.00")
    )
    session.add(item)
    await session.flush()
    
    location = Location(
        location_name="API Test Location",
        location_code="ATL001",
        location_type="WAREHOUSE",
        address="456 API Test Street"
    )
    session.add(location)
    await session.flush()
    
    stock_level = StockLevel(
        item_id=str(item.id),
        location_id=str(location.id),
        quantity_on_hand=Decimal("150"),
        quantity_available=Decimal("100"),
        quantity_on_rent=Decimal("50")
    )
    session.add(stock_level)
    await session.flush()
    
    await session.commit()
    
    return {
        "item": item,
        "location": location,
        "stock_level": stock_level,
        "brand": brand,
        "category": category
    }


class TestStockMovementHistoryAPI:
    """Test stock movement history endpoints."""
    
    async def test_get_stock_level_movements(self, client: AsyncClient, setup_test_data):
        """Test getting stock movements for a specific stock level."""
        stock_level = setup_test_data["stock_level"]
        
        # Create some test movements first via manual movement endpoint
        await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "ADJUSTMENT_POSITIVE",
                "quantity_change": "25",
                "reason": "API test adjustment"
            }
        )
        
        # Get movements
        response = await client.get(f"/api/inventory/stock/{stock_level.id}/movements")
        
        assert response.status_code == status.HTTP_200_OK
        movements = response.json()
        assert isinstance(movements, list)
        assert len(movements) >= 1
        
        # Check movement structure
        if movements:
            movement = movements[0]
            assert "id" in movement
            assert "movement_type" in movement
            assert "quantity_change" in movement
            assert "reason" in movement
            assert "created_at" in movement
    
    async def test_get_stock_level_movements_pagination(self, client: AsyncClient, setup_test_data):
        """Test pagination for stock level movements."""
        stock_level = setup_test_data["stock_level"]
        
        # Create multiple movements
        for i in range(5):
            await client.post(
                f"/api/inventory/stock/{stock_level.id}/movements/manual",
                params={
                    "movement_type": "ADJUSTMENT_POSITIVE",
                    "quantity_change": "5",
                    "reason": f"API test movement {i}"
                }
            )
        
        # Test pagination
        response = await client.get(
            f"/api/inventory/stock/{stock_level.id}/movements",
            params={"skip": 0, "limit": 3}
        )
        
        assert response.status_code == status.HTTP_200_OK
        movements = response.json()
        assert len(movements) <= 3
    
    async def test_get_item_movements(self, client: AsyncClient, setup_test_data):
        """Test getting movements for a specific item."""
        item = setup_test_data["item"]
        stock_level = setup_test_data["stock_level"]
        
        # Create movements
        await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "PURCHASE",
                "quantity_change": "30",
                "reason": "API test purchase"
            }
        )
        
        # Get movements by item
        response = await client.get(f"/api/inventory/items/{item.id}/movements")
        
        assert response.status_code == status.HTTP_200_OK
        movements = response.json()
        assert isinstance(movements, list)
        assert len(movements) >= 1
    
    async def test_get_item_movements_with_filter(self, client: AsyncClient, setup_test_data):
        """Test getting item movements with movement type filter."""
        item = setup_test_data["item"]
        stock_level = setup_test_data["stock_level"]
        
        # Create different types of movements
        await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "PURCHASE",
                "quantity_change": "20",
                "reason": "API test purchase"
            }
        )
        
        await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "ADJUSTMENT_POSITIVE",
                "quantity_change": "10",
                "reason": "API test adjustment"
            }
        )
        
        # Filter by movement type
        response = await client.get(
            f"/api/inventory/items/{item.id}/movements",
            params={"movement_type": "PURCHASE"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        movements = response.json()
        
        # All movements should be PURCHASE type
        for movement in movements:
            assert movement["movement_type"] == "PURCHASE"
    
    async def test_get_movement_summary(self, client: AsyncClient, setup_test_data):
        """Test getting movement summary for an item."""
        item = setup_test_data["item"]
        stock_level = setup_test_data["stock_level"]
        
        # Create mixed movements
        movements_to_create = [
            ("PURCHASE", "50"),
            ("SALE", "-20"),
            ("ADJUSTMENT_POSITIVE", "15")
        ]
        
        for movement_type, quantity in movements_to_create:
            await client.post(
                f"/api/inventory/stock/{stock_level.id}/movements/manual",
                params={
                    "movement_type": movement_type,
                    "quantity_change": quantity,
                    "reason": f"API test {movement_type}"
                }
            )
        
        # Get summary
        response = await client.get(f"/api/inventory/items/{item.id}/movements/summary")
        
        assert response.status_code == status.HTTP_200_OK
        summary = response.json()
        
        assert "total_movements" in summary
        assert "total_increases" in summary
        assert "total_decreases" in summary
        assert "net_change" in summary
        assert "movement_types" in summary
        
        assert summary["total_movements"] >= 3
        assert float(summary["net_change"]) == 45.0  # 50 - 20 + 15


class TestManualStockMovementAPI:
    """Test manual stock movement creation API."""
    
    async def test_create_manual_stock_movement(self, client: AsyncClient, setup_test_data):
        """Test creating a manual stock movement."""
        stock_level = setup_test_data["stock_level"]
        
        response = await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "ADJUSTMENT_POSITIVE",
                "quantity_change": "35",
                "reason": "Manual adjustment for testing",
                "notes": "API test notes"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        movement = response.json()
        
        assert movement["movement_type"] == "ADJUSTMENT_POSITIVE"
        assert float(movement["quantity_change"]) == 35.0
        assert movement["reason"] == "Manual adjustment for testing"
        assert movement["notes"] == "API test notes"
        assert movement["reference_type"] == "MANUAL_ADJUSTMENT"
    
    async def test_create_manual_stock_movement_validation_error(self, client: AsyncClient, setup_test_data):
        """Test validation error for invalid stock movement."""
        stock_level = setup_test_data["stock_level"]
        
        # Try to create movement with excessive negative quantity
        response = await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "ADJUSTMENT_NEGATIVE",
                "quantity_change": "-1000",  # More than available
                "reason": "Invalid adjustment"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_create_manual_stock_movement_not_found(self, client: AsyncClient):
        """Test manual movement creation with non-existent stock level."""
        from uuid import uuid4
        fake_id = uuid4()
        
        response = await client.post(
            f"/api/inventory/stock/{fake_id}/movements/manual",
            params={
                "movement_type": "ADJUSTMENT_POSITIVE",
                "quantity_change": "10",
                "reason": "Test movement"
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRentalStockOperationsAPI:
    """Test rental stock operations via API."""
    
    async def test_rent_out_stock(self, client: AsyncClient, setup_test_data):
        """Test renting out stock via API."""
        stock_level = setup_test_data["stock_level"]
        
        response = await client.post(
            f"/api/inventory/stock/{stock_level.id}/rent-out",
            params={
                "quantity": "25",
                "transaction_id": "TXN-API-RENT-001"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        movement = response.json()
        
        assert movement["movement_type"] == "RENTAL_OUT"
        assert float(movement["quantity_change"]) == -25.0  # Negative from available perspective
        assert movement["reference_type"] == "TRANSACTION"
        assert movement["reference_id"] == "TXN-API-RENT-001"
    
    async def test_return_from_rent(self, client: AsyncClient, setup_test_data):
        """Test returning stock from rent via API."""
        stock_level = setup_test_data["stock_level"]
        
        response = await client.post(
            f"/api/inventory/stock/{stock_level.id}/return-from-rent",
            params={
                "quantity": "15",
                "transaction_id": "TXN-API-RETURN-001"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        movement = response.json()
        
        assert movement["movement_type"] == "RENTAL_RETURN"
        assert float(movement["quantity_change"]) == 15.0  # Positive to available
        assert movement["reference_type"] == "TRANSACTION"
        assert movement["reference_id"] == "TXN-API-RETURN-001"
    
    async def test_rent_out_insufficient_stock(self, client: AsyncClient, setup_test_data):
        """Test renting out more stock than available."""
        stock_level = setup_test_data["stock_level"]
        
        response = await client.post(
            f"/api/inventory/stock/{stock_level.id}/rent-out",
            params={
                "quantity": "1000",  # More than available
                "transaction_id": "TXN-API-INVALID"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_return_more_than_rented(self, client: AsyncClient, setup_test_data):
        """Test returning more stock than currently rented."""
        stock_level = setup_test_data["stock_level"]
        
        response = await client.post(
            f"/api/inventory/stock/{stock_level.id}/return-from-rent",
            params={
                "quantity": "1000",  # More than on rent
                "transaction_id": "TXN-API-INVALID-RETURN"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMovementsByReferenceAPI:
    """Test getting movements by reference."""
    
    async def test_get_movements_by_reference(self, client: AsyncClient, setup_test_data):
        """Test getting movements by reference ID."""
        stock_level = setup_test_data["stock_level"]
        
        # Create movement with specific reference
        await client.post(
            f"/api/inventory/stock/{stock_level.id}/rent-out",
            params={
                "quantity": "20",
                "transaction_id": "TXN-REF-TEST-001"
            }
        )
        
        # Get movements by reference
        response = await client.get(
            "/api/inventory/movements/reference/TRANSACTION/TXN-REF-TEST-001"
        )
        
        assert response.status_code == status.HTTP_200_OK
        movements = response.json()
        assert isinstance(movements, list)
        assert len(movements) >= 1
        
        # All movements should have the same reference
        for movement in movements:
            assert movement["reference_type"] == "TRANSACTION"
            assert movement["reference_id"] == "TXN-REF-TEST-001"


class TestMovementsByDateRangeAPI:
    """Test getting movements by date range."""
    
    async def test_get_movements_by_date_range(self, client: AsyncClient, setup_test_data):
        """Test getting movements within a date range."""
        stock_level = setup_test_data["stock_level"]
        
        # Create movement
        await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "ADJUSTMENT_POSITIVE",
                "quantity_change": "30",
                "reason": "Date range test"
            }
        )
        
        # Get movements for today
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%dT00:00:00")
        end_date = today.strftime("%Y-%m-%dT23:59:59")
        
        response = await client.get(
            "/api/inventory/movements/range",
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        movements = response.json()
        assert isinstance(movements, list)
        assert len(movements) >= 1
    
    async def test_get_movements_by_date_range_with_filters(self, client: AsyncClient, setup_test_data):
        """Test getting movements by date range with additional filters."""
        item = setup_test_data["item"]
        location = setup_test_data["location"]
        stock_level = setup_test_data["stock_level"]
        
        # Create movement
        await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "PURCHASE",
                "quantity_change": "40",
                "reason": "Filtered date range test"
            }
        )
        
        # Get movements with filters
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%dT00:00:00")
        end_date = today.strftime("%Y-%m-%dT23:59:59")
        
        response = await client.get(
            "/api/inventory/movements/range",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "item_id": str(item.id),
                "location_id": str(location.id),
                "movement_type": "PURCHASE"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        movements = response.json()
        assert isinstance(movements, list)
        
        # All movements should match filters
        for movement in movements:
            assert movement["item_id"] == str(item.id)
            assert movement["location_id"] == str(location.id)
            assert movement["movement_type"] == "PURCHASE"


class TestErrorHandling:
    """Test error handling in stock movement APIs."""
    
    async def test_invalid_movement_type(self, client: AsyncClient, setup_test_data):
        """Test invalid movement type in API."""
        stock_level = setup_test_data["stock_level"]
        
        response = await client.post(
            f"/api/inventory/stock/{stock_level.id}/movements/manual",
            params={
                "movement_type": "INVALID_TYPE",
                "quantity_change": "10",
                "reason": "Invalid type test"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_invalid_uuid_in_path(self, client: AsyncClient):
        """Test invalid UUID in API path."""
        response = await client.get("/api/inventory/stock/invalid-uuid/movements")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_negative_pagination_params(self, client: AsyncClient, setup_test_data):
        """Test negative pagination parameters."""
        stock_level = setup_test_data["stock_level"]
        
        response = await client.get(
            f"/api/inventory/stock/{stock_level.id}/movements",
            params={"skip": -1, "limit": 10}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_excessive_limit_param(self, client: AsyncClient, setup_test_data):
        """Test excessive limit parameter."""
        stock_level = setup_test_data["stock_level"]
        
        response = await client.get(
            f"/api/inventory/stock/{stock_level.id}/movements",
            params={"skip": 0, "limit": 2000}  # Over the 1000 limit
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_complete_stock_movement_api_workflow(client: AsyncClient, setup_test_data):
    """Test complete workflow using stock movement APIs."""
    stock_level = setup_test_data["stock_level"]
    item = setup_test_data["item"]
    
    # 1. Add stock via manual movement
    purchase_response = await client.post(
        f"/api/inventory/stock/{stock_level.id}/movements/manual",
        params={
            "movement_type": "PURCHASE",
            "quantity_change": "100",
            "reason": "Initial purchase for workflow test"
        }
    )
    assert purchase_response.status_code == status.HTTP_200_OK
    
    # 2. Rent out some stock
    rent_response = await client.post(
        f"/api/inventory/stock/{stock_level.id}/rent-out",
        params={
            "quantity": "30",
            "transaction_id": "TXN-WORKFLOW-RENT"
        }
    )
    assert rent_response.status_code == status.HTTP_200_OK
    
    # 3. Return some stock
    return_response = await client.post(
        f"/api/inventory/stock/{stock_level.id}/return-from-rent",
        params={
            "quantity": "15",
            "transaction_id": "TXN-WORKFLOW-RETURN"
        }
    )
    assert return_response.status_code == status.HTTP_200_OK
    
    # 4. Get movement history
    history_response = await client.get(f"/api/inventory/stock/{stock_level.id}/movements")
    assert history_response.status_code == status.HTTP_200_OK
    movements = history_response.json()
    assert len(movements) >= 3  # Purchase, rent out, return
    
    # 5. Get movement summary
    summary_response = await client.get(f"/api/inventory/items/{item.id}/movements/summary")
    assert summary_response.status_code == status.HTTP_200_OK
    summary = summary_response.json()
    assert summary["total_movements"] >= 3
    
    # 6. Verify rental transaction movements
    rental_movements_response = await client.get(
        "/api/inventory/movements/reference/TRANSACTION/TXN-WORKFLOW-RENT"
    )
    assert rental_movements_response.status_code == status.HTTP_200_OK
    rental_movements = rental_movements_response.json()
    assert len(rental_movements) == 1
    assert rental_movements[0]["movement_type"] == "RENTAL_OUT"