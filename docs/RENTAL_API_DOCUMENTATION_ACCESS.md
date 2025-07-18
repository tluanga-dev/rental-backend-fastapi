# Rental Filtering API - Documentation Access Guide

## Overview
The rental filtering API endpoint is fully documented in the FastAPI automatic documentation. The endpoint documentation includes all parameters, response models, and example usage.

## Accessing API Documentation

### 1. Swagger UI (Interactive Documentation)
**URL**: http://localhost:8000/docs

Navigate to the Transactions section and look for:
- **GET /api/transactions/rentals** - Get Rental Transactions

Features:
- Interactive API testing
- Parameter descriptions
- Response examples
- Authentication testing with "Authorize" button

### 2. ReDoc (Alternative Documentation)
**URL**: http://localhost:8000/redoc

Navigate to:
- **Transactions** → **Get Rental Transactions**

Features:
- Clean, readable documentation
- Better for printing/PDF export
- Detailed schema information

### 3. OpenAPI JSON Schema
**URL**: http://localhost:8000/openapi.json

Direct access to the OpenAPI 3.0 specification for:
- API client generation
- Postman import
- Custom documentation tools

## Rental Endpoint Documentation Details

### Endpoint
```
GET /api/transactions/rentals
```

### Authentication
- **Type**: Bearer Token
- **Header**: `Authorization: Bearer <token>`
- **How to authenticate in Swagger UI**:
  1. Click the "Authorize" button
  2. Enter your bearer token
  3. Click "Authorize"

### Parameters (as shown in docs)
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| skip | integer | No | Number of items to skip (min: 0, default: 0) |
| limit | integer | No | Number of items to return (min: 1, max: 1000, default: 100) |
| customer_id | string (UUID) | No | Filter by customer ID |
| location_id | string (UUID) | No | Filter by location ID |
| status | string (enum) | No | Filter by transaction status |
| rental_status | string (enum) | No | Filter by rental status |
| date_from | string (date) | No | Filter by rental start date (from) |
| date_to | string (date) | No | Filter by rental end date (to) |
| overdue_only | boolean | No | Show only overdue rentals (default: false) |

### Response Model
- **Type**: Array of rental transaction objects
- **Content-Type**: application/json
- **Schema**: List[Dict[str, Any]]

Each rental transaction includes:
- Transaction details (id, number, dates, amounts)
- Rental-specific fields (rental dates, status, lifecycle)
- Customer and location references
- Financial information

### Status Enums

**Transaction Status Options**:
- DRAFT
- CONFIRMED
- IN_PROGRESS
- COMPLETED
- CANCELLED
- REFUNDED

**Rental Status Options**:
- ACTIVE
- LATE
- EXTENDED
- PARTIAL_RETURN
- LATE_PARTIAL_RETURN
- COMPLETED

## Testing the API in Swagger UI

1. **Open Swagger UI**: http://localhost:8000/docs
2. **Authenticate**: Click "Authorize" and enter your token
3. **Find the endpoint**: Expand "Transactions" section
4. **Click on** `GET /api/transactions/rentals`
5. **Try it out**: Click the "Try it out" button
6. **Set parameters**: Fill in any filters you want to test
7. **Execute**: Click "Execute" to send the request
8. **View results**: See the response code, headers, and body

## Example cURL from Swagger UI
After testing in Swagger UI, you can copy the generated cURL command for use in scripts or documentation.

## API Client Generation
Using the OpenAPI spec, you can generate API clients in various languages:

```bash
# Example using openapi-generator
openapi-generator generate -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./generated/api-client
```

## Notes
- The documentation is automatically generated from the FastAPI route definitions
- Any changes to the endpoint will be reflected immediately in the docs
- The documentation includes validation rules (min/max values, required fields, etc.)
- Response examples are based on the actual response models defined in the code