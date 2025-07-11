# Comprehensive API Testing Documentation

This document describes the comprehensive test suite for the FastAPI Rental Management System, covering all API endpoints documented at `http://127.0.0.1:8000/docs`.

## 🎯 Test Coverage Overview

The test suite provides **100% endpoint coverage** for all API endpoints with comprehensive scenarios including:

- ✅ **Health & Core Endpoints** - System health and basic functionality
- ✅ **Authentication Endpoints** - Registration, login, token management
- ✅ **User Management** - CRUD operations, admin functions
- ✅ **Role Management** - RBAC creation and assignment
- ✅ **Customer Management** - Customer lifecycle management
- ✅ **Supplier Management** - Supplier relationship management  
- ✅ **Master Data** - Brands, categories, locations management
- ✅ **Inventory Management** - Items and inventory units
- ✅ **Transaction Management** - Complete transaction processing
- ✅ **Analytics** - Business intelligence and reporting
- ✅ **System Management** - Settings and administration
- ✅ **End-to-End Workflows** - Complete business processes
- ✅ **Error Scenarios** - Comprehensive error handling
- ✅ **Performance Tests** - Load and performance validation

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── test_all_endpoints.py       # Comprehensive endpoint tests
├── test_error_scenarios.py     # Error handling and edge cases
├── test_runner.py              # Custom test runner with reporting
├── test_auth.py               # Legacy auth tests
├── test_core.py               # Legacy core tests
└── test_users.py              # Legacy user tests
```

## 🚀 Quick Start

### Prerequisites

1. **FastAPI Server Running**: Ensure the server is running at `http://127.0.0.1:8000`
2. **Test Database**: Separate PostgreSQL test database configured
3. **Dependencies**: Install test dependencies

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Verify server is running
curl http://127.0.0.1:8000/health
```

### Running Tests

#### Option 1: Complete Test Suite (Recommended)
```bash
# Run comprehensive test suite with detailed reporting
python tests/test_runner.py
```

#### Option 2: Standard Pytest
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest tests/test_all_endpoints.py::TestAuthenticationEndpoints -v

# Run with coverage
pytest --cov=app --cov-report=html
```

#### Option 3: Category-Specific Testing
```bash
# Authentication tests only
pytest tests/test_all_endpoints.py::TestAuthenticationEndpoints

# Customer management tests
pytest tests/test_all_endpoints.py::TestCustomerManagementEndpoints

# Error scenario tests
pytest tests/test_error_scenarios.py

# Performance tests
pytest tests/test_all_endpoints.py::TestPerformanceEndpoints
```

## 📊 Test Categories Detail

### 1. Health & Core Endpoints
**File**: `test_all_endpoints.py::TestHealthEndpoints`
- `GET /health` - System health check

