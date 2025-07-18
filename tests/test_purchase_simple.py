"""
Simple test for purchase transaction endpoint to verify basic functionality.
"""

import pytest
from uuid import uuid4
from datetime import date
from fastapi.testclient import TestClient
from app.main import app


class TestPurchaseTransactionSimple:
    """Simple test suite for purchase transaction endpoint."""
    
    def test_purchase_endpoint_exists(self):
        """Test that the purchase endpoint exists and is accessible."""
        client = TestClient(app)
        
        # Make a request without auth to check the endpoint exists
        response = client.post("/api/transactions/new-purchase", json={})
        
        # Should return 401 (unauthorized) not 404 (not found)
        # This confirms the endpoint exists
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_purchase_validation_missing_fields(self):
        """Test validation with missing required fields."""
        client = TestClient(app)
        
        # Create a basic auth header (will fail but shows validation works)
        headers = {"Authorization": "Bearer fake_token"}
        
        response = client.post(
            "/api/transactions/new-purchase",
            json={},
            headers=headers
        )
        
        # Should return 422 (validation error) for missing fields
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        
        # Check that validation errors mention required fields
        error_messages = str(data["detail"])
        assert "supplier_id" in error_messages or "required" in error_messages.lower()
    
    def test_purchase_validation_invalid_uuid(self):
        """Test validation with invalid UUID format."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        invalid_request = {
            "supplier_id": "invalid-uuid",
            "location_id": "invalid-uuid",
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": "invalid-uuid",
                    "quantity": 10,
                    "unit_cost": 25.50,
                    "condition": "A"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=invalid_request,
            headers=headers
        )
        
        # Should return 422 (validation error) for invalid UUID
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_purchase_validation_invalid_date(self):
        """Test validation with invalid date format."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        invalid_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": "invalid-date",
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 10,
                    "unit_cost": 25.50,
                    "condition": "A"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=invalid_request,
            headers=headers
        )
        
        # Should return 422 (validation error) for invalid date
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_purchase_validation_invalid_quantity(self):
        """Test validation with invalid quantity values."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        # Test with zero quantity
        invalid_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 0,  # Invalid
                    "unit_cost": 25.50,
                    "condition": "A"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=invalid_request,
            headers=headers
        )
        
        # Should return 422 (validation error) for invalid quantity
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_purchase_validation_invalid_condition(self):
        """Test validation with invalid condition code."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        invalid_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 10,
                    "unit_cost": 25.50,
                    "condition": "X"  # Invalid condition
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=invalid_request,
            headers=headers
        )
        
        # Should return 422 (validation error) for invalid condition
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_purchase_validation_empty_items(self):
        """Test validation with empty items list."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        invalid_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": "2024-01-15",
            "items": []  # Empty items list
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=invalid_request,
            headers=headers
        )
        
        # Should return 422 (validation error) for empty items
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_purchase_validation_negative_amounts(self):
        """Test validation with negative amounts."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        # Test with negative unit cost
        invalid_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 10,
                    "unit_cost": -25.50,  # Negative cost
                    "condition": "A"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=invalid_request,
            headers=headers
        )
        
        # Should return 422 (validation error) for negative cost
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_purchase_validation_invalid_tax_rate(self):
        """Test validation with invalid tax rate."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        # Test with tax rate over 100%
        invalid_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 10,
                    "unit_cost": 25.50,
                    "tax_rate": 150.0,  # Over 100%
                    "condition": "A"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=invalid_request,
            headers=headers
        )
        
        # Should return 422 (validation error) for invalid tax rate
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_purchase_validation_string_length_limits(self):
        """Test validation with string length limits."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        # Test with notes too long
        invalid_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": "2024-01-15",
            "notes": "x" * 1001,  # Over 1000 character limit
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 10,
                    "unit_cost": 25.50,
                    "condition": "A"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=invalid_request,
            headers=headers
        )
        
        # Should return 422 (validation error) for string too long
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_purchase_validation_valid_structure(self):
        """Test that a well-formed request passes validation (but fails auth)."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        # Create a valid request structure
        valid_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": date.today().isoformat(),
            "notes": "Test purchase transaction",
            "reference_number": "TEST-001",
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 10,
                    "unit_cost": 25.50,
                    "tax_rate": 8.5,
                    "discount_amount": 5.00,
                    "condition": "A",
                    "notes": "Test item"
                },
                {
                    "item_id": str(uuid4()),
                    "quantity": 5,
                    "unit_cost": 35.00,
                    "condition": "B"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=valid_request,
            headers=headers
        )
        
        # Should return 401 (unauthorized) not 422 (validation error)
        # This means validation passed but authentication failed
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_purchase_condition_codes(self):
        """Test all valid condition codes."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        conditions = ["A", "B", "C", "D"]
        
        for condition in conditions:
            valid_request = {
                "supplier_id": str(uuid4()),
                "location_id": str(uuid4()),
                "purchase_date": date.today().isoformat(),
                "items": [
                    {
                        "item_id": str(uuid4()),
                        "quantity": 1,
                        "unit_cost": 10.00,
                        "condition": condition
                    }
                ]
            }
            
            response = client.post(
                "/api/transactions/new-purchase",
                json=valid_request,
                headers=headers
            )
            
            # Should return 401 (unauthorized) not 422 (validation error)
            # This means validation passed for this condition code
            assert response.status_code == 401, f"Condition {condition} should be valid"
    
    def test_purchase_optional_fields(self):
        """Test that optional fields work correctly."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        # Test with minimal required fields only
        minimal_request = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": date.today().isoformat(),
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 10,
                    "unit_cost": 25.50,
                    "condition": "A"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=minimal_request,
            headers=headers
        )
        
        # Should return 401 (unauthorized) not 422 (validation error)
        # This means validation passed with minimal fields
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_purchase_decimal_precision(self):
        """Test decimal precision handling."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer fake_token"}
        
        # Test with various decimal precisions
        request_with_decimals = {
            "supplier_id": str(uuid4()),
            "location_id": str(uuid4()),
            "purchase_date": date.today().isoformat(),
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 3,
                    "unit_cost": 33.333,  # Repeating decimal
                    "tax_rate": 7.75,     # Two decimal places
                    "discount_amount": 1.99,
                    "condition": "A"
                }
            ]
        }
        
        response = client.post(
            "/api/transactions/new-purchase",
            json=request_with_decimals,
            headers=headers
        )
        
        # Should return 401 (unauthorized) not 422 (validation error)
        # This means validation passed with decimal values
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data