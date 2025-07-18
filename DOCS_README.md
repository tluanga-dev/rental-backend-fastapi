# Rental Management System API Documentation

## 🚀 Quick Start

### Start the System
```bash
# Start all services (PostgreSQL, Redis, FastAPI)
./start_with_docs.sh

# OR manually with Docker Compose
docker-compose --profile dev up -d
```

### Access Documentation
Once the system is running, access the API documentation at:

- **Swagger UI** (Interactive): http://localhost:8000/docs
- **ReDoc** (Clean): http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Check Status
```bash
# Check if services are running
./docs_info.sh

# Check health
curl http://localhost:8000/health
```

## 📋 Purchase Transaction API

### Overview
The Purchase Transaction API allows you to create purchase transactions with automatic stock level updates and comprehensive validation.

### Endpoint
```
POST /api/transactions/new-purchase
```

### Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

### Request Format
```json
{
  "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
  "location_id": "456e7890-e89b-12d3-a456-426614174001",
  "purchase_date": "2024-01-15",
  "notes": "Optional purchase notes",
  "reference_number": "PO-2024-001",
  "items": [
    {
      "item_id": "789e0123-e89b-12d3-a456-426614174002",
      "quantity": 10,
      "unit_cost": 25.50,
      "tax_rate": 8.5,
      "discount_amount": 5.00,
      "condition": "A",
      "notes": "Item-specific notes"
    }
  ]
}
```

### Field Validation

#### Required Fields
- `supplier_id`: Valid UUID of existing supplier
- `location_id`: Valid UUID of existing location
- `purchase_date`: Date in YYYY-MM-DD format
- `items`: Array with at least 1 item

#### Item Validation
- `item_id`: Valid UUID of existing item
- `quantity`: Integer ≥ 1
- `unit_cost`: Decimal ≥ 0
- `condition`: Must be "A", "B", "C", or "D"
- `tax_rate`: Decimal 0-100 (optional)
- `discount_amount`: Decimal ≥ 0 (optional)

#### Condition Codes
- **A**: New/Excellent condition
- **B**: Good condition
- **C**: Fair condition
- **D**: Poor condition

### Response Format
```json
{
  "success": true,
  "message": "Purchase transaction created successfully",
  "transaction_id": "abc12345-e89b-12d3-a456-426614174004",
  "transaction_number": "PUR-20240115-0001",
  "data": {
    "id": "abc12345-e89b-12d3-a456-426614174004",
    "transaction_number": "PUR-20240115-0001",
    "transaction_type": "PURCHASE",
    "status": "COMPLETED",
    "payment_status": "PENDING",
    "subtotal": 255.00,
    "discount_amount": 5.00,
    "tax_amount": 21.25,
    "total_amount": 271.25,
    "transaction_lines": [
      {
        "id": "def45678-e89b-12d3-a456-426614174005",
        "line_number": 1,
        "item_id": "789e0123-e89b-12d3-a456-426614174002",
        "description": "Purchase: 789e0123-e89b-12d3-a456-426614174002 (Condition: A)",
        "quantity": 10,
        "unit_price": 25.50,
        "tax_rate": 8.5,
        "tax_amount": 21.25,
        "discount_amount": 5.00,
        "line_total": 271.25
      }
    ]
  }
}
```

## 🔧 Example Usage

### 1. Get Authentication Token
```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123",
    "full_name": "Test User"
  }'

# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "testuser",
    "password": "TestPass123"
  }'
```

### 2. Create Purchase Transaction
```bash
# Using the example request file
curl -X POST http://localhost:8000/api/transactions/new-purchase \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d @example_purchase_request.json

# Or inline JSON
curl -X POST http://localhost:8000/api/transactions/new-purchase \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
    "location_id": "456e7890-e89b-12d3-a456-426614174001",
    "purchase_date": "2024-01-15",
    "items": [
      {
        "item_id": "789e0123-e89b-12d3-a456-426614174002",
        "quantity": 10,
        "unit_cost": 25.50,
        "condition": "A"
      }
    ]
  }'
```

## 🎯 Key Features

### ✅ Complete Validation
- UUID format validation for all ID fields
- Date format validation (YYYY-MM-DD)
- Numeric range validation (quantities, rates, amounts)
- String length validation (notes, reference numbers)
- Condition code validation (A, B, C, D)

### ✅ Automatic Stock Updates
- Creates new stock levels for items not in inventory
- Updates existing stock levels by adding purchased quantities
- Maintains stock availability calculations
- Handles multiple locations and items

### ✅ Financial Calculations
- Accurate subtotal, discount, tax, and total calculations
- Line-level and transaction-level totals
- Proper decimal precision handling
- Support for different tax rates per item

### ✅ Transaction Management
- Unique transaction number generation (PUR-YYYYMMDD-XXXX)
- Complete audit trail with timestamps
- Transaction status tracking
- Payment status management

### ✅ Error Handling
- Comprehensive validation error messages
- Entity not found errors (supplier, location, item)
- Conflict detection (duplicate transaction numbers)
- Database transaction rollback on errors

## 🐛 Common Issues

### Authentication Errors
- **401 Unauthorized**: Include valid JWT token in Authorization header
- **403 Forbidden**: Check user permissions and token validity

### Validation Errors
- **422 Unprocessable Entity**: Check request format and field validation
- **400 Bad Request**: Verify JSON structure and required fields

### Entity Not Found
- **404 Not Found**: Ensure supplier, location, and item IDs exist in the system

### Database Errors
- **500 Internal Server Error**: Check database connection and logs

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Service Status
```bash
docker-compose ps
```

### Application Logs
```bash
docker-compose logs -f app
```

### Database Logs
```bash
docker-compose logs -f db
```

## 🛠️ Development

### Stop Services
```bash
docker-compose down
```

### Restart Application
```bash
docker-compose restart app
```

### View Database
```bash
docker-compose exec db psql -U fastapi_user -d fastapi_db
```

### Run Tests
```bash
docker-compose exec app pytest
```

## 📚 Additional Resources

- [Purchase Transaction Payload Documentation](docs/PURCHASE_TRANSACTION_PAYLOAD.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [ReDoc Documentation](https://redocly.com/redoc/)

---

**🎉 Your purchase transaction API is ready to use!**

Access the interactive documentation at http://localhost:8000/docs to explore all available endpoints and test the API directly from your browser.