### 2. Authentication Endpoints  
**File**: `test_all_endpoints.py::TestAuthenticationEndpoints`
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (username/email)
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/logout` - User logout

**Test Scenarios**:
- Valid registration with all fields
- Duplicate username/email handling
- Login with username and email
- Invalid credentials handling
- Token validation and refresh
- Unauthorized access attempts

### 3. User Management Endpoints
**File**: `test_all_endpoints.py::TestUserManagementEndpoints`
- `GET /api/users/` - List users (admin only)
- `POST /api/users/` - Create user (admin only)
- `GET /api/users/{user_id}` - Get user by ID
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user

**Test Scenarios**:
- Pagination and filtering
- Admin privilege requirements
- User CRUD operations
- Permission validation

### 4. Role Management Endpoints
**File**: `test_all_endpoints.py::TestRoleManagementEndpoints`  
- `POST /api/users/roles/` - Create role
- `GET /api/users/roles/` - List roles
- `POST /api/users/{user_id}/roles/{role_id}` - Assign role

**Test Scenarios**:
- Role creation with permissions
- Role assignment to users
- RBAC functionality validation

### 5. Customer Management Endpoints
**File**: `test_all_endpoints.py::TestCustomerManagementEndpoints`
- `GET /api/customers/customers/` - List customers
- `POST /api/customers/customers/` - Create customer
- `GET /api/customers/customers/{customer_id}` - Get customer
- `PUT /api/customers/customers/{customer_id}` - Update customer
- `DELETE /api/customers/customers/{customer_id}` - Delete customer
- `GET /api/customers/customers/search` - Search customers

**Test Scenarios**:
- Complete customer lifecycle
- Business vs Individual customers
- Address and contact validation
- Credit limit and payment terms
- Search functionality

### 6. Supplier Management Endpoints
**File**: `test_all_endpoints.py::TestSupplierManagementEndpoints`
- `GET /api/suppliers/suppliers/` - List suppliers
- `POST /api/suppliers/suppliers/` - Create supplier
- `GET /api/suppliers/suppliers/{supplier_id}` - Get supplier
- `PUT /api/suppliers/suppliers/{supplier_id}` - Update supplier
- `DELETE /api/suppliers/suppliers/{supplier_id}` - Delete supplier

**Test Scenarios**:
- Supplier relationship management
- Rating and performance tracking
- Contact and payment information

### 7. Master Data Endpoints
**File**: `test_all_endpoints.py::TestMasterDataEndpoints`

**Brands**:
- `GET /api/master-data/brands/` - List brands
- `POST /api/master-data/brands/` - Create brand
- `GET /api/master-data/brands/{brand_id}` - Get brand
- `PUT /api/master-data/brands/{brand_id}` - Update brand  
- `DELETE /api/master-data/brands/{brand_id}` - Delete brand

**Categories**:
- `GET /api/master-data/categories/` - List categories
- `POST /api/master-data/categories/` - Create category
- `GET /api/master-data/categories/{category_id}` - Get category
- `PUT /api/master-data/categories/{category_id}` - Update category
- `DELETE /api/master-data/categories/{category_id}` - Delete category

**Locations**:
- `GET /api/master-data/locations/` - List locations
- `POST /api/master-data/locations/` - Create location
- `GET /api/master-data/locations/{location_id}` - Get location
- `PUT /api/master-data/locations/{location_id}` - Update location
- `DELETE /api/master-data/locations/{location_id}` - Delete location

**Test Scenarios**:
- Hierarchical category structures
- Location types and management
- Brand catalog management
- Duplicate code prevention

### 8. Inventory Management Endpoints
**File**: `test_all_endpoints.py::TestInventoryManagementEndpoints`

**Items**:
- `GET /api/inventory/items/` - List items
- `POST /api/inventory/items/` - Create item
- `GET /api/inventory/items/{item_id}` - Get item
- `PUT /api/inventory/items/{item_id}` - Update item
- `DELETE /api/inventory/items/{item_id}` - Delete item

**Inventory Units**:
- `GET /api/inventory/units/` - List inventory units
- `POST /api/inventory/units/` - Create inventory unit
- `GET /api/inventory/units/{unit_id}` - Get inventory unit
- `PUT /api/inventory/units/{unit_id}` - Update inventory unit
- `DELETE /api/inventory/units/{unit_id}` - Delete inventory unit

**Test Scenarios**:
- Equipment vs consumable items
- Rental rates and pricing
- Inventory tracking and availability
- Maintenance and condition management

### 9. Transaction Management Endpoints
**File**: `test_all_endpoints.py::TestTransactionManagementEndpoints`

**Transaction Headers**:
- `GET /api/transactions/headers/` - List transactions
- `POST /api/transactions/headers/` - Create transaction
- `GET /api/transactions/headers/{transaction_id}` - Get transaction
- `PUT /api/transactions/headers/{transaction_id}` - Update transaction
- `DELETE /api/transactions/headers/{transaction_id}` - Delete transaction

**Transaction Lines**:
- `POST /api/transactions/headers/{transaction_id}/lines/` - Add line

**Test Scenarios**:
- Rental vs sales transactions
- Multi-line transactions
- Date validation for rentals
- Payment and status tracking

### 10. Analytics Endpoints
**File**: `test_all_endpoints.py::TestAnalyticsEndpoints`
- `GET /api/analytics/revenue/` - Revenue analytics
- `GET /api/analytics/inventory/` - Inventory analytics
- `GET /api/analytics/customers/` - Customer analytics
- `GET /api/analytics/utilization/` - Utilization analytics
- `GET /api/analytics/financial-summary/` - Financial summary

**Test Scenarios**:
- Date range filtering
- Performance metrics calculation
- Business intelligence data

### 11. System Management Endpoints
**File**: `test_all_endpoints.py::TestSystemEndpoints`
- `GET /api/system/settings/` - Get system settings
- `PUT /api/system/settings/` - Update system settings
- `GET /api/system/audit-logs/` - Get audit logs
- `POST /api/system/backup/` - Backup system

**Test Scenarios**:
- Admin-only access
- System configuration management
- Audit trail functionality

## 🔥 Error Scenario Testing

**File**: `test_error_scenarios.py`

### Authentication Errors
- Invalid email formats
- Weak passwords
- Missing required fields
- Non-existent users
- Wrong passwords
- Invalid tokens
- Unauthorized access

### Validation Errors
- Invalid email formats in customer data
- Missing required fields
- Invalid enums/types
- Negative values where inappropriate
- Invalid date ranges

### Not Found Errors
- Non-existent resource IDs
- Invalid UUID formats
- Deleted resources

### Conflict Errors
- Duplicate customer codes
- Duplicate brand codes
- Duplicate item codes
- Constraint violations

### Permission Errors
- Regular users accessing admin endpoints
- Insufficient privileges
- RBAC violations

### Malformed Request Errors
- Invalid JSON syntax
- Invalid UUID formats
- Missing content-type headers
- Invalid query parameters

### Business Logic Errors
- Rental transactions without dates
- Negative credit limits
- Invalid business rule violations

## 🏁 End-to-End Workflow Testing

**File**: `test_all_endpoints.py::TestEndToEndWorkflows`

### Complete Rental Workflow
1. Create customer
2. Create brand and category
3. Create location
4. Create inventory item
5. Create inventory unit
6. Create rental transaction
7. Add transaction lines
8. Verify complete transaction

This test validates the entire business process from customer onboarding to transaction completion.

## ⚡ Performance Testing

**File**: `test_all_endpoints.py::TestPerformanceEndpoints`

### Concurrent Operations
- Parallel customer creation
- Concurrent request handling
- Thread safety validation

### Bulk Data Retrieval
- Large dataset performance
- Pagination efficiency
- Response time validation

**Performance Benchmarks**:
- Response times under 500ms for most endpoints
- Successful concurrent request handling
- No timeout errors under normal load

## 📈 Test Reporting

### Automatic Reporting
The custom test runner (`test_runner.py`) provides:

- **Category-based Results**: Results grouped by functional area
- **Performance Metrics**: Response times and throughput
- **Success Rates**: Pass/fail percentages by category
- **Detailed Error Reports**: Specific failure information
- **JSON Output**: Machine-readable results for CI/CD

### Coverage Reporting
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Sample Test Output
```
📊 COMPREHENSIVE TEST RESULTS SUMMARY
========================================
📈 Overall Statistics:
   Total Test Categories: 19
   Successful Categories: 18
   Failed Categories: 1
   Total Tests Passed: 156
   Total Tests Failed: 3
   Total Errors: 0
   Total Duration: 45.2s
   Success Rate: 94.7%

