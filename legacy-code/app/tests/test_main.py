import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.main import app


@pytest.mark.integration
class TestMainApplication:
    """Test main application functionality."""
    
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "features" in data
        assert "docs" in data
        assert "redoc" in data
        assert data["version"] == "2.0.0"
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0
    
    async def test_health_check_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert data["architecture"] == "Domain-Driven Design"
        assert "modules" in data
        assert "endpoints" in data
        assert "database" in data
        assert isinstance(data["modules"], list)
        assert len(data["modules"]) > 0
    
    async def test_openapi_docs(self, client: AsyncClient):
        """Test OpenAPI documentation endpoint."""
        response = await client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "Rental Management System"
        assert data["info"]["version"] == "1.0.0"
    
    async def test_docs_endpoint(self, client: AsyncClient):
        """Test Swagger UI docs endpoint."""
        response = await client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    async def test_redoc_endpoint(self, client: AsyncClient):
        """Test ReDoc endpoint."""
        response = await client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are present."""
        response = await client.options("/")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    async def test_404_endpoint(self, client: AsyncClient):
        """Test 404 error handling."""
        response = await client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found" in data["detail"]
    
    async def test_api_v1_prefix(self, client: AsyncClient):
        """Test API v1 prefix is working."""
        # This endpoint should exist based on our auth routes
        response = await client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
    
    async def test_request_id_header(self, client: AsyncClient):
        """Test that request ID is generated (if implemented)."""
        response = await client.get("/")
        
        assert response.status_code == 200
        # Request ID might be added in headers in production
        # This is a placeholder test for future implementation
    
    async def test_security_headers(self, client: AsyncClient):
        """Test security headers are present."""
        response = await client.get("/")
        
        assert response.status_code == 200
        # Security headers might be added in production
        # This is a placeholder test for future implementation
    
    async def test_json_response_format(self, client: AsyncClient):
        """Test JSON response format consistency."""
        response = await client.get("/")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"
        
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)
    
    async def test_api_version_consistency(self, client: AsyncClient):
        """Test API version consistency across endpoints."""
        # Test root endpoint
        response = await client.get("/")
        assert response.status_code == 200
        root_data = response.json()
        
        # Test health endpoint
        response = await client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        
        # Versions should be consistent
        assert root_data["version"] == health_data["version"]
    
    async def test_application_startup(self, client: AsyncClient):
        """Test application startup is successful."""
        # If we can make requests, the app started successfully
        response = await client.get("/health")
        assert response.status_code == 200
        
        # Test database connection is working
        data = response.json()
        assert "database" in data
        assert "SQLite" in data["database"]
    
    async def test_exception_handling(self, client: AsyncClient):
        """Test global exception handling."""
        # Test validation error handling
        response = await client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422
        
        # Test 404 handling
        response = await client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # Test method not allowed
        response = await client.post("/")
        assert response.status_code == 405
    
    async def test_content_negotiation(self, client: AsyncClient):
        """Test content negotiation."""
        # Test JSON response
        response = await client.get("/", headers={"Accept": "application/json"})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        
        # Test HTML docs
        response = await client.get("/docs", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    async def test_rate_limiting_placeholder(self, client: AsyncClient):
        """Test rate limiting (placeholder for future implementation)."""
        # Make multiple requests
        for _ in range(5):
            response = await client.get("/")
            assert response.status_code == 200
        
        # Rate limiting not implemented yet, but structure is ready
        # This test ensures no errors occur with multiple requests
    
    async def test_middleware_chain(self, client: AsyncClient):
        """Test middleware chain is working."""
        response = await client.get("/")
        
        assert response.status_code == 200
        # CORS middleware should add headers
        assert "access-control-allow-origin" in response.headers
        
        # Exception handling middleware should be working
        # (tested implicitly by other tests)
    
    async def test_database_health(self, client: AsyncClient):
        """Test database health check."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        
        # Database should be accessible
        assert "SQLite" in data["database"]
    
    async def test_application_metadata(self, client: AsyncClient):
        """Test application metadata."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required metadata
        assert "message" in data
        assert "version" in data
        assert "description" in data
        assert "features" in data
        
        # Check feature list
        features = data["features"]
        expected_features = [
            "Authentication & User Management",
            "Customer & Supplier Management",
            "Master Data Management",
            "Inventory Management",
            "Transaction Processing",
            "Rental Operations",
            "Analytics & Reporting",
            "System Management"
        ]
        
        for feature in expected_features:
            assert feature in features