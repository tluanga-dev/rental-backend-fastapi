"""
API-level tests for the sale endpoint.
Tests the actual API endpoints without direct database access.
"""
import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4
from fastapi.testclient import TestClient


class TestSaleEndpointAPI:
    """Test sale endpoint via API calls."""

    def test_sale_endpoint_exists(self, client: TestClient):
        """Test that the sale endpoint exists."""
        response = client.post("/api/transactions/new-sale", json={})
        # Should return 422 for missing fields, not 404
        assert response.status_code in [422, 401]  # 422 for validation, 401 if auth required

    def test_invalid_sale_payload_validation(self, client: TestClient):
        """Test validation of invalid payloads."""
        # Test missing customer_id
        response = client.post("/api/transactions/new-sale", json={
            "transaction_date": "2024-07-15",
            "items": []
        })
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("customer_id" in str(error) for error in errors)

        # Test empty items
        response = client.post("/api/transactions/new-sale", json={
            "customer_id": str(uuid4()),
            "transaction_date": "2024-07-15",
            "items": []
        })
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("at least 1 item" in str(error).lower() for error in errors)

    def test_sale_payload_field_types(self, client: TestClient):
        """Test field type validation."""
        # Test invalid UUID
        response = client.post("/api/transactions/new-sale", json={
            "customer_id": "not-a-uuid",
            "transaction_date": "2024-07-15",
            "items": [{"item_id": str(uuid4()), "quantity": 1, "unit_cost": 10.0}]
        })
        assert response.status_code == 422

        # Test invalid date format
        response = client.post("/api/transactions/new-sale", json={
            "customer_id": str(uuid4()),
            "transaction_date": "15-07-2024",  # Wrong format
            "items": [{"item_id": str(uuid4()), "quantity": 1, "unit_cost": 10.0}]
        })
        assert response.status_code == 422

    def test_sale_item_validation(self, client: TestClient):
        """Test sale item field validation."""
        # Test negative quantity
        response = client.post("/api/transactions/new-sale", json={
            "customer_id": str(uuid4()),
            "transaction_date": "2024-07-15",
            "items": [{
                "item_id": str(uuid4()),
                "quantity": -1,  # Invalid
                "unit_cost": 10.0
            }]
        })
        assert response.status_code == 422

        # Test negative unit cost
        response = client.post("/api/transactions/new-sale", json={
            "customer_id": str(uuid4()),
            "transaction_date": "2024-07-15",
            "items": [{
                "item_id": str(uuid4()),
                "quantity": 1,
                "unit_cost": -10.0  # Invalid
            }]
        })
        assert response.status_code == 422

        # Test tax rate > 100
        response = client.post("/api/transactions/new-sale", json={
            "customer_id": str(uuid4()),
            "transaction_date": "2024-07-15",
            "items": [{
                "item_id": str(uuid4()),
                "quantity": 1,
                "unit_cost": 10.0,
                "tax_rate": 150.0  # Invalid
            }]
        })
        assert response.status_code == 422

    def test_sale_with_valid_structure(self, client: TestClient):
        """Test sale with valid structure (will fail on non-existent entities)."""
        payload = {
            "customer_id": str(uuid4()),
            "transaction_date": "2024-07-15",
            "notes": "Test sale",
            "reference_number": "REF-001",
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 2,
                    "unit_cost": 25.50,
                    "tax_rate": 8.5,
                    "discount_amount": 5.00,
                    "notes": "Test item 1"
                },
                {
                    "item_id": str(uuid4()),
                    "quantity": 1,
                    "unit_cost": 100.00,
                    "tax_rate": 8.5,
                    "discount_amount": 0.00,
                    "notes": "Test item 2"
                }
            ]
        }
        
        response = client.post("/api/transactions/new-sale", json=payload)
        
        # Should return 404 for non-existent customer/items, not 422
        if response.status_code == 404:
            assert "not found" in response.json()["detail"].lower()
        elif response.status_code == 401:
            # Auth required
            assert "Not authenticated" in response.json()["detail"]
        else:
            # If successful (unlikely without real data)
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "transaction_id" in data

    def test_sale_endpoint_methods(self, client: TestClient):
        """Test that only POST is allowed."""
        # GET should not be allowed
        response = client.get("/api/transactions/new-sale")
        assert response.status_code in [405, 404]  # Method not allowed or not found
        
        # PUT should not be allowed
        response = client.put("/api/transactions/new-sale", json={})
        assert response.status_code in [405, 404]
        
        # DELETE should not be allowed
        response = client.delete("/api/transactions/new-sale")
        assert response.status_code in [405, 404]

    def test_transaction_listing_endpoint(self, client: TestClient):
        """Test transaction listing endpoint exists."""
        response = client.get("/api/transactions/")
        # Should return 200 or 401 if auth required
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_transaction_detail_endpoint(self, client: TestClient):
        """Test transaction detail endpoint exists."""
        fake_id = str(uuid4())
        response = client.get(f"/api/transactions/{fake_id}")
        # Should return 404 for non-existent ID or 401 if auth required
        assert response.status_code in [404, 401]

    def test_large_sale_payload(self, client: TestClient):
        """Test handling of large sale with many items."""
        items = []
        for i in range(50):  # 50 items
            items.append({
                "item_id": str(uuid4()),
                "quantity": i + 1,
                "unit_cost": 10.00 + i,
                "tax_rate": 8.5,
                "discount_amount": 0.0,
                "notes": f"Item {i+1}"
            })
        
        payload = {
            "customer_id": str(uuid4()),
            "transaction_date": "2024-07-15",
            "notes": "Large sale test",
            "reference_number": "REF-LARGE-001",
            "items": items
        }
        
        response = client.post("/api/transactions/new-sale", json=payload)
        # Should handle large payload without crashing
        assert response.status_code in [404, 401, 201, 422]

    def test_sale_special_characters(self, client: TestClient):
        """Test handling of special characters in text fields."""
        payload = {
            "customer_id": str(uuid4()),
            "transaction_date": "2024-07-15",
            "notes": "Test with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "reference_number": "REF-SPECIAL-001",
            "items": [{
                "item_id": str(uuid4()),
                "quantity": 1,
                "unit_cost": 10.00,
                "tax_rate": 0.0,
                "discount_amount": 0.0,
                "notes": "Unicode test: 你好世界 🌍 café"
            }]
        }
        
        response = client.post("/api/transactions/new-sale", json=payload)
        # Should handle special characters without crashing
        assert response.status_code in [404, 401, 201, 422]

    def test_sale_decimal_precision(self, client: TestClient):
        """Test handling of decimal precision."""
        payload = {
            "customer_id": str(uuid4()),
            "transaction_date": "2024-07-15",
            "items": [{
                "item_id": str(uuid4()),
                "quantity": 1,
                "unit_cost": 10.99999,  # Many decimal places
                "tax_rate": 8.525,  # Three decimal places
                "discount_amount": 0.001,  # Small decimal
                "notes": "Decimal test"
            }]
        }
        
        response = client.post("/api/transactions/new-sale", json=payload)
        # Should handle decimals appropriately
        assert response.status_code in [404, 401, 201, 422]