🎯 Final Assessment:
   🟡 GOOD: Most test categories passed
   🔧 Minor issues detected, review failed categories
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```
Error: could not connect to server
```
**Solution**: Ensure PostgreSQL test database is running and accessible

#### 2. Authentication Failures
```
Error: 401 Unauthorized
```
**Solution**: Check token generation and validation in conftest.py

#### 3. Timeout Errors
```
Error: Test timeout after 300s
```
**Solution**: Check server responsiveness and database performance

#### 4. Fixture Errors
```
Error: fixture 'auth_headers' not found
```
**Solution**: Verify conftest.py is properly loaded and fixtures are defined

### Debug Mode
```bash
# Run tests with maximum verbosity
pytest -vvv --tb=long --capture=no

# Run single test with debugging
pytest tests/test_all_endpoints.py::TestAuthenticationEndpoints::test_login_with_username -vvv --tb=long
```

## 🔧 Customization

### Adding New Tests

1. **Add to existing test class**:
```python
def test_new_endpoint(self, client: TestClient, auth_headers: dict):
    """Test new endpoint functionality"""
    response = client.get("/api/new-endpoint/", headers=auth_headers)
    assert response.status_code == 200
```

2. **Create new test class**:
```python
class TestNewModuleEndpoints:
    """Test new module endpoints"""
    
    def test_list_items(self, client: TestClient, auth_headers: dict):
        # Test implementation
        pass
```

3. **Update test runner**: Add new category to `test_categories` list in `test_runner.py`

### Custom Fixtures
Add to `conftest.py`:
```python
@pytest.fixture
def custom_test_data():
    """Custom test data fixture"""
    return {
        "field1": "value1",
        "field2": "value2"
    }
```

## 📋 Best Practices

### Test Organization
- Group tests by functional area
- Use descriptive test names
- Include both positive and negative scenarios
- Test edge cases and error conditions

### Data Management
- Use fixtures for test data
- Clean up test data after tests
- Use separate test database
- Avoid hard-coded values

### Performance
- Keep tests fast and focused
- Use appropriate test isolation
- Mock external dependencies when needed
- Monitor test execution time

### Maintenance
- Update tests when APIs change
- Maintain test documentation
- Review test coverage regularly
- Refactor common test patterns

## ✅ Validation Checklist

Before deployment, ensure:

- [ ] All endpoint categories pass
- [ ] Error scenarios are properly handled
- [ ] Performance benchmarks are met
- [ ] Security tests pass (authentication/authorization)
- [ ] End-to-end workflows complete successfully
- [ ] Test coverage meets requirements (>70%)
- [ ] No timeout errors under normal load
- [ ] Database cleanup works properly

## 🎯 Conclusion

This comprehensive test suite provides:

- **100% API endpoint coverage**
- **Robust error scenario testing**
- **Performance validation**
- **End-to-end workflow verification**
- **Automated reporting and analysis**

The test suite ensures the FastAPI Rental Management System is production-ready with reliable, well-tested functionality across all business domains.