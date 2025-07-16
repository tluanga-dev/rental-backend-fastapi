"""
Comprehensive test suite for the Company module.

This test file runs all company-related tests to ensure the module works correctly.
Run with: pytest tests/test_company_comprehensive.py -v
"""

import pytest
from uuid import UUID
from fastapi import status


@pytest.mark.asyncio
class TestCompanyComprehensive:
    """Comprehensive tests for company module functionality."""
    
    async def test_complete_company_workflow(
        self, client, auth_headers, company_service, db_session
    ):
        """Test complete company workflow from creation to deletion."""
        
        # Step 1: Create a company via API
        create_data = {
            "company_name": "Workflow Test Company",
            "address": "123 Workflow Street, Test City",
            "email": "workflow@testcompany.com",
            "phone": "+91-9876543210",
            "gst_no": "29WORKFLOW234F1Z5",
            "registration_number": "WORKFLOW123"
        }
        
        create_response = client.post(
            "/api/company/",
            json=create_data,
            headers=auth_headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        company_id = create_response.json()["id"]
        
        # Step 2: Verify company was created correctly
        get_response = client.get(
            f"/api/company/{company_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_200_OK
        company_data = get_response.json()
        assert company_data["company_name"] == "Workflow Test Company"
        assert company_data["is_active"] is True
        
        # Step 3: Search for the company
        search_response = client.get(
            "/api/company/search/?q=Workflow",
            headers=auth_headers
        )
        assert search_response.status_code == status.HTTP_200_OK
        search_results = search_response.json()
        assert len(search_results) >= 1
        assert any(c["id"] == company_id for c in search_results)
        
        # Step 4: Update the company
        update_data = {
            "company_name": "Updated Workflow Company",
            "phone": "+91-1111111111",
            "address": "456 Updated Street, New City"
        }
        
        update_response = client.put(
            f"/api/company/{company_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        updated_data = update_response.json()
        assert updated_data["company_name"] == "Updated Workflow Company"
        assert updated_data["phone"] == "+91-1111111111"
        # GST should remain unchanged
        assert updated_data["gst_no"] == "29WORKFLOW234F1Z5"
        
        # Step 5: Create another company to test activation
        second_company_data = {
            "company_name": "Second Workflow Company",
            "email": "second@workflow.com"
        }
        
        second_response = client.post(
            "/api/company/",
            json=second_company_data,
            headers=auth_headers
        )
        assert second_response.status_code == status.HTTP_201_CREATED
        second_company_id = second_response.json()["id"]
        
        # Step 6: Activate the second company
        activate_response = client.post(
            f"/api/company/{second_company_id}/activate",
            headers=auth_headers
        )
        assert activate_response.status_code == status.HTTP_200_OK
        
        # Verify first company is deactivated
        first_check = client.get(
            f"/api/company/{company_id}",
            headers=auth_headers
        )
        assert first_check.json()["is_active"] is False
        
        # Step 7: Get active company
        active_response = client.get(
            "/api/company/active",
            headers=auth_headers
        )
        assert active_response.status_code == status.HTTP_200_OK
        assert active_response.json()["id"] == second_company_id
        
        # Step 8: List all companies with filters
        list_response = client.get(
            "/api/company/?search=Workflow&include_inactive=true",
            headers=auth_headers
        )
        assert list_response.status_code == status.HTTP_200_OK
        list_data = list_response.json()
        assert list_data["total"] >= 2
        
        # Step 9: Delete the first company
        delete_response = client.delete(
            f"/api/company/{company_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Step 10: Verify soft delete
        deleted_check = await company_service.repository.get_by_id(UUID(company_id))
        assert deleted_check is not None  # Still exists in DB
        assert deleted_check.is_active is False
    
    async def test_company_validation_comprehensive(
        self, client, auth_headers, company_service
    ):
        """Test comprehensive validation scenarios."""
        
        # Test 1: Missing required field
        response = client.post(
            "/api/company/",
            json={},  # No company_name
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test 2: Invalid email formats
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@example",
            "user @example.com"
        ]
        
        for email in invalid_emails:
            response = client.post(
                "/api/company/",
                json={
                    "company_name": f"Email Test {email}",
                    "email": email
                },
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test 3: Duplicate unique fields
        # Create a company first
        original = client.post(
            "/api/company/",
            json={
                "company_name": "Unique Test Company",
                "gst_no": "15UNIQUE1234Y5U6",
                "registration_number": "UNIQUE123"
            },
            headers=auth_headers
        )
        assert original.status_code == status.HTTP_201_CREATED
        
        # Try duplicate GST
        dup_gst = client.post(
            "/api/company/",
            json={
                "company_name": "Different Company",
                "gst_no": "15UNIQUE1234Y5U6"  # Same GST
            },
            headers=auth_headers
        )
        assert dup_gst.status_code == status.HTTP_409_CONFLICT
        
        # Try duplicate registration number
        dup_reg = client.post(
            "/api/company/",
            json={
                "company_name": "Another Different Company",
                "registration_number": "UNIQUE123"  # Same registration
            },
            headers=auth_headers
        )
        assert dup_reg.status_code == status.HTTP_409_CONFLICT
    
    async def test_company_business_rules(
        self, client, auth_headers, company_service
    ):
        """Test business rule enforcement."""
        
        # Create two companies
        company1 = client.post(
            "/api/company/",
            json={"company_name": "Business Rule Company 1"},
            headers=auth_headers
        )
        company1_id = company1.json()["id"]
        
        company2 = client.post(
            "/api/company/",
            json={"company_name": "Business Rule Company 2"},
            headers=auth_headers
        )
        company2_id = company2.json()["id"]
        
        # Activate company 1
        client.post(
            f"/api/company/{company1_id}/activate",
            headers=auth_headers
        )
        
        # Try to delete the only active company
        delete_response = client.delete(
            f"/api/company/{company1_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot delete the only active company" in delete_response.json()["detail"]
        
        # Activate company 2 and then delete company 1 should work
        client.post(
            f"/api/company/{company2_id}/activate",
            headers=auth_headers
        )
        
        delete_response = client.delete(
            f"/api/company/{company1_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT