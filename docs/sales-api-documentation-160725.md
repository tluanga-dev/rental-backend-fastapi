# Sales API Documentation

**Document Version**: 1.0  
**Date**: 16-07-2025  
**API Base URL**: `http://localhost:8000/api`

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Sales Endpoints](#sales-endpoints)
   - [Create New Sale](#create-new-sale)
   - [List Sales](#list-sales)
   - [Get Sale Details](#get-sale-details)
   - [Get Sale by Number](#get-sale-by-number)
   - [Update Sale Status](#update-sale-status)
   - [Cancel Sale](#cancel-sale)
4. [Sales Reports](#sales-reports)
   - [Daily Sales Summary](#daily-sales-summary)
   - [Sales by Customer](#sales-by-customer)
   - [Sales by Item](#sales-by-item)
5. [Related Endpoints](#related-endpoints)
   - [Check Item Availability](#check-item-availability)
   - [Get Customer Sales History](#get-customer-sales-history)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## Overview

The Sales API provides comprehensive functionality for managing sales transactions in the rental management system. It handles sales creation, inventory updates, customer management, and reporting.

### Key Features
- Real-time inventory validation and updates
- Automatic tax calculations
- Discount management
- Transaction number generation
- Comprehensive audit trail
- Sales analytics and reporting

## Authentication

All endpoints require Bearer token authentication:

```http
Authorization: Bearer <access_token>
```

To obtain a token:
```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Sales Endpoints

### Create New Sale

Creates a new sale transaction with automatic inventory deduction and financial calculations.

**Endpoint**: `POST /transactions/new-sale`

**Headers**:
```http
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "transaction_date": "2024-07-16",
  "notes": "VIP customer - apply loyalty discount",
  "reference_number": "PO-2024-789",
  "items": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "quantity": 3,
      "unit_cost": 49.99,
      "tax_rate": 8.5,
      "discount_amount": 5.00,
      "notes": "Red color variant requested"
    },
    {
      "item_id": "7c5b8d24-8903-4673-b4fd-2e074f88cde6",
      "quantity": 1,
      "unit_cost": 199.99,
      "tax_rate": 8.5,
      "discount_amount": 20.00,
      "notes": "Extended warranty included"
    }
  ]
}
```

**Field Specifications**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `customer_id` | UUID | Yes | Must exist | Customer making the purchase |
| `transaction_date` | string | Yes | YYYY-MM-DD format | Date of sale |
| `notes` | string | No | Max 500 chars | Transaction-level notes |
| `reference_number` | string | No | Max 50 chars | External reference (PO number, etc.) |
| `items` | array | Yes | Min 1 item | List of items being sold |
| `items[].item_id` | UUID | Yes | Must exist, must be saleable | Item being sold |
| `items[].quantity` | integer | Yes | Min: 1, Max: 9999 | Quantity to sell |
| `items[].unit_cost` | decimal | Yes | Min: 0, Max: 99999999.99 | Selling price per unit |
| `items[].tax_rate` | decimal | No | 0-100, Default: 0 | Tax percentage |
| `items[].discount_amount` | decimal | No | Min: 0, Default: 0 | Total discount for this line |
| `items[].notes` | string | No | Max 200 chars | Line-item specific notes |

**Success Response** (201 Created):
```json
{
  "success": true,
  "message": "Sale transaction created successfully",
  "transaction_id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
  "transaction_number": "SAL-20240716-0042",
  "data": {
    "id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
    "transaction_number": "SAL-20240716-0042",
    "transaction_type": "SALE",
    "status": "COMPLETED",
    "payment_status": "PAID",
    "customer": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Acme Corporation",
      "code": "CUST-0042",
      "email": "purchasing@acme.com",
      "phone": "+1-555-0123"
    },
    "transaction_date": "2024-07-16",
    "financial_summary": {
      "subtotal": 349.96,
      "tax_amount": 29.75,
      "discount_amount": 25.00,
      "shipping_amount": 0.00,
      "total_amount": 354.71,
      "paid_amount": 354.71,
      "balance_due": 0.00
    },
    "notes": "VIP customer - apply loyalty discount",
    "reference_number": "PO-2024-789",
    "created_at": "2024-07-16T14:30:00Z",
    "created_by": "john.doe@company.com",
    "transaction_lines": [
      {
        "id": "1a2b3c4d-5678-4562-b3fc-9e8f7d6c5b4a",
        "line_number": 1,
        "line_type": "PRODUCT",
        "item": {
          "id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
          "sku": "WDG-RED-M",
          "name": "Premium Widget - Red",
          "brand": "WidgetCo"
        },
        "quantity": 3,
        "unit_price": 49.99,
        "financial": {
          "subtotal": 149.97,
          "tax_rate": 8.5,
          "tax_amount": 12.75,
          "discount_amount": 5.00,
          "line_total": 157.72
        },
        "notes": "Red color variant requested"
      },
      {
        "id": "2b3c4d5e-6789-4673-c4fd-af9g8e7d6c5b",
        "line_number": 2,
        "line_type": "PRODUCT",
        "item": {
          "id": "7c5b8d24-8903-4673-b4fd-2e074f88cde6",
          "sku": "GADGET-PRO-2024",
          "name": "Professional Gadget 2024",
          "brand": "TechPro"
        },
        "quantity": 1,
        "unit_price": 199.99,
        "financial": {
          "subtotal": 199.99,
          "tax_rate": 8.5,
          "tax_amount": 17.00,
          "discount_amount": 20.00,
          "line_total": 196.99
        },
        "notes": "Extended warranty included"
      }
    ],
    "inventory_updates": [
      {
        "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
        "item_name": "Premium Widget - Red",
        "quantity_before": 50,
        "quantity_sold": 3,
        "quantity_after": 47,
        "location": "Main Warehouse"
      },
      {
        "item_id": "7c5b8d24-8903-4673-b4fd-2e074f88cde6",
        "item_name": "Professional Gadget 2024",
        "quantity_before": 15,
        "quantity_sold": 1,
        "quantity_after": 14,
        "location": "Main Warehouse"
      }
    ]
  }
}
```

**Error Responses**:

*Customer Not Found (404)*:
```json
{
  "detail": "Customer with ID 3fa85f64-5717-4562-b3fc-2c963f66afa6 not found"
}
```

*Item Not Found (404)*:
```json
{
  "detail": "Item with ID 8b4a9c13-7892-4562-a3fc-1d963f77bcd5 not found"
}
```

*Insufficient Stock (400)*:
```json
{
  "detail": "Insufficient stock for item 'Premium Widget - Red'. Available: 2, Requested: 3"
}
```

*Item Not Saleable (400)*:
```json
{
  "detail": "Item 'Display Model X' is not available for sale"
}
```

*Validation Error (422)*:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "items", 0, "quantity"],
      "msg": "ensure this value is greater than or equal to 1",
      "input": 0,
      "ctx": {"limit_value": 1}
    }
  ]
}
```

---

### List Sales

Retrieves a paginated list of sales transactions with filtering options.

**Endpoint**: `GET /transactions/?transaction_type=SALE`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transaction_type` | string | - | Filter by type (use "SALE") |
| `skip` | integer | 0 | Records to skip for pagination |
| `limit` | integer | 100 | Max records to return (max: 1000) |
| `status` | string | - | PENDING, COMPLETED, CANCELLED |
| `payment_status` | string | - | PENDING, PARTIAL, PAID, REFUNDED |
| `customer_id` | UUID | - | Filter by specific customer |
| `date_from` | string | - | Start date (YYYY-MM-DD) |
| `date_to` | string | - | End date (YYYY-MM-DD) |
| `min_amount` | decimal | - | Minimum total amount |
| `max_amount` | decimal | - | Maximum total amount |
| `search` | string | - | Search in transaction number, notes, reference |
| `sort_by` | string | created_at | Field to sort by |
| `sort_order` | string | desc | asc or desc |

**Example Request**:
```http
GET /transactions/?transaction_type=SALE&date_from=2024-07-01&date_to=2024-07-16&limit=20
```

**Success Response** (200 OK):
```json
{
  "items": [
    {
      "id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
      "transaction_number": "SAL-20240716-0042",
      "transaction_type": "SALE",
      "status": "COMPLETED",
      "payment_status": "PAID",
      "customer": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Acme Corporation",
        "code": "CUST-0042"
      },
      "transaction_date": "2024-07-16",
      "total_amount": 354.71,
      "paid_amount": 354.71,
      "balance_due": 0.00,
      "item_count": 2,
      "notes": "VIP customer - apply loyalty discount",
      "reference_number": "PO-2024-789",
      "created_at": "2024-07-16T14:30:00Z",
      "created_by": "john.doe@company.com"
    },
    {
      "id": "8e4f6g74-5718-3562-a4fd-2e064f77bcd6",
      "transaction_number": "SAL-20240716-0041",
      "transaction_type": "SALE",
      "status": "COMPLETED",
      "payment_status": "PARTIAL",
      "customer": {
        "id": "4gb96g75-6828-5673-c5gf-3d074g88dce7",
        "name": "Smith Industries",
        "code": "CUST-0089"
      },
      "transaction_date": "2024-07-16",
      "total_amount": 1250.00,
      "paid_amount": 500.00,
      "balance_due": 750.00,
      "item_count": 5,
      "notes": "Net 30 payment terms",
      "reference_number": null,
      "created_at": "2024-07-16T10:15:00Z",
      "created_by": "jane.smith@company.com"
    }
  ],
  "total": 156,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

---

### Get Sale Details

Retrieves complete details of a specific sale transaction.

**Endpoint**: `GET /transactions/{transaction_id}`

**Path Parameters**:
- `transaction_id` (UUID): The sale transaction ID

**Example Request**:
```http
GET /transactions/9d5f7g85-6829-4673-b5ge-3f175g99dgf7
```

**Success Response** (200 OK):
```json
{
  "id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
  "transaction_number": "SAL-20240716-0042",
  "transaction_type": "SALE",
  "status": "COMPLETED",
  "payment_status": "PAID",
  "customer": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Acme Corporation",
    "code": "CUST-0042",
    "email": "purchasing@acme.com",
    "phone": "+1-555-0123",
    "address": "123 Business Ave, Metro City, MC 12345"
  },
  "location": {
    "id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
    "name": "Main Warehouse",
    "code": "WH-001"
  },
  "transaction_date": "2024-07-16",
  "due_date": null,
  "financial_summary": {
    "subtotal": 349.96,
    "tax_amount": 29.75,
    "discount_amount": 25.00,
    "shipping_amount": 0.00,
    "total_amount": 354.71,
    "paid_amount": 354.71,
    "balance_due": 0.00
  },
  "payment_info": {
    "method": "CREDIT_CARD",
    "reference": "****1234",
    "payment_date": "2024-07-16T14:30:00Z"
  },
  "notes": "VIP customer - apply loyalty discount",
  "reference_number": "PO-2024-789",
  "audit_trail": {
    "created_at": "2024-07-16T14:30:00Z",
    "created_by": "john.doe@company.com",
    "updated_at": "2024-07-16T14:30:00Z",
    "updated_by": "john.doe@company.com"
  },
  "transaction_lines": [
    {
      "id": "1a2b3c4d-5678-4562-b3fc-9e8f7d6c5b4a",
      "line_number": 1,
      "line_type": "PRODUCT",
      "item": {
        "id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
        "sku": "WDG-RED-M",
        "name": "Premium Widget - Red",
        "description": "High-quality widget in vibrant red color",
        "brand": "WidgetCo",
        "category": "Widgets"
      },
      "quantity": 3,
      "unit_price": 49.99,
      "unit_cost": 30.00,
      "financial": {
        "subtotal": 149.97,
        "tax_rate": 8.5,
        "tax_amount": 12.75,
        "discount_rate": 0.00,
        "discount_amount": 5.00,
        "line_total": 157.72
      },
      "profit_margin": {
        "cost": 90.00,
        "profit": 59.97,
        "margin_percent": 39.98
      },
      "notes": "Red color variant requested"
    }
  ]
}
```

**Error Response** (404):
```json
{
  "detail": "Transaction not found"
}
```

---

### Get Sale by Number

Retrieves a sale transaction by its unique transaction number.

**Endpoint**: `GET /transactions/number/{transaction_number}`

**Path Parameters**:
- `transaction_number` (string): The transaction number (e.g., SAL-20240716-0042)

**Example Request**:
```http
GET /transactions/number/SAL-20240716-0042
```

**Response**: Same structure as [Get Sale Details](#get-sale-details)

---

### Update Sale Status

Updates the status of a sale transaction (requires appropriate permissions).

**Endpoint**: `PATCH /transactions/{transaction_id}/status`

**Request Body**:
```json
{
  "status": "CANCELLED",
  "reason": "Customer requested cancellation",
  "notes": "Will reorder next month"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Transaction status updated successfully",
  "data": {
    "id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
    "transaction_number": "SAL-20240716-0042",
    "status": "CANCELLED",
    "previous_status": "COMPLETED",
    "updated_at": "2024-07-16T15:45:00Z",
    "updated_by": "admin@company.com"
  }
}
```

---

### Cancel Sale

Cancels a sale and reverses inventory changes.

**Endpoint**: `POST /transactions/{transaction_id}/cancel`

**Request Body**:
```json
{
  "reason": "CUSTOMER_REQUEST",
  "notes": "Customer found better price elsewhere",
  "restore_inventory": true
}
```

**Reason Options**:
- `CUSTOMER_REQUEST`
- `PAYMENT_FAILED`
- `OUT_OF_STOCK`
- `DUPLICATE_ORDER`
- `FRAUD_SUSPECTED`
- `OTHER`

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Sale cancelled successfully",
  "data": {
    "transaction_id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
    "transaction_number": "SAL-20240716-0042",
    "status": "CANCELLED",
    "cancellation_date": "2024-07-16T16:00:00Z",
    "cancelled_by": "admin@company.com",
    "inventory_restored": true,
    "refund_amount": 354.71
  }
}
```

---

## Sales Reports

### Daily Sales Summary

Get sales summary for a specific date or date range.

**Endpoint**: `GET /reports/sales/daily-summary`

**Query Parameters**:
- `date` (string): Specific date (YYYY-MM-DD)
- `date_from` (string): Start date for range
- `date_to` (string): End date for range

**Example Request**:
```http
GET /reports/sales/daily-summary?date=2024-07-16
```

**Success Response** (200 OK):
```json
{
  "date": "2024-07-16",
  "summary": {
    "total_sales": 42,
    "completed_sales": 38,
    "cancelled_sales": 4,
    "total_revenue": 15420.50,
    "total_tax": 1309.74,
    "total_discount": 520.00,
    "net_revenue": 14210.24,
    "average_sale_value": 367.15,
    "top_selling_items": [
      {
        "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
        "item_name": "Premium Widget - Red",
        "quantity_sold": 25,
        "revenue": 1249.75
      }
    ],
    "sales_by_hour": [
      {"hour": "09:00", "sales": 3, "revenue": 890.50},
      {"hour": "10:00", "sales": 5, "revenue": 1420.25},
      {"hour": "11:00", "sales": 8, "revenue": 2156.00}
    ],
    "payment_methods": [
      {"method": "CREDIT_CARD", "count": 25, "amount": 9250.30},
      {"method": "CASH", "count": 10, "amount": 3420.20},
      {"method": "DEBIT_CARD", "count": 7, "amount": 2750.00}
    ]
  }
}
```

---

### Sales by Customer

Get sales analytics grouped by customer.

**Endpoint**: `GET /reports/sales/by-customer`

**Query Parameters**:
- `date_from` (string): Start date
- `date_to` (string): End date
- `limit` (integer): Number of customers to return
- `sort_by` (string): revenue, transaction_count, average_value

**Success Response** (200 OK):
```json
{
  "period": {
    "from": "2024-07-01",
    "to": "2024-07-16"
  },
  "customers": [
    {
      "customer": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Acme Corporation",
        "code": "CUST-0042"
      },
      "metrics": {
        "total_transactions": 15,
        "total_revenue": 5420.50,
        "average_transaction": 361.37,
        "total_items": 45,
        "last_purchase_date": "2024-07-16"
      }
    }
  ],
  "summary": {
    "total_customers": 156,
    "active_customers": 89,
    "new_customers": 12
  }
}
```

---

### Sales by Item

Get sales performance by item.

**Endpoint**: `GET /reports/sales/by-item`

**Query Parameters**:
- `date_from` (string): Start date
- `date_to` (string): End date
- `category_id` (UUID): Filter by category
- `brand_id` (UUID): Filter by brand
- `limit` (integer): Number of items to return

**Success Response** (200 OK):
```json
{
  "period": {
    "from": "2024-07-01",
    "to": "2024-07-16"
  },
  "items": [
    {
      "item": {
        "id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
        "sku": "WDG-RED-M",
        "name": "Premium Widget - Red",
        "category": "Widgets",
        "brand": "WidgetCo"
      },
      "metrics": {
        "quantity_sold": 125,
        "revenue": 6248.75,
        "average_price": 49.99,
        "profit": 2374.25,
        "margin_percent": 38.00,
        "transaction_count": 42
      }
    }
  ]
}
```

---

## Related Endpoints

### Check Item Availability

Verify item stock before creating a sale.

**Endpoint**: `GET /inventory/items/{item_id}/availability`

**Success Response** (200 OK):
```json
{
  "item": {
    "id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
    "sku": "WDG-RED-M",
    "name": "Premium Widget - Red"
  },
  "availability": {
    "in_stock": true,
    "quantity_available": 47,
    "quantity_reserved": 5,
    "quantity_on_order": 50,
    "locations": [
      {
        "location_id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
        "location_name": "Main Warehouse",
        "quantity": 47
      }
    ]
  },
  "pricing": {
    "sale_price": 49.99,
    "min_price": 44.99,
    "suggested_price": 49.99
  }
}
```

---

### Get Customer Sales History

Retrieve a customer's purchase history.

**Endpoint**: `GET /customers/{customer_id}/sales`

**Query Parameters**:
- `skip` (integer): Pagination offset
- `limit` (integer): Records per page
- `date_from` (string): Filter start date
- `date_to` (string): Filter end date

**Success Response** (200 OK):
```json
{
  "customer": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Acme Corporation",
    "code": "CUST-0042"
  },
  "sales_summary": {
    "total_purchases": 45,
    "total_spent": 12560.75,
    "average_purchase": 279.13,
    "first_purchase": "2023-05-15",
    "last_purchase": "2024-07-16"
  },
  "recent_sales": [
    {
      "id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
      "transaction_number": "SAL-20240716-0042",
      "date": "2024-07-16",
      "total": 354.71,
      "status": "COMPLETED",
      "item_count": 2
    }
  ]
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Common Scenarios |
|------|---------|------------------|
| 200 | Success | Data retrieved successfully |
| 201 | Created | Sale created successfully |
| 400 | Bad Request | Business logic error (insufficient stock, invalid data) |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | User lacks required permissions |
| 404 | Not Found | Customer, item, or transaction not found |
| 422 | Unprocessable Entity | Validation error in request data |
| 500 | Internal Server Error | Unexpected server error |

### Error Response Format

**Standard Error**:
```json
{
  "detail": "Detailed error message"
}
```

**Validation Error** (422):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "field_name"],
      "msg": "Error description",
      "input": "provided_value",
      "ctx": {"additional": "context"}
    }
  ]
}
```

### Common Error Scenarios

1. **Insufficient Stock**:
```json
{
  "detail": "Insufficient stock for item 'Premium Widget'. Available: 5, Requested: 10",
  "error_code": "INSUFFICIENT_STOCK",
  "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
  "available_quantity": 5,
  "requested_quantity": 10
}
```

2. **Customer Credit Limit**:
```json
{
  "detail": "Customer has exceeded credit limit",
  "error_code": "CREDIT_LIMIT_EXCEEDED",
  "credit_limit": 5000.00,
  "current_balance": 4500.00,
  "transaction_amount": 750.00
}
```

3. **Item Not Saleable**:
```json
{
  "detail": "Item 'Display Unit' is marked as not for sale",
  "error_code": "ITEM_NOT_SALEABLE",
  "item_id": "7c5b8d24-8903-4673-b4fd-2e074f88cde6"
}
```

---

## Best Practices

### 1. Transaction Management
- Always validate stock availability before submitting a sale
- Use idempotency keys for network retry scenarios
- Implement optimistic UI updates with proper rollback

### 2. Error Handling
```javascript
try {
  const response = await createSale(saleData);
  if (response.success) {
    showSuccessMessage('Sale created successfully');
    navigateToSale(response.transaction_id);
  }
} catch (error) {
  if (error.status === 400 && error.data.error_code === 'INSUFFICIENT_STOCK') {
    showStockError(error.data);
  } else if (error.status === 422) {
    showValidationErrors(error.data.detail);
  } else {
    showGenericError('Unable to process sale. Please try again.');
  }
}
```

### 3. Pagination Implementation
```javascript
const fetchSales = async (page = 1, pageSize = 20) => {
  const skip = (page - 1) * pageSize;
  const response = await api.get(`/transactions/?transaction_type=SALE&skip=${skip}&limit=${pageSize}`);
  
  return {
    items: response.items,
    currentPage: page,
    totalPages: Math.ceil(response.total / pageSize),
    totalItems: response.total
  };
};
```

### 4. Real-time Inventory Check
```javascript
const checkAvailability = async (itemId, quantity) => {
  const availability = await api.get(`/inventory/items/${itemId}/availability`);
  return availability.quantity_available >= quantity;
};

// Use debouncing for quantity inputs
const debouncedCheck = debounce(checkAvailability, 500);
```

### 5. Date Handling
```javascript
// Always send dates in ISO format
const saleDate = new Date().toISOString().split('T')[0]; // "2024-07-16"

// Convert UTC to local for display
const displayDate = new Date(sale.created_at).toLocaleString();
```

### 6. Decimal Precision
```javascript
// Use string representation for decimals
const calculateTotal = (items) => {
  return items.reduce((total, item) => {
    const lineTotal = (
      parseFloat(item.quantity) * 
      parseFloat(item.unit_cost) * 
      (1 + parseFloat(item.tax_rate) / 100) - 
      parseFloat(item.discount_amount)
    ).toFixed(2);
    return (parseFloat(total) + parseFloat(lineTotal)).toFixed(2);
  }, "0.00");
};
```

### 7. Caching Strategy
```javascript
// Cache frequently used data
const customerCache = new Map();
const itemCache = new Map();

const getCachedCustomer = async (customerId) => {
  if (!customerCache.has(customerId)) {
    const customer = await api.get(`/customers/${customerId}`);
    customerCache.set(customerId, customer);
  }
  return customerCache.get(customerId);
};
```

### 8. Optimistic Updates
```javascript
const createSaleOptimistic = async (saleData) => {
  // Update UI immediately
  addSaleToList(saleData);
  updateInventoryDisplay(saleData.items);
  
  try {
    const response = await api.post('/transactions/new-sale', saleData);
    // Update with actual data
    updateSaleInList(response.data);
  } catch (error) {
    // Rollback on error
    removeSaleFromList(saleData);
    revertInventoryDisplay(saleData.items);
    throw error;
  }
};
```

### 9. Performance Optimization
- Implement virtual scrolling for large transaction lists
- Use pagination with reasonable page sizes (20-50 items)
- Batch API calls when checking multiple items
- Implement proper loading states
- Cache static data (customers, items, categories)

### 10. Security Considerations
- Never store sensitive payment information in local storage
- Validate all calculations on the backend
- Implement proper CSRF protection
- Use HTTPS in production
- Sanitize all user inputs before display

---

## Appendix

### Transaction Status Flow
```
DRAFT → PENDING → COMPLETED
         ↓           ↓
      CANCELLED  CANCELLED
```

### Payment Status Flow
```
PENDING → PARTIAL → PAID
    ↓        ↓        ↓
CANCELLED CANCELLED REFUNDED
```

### Date/Time Formats
- **Date**: `YYYY-MM-DD` (e.g., "2024-07-16")
- **DateTime**: `YYYY-MM-DDTHH:MM:SSZ` (e.g., "2024-07-16T14:30:00Z")
- All times are in UTC

### Currency and Decimal Handling
- All monetary values are in system default currency
- Decimals use up to 2 decimal places
- Use string representation to avoid floating-point issues

### Rate Limiting
- API calls are limited to 1000 requests per hour per user
- Batch operations count as single requests
- 429 status code returned when limit exceeded

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 16-07-2025 | Initial comprehensive sales API documentation |

---

**End of Document**