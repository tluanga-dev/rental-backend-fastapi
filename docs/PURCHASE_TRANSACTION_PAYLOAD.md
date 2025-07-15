# Purchase Transaction Payload Documentation

## Overview

This document provides comprehensive documentation for the purchase transaction payload structure, including expected data types, validation rules, and JSON examples for the `/api/transactions/new-purchase` endpoint.

## Table of Contents

1. [Request Structure](#request-structure)
2. [Field Definitions](#field-definitions)
3. [Validation Rules](#validation-rules)
4. [JSON Examples](#json-examples)
5. [Response Structure](#response-structure)
6. [Error Responses](#error-responses)

## Request Structure

### Endpoint
```
POST /api/transactions/new-purchase
```

### Content-Type
```
application/json
```

### Request Schema

```typescript
interface NewPurchaseRequest {
  supplier_id: string;           // UUID string (required)
  location_id: string;           // UUID string (required)
  purchase_date: string;         // Date string in YYYY-MM-DD format (required)
  notes?: string;                // Optional notes (max 1000 characters)
  reference_number?: string;     // Optional reference (max 50 characters)
  items: PurchaseItem[];         // Array of purchase items (required, min 1 item)
}

interface PurchaseItem {
  item_id: string;               // UUID string (required)
  quantity: number;              // Integer >= 1 (required)
  unit_cost: number;             // Decimal >= 0 (required)
  tax_rate?: number;             // Decimal 0-100 (optional, default: 0)
  discount_amount?: number;      // Decimal >= 0 (optional, default: 0)
  condition: string;             // Enum: "A", "B", "C", "D" (required)
  notes?: string;                // Optional notes (max 500 characters)
}
```

## Field Definitions

### Header Fields

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `supplier_id` | String (UUID) | Yes | Unique identifier for the supplier | Must be valid UUID format |
| `location_id` | String (UUID) | Yes | Unique identifier for the location | Must be valid UUID format |
| `purchase_date` | String (Date) | Yes | Date of the purchase | Must be in YYYY-MM-DD format |
| `notes` | String | No | Additional notes for the purchase | Max 1000 characters |
| `reference_number` | String | No | External reference number | Max 50 characters |
| `items` | Array | Yes | List of items being purchased | Min 1 item required |

### Item Fields

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `item_id` | String (UUID) | Yes | Unique identifier for the item | Must be valid UUID format |
| `quantity` | Integer | Yes | Number of items being purchased | Must be >= 1 |
| `unit_cost` | Decimal | Yes | Cost per unit of the item | Must be >= 0 |
| `tax_rate` | Decimal | No | Tax rate percentage | Must be 0-100 (default: 0) |
| `discount_amount` | Decimal | No | Discount amount for this item | Must be >= 0 (default: 0) |
| `condition` | String (Enum) | Yes | Condition of the item | Must be one of: "A", "B", "C", "D" |
| `notes` | String | No | Additional notes for this item | Max 500 characters |

### Condition Codes

| Code | Description |
|------|-------------|
| `A` | New/Excellent condition |
| `B` | Good condition |
| `C` | Fair condition |
| `D` | Poor condition |

## Validation Rules

### UUID Validation
- Must be in standard UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Case-insensitive
- Must reference existing entities in the database

### Date Validation
- Must be in ISO date format: `YYYY-MM-DD`
- Must be a valid calendar date
- Supports leap years (e.g., 2024-02-29)

### Numeric Validation
- `quantity`: Must be a positive integer (>= 1)
- `unit_cost`: Must be a non-negative decimal (>= 0)
- `tax_rate`: Must be between 0 and 100 (inclusive)
- `discount_amount`: Must be a non-negative decimal (>= 0)

### String Validation
- `notes`: Max 1000 characters for purchase notes, 500 for item notes
- `reference_number`: Max 50 characters
- `condition`: Must be exactly one of: "A", "B", "C", "D"

### Array Validation
- `items`: Must contain at least 1 item
- Maximum recommended: 1000 items per transaction

## JSON Examples

### 1. Minimal Purchase (Required Fields Only)

```json
{
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
}
```

### 2. Complete Purchase (All Fields)

```json
{
  "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
  "location_id": "456e7890-e89b-12d3-a456-426614174001",
  "purchase_date": "2024-01-15",
  "notes": "Q1 2024 inventory replenishment - urgent order",
  "reference_number": "PO-2024-Q1-001",
  "items": [
    {
      "item_id": "789e0123-e89b-12d3-a456-426614174002",
      "quantity": 50,
      "unit_cost": 25.50,
      "tax_rate": 8.5,
      "discount_amount": 50.00,
      "condition": "A",
      "notes": "Brand new items - priority stock"
    },
    {
      "item_id": "012e3456-e89b-12d3-a456-426614174003",
      "quantity": 30,
      "unit_cost": 15.75,
      "tax_rate": 8.5,
      "discount_amount": 0,
      "condition": "B",
      "notes": "Slightly used but good quality"
    }
  ]
}
```

### 3. Multi-Item Purchase with Different Conditions

```json
{
  "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
  "location_id": "456e7890-e89b-12d3-a456-426614174001",
  "purchase_date": "2024-01-15",
  "notes": "Mixed condition inventory purchase",
  "reference_number": "MIX-2024-001",
  "items": [
    {
      "item_id": "789e0123-e89b-12d3-a456-426614174002",
      "quantity": 100,
      "unit_cost": 50.00,
      "tax_rate": 10.0,
      "condition": "A",
      "notes": "New premium items"
    },
    {
      "item_id": "012e3456-e89b-12d3-a456-426614174003",
      "quantity": 75,
      "unit_cost": 40.00,
      "tax_rate": 10.0,
      "discount_amount": 100.00,
      "condition": "B",
      "notes": "Good condition with bulk discount"
    },
    {
      "item_id": "345e6789-e89b-12d3-a456-426614174004",
      "quantity": 50,
      "unit_cost": 30.00,
      "tax_rate": 8.5,
      "discount_amount": 200.00,
      "condition": "C",
      "notes": "Fair condition - clearance items"
    },
    {
      "item_id": "678e9012-e89b-12d3-a456-426614174005",
      "quantity": 25,
      "unit_cost": 20.00,
      "tax_rate": 5.0,
      "discount_amount": 150.00,
      "condition": "D",
      "notes": "Poor condition - for parts/repair"
    }
  ]
}
```

### 4. Large Batch Purchase

```json
{
  "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
  "location_id": "456e7890-e89b-12d3-a456-426614174001",
  "purchase_date": "2024-01-15",
  "notes": "Large batch purchase for new store opening",
  "reference_number": "BATCH-2024-STORE-001",
  "items": [
    {
      "item_id": "789e0123-e89b-12d3-a456-426614174002",
      "quantity": 500,
      "unit_cost": 12.99,
      "tax_rate": 8.5,
      "discount_amount": 500.00,
      "condition": "A",
      "notes": "Bulk order - new store inventory"
    },
    {
      "item_id": "012e3456-e89b-12d3-a456-426614174003",
      "quantity": 300,
      "unit_cost": 24.99,
      "tax_rate": 8.5,
      "discount_amount": 750.00,
      "condition": "A",
      "notes": "Premium items for display"
    },
    {
      "item_id": "345e6789-e89b-12d3-a456-426614174004",
      "quantity": 200,
      "unit_cost": 8.50,
      "tax_rate": 8.5,
      "discount_amount": 200.00,
      "condition": "B",
      "notes": "Budget items for rental stock"
    }
  ]
}
```

### 5. Edge Case Examples

#### Boundary Values
```json
{
  "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
  "location_id": "456e7890-e89b-12d3-a456-426614174001",
  "purchase_date": "2024-02-29",
  "notes": "Edge case testing - leap year date",
  "items": [
    {
      "item_id": "789e0123-e89b-12d3-a456-426614174002",
      "quantity": 1,
      "unit_cost": 0.01,
      "tax_rate": 0,
      "discount_amount": 0,
      "condition": "A",
      "notes": "Minimum values test"
    },
    {
      "item_id": "012e3456-e89b-12d3-a456-426614174003",
      "quantity": 9999,
      "unit_cost": 9999.99,
      "tax_rate": 100,
      "discount_amount": 999.99,
      "condition": "D",
      "notes": "Maximum values test"
    }
  ]
}
```

#### Special Characters
```json
{
  "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
  "location_id": "456e7890-e89b-12d3-a456-426614174001",
  "purchase_date": "2024-01-15",
  "notes": "Special characters test: émojis 🎉, unicode ñ, quotes \"double\" & 'single', <tags>",
  "reference_number": "SPECIAL-CHARS-001",
  "items": [
    {
      "item_id": "789e0123-e89b-12d3-a456-426614174002",
      "quantity": 10,
      "unit_cost": 25.50,
      "condition": "A",
      "notes": "Unicode test: café, résumé, naïve, @#$%^&*()[]{}|\\:;\"<>?,./"
    }
  ]
}
```

## Response Structure

### Success Response (201 Created)

```json
{
  "success": true,
  "message": "Purchase transaction created successfully",
  "transaction_id": "abc12345-e89b-12d3-a456-426614174004",
  "transaction_number": "PUR-20240115-7823",
  "data": {
    "id": "abc12345-e89b-12d3-a456-426614174004",
    "transaction_number": "PUR-20240115-7823",
    "transaction_type": "PURCHASE",
    "transaction_date": "2024-01-15T00:00:00Z",
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "location_id": "456e7890-e89b-12d3-a456-426614174001",
    "status": "COMPLETED",
    "payment_status": "PENDING",
    "subtotal": 2750.00,
    "discount_amount": 50.00,
    "tax_amount": 237.75,
    "total_amount": 2937.75,
    "paid_amount": 0.00,
    "notes": "Q1 2024 inventory replenishment",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "transaction_lines": [
      {
        "id": "def45678-e89b-12d3-a456-426614174005",
        "line_number": 1,
        "item_id": "789e0123-e89b-12d3-a456-426614174002",
        "description": "Purchase: 789e0123-e89b-12d3-a456-426614174002 (Condition: A)",
        "quantity": 100,
        "unit_price": 15.50,
        "tax_rate": 8.5,
        "tax_amount": 131.75,
        "discount_amount": 50.00,
        "line_total": 1631.75,
        "notes": "Brand new items",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### Response Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `success` | Boolean | Always `true` for successful requests |
| `message` | String | Success message |
| `transaction_id` | String (UUID) | Unique identifier for the created transaction |
| `transaction_number` | String | Human-readable transaction number (format: PUR-YYYYMMDD-XXXX) |
| `data` | Object | Complete transaction details |
| `data.id` | String (UUID) | Same as transaction_id |
| `data.transaction_number` | String | Same as transaction_number |
| `data.transaction_type` | String | Always "PURCHASE" |
| `data.transaction_date` | String (ISO DateTime) | Purchase date with time |
| `data.customer_id` | String (UUID) | Supplier ID (stored in customer_id field) |
| `data.location_id` | String (UUID) | Location ID |
| `data.status` | String | Transaction status (usually "COMPLETED") |
| `data.payment_status` | String | Payment status (usually "PENDING") |
| `data.subtotal` | Decimal | Subtotal before discounts and taxes |
| `data.discount_amount` | Decimal | Total discount amount |
| `data.tax_amount` | Decimal | Total tax amount |
| `data.total_amount` | Decimal | Final total amount |
| `data.paid_amount` | Decimal | Amount paid (usually 0 initially) |
| `data.notes` | String | Purchase notes |
| `data.transaction_lines` | Array | Array of line items |

### Transaction Line Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String (UUID) | Unique line item identifier |
| `line_number` | Integer | Sequential line number |
| `item_id` | String (UUID) | Item identifier |
| `description` | String | Line description with condition |
| `quantity` | Decimal | Quantity purchased |
| `unit_price` | Decimal | Unit cost |
| `tax_rate` | Decimal | Tax rate percentage |
| `tax_amount` | Decimal | Calculated tax amount |
| `discount_amount` | Decimal | Discount amount |
| `line_total` | Decimal | Total for this line |
| `notes` | String | Line item notes |

## Error Responses

### Validation Error (422 Unprocessable Entity)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "supplier_id"],
      "msg": "Field required",
      "input": {
        "location_id": "456e7890-e89b-12d3-a456-426614174001",
        "purchase_date": "2024-01-15",
        "items": [...]
      }
    },
    {
      "type": "string_pattern_mismatch",
      "loc": ["body", "items", 0, "condition"],
      "msg": "String should match pattern '^[A-D]$'",
      "input": "E"
    }
  ]
}
```

### Entity Not Found Error (404 Not Found)

```json
{
  "detail": "Supplier with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

### Common Validation Errors

#### Missing Required Fields
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "supplier_id"],
      "msg": "Field required"
    }
  ]
}
```

#### Invalid UUID Format
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "supplier_id"],
      "msg": "Invalid UUID format: not-a-uuid"
    }
  ]
}
```

#### Invalid Date Format
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "purchase_date"],
      "msg": "Invalid date format. Use YYYY-MM-DD format."
    }
  ]
}
```

#### Invalid Condition
```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "items", 0, "condition"],
      "msg": "Input should be 'A', 'B', 'C' or 'D'"
    }
  ]
}
```

#### Negative Values
```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["body", "items", 0, "quantity"],
      "msg": "Input should be greater than or equal to 1"
    }
  ]
}
```

#### Tax Rate Out of Range
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "items", 0, "tax_rate"],
      "msg": "Input should be less than or equal to 100"
    }
  ]
}
```

#### Empty Items Array
```json
{
  "detail": [
    {
      "type": "too_short",
      "loc": ["body", "items"],
      "msg": "List should have at least 1 item after validation"
    }
  ]
}
```

## Best Practices

### 1. Data Validation
- Always validate UUIDs on the client side before sending
- Ensure dates are in the correct format (YYYY-MM-DD)
- Validate numeric ranges before submission
- Check condition codes against allowed values

### 2. Error Handling
- Handle all possible HTTP status codes (422, 404, 500)
- Parse validation errors to provide user-friendly messages
- Implement retry logic for transient errors

### 3. Performance
- Batch multiple items in a single request when possible
- Avoid sending unnecessary optional fields if they're empty
- Keep notes concise but informative

### 4. Security
- Never expose internal system data in notes
- Sanitize all text inputs on the client side
- Use HTTPS for all API requests

### 5. Testing
- Test with various data combinations
- Test edge cases (minimum/maximum values)
- Test with special characters and Unicode
- Test large batch purchases

## Integration Examples

### JavaScript/TypeScript

```typescript
interface PurchaseRequest {
  supplier_id: string;
  location_id: string;
  purchase_date: string;
  notes?: string;
  reference_number?: string;
  items: PurchaseItem[];
}

