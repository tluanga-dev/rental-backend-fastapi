# Sale Transaction API Documentation

**Document Version**: 1.0  
**Date**: 16-07-2025  
**API Base URL**: `http://localhost:8000/api`

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Create New Sale](#create-new-sale)
4. [List Transactions](#list-transactions)
5. [Get Transaction Details](#get-transaction-details)
6. [Get Transaction by Number](#get-transaction-by-number)
7. [Get Transaction with Lines](#get-transaction-with-lines)
8. [Error Responses](#error-responses)
9. [Data Types and Constraints](#data-types-and-constraints)

---

## Overview

The Sale Transaction API provides endpoints for creating and managing sales transactions. This includes creating new sales, retrieving transaction lists, and accessing detailed transaction information.

## Authentication

All endpoints require authentication via Bearer token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

---

## Create New Sale

Creates a new sale transaction with automatic inventory updates.

### Endpoint
```http
POST /transactions/new-sale
```

### Request Headers
```http
Content-Type: application/json
Authorization: Bearer <access_token>
```

### Request Payload

```json
{
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "transaction_date": "2024-07-15",
  "notes": "Sale to John Doe - Summer promotion",
  "reference_number": "REF-2024-001",
  "items": [
    {
      "item_id": "660e8400-e29b-41d4-a716-446655440001",
      "quantity": 2,
      "unit_cost": 99.99,
      "tax_rate": 8.5,
      "discount_amount": 10.00,
      "notes": "Blue widget - customer requested gift wrap"
    },
    {
      "item_id": "770e8400-e29b-41d4-a716-446655440002",
      "quantity": 1,
      "unit_cost": 149.99,
      "tax_rate": 8.5,
      "discount_amount": 0.00,
      "notes": "Premium gadget"
    }
  ]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer_id` | string (UUID) | Yes | UUID of the customer making the purchase |
| `transaction_date` | string | Yes | Transaction date in YYYY-MM-DD format |
| `notes` | string | No | Additional notes about the sale (max 500 chars) |
| `reference_number` | string | No | External reference number (max 50 chars) |
| `items` | array | Yes | List of items being sold (min 1 item) |
| `items[].item_id` | string (UUID) | Yes | UUID of the item being sold |
| `items[].quantity` | integer | Yes | Quantity being sold (min: 1) |
| `items[].unit_cost` | decimal | Yes | Unit price for the item (min: 0) |
| `items[].tax_rate` | decimal | No | Tax rate percentage (0-100, default: 0) |
| `items[].discount_amount` | decimal | No | Discount amount per item (min: 0, default: 0) |
| `items[].notes` | string | No | Notes for this line item |

### Success Response

**Status Code**: 201 Created

```json
{
  "success": true,
  "message": "Sale transaction created successfully",
  "transaction_id": "880e8400-e29b-41d4-a716-446655440003",
  "transaction_number": "SAL-20240715-1234",
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "transaction_number": "SAL-20240715-1234",
    "transaction_type": "SALE",
    "status": "COMPLETED",
    "payment_status": "PAID",
    "customer_id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_name": "John Doe",
    "transaction_date": "2024-07-15",
    "subtotal": 349.97,
    "tax_amount": 29.75,
    "discount_amount": 10.00,
    "total_amount": 369.72,
    "paid_amount": 369.72,
    "notes": "Sale to John Doe - Summer promotion",
    "reference_number": "REF-2024-001",
    "created_at": "2024-07-15T10:30:00Z",
    "transaction_lines": [
      {
        "id": "990e8400-e29b-41d4-a716-446655440004",
        "line_number": 1,
        "item_id": "660e8400-e29b-41d4-a716-446655440001",
        "item_name": "Blue Widget",
        "quantity": 2,
        "unit_price": 99.99,
        "tax_rate": 8.5,
        "tax_amount": 17.00,
        "discount_amount": 10.00,
        "line_total": 206.98,
        "notes": "Blue widget - customer requested gift wrap"
      },
      {
        "id": "aa0e8400-e29b-41d4-a716-446655440005",
        "line_number": 2,
        "item_id": "770e8400-e29b-41d4-a716-446655440002",
        "item_name": "Premium Gadget",
        "quantity": 1,
        "unit_price": 149.99,
        "tax_rate": 8.5,
        "tax_amount": 12.75,
        "discount_amount": 0.00,
        "line_total": 162.74,
        "notes": "Premium gadget"
      }
    ]
  }
}
```

### Error Responses

**Customer Not Found** (404):
```json
{
  "detail": "Customer with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Item Not Found** (404):
```json
{
  "detail": "Item with ID 660e8400-e29b-41d4-a716-446655440001 not found"
}
```

**Insufficient Stock** (400):
```json
{
  "detail": "Insufficient stock for item Blue Widget. Available: 5, Requested: 10"
}
```

**Validation Error** (422):
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "customer_id"],
      "msg": "Field required",
      "input": {},
      "url": "https://errors.pydantic.dev/2.5/v/missing"
    }
  ]
}
```

---

## List Transactions

Retrieves a paginated list of transactions with optional filtering.

### Endpoint
```http
GET /transactions/
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip |
| `limit` | integer | No | 100 | Maximum records to return (max: 1000) |
| `transaction_type` | string | No | - | Filter by type: SALE, PURCHASE, RENTAL, RETURN |
| `status` | string | No | - | Filter by status: PENDING, COMPLETED, CANCELLED |
| `customer_id` | UUID | No | - | Filter by customer ID |
| `date_from` | string | No | - | Filter from date (YYYY-MM-DD) |
| `date_to` | string | No | - | Filter to date (YYYY-MM-DD) |
| `search` | string | No | - | Search in transaction number or notes |

### Example Request
```http
GET /transactions/?transaction_type=SALE&limit=10&skip=0
```

### Success Response

**Status Code**: 200 OK

```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "transaction_number": "SAL-20240715-1234",
    "transaction_type": "SALE",
    "status": "COMPLETED",
    "payment_status": "PAID",
    "customer_id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_name": "John Doe",
    "transaction_date": "2024-07-15",
    "total_amount": 369.72,
    "notes": "Sale to John Doe - Summer promotion",
    "created_at": "2024-07-15T10:30:00Z",
    "updated_at": "2024-07-15T10:30:00Z"
  },
  {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "transaction_number": "SAL-20240715-1235",
    "transaction_type": "SALE",
    "status": "COMPLETED",
    "payment_status": "PAID",
    "customer_id": "cc0e8400-e29b-41d4-a716-446655440007",
    "customer_name": "Jane Smith",
    "transaction_date": "2024-07-15",
    "total_amount": 250.00,
    "notes": "Regular customer purchase",
    "created_at": "2024-07-15T11:45:00Z",
    "updated_at": "2024-07-15T11:45:00Z"
  }
]
```

---

## Get Transaction Details

Retrieves detailed information about a specific transaction by ID.

### Endpoint
```http
GET /transactions/{transaction_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transaction_id` | UUID | Yes | Transaction ID |

### Example Request
```http
GET /transactions/880e8400-e29b-41d4-a716-446655440003
```

### Success Response

**Status Code**: 200 OK

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "transaction_number": "SAL-20240715-1234",
  "transaction_type": "SALE",
  "status": "COMPLETED",
  "payment_status": "PAID",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_name": "John Doe",
  "transaction_date": "2024-07-15",
  "subtotal": 349.97,
  "tax_amount": 29.75,
  "discount_amount": 10.00,
  "total_amount": 369.72,
  "paid_amount": 369.72,
  "balance_due": 0.00,
  "notes": "Sale to John Doe - Summer promotion",
  "reference_number": "REF-2024-001",
  "created_at": "2024-07-15T10:30:00Z",
  "updated_at": "2024-07-15T10:30:00Z",
  "created_by": "admin@example.com",
  "updated_by": "admin@example.com"
}
```

### Error Response

**Transaction Not Found** (404):
```json
{
  "detail": "Transaction not found"
}
```

---

## Get Transaction by Number

Retrieves a transaction by its unique transaction number.

### Endpoint
```http
GET /transactions/number/{transaction_number}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transaction_number` | string | Yes | Transaction number (e.g., SAL-20240715-1234) |

### Example Request
```http
GET /transactions/number/SAL-20240715-1234
```

### Success Response

Same as [Get Transaction Details](#get-transaction-details)

---

## Get Transaction with Lines

Retrieves a transaction along with all its line items.

### Endpoint
```http
GET /transactions/{transaction_id}/with-lines
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transaction_id` | UUID | Yes | Transaction ID |

### Example Request
```http
GET /transactions/880e8400-e29b-41d4-a716-446655440003/with-lines
```

### Success Response

**Status Code**: 200 OK

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "transaction_number": "SAL-20240715-1234",
  "transaction_type": "SALE",
  "status": "COMPLETED",
  "payment_status": "PAID",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_name": "John Doe",
  "transaction_date": "2024-07-15",
  "subtotal": 349.97,
  "tax_amount": 29.75,
  "discount_amount": 10.00,
  "total_amount": 369.72,
  "paid_amount": 369.72,
  "balance_due": 0.00,
  "notes": "Sale to John Doe - Summer promotion",
  "reference_number": "REF-2024-001",
  "created_at": "2024-07-15T10:30:00Z",
  "updated_at": "2024-07-15T10:30:00Z",
  "transaction_lines": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "transaction_id": "880e8400-e29b-41d4-a716-446655440003",
      "line_number": 1,
      "line_type": "PRODUCT",
      "item_id": "660e8400-e29b-41d4-a716-446655440001",
      "item_name": "Blue Widget",
      "item_sku": "BW-001",
      "quantity": 2,
      "unit_price": 99.99,
      "tax_rate": 8.5,
      "tax_amount": 17.00,
      "discount_rate": 0.00,
      "discount_amount": 10.00,
      "line_subtotal": 199.98,
      "line_total": 206.98,
      "description": "Blue Widget - Standard Size",
      "notes": "Blue widget - customer requested gift wrap",
      "created_at": "2024-07-15T10:30:00Z"
    },
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "transaction_id": "880e8400-e29b-41d4-a716-446655440003",
      "line_number": 2,
      "line_type": "PRODUCT",
      "item_id": "770e8400-e29b-41d4-a716-446655440002",
      "item_name": "Premium Gadget",
      "item_sku": "PG-001",
      "quantity": 1,
      "unit_price": 149.99,
      "tax_rate": 8.5,
      "tax_amount": 12.75,
      "discount_rate": 0.00,
      "discount_amount": 0.00,
      "line_subtotal": 149.99,
      "line_total": 162.74,
      "description": "Premium Gadget - Latest Model",
      "notes": "Premium gadget",
      "created_at": "2024-07-15T10:30:00Z"
    }
  ]
}
```

---

## Error Responses

### Common HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created successfully |
| 400 | Bad request (business logic error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 422 | Validation error |
| 500 | Internal server error |

### Standard Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error Response Format (422)

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "items", 0, "quantity"],
      "msg": "ensure this value is greater than or equal to 1",
      "input": 0,
      "ctx": {"limit_value": 1},
      "url": "https://errors.pydantic.dev/2.5/v/greater_than_equal"
    }
  ]
}
```

---

## Data Types and Constraints

### UUID Format
All IDs use UUID v4 format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`

Example: `550e8400-e29b-41d4-a716-446655440000`

### Date Format
All dates use ISO 8601 format: `YYYY-MM-DD`

Example: `2024-07-15`

### DateTime Format
All timestamps use ISO 8601 format with timezone: `YYYY-MM-DDTHH:MM:SSZ`

Example: `2024-07-15T10:30:00Z`

### Decimal Fields
- **unit_cost**: Up to 10 digits with 2 decimal places (e.g., 99999999.99)
- **tax_rate**: 0-100 with up to 2 decimal places (e.g., 8.50)
- **discount_amount**: Up to 10 digits with 2 decimal places
- **Amounts**: All monetary amounts are in the system's default currency

### String Length Constraints
- **notes**: Maximum 500 characters
- **reference_number**: Maximum 50 characters
- **item notes**: Maximum 200 characters

### Transaction Number Format
`{TYPE}-{YYYYMMDD}-{XXXX}`

Where:
- `{TYPE}`: Transaction type prefix (SAL for sales)
- `{YYYYMMDD}`: Date in YYYYMMDD format
- `{XXXX}`: Sequential 4-digit number for the day

Example: `SAL-20240715-1234`

---

## Additional Notes for Frontend Developers

### 1. Authentication Flow
- Obtain access token from `/api/auth/login` endpoint
- Include token in all requests
- Handle 401 responses by refreshing token or redirecting to login

### 2. Error Handling
- Always check for `detail` field in error responses
- For 422 errors, parse the `detail` array to show field-specific errors
- Implement retry logic for 5xx errors

### 3. Pagination
- Use `skip` and `limit` parameters for large lists
- Default limit is 100, maximum is 1000
- Calculate pages: `page = (skip / limit) + 1`

### 4. Date Handling
- Send dates in `YYYY-MM-DD` format
- Timezone handling: All dates are stored in UTC
- Convert to local timezone for display

### 5. Decimal Precision
- Use string representation for decimal values to avoid floating-point issues
- Round monetary values to 2 decimal places
- Calculate totals on frontend for immediate feedback

### 6. Inventory Impact
- Sales automatically reduce inventory levels
- Check stock availability before submitting sale
- Handle insufficient stock errors gracefully

### 7. Transaction States
- `COMPLETED`: Transaction is finalized
- `PENDING`: Transaction awaiting payment
- `CANCELLED`: Transaction was cancelled

### 8. Performance Tips
- Cache customer and item lists
- Use pagination for transaction lists
- Implement debouncing for search inputs
- Show loading states during API calls

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 16-07-2025 | Initial documentation for sale transaction endpoints |

---

**End of Document**