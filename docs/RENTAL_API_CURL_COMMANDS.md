# Rental API cURL Commands Documentation

This document provides working cURL commands for testing the Rental API endpoints.

## Authentication

### Login and Get Token
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@admin.com",
    "password": "Admin@123"
  }'
```

Store the `access_token` from the response:
```bash
TOKEN="your_access_token_here"
```

## Rental Transaction Endpoints

### 1. Get Available Rental Items
```bash
curl -X GET "http://localhost:8000/api/transactions/rentable-items?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Get Customers
```bash
curl -X GET "http://localhost:8000/api/customers/?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Create Rental Transaction
```bash
curl -X POST "http://localhost:8000/api/transactions/new-rental" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_date": "2025-07-18",
    "customer_id": "95d9e0d5-3086-4bfb-bbb2-736cafed6d43",
    "location_id": "245bea95-c842-4066-9997-49e08abb0be0",
    "payment_method": "CASH",
    "payment_reference": "REF-2025-TEST-001",
    "notes": "Test rental transaction via curl",
    "deposit_amount": 500.00,
    "delivery_required": false,
    "pickup_required": false,
    "items": [
      {
        "item_id": "3d69497d-1d48-45cd-8cfe-11abcd21e6c7",
        "quantity": 1,
        "rental_period_value": 7,
        "tax_rate": 10.0,
        "discount_amount": 0.00,
        "rental_start_date": "2025-07-18",
        "rental_end_date": "2025-07-25",
        "notes": "JCB Land Mover rental for test"
      }
    ]
  }'
```

**Note**: The rental creation endpoint currently has performance issues and may timeout due to inventory stock management processing. This is a known issue that needs optimization.

## Rental Retrieval and Filtering

### 4. Get All Rentals (Basic)
```bash
curl -X GET "http://localhost:8000/api/transactions/rentals" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Get Rentals with Pagination
```bash
curl -X GET "http://localhost:8000/api/transactions/rentals?limit=10&skip=0" \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Filter Rentals by Customer
```bash
curl -X GET "http://localhost:8000/api/transactions/rentals?customer_id=95d9e0d5-3086-4bfb-bbb2-736cafed6d43" \
  -H "Authorization: Bearer $TOKEN"
```

### 7. Filter Rentals by Location
```bash
curl -X GET "http://localhost:8000/api/transactions/rentals?location_id=245bea95-c842-4066-9997-49e08abb0be0" \
  -H "Authorization: Bearer $TOKEN"
```

### 8. Filter Rentals by Transaction Status
```bash
# Valid statuses: PENDING, PROCESSING, COMPLETED, CANCELLED, ON_HOLD, IN_PROGRESS
curl -X GET "http://localhost:8000/api/transactions/rentals?status=PENDING" \
  -H "Authorization: Bearer $TOKEN"
```

### 9. Filter Rentals by Rental Status
```bash
# Valid rental statuses: ACTIVE, LATE, EXTENDED, PARTIAL_RETURN, LATE_PARTIAL_RETURN, COMPLETED
curl -X GET "http://localhost:8000/api/transactions/rentals?rental_status=ACTIVE" \
  -H "Authorization: Bearer $TOKEN"
```

### 10. Get Specific Rental by Transaction ID
```bash
curl -X GET "http://localhost:8000/api/transactions/{transaction_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### 11. Get Specific Rental by Transaction Number
```bash
curl -X GET "http://localhost:8000/api/transactions/number/{transaction_number}" \
  -H "Authorization: Bearer $TOKEN"
```

## Error Handling Examples

### Invalid UUID Format
```bash
curl -X GET "http://localhost:8000/api/transactions/rentals?customer_id=invalid-id" \
  -H "Authorization: Bearer $TOKEN"
```

### Invalid Status Value
```bash
curl -X GET "http://localhost:8000/api/transactions/rentals?status=INVALID_STATUS" \
  -H "Authorization: Bearer $TOKEN"
```

### Invalid Rental Status Value
```bash
curl -X GET "http://localhost:8000/api/transactions/rentals?rental_status=INVALID_STATUS" \
  -H "Authorization: Bearer $TOKEN"
```

## Test Results Summary

### ✅ Working Endpoints:
- Authentication (`/api/auth/login`)
- Rental items lookup (`/api/transactions/rentable-items`)
- Customer lookup (`/api/customers/`)
- Rental retrieval (`/api/transactions/rentals`)
- All filtering options (customer, location, status, rental_status)
- Pagination (limit, skip)
- Error handling and validation

### ⚠️ Performance Issues:
- Rental creation (`/api/transactions/new-rental`) - Times out due to inventory stock management processing

### 🔧 Required Data:
- `customer_id`: Valid UUID of existing customer
- `location_id`: Valid UUID of existing location (available from rentable items)
- `item_id`: Valid UUID of rentable item

### 📋 Valid Enum Values:
- **Transaction Status**: PENDING, PROCESSING, COMPLETED, CANCELLED, ON_HOLD, IN_PROGRESS
- **Rental Status**: ACTIVE, LATE, EXTENDED, PARTIAL_RETURN, LATE_PARTIAL_RETURN, COMPLETED
- **Payment Method**: CASH, CREDIT_CARD, DEBIT_CARD, BANK_TRANSFER, CHEQUE, ONLINE, CREDIT_ACCOUNT

### 🛠️ Recommendations:
1. Fix inventory stock management performance issues in rental creation
2. Consider implementing async processing for rental creation
3. Add proper timeout handling for long-running operations
4. Optimize database queries in the rental creation service