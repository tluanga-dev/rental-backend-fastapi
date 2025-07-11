"""
Simple health test without complex fixtures
"""

import requests
import pytest


def test_health_endpoint_direct():
    """Test health endpoint with direct HTTP request"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "FastAPI Project"
        print(f"✅ Health check passed: {data}")
    except requests.exceptions.ConnectionError:
        pytest.skip("FastAPI server not running at http://127.0.0.1:8000")
    except Exception as e:
        pytest.fail(f"Health check failed: {e}")


def test_openapi_docs_available():
    """Test that OpenAPI docs are available"""
    try:
        response = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        assert response.status_code == 200
        print("✅ OpenAPI docs are accessible")
    except requests.exceptions.ConnectionError:
        pytest.skip("FastAPI server not running at http://127.0.0.1:8000")
    except Exception as e:
        pytest.fail(f"Docs check failed: {e}")


def test_openapi_json_available():
    """Test that OpenAPI JSON spec is available"""
    try:
        response = requests.get("http://127.0.0.1:8000/openapi.json", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        print(f"✅ OpenAPI spec available with {len(data['paths'])} endpoints")
    except requests.exceptions.ConnectionError:
        pytest.skip("FastAPI server not running at http://127.0.0.1:8000")
    except Exception as e:
        pytest.fail(f"OpenAPI spec check failed: {e}")