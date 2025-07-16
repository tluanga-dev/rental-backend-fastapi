import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.models import Company


@pytest.mark.asyncio
class TestCompanyAPI:
    """Test cases for company API endpoints."""
    
    def test_create_company(self, client: TestClient, auth_headers: dict):
        """Test creating a company via API."""
        # Arrange
        company_data = {
            "company_name": "API Test Company",
            "address": "API Test Address",
            "email": "api@testcompany.com",
            "phone": "+91-3333333333",
            "gst_no": "15QWERT1234Y5U6",
            "registration_number": "APIREG123"
        }
        
        # Act
        response = client.post(
            "/api/company/",
            json=company_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["company_name"] == "API Test Company"
        assert data["email"] == "api@testcompany.com"
        assert data["gst_no"] == "15QWERT1234Y5U6"
        assert data["is_active"] is True
        assert "id" in data
    
    def test_create_company_invalid_email(self, client: TestClient, auth_headers: dict):
        """Test creating a company with invalid email."""
        # Arrange
        company_data = {
            "company_name": "Invalid Email Company",
            "email": "invalid-email"  # Invalid email format
        }
        
        # Act
        response = client.post(
            "/api/company/",
            json=company_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_company_duplicate_name(
        self, client: TestClient, auth_headers: dict, test_company: Company
    ):
        """Test creating a company with duplicate name."""
        # Arrange
        company_data = {
            "company_name": test_company.company_name,  # Duplicate name
            "email": "another@email.com"
        }
        
        # Act
        response = client.post(
            "/api/company/",
            json=company_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]
    
    def test_get_company(
        self, client: TestClient, auth_headers: dict, test_company: Company
    ):
        """Test getting a company by ID."""
        # Act
        response = client.get(
            f"/api/company/{test_company.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_company.id)
        assert data["company_name"] == test_company.company_name
        assert data["email"] == test_company.email
    
    def test_get_company_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting a non-existent company."""
        # Act
        response = client.get(
            "/api/company/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_active_company(
        self, client: TestClient, auth_headers: dict, test_company: Company
    ):
        """Test getting the active company."""
        # Act
        response = client.get(
            "/api/company/active",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is True
    
    def test_list_companies(
        self, client: TestClient, auth_headers: dict, test_company: Company, test_company_2: Company
    ):
        """Test listing companies."""
        # Act
        response = client.get(
            "/api/company/",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2
        assert data["page"] == 1
        assert "has_next" in data
        assert "has_previous" in data
    
    def test_list_companies_with_pagination(
        self, client: TestClient, auth_headers: dict, test_company: Company, test_company_2: Company
    ):
        """Test listing companies with pagination."""
        # Act
        response = client.get(
            "/api/company/?page=1&page_size=1",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page_size"] == 1
        assert data["has_next"] is True
    
    def test_list_companies_with_filter(
        self, client: TestClient, auth_headers: dict, test_company: Company
    ):
        """Test listing companies with filters."""
        # Act
        response = client.get(
            f"/api/company/?email={test_company.email}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert any(item["email"] == test_company.email for item in data["items"])
    
    def test_list_companies_with_search(
        self, client: TestClient, auth_headers: dict, test_company: Company
    ):
        """Test listing companies with search."""
        # Act
        response = client.get(
            "/api/company/?search=Test",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
    
    def test_update_company(
        self, client: TestClient, auth_headers: dict, test_company: Company
    ):
        """Test updating a company."""
        # Arrange
        update_data = {
            "company_name": "Updated API Company",
            "email": "updated@apicompany.com"
        }
        
        # Act
        response = client.put(
            f"/api/company/{test_company.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["company_name"] == "Updated API Company"
        assert data["email"] == "updated@apicompany.com"
        # Unchanged fields should remain
        assert data["gst_no"] == test_company.gst_no
    
    def test_update_company_partial(
        self, client: TestClient, auth_headers: dict, test_company: Company
    ):
        """Test partial update of a company."""
        # Arrange
        update_data = {
            "phone": "+91-4444444444"
        }
        
        # Act
        response = client.put(
            f"/api/company/{test_company.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["phone"] == "+91-4444444444"
        # Other fields should remain unchanged
        assert data["company_name"] == test_company.company_name
        assert data["email"] == test_company.email
    
    def test_delete_company(
        self, client: TestClient, auth_headers: dict, test_company: Company, test_company_2: Company
    ):
        """Test deleting a company."""
        # First activate the second company
        client.post(
            f"/api/company/{test_company_2.id}/activate",
            headers=auth_headers
        )
        
        # Act
        response = client.delete(
            f"/api/company/{test_company.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify company is deactivated
        get_response = client.get(
            f"/api/company/{test_company.id}",
            headers=auth_headers
        )
        assert get_response.json()["is_active"] is False
    
    def test_activate_company(
        self, client: TestClient, auth_headers: dict, test_company: Company, test_company_2: Company
    ):
        """Test activating a company."""
        # Act
        response = client.post(
            f"/api/company/{test_company_2.id}/activate",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_company_2.id)
        assert data["is_active"] is True
        
        # Verify first company is deactivated
        get_response = client.get(
            f"/api/company/{test_company.id}",
            headers=auth_headers
        )
        assert get_response.json()["is_active"] is False
    
    def test_search_companies(
        self, client: TestClient, auth_headers: dict, test_company: Company
    ):
        """Test searching companies."""
        # Act
        response = client.get(
            f"/api/company/search/?q={test_company.gst_no[:5]}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(item["id"] == str(test_company.id) for item in data)
    
    def test_search_companies_no_results(
        self, client: TestClient, auth_headers: dict
    ):
        """Test searching companies with no results."""
        # Act
        response = client.get(
            "/api/company/search/?q=NONEXISTENT999",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0