interface PurchaseItem {
  item_id: string;
  quantity: number;
  unit_cost: number;
  tax_rate?: number;
  discount_amount?: number;
  condition: 'A' | 'B' | 'C' | 'D';
  notes?: string;
}

async function createPurchase(purchase: PurchaseRequest): Promise<any> {
  try {
    const response = await fetch('/api/transactions/new-purchase', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(purchase),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Purchase creation failed: ${error.detail}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Purchase creation error:', error);
    throw error;
  }
}
```

### Python

```python
import requests
import json
from typing import List, Optional
from datetime import date

class PurchaseItem:
    def __init__(self, item_id: str, quantity: int, unit_cost: float, 
                 condition: str, tax_rate: Optional[float] = None,
                 discount_amount: Optional[float] = None, 
                 notes: Optional[str] = None):
        self.item_id = item_id
        self.quantity = quantity
        self.unit_cost = unit_cost
        self.condition = condition
        self.tax_rate = tax_rate
        self.discount_amount = discount_amount
        self.notes = notes

def create_purchase(supplier_id: str, location_id: str, 
                   purchase_date: date, items: List[PurchaseItem],
                   notes: Optional[str] = None, 
                   reference_number: Optional[str] = None) -> dict:
    
    payload = {
        "supplier_id": supplier_id,
        "location_id": location_id,
        "purchase_date": purchase_date.strftime("%Y-%m-%d"),
        "items": [item.__dict__ for item in items]
    }
    
    if notes:
        payload["notes"] = notes
    if reference_number:
        payload["reference_number"] = reference_number
    
    response = requests.post(
        "http://localhost:8000/api/transactions/new-purchase",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Purchase creation failed: {response.text}")
```

This documentation provides a complete reference for integrating with the purchase transaction API, including all data types, validation rules, examples, and error handling scenarios.