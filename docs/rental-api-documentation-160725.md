# Rental API Documentation

**Document Version**: 1.0  
**Date**: 16-07-2025  
**API Base URL**: `http://localhost:8000/api`

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rental Management](#rental-management)
   - [Create New Rental](#create-new-rental)
   - [List Rentals](#list-rentals)
   - [Get Rental Details](#get-rental-details)
   - [Get Rental by Number](#get-rental-by-number)
   - [Update Rental Status](#update-rental-status)
   - [Extend Rental Period](#extend-rental-period)
   - [Calculate Rental Charges](#calculate-rental-charges)
4. [Rental Returns](#rental-returns)
   - [Create Rental Return](#create-rental-return)
   - [List Returns](#list-returns)
   - [Get Return Details](#get-return-details)
   - [Process Damage Assessment](#process-damage-assessment)
5. [Rental Availability](#rental-availability)
   - [Check Item Availability](#check-item-availability)
   - [Get Available Items](#get-available-items)
   - [Reserve Items](#reserve-items)
   - [Cancel Reservation](#cancel-reservation)
6. [Customer Rentals](#customer-rentals)
   - [Get Customer Active Rentals](#get-customer-active-rentals)
   - [Get Customer Rental History](#get-customer-rental-history)
   - [Get Customer Overdue Rentals](#get-customer-overdue-rentals)
7. [Rental Reports](#rental-reports)
   - [Rental Revenue Report](#rental-revenue-report)
   - [Item Utilization Report](#item-utilization-report)
   - [Overdue Rentals Report](#overdue-rentals-report)
8. [Rental Agreements](#rental-agreements)
   - [Generate Rental Agreement](#generate-rental-agreement)
   - [Get Agreement Template](#get-agreement-template)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

---

## Overview

The Rental API provides comprehensive functionality for managing equipment and item rentals. It handles the complete rental lifecycle from reservation to return, including availability checking, pricing calculations, damage assessments, and reporting.

### Key Features
- Real-time availability checking
- Flexible rental period management
- Automated pricing calculations
- Late fee and damage charge handling
- Multi-location support
- Rental agreement generation
- Comprehensive reporting
- Customer rental history tracking

### Rental Workflow
```
RESERVATION → CONFIRMED → PICKED_UP → ACTIVE → RETURNED → COMPLETED
     ↓            ↓           ↓         ↓         ↓
  CANCELLED   CANCELLED   CANCELLED  OVERDUE  DISPUTED
```

---

## Authentication

All endpoints require Bearer token authentication:

```http
Authorization: Bearer <access_token>
```

---

## Rental Management

### Create New Rental

Creates a new rental transaction with automatic inventory allocation.

**Endpoint**: `POST /transactions/new-rental`

**Request Headers**:
```http
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "transaction_date": "2024-07-16",
  "location_id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
  "notes": "Corporate event rental - handle with care",
  "reference_number": "EVENT-2024-789",
  "deposit_amount": 500.00,
  "delivery_required": true,
  "delivery_address": "123 Event Plaza, Metro City, MC 12345",
  "delivery_date": "2024-07-18",
  "delivery_time": "09:00",
  "pickup_required": true,
  "pickup_date": "2024-07-22",
  "pickup_time": "17:00",
  "items": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "quantity": 10,
      "rental_period_type": "DAILY",
      "rental_period_value": 4,
      "rental_start_date": "2024-07-18",
      "rental_end_date": "2024-07-22",
      "unit_rate": 25.00,
      "discount_type": "PERCENTAGE",
      "discount_value": 10.0,
      "notes": "Premium speakers for main stage",
      "accessories": [
        {
          "item_id": "9c5a8d14-8903-5673-b4fd-2e074f88cde7",
          "quantity": 10,
          "description": "Speaker stands"
        }
      ]
    },
    {
      "item_id": "7c5b8d24-8903-4673-b4fd-2e074f88cde6",
      "quantity": 2,
      "rental_period_type": "DAILY",
      "rental_period_value": 4,
      "rental_start_date": "2024-07-18",
      "rental_end_date": "2024-07-22",
      "unit_rate": 150.00,
      "discount_type": "FIXED",
      "discount_value": 50.00,
      "notes": "Mixing console for sound control"
    }
  ],
  "payment_method": "CREDIT_CARD",
  "payment_reference": "AUTH-123456"
}
```

**Field Specifications**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `customer_id` | UUID | Yes | Must exist | Customer renting the items |
| `transaction_date` | string | Yes | YYYY-MM-DD | Date of rental creation |
| `location_id` | UUID | Yes | Must exist | Pickup location |
| `notes` | string | No | Max 500 chars | General rental notes |
| `reference_number` | string | No | Max 50 chars | External reference |
| `deposit_amount` | decimal | No | Min: 0 | Security deposit |
| `delivery_required` | boolean | No | Default: false | Delivery needed |
| `delivery_address` | string | If delivery | Max 500 chars | Delivery location |
| `delivery_date` | string | If delivery | YYYY-MM-DD | Delivery date |
| `delivery_time` | string | If delivery | HH:MM | Delivery time |
| `pickup_required` | boolean | No | Default: false | Pickup service needed |
| `pickup_date` | string | If pickup | YYYY-MM-DD | Pickup date |
| `pickup_time` | string | If pickup | HH:MM | Pickup time |
| `items` | array | Yes | Min 1 item | Items to rent |
| `payment_method` | string | Yes | See values | Payment method |
| `payment_reference` | string | No | Max 100 chars | Payment reference |

**Item Fields**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `item_id` | UUID | Yes | Must be rentable | Item to rent |
| `quantity` | integer | Yes | Min: 1 | Quantity to rent |
| `rental_period_type` | string | Yes | HOURLY, DAILY, WEEKLY, MONTHLY | Period type |
| `rental_period_value` | integer | Yes | Min: 1 | Number of periods |
| `rental_start_date` | string | Yes | YYYY-MM-DD | Rental start date |
| `rental_end_date` | string | Yes | YYYY-MM-DD | Rental end date |
| `unit_rate` | decimal | Yes | Min: 0 | Rate per unit per period |
| `discount_type` | string | No | PERCENTAGE, FIXED | Discount type |
| `discount_value` | decimal | No | Min: 0 | Discount value |
| `notes` | string | No | Max 200 chars | Item-specific notes |
| `accessories` | array | No | - | Included accessories |

**Success Response** (201 Created):
```json
{
  "success": true,
  "message": "Rental transaction created successfully",
  "transaction_id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
  "transaction_number": "RNT-20240716-0089",
  "data": {
    "id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
    "transaction_number": "RNT-20240716-0089",
    "transaction_type": "RENTAL",
    "status": "CONFIRMED",
    "rental_status": "RESERVED",
    "customer": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Acme Events Inc.",
      "code": "CUST-0042",
      "email": "events@acme.com",
      "phone": "+1-555-0123"
    },
    "location": {
      "id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
      "name": "Main Warehouse",
      "code": "WH-001"
    },
    "transaction_date": "2024-07-16",
    "rental_period": {
      "start_date": "2024-07-18",
      "end_date": "2024-07-22",
      "total_days": 4,
      "business_days": 3
    },
    "financial_summary": {
      "subtotal": 2200.00,
      "discount_amount": 250.00,
      "tax_amount": 165.75,
      "delivery_charge": 150.00,
      "pickup_charge": 150.00,
      "deposit_amount": 500.00,
      "total_amount": 2415.75,
      "paid_amount": 500.00,
      "balance_due": 1915.75
    },
    "delivery_info": {
      "delivery_required": true,
      "delivery_address": "123 Event Plaza, Metro City, MC 12345",
      "delivery_date": "2024-07-18",
      "delivery_time": "09:00",
      "delivery_status": "SCHEDULED",
      "pickup_required": true,
      "pickup_date": "2024-07-22",
      "pickup_time": "17:00",
      "pickup_status": "SCHEDULED"
    },
    "notes": "Corporate event rental - handle with care",
    "reference_number": "EVENT-2024-789",
    "created_at": "2024-07-16T10:30:00Z",
    "created_by": "john.doe@company.com",
    "rental_items": [
      {
        "id": "1a2b3c4d-5678-4562-b3fc-9e8f7d6c5b4a",
        "line_number": 1,
        "item": {
          "id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
          "sku": "SPK-PRO-15",
          "name": "Professional Speaker 15\"",
          "category": "Audio Equipment"
        },
        "quantity": 10,
        "rental_rate": {
          "period_type": "DAILY",
          "period_value": 4,
          "unit_rate": 25.00,
          "total_periods": 4,
          "line_subtotal": 1000.00
        },
        "discount": {
          "type": "PERCENTAGE",
          "value": 10.0,
          "amount": 100.00
        },
        "line_total": 900.00,
        "notes": "Premium speakers for main stage",
        "accessories": [
          {
            "item_id": "9c5a8d14-8903-5673-b4fd-2e074f88cde7",
            "name": "Speaker stands",
            "quantity": 10
          }
        ],
        "reserved_units": [
          "UNIT-SPK-001", "UNIT-SPK-002", "UNIT-SPK-003",
          "UNIT-SPK-004", "UNIT-SPK-005", "UNIT-SPK-006",
          "UNIT-SPK-007", "UNIT-SPK-008", "UNIT-SPK-009",
          "UNIT-SPK-010"
        ]
      },
      {
        "id": "2b3c4d5e-6789-4673-c4fd-af9g8e7d6c5b",
        "line_number": 2,
        "item": {
          "id": "7c5b8d24-8903-4673-b4fd-2e074f88cde6",
          "sku": "MIX-CONSOLE-32",
          "name": "32-Channel Mixing Console",
          "category": "Audio Equipment"
        },
        "quantity": 2,
        "rental_rate": {
          "period_type": "DAILY",
          "period_value": 4,
          "unit_rate": 150.00,
          "total_periods": 4,
          "line_subtotal": 1200.00
        },
        "discount": {
          "type": "FIXED",
          "value": 50.00,
          "amount": 50.00
        },
        "line_total": 1150.00,
        "notes": "Mixing console for sound control",
        "reserved_units": ["UNIT-MIX-001", "UNIT-MIX-002"]
      }
    ],
    "rental_agreement": {
      "agreement_number": "AGR-20240716-0089",
      "template_id": "standard_rental_v2",
      "signed": false,
      "signature_required": true,
      "agreement_url": "/api/rentals/agreements/AGR-20240716-0089"
    }
  }
}
```

**Error Responses**:

*Item Not Available (400)*:
```json
{
  "detail": "Item 'Professional Speaker 15\"' has insufficient availability. Requested: 10, Available: 7",
  "error_code": "INSUFFICIENT_AVAILABILITY",
  "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
  "requested_quantity": 10,
  "available_quantity": 7,
  "suggestions": [
    {
      "location_id": "6d7e8f90-0123-4567-c8d9-0e1f2g3h4i5j",
      "location_name": "Secondary Warehouse",
      "available_quantity": 5
    }
  ]
}
```

*Date Conflict (400)*:
```json
{
  "detail": "Rental end date must be after start date",
  "error_code": "INVALID_RENTAL_PERIOD",
  "start_date": "2024-07-22",
  "end_date": "2024-07-18"
}
```

---

### List Rentals

Retrieves a paginated list of rental transactions with filtering options.

**Endpoint**: `GET /transactions/?transaction_type=RENTAL`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transaction_type` | string | - | Use "RENTAL" for rentals |
| `skip` | integer | 0 | Pagination offset |
| `limit` | integer | 100 | Max records (max: 1000) |
| `rental_status` | string | - | RESERVED, PICKED_UP, ACTIVE, OVERDUE, RETURNED |
| `customer_id` | UUID | - | Filter by customer |
| `location_id` | UUID | - | Filter by location |
| `start_date_from` | string | - | Rental start date from |
| `start_date_to` | string | - | Rental start date to |
| `end_date_from` | string | - | Rental end date from |
| `end_date_to` | string | - | Rental end date to |
| `overdue_only` | boolean | false | Show only overdue rentals |
| `active_only` | boolean | false | Show only active rentals |
| `search` | string | - | Search in transaction number, customer, notes |
| `sort_by` | string | created_at | Field to sort by |
| `sort_order` | string | desc | asc or desc |

**Example Request**:
```http
GET /transactions/?transaction_type=RENTAL&rental_status=ACTIVE&active_only=true&limit=20
```

**Success Response** (200 OK):
```json
{
  "items": [
    {
      "id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
      "transaction_number": "RNT-20240716-0089",
      "transaction_type": "RENTAL",
      "status": "ACTIVE",
      "rental_status": "PICKED_UP",
      "customer": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Acme Events Inc.",
        "code": "CUST-0042"
      },
      "rental_period": {
        "start_date": "2024-07-18",
        "end_date": "2024-07-22",
        "days_remaining": 2,
        "is_overdue": false
      },
      "financial": {
        "total_amount": 2415.75,
        "paid_amount": 500.00,
        "balance_due": 1915.75
      },
      "items_count": 2,
      "total_quantity": 12,
      "location": {
        "id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
        "name": "Main Warehouse"
      },
      "created_at": "2024-07-16T10:30:00Z"
    }
  ],
  "total": 47,
  "page": 1,
  "size": 20,
  "pages": 3,
  "summary": {
    "total_active": 15,
    "total_overdue": 3,
    "total_reserved": 12,
    "total_revenue": 45678.90
  }
}
```

---

### Get Rental Details

Retrieves complete details of a specific rental transaction.

**Endpoint**: `GET /transactions/{transaction_id}`

**Path Parameters**:
- `transaction_id` (UUID): The rental transaction ID

**Success Response** (200 OK):
```json
{
  "id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
  "transaction_number": "RNT-20240716-0089",
  "transaction_type": "RENTAL",
  "status": "ACTIVE",
  "rental_status": "PICKED_UP",
  "customer": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Acme Events Inc.",
    "code": "CUST-0042",
    "email": "events@acme.com",
    "phone": "+1-555-0123",
    "address": "456 Corporate Blvd, Metro City, MC 12345",
    "credit_limit": 10000.00,
    "current_balance": 3500.00
  },
  "location": {
    "id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
    "name": "Main Warehouse",
    "code": "WH-001",
    "address": "789 Storage Way, Industrial Zone"
  },
  "transaction_date": "2024-07-16",
  "rental_period": {
    "start_date": "2024-07-18",
    "end_date": "2024-07-22",
    "original_end_date": "2024-07-22",
    "total_days": 4,
    "business_days": 3,
    "days_elapsed": 2,
    "days_remaining": 2,
    "is_overdue": false,
    "extensions": []
  },
  "financial_summary": {
    "subtotal": 2200.00,
    "discount_amount": 250.00,
    "tax_amount": 165.75,
    "delivery_charge": 150.00,
    "pickup_charge": 150.00,
    "late_fees": 0.00,
    "damage_charges": 0.00,
    "other_charges": 0.00,
    "deposit_amount": 500.00,
    "total_amount": 2415.75,
    "paid_amount": 500.00,
    "balance_due": 1915.75,
    "refundable_deposit": 500.00
  },
  "payment_history": [
    {
      "date": "2024-07-16T10:30:00Z",
      "amount": 500.00,
      "type": "DEPOSIT",
      "method": "CREDIT_CARD",
      "reference": "AUTH-123456",
      "notes": "Security deposit"
    }
  ],
  "delivery_info": {
    "delivery_required": true,
    "delivery_address": "123 Event Plaza, Metro City, MC 12345",
    "delivery_contact": "Jane Smith",
    "delivery_phone": "+1-555-9876",
    "delivery_date": "2024-07-18",
    "delivery_time": "09:00",
    "delivery_status": "COMPLETED",
    "delivery_completed_at": "2024-07-18T09:15:00Z",
    "delivery_notes": "Delivered to loading dock, signed by J. Smith",
    "pickup_required": true,
    "pickup_date": "2024-07-22",
    "pickup_time": "17:00",
    "pickup_status": "SCHEDULED"
  },
  "notes": "Corporate event rental - handle with care",
  "reference_number": "EVENT-2024-789",
  "audit_trail": {
    "created_at": "2024-07-16T10:30:00Z",
    "created_by": "john.doe@company.com",
    "updated_at": "2024-07-18T09:15:00Z",
    "updated_by": "delivery@company.com",
    "picked_up_at": "2024-07-18T09:15:00Z",
    "picked_up_by": "mike.jones@company.com"
  },
  "rental_items": [
    {
      "id": "1a2b3c4d-5678-4562-b3fc-9e8f7d6c5b4a",
      "line_number": 1,
      "item": {
        "id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
        "sku": "SPK-PRO-15",
        "name": "Professional Speaker 15\"",
        "description": "High-power professional speaker system",
        "category": "Audio Equipment",
        "brand": "ProSound"
      },
      "quantity": 10,
      "quantity_returned": 0,
      "quantity_damaged": 0,
      "rental_rate": {
        "period_type": "DAILY",
        "period_value": 4,
        "unit_rate": 25.00,
        "total_periods": 4,
        "line_subtotal": 1000.00
      },
      "discount": {
        "type": "PERCENTAGE",
        "value": 10.0,
        "amount": 100.00
      },
      "line_total": 900.00,
      "notes": "Premium speakers for main stage",
      "condition_out": "EXCELLENT",
      "condition_notes_out": "All units tested and working perfectly",
      "accessories": [
        {
          "item_id": "9c5a8d14-8903-5673-b4fd-2e074f88cde7",
          "name": "Speaker stands",
          "quantity": 10,
          "returned": 0
        }
      ],
      "reserved_units": [
        {
          "unit_code": "UNIT-SPK-001",
          "serial_number": "PS15-2024-001",
          "condition": "EXCELLENT",
          "status": "ON_RENT"
        }
      ]
    }
  ],
  "rental_agreement": {
    "agreement_number": "AGR-20240716-0089",
    "template_id": "standard_rental_v2",
    "signed": true,
    "signed_at": "2024-07-16T11:00:00Z",
    "signed_by": "John Doe - Acme Events",
    "signature_method": "ELECTRONIC",
    "agreement_url": "/api/rentals/agreements/AGR-20240716-0089",
    "terms_accepted": true
  },
  "insurance": {
    "required": true,
    "provided": true,
    "policy_number": "INS-2024-4567",
    "coverage_amount": 50000.00,
    "deductible": 500.00,
    "provider": "RentalGuard Insurance"
  }
}
```

---

### Get Rental by Number

Retrieves a rental by its transaction number.

**Endpoint**: `GET /transactions/number/{transaction_number}`

**Example Request**:
```http
GET /transactions/number/RNT-20240716-0089
```

---

### Update Rental Status

Updates the status of a rental transaction.

**Endpoint**: `PATCH /transactions/{transaction_id}/rental-status`

**Request Body**:
```json
{
  "status": "PICKED_UP",
  "notes": "Customer collected all items, verified working condition",
  "picked_up_by": "John Doe",
  "pickup_signature": "base64_signature_data"
}
```

**Status Values**:
- `RESERVED` - Items reserved but not picked up
- `PICKED_UP` - Items collected by customer
- `ACTIVE` - Rental in progress
- `OVERDUE` - Past due date
- `RETURNED` - Items returned
- `COMPLETED` - Rental completed and closed

---

### Extend Rental Period

Extends the rental period for active rentals.

**Endpoint**: `POST /rentals/{rental_id}/extend`

**Request Body**:
```json
{
  "new_end_date": "2024-07-25",
  "reason": "Event extended by 3 days",
  "apply_original_rate": true,
  "discount_type": "PERCENTAGE",
  "discount_value": 5.0
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Rental period extended successfully",
  "data": {
    "rental_id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
    "original_end_date": "2024-07-22",
    "new_end_date": "2024-07-25",
    "additional_days": 3,
    "additional_charges": {
      "subtotal": 825.00,
      "discount": 41.25,
      "tax": 66.52,
      "total": 850.27
    },
    "new_total_amount": 3266.02,
    "new_balance_due": 2766.02
  }
}
```

---

### Calculate Rental Charges

Calculates rental charges before creating a rental.

**Endpoint**: `POST /rentals/calculate-charges`

**Request Body**:
```json
{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "items": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "quantity": 10,
      "rental_period_type": "DAILY",
      "rental_period_value": 4,
      "rental_start_date": "2024-07-18",
      "rental_end_date": "2024-07-22",
      "discount_type": "PERCENTAGE",
      "discount_value": 10.0
    }
  ],
  "delivery_required": true,
  "pickup_required": true,
  "apply_tax": true
}
```

**Success Response** (200 OK):
```json
{
  "calculation_date": "2024-07-16T12:00:00Z",
  "rental_period": {
    "start_date": "2024-07-18",
    "end_date": "2024-07-22",
    "total_days": 4,
    "billable_days": 4
  },
  "item_charges": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "item_name": "Professional Speaker 15\"",
      "quantity": 10,
      "rate_per_unit": 25.00,
      "periods": 4,
      "subtotal": 1000.00,
      "discount": 100.00,
      "total": 900.00
    }
  ],
  "summary": {
    "items_subtotal": 1000.00,
    "total_discount": 100.00,
    "taxable_amount": 900.00,
    "tax_rate": 8.5,
    "tax_amount": 76.50,
    "delivery_charge": 150.00,
    "pickup_charge": 150.00,
    "suggested_deposit": 500.00,
    "total_amount": 1276.50
  },
  "customer_pricing": {
    "is_vip": true,
    "has_contract": true,
    "contract_discount": 5.0,
    "loyalty_discount": 0.0
  }
}
```

---

## Rental Returns

### Create Rental Return

Processes the return of rented items.

**Endpoint**: `POST /rentals/{rental_id}/return`

**Request Body**:
```json
{
  "return_date": "2024-07-22",
  "return_location_id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
  "received_by": "warehouse@company.com",
  "return_items": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "return_quantity": 10,
      "condition_on_return": "GOOD",
      "damage_assessment": {
        "has_damage": true,
        "damage_description": "Minor scuff on one unit",
        "damaged_units": ["UNIT-SPK-003"],
        "damage_charge": 50.00,
        "photos": ["damage_photo_1.jpg", "damage_photo_2.jpg"]
      },
      "cleaning_required": true,
      "cleaning_fee": 25.00,
      "notes": "All units returned, one with minor cosmetic damage"
    },
    {
      "item_id": "7c5b8d24-8903-4673-b4fd-2e074f88cde6",
      "return_quantity": 2,
      "condition_on_return": "EXCELLENT",
      "damage_assessment": {
        "has_damage": false
      },
      "cleaning_required": false,
      "notes": "Perfect condition"
    }
  ],
  "late_return": false,
  "overall_notes": "Customer was satisfied with rental",
  "final_inspection_complete": true
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Rental return processed successfully",
  "return_id": "4e5f6g74-6728-4562-b5ge-4f175g99dgf8",
  "return_number": "RTN-20240722-0045",
  "data": {
    "rental_id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
    "rental_number": "RNT-20240716-0089",
    "return_date": "2024-07-22",
    "return_status": "COMPLETED",
    "on_time_return": true,
    "items_returned": [
      {
        "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
        "item_name": "Professional Speaker 15\"",
        "quantity_rented": 10,
        "quantity_returned": 10,
        "condition": "GOOD",
        "damage_details": {
          "damaged_count": 1,
          "damage_charge": 50.00,
          "description": "Minor scuff on one unit"
        },
        "cleaning_fee": 25.00
      },
      {
        "item_id": "7c5b8d24-8903-4673-b4fd-2e074f88cde6",
        "item_name": "32-Channel Mixing Console",
        "quantity_rented": 2,
        "quantity_returned": 2,
        "condition": "EXCELLENT"
      }
    ],
    "charges_summary": {
      "rental_charges": 2050.00,
      "late_fees": 0.00,
      "damage_charges": 50.00,
      "cleaning_fees": 25.00,
      "other_charges": 0.00,
      "total_charges": 2125.00,
      "deposit_amount": 500.00,
      "deposit_deductions": 75.00,
      "deposit_refund": 425.00,
      "balance_due": 1625.00
    },
    "inventory_updates": {
      "items_returned_to_stock": 12,
      "items_sent_for_repair": 1,
      "items_written_off": 0
    }
  }
}
```

---

### List Returns

Retrieves a list of rental returns.

**Endpoint**: `GET /rentals/returns`

**Query Parameters**:
- `skip` (integer): Pagination offset
- `limit` (integer): Page size
- `return_date_from` (string): Filter by return date
- `return_date_to` (string): Filter by return date
- `has_damage` (boolean): Filter by damage status
- `customer_id` (UUID): Filter by customer

---

### Get Return Details

Retrieves details of a specific return.

**Endpoint**: `GET /rentals/returns/{return_id}`

---

### Process Damage Assessment

Updates damage assessment after detailed inspection.

**Endpoint**: `POST /rentals/returns/{return_id}/damage-assessment`

**Request Body**:
```json
{
  "assessments": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "unit_code": "UNIT-SPK-003",
      "damage_type": "COSMETIC",
      "severity": "MINOR",
      "repair_needed": false,
      "repair_cost_estimate": 0.00,
      "write_off": false,
      "charge_to_customer": 50.00,
      "notes": "Surface scratch, does not affect functionality",
      "photos": ["assessment_1.jpg", "assessment_2.jpg"]
    }
  ],
  "assessment_complete": true,
  "assessed_by": "tech@company.com"
}
```

---

## Rental Availability

### Check Item Availability

Checks availability of items for a specific period.

**Endpoint**: `POST /rentals/check-availability`

**Request Body**:
```json
{
  "items": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "quantity": 15,
      "start_date": "2024-07-25",
      "end_date": "2024-07-28"
    }
  ],
  "location_id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
  "check_alternative_locations": true
}
```

**Success Response** (200 OK):
```json
{
  "check_date": "2024-07-16T14:00:00Z",
  "period": {
    "start_date": "2024-07-25",
    "end_date": "2024-07-28"
  },
  "availability": [
    {
      "item": {
        "id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
        "sku": "SPK-PRO-15",
        "name": "Professional Speaker 15\""
      },
      "requested_quantity": 15,
      "primary_location": {
        "location_id": "5c6d7e8f-9012-3456-b7c8-9d0e1f2g3h4i",
        "location_name": "Main Warehouse",
        "available": 12,
        "reserved": 3,
        "on_rent": 10,
        "total_stock": 25,
        "can_fulfill": false
      },
      "alternative_locations": [
        {
          "location_id": "6d7e8f90-0123-4567-c8d9-0e1f2g3h4i5j",
          "location_name": "Secondary Warehouse",
          "available": 8,
          "distance_km": 15.5,
          "transfer_time_hours": 2
        }
      ],
      "availability_status": "PARTIAL",
      "total_available_all_locations": 20,
      "suggestions": {
        "split_locations": true,
        "alternative_dates": [
          {
            "start_date": "2024-07-29",
            "end_date": "2024-08-01",
            "available": 15
          }
        ],
        "similar_items": [
          {
            "item_id": "9b5a8d14-8903-5673-b4fd-2e074f88cde7",
            "name": "Professional Speaker 12\"",
            "available": 20,
            "compatibility": "COMPATIBLE"
          }
        ]
      }
    }
  ],
  "can_fulfill_order": false,
  "partial_fulfillment_possible": true
}
```

---

### Get Available Items

Gets list of available items for rent.

**Endpoint**: `GET /rentals/available-items`

**Query Parameters**:
- `category_id` (UUID): Filter by category
- `start_date` (string): Rental start date
- `end_date` (string): Rental end date
- `location_id` (UUID): Filter by location
- `min_quantity` (integer): Minimum available quantity
- `search` (string): Search in name/description

---

### Reserve Items

Creates a reservation for items.

**Endpoint**: `POST /rentals/reservations`

**Request Body**:
```json
{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "items": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "quantity": 10,
      "start_date": "2024-07-25",
      "end_date": "2024-07-28"
    }
  ],
  "hold_until": "2024-07-20T17:00:00Z",
  "notes": "Tentative reservation for corporate event"
}
```

---

### Cancel Reservation

Cancels a reservation and releases items.

**Endpoint**: `DELETE /rentals/reservations/{reservation_id}`

---

## Customer Rentals

### Get Customer Active Rentals

Retrieves active rentals for a specific customer.

**Endpoint**: `GET /customers/{customer_id}/rentals/active`

**Success Response** (200 OK):
```json
{
  "customer": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Acme Events Inc.",
    "code": "CUST-0042"
  },
  "active_rentals": [
    {
      "rental_id": "9d5f7g85-6829-4673-b5ge-3f175g99dgf7",
      "rental_number": "RNT-20240716-0089",
      "start_date": "2024-07-18",
      "end_date": "2024-07-22",
      "days_remaining": 2,
      "total_items": 12,
      "total_value": 2415.75,
      "balance_due": 1915.75,
      "status": "ACTIVE",
      "is_overdue": false
    }
  ],
  "summary": {
    "total_active_rentals": 3,
    "total_items_on_rent": 25,
    "total_value_on_rent": 8750.00,
    "total_balance_due": 6250.00,
    "has_overdue": false
  }
}
```

---

### Get Customer Rental History

Retrieves rental history for a customer.

**Endpoint**: `GET /customers/{customer_id}/rentals/history`

**Query Parameters**:
- `date_from` (string): Start date filter
- `date_to` (string): End date filter
- `include_cancelled` (boolean): Include cancelled rentals
- `skip` (integer): Pagination offset
- `limit` (integer): Page size

---

### Get Customer Overdue Rentals

Retrieves overdue rentals for a customer.

**Endpoint**: `GET /customers/{customer_id}/rentals/overdue`

---

## Rental Reports

### Rental Revenue Report

Generates rental revenue report.

**Endpoint**: `GET /reports/rentals/revenue`

**Query Parameters**:
- `period` (string): daily, weekly, monthly, yearly
- `date_from` (string): Start date
- `date_to` (string): End date
- `group_by` (string): category, customer, location
- `location_id` (UUID): Filter by location

**Success Response** (200 OK):
```json
{
  "report_period": {
    "from": "2024-07-01",
    "to": "2024-07-16"
  },
  "revenue_summary": {
    "total_revenue": 145678.90,
    "rental_income": 125000.00,
    "late_fees": 2500.00,
    "damage_charges": 1800.00,
    "delivery_charges": 8500.00,
    "other_income": 7878.90,
    "average_rental_value": 567.89,
    "total_rentals": 256
  },
  "revenue_by_period": [
    {
      "date": "2024-07-01",
      "revenue": 8900.50,
      "rentals": 15
    }
  ],
  "top_revenue_items": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "item_name": "Professional Speaker 15\"",
      "revenue": 25600.00,
      "rental_count": 45,
      "average_rental": 569.00
    }
  ]
}
```

---

### Item Utilization Report

Shows how efficiently items are being rented.

**Endpoint**: `GET /reports/rentals/utilization`

**Success Response** (200 OK):
```json
{
  "report_period": {
    "from": "2024-07-01",
    "to": "2024-07-16",
    "total_days": 16
  },
  "utilization_summary": {
    "average_utilization_rate": 68.5,
    "peak_utilization_date": "2024-07-10",
    "lowest_utilization_date": "2024-07-05"
  },
  "item_utilization": [
    {
      "item": {
        "id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
        "name": "Professional Speaker 15\"",
        "total_units": 25
      },
      "utilization": {
        "days_rented": 180,
        "possible_rental_days": 400,
        "utilization_rate": 45.0,
        "revenue_per_unit": 456.00,
        "times_rented": 12
      }
    }
  ]
}
```

---

### Overdue Rentals Report

Lists all overdue rentals.

**Endpoint**: `GET /reports/rentals/overdue`

**Success Response** (200 OK):
```json
{
  "report_date": "2024-07-16",
  "overdue_summary": {
    "total_overdue": 8,
    "total_overdue_value": 12456.00,
    "average_days_overdue": 3.5,
    "customers_affected": 6
  },
  "overdue_rentals": [
    {
      "rental_id": "8e4f6g74-5718-3562-a4fd-2e064f77bcd6",
      "rental_number": "RNT-20240710-0056",
      "customer": {
        "id": "4gb96g75-6828-5673-c5gf-3d074g88dce7",
        "name": "Smith Industries",
        "phone": "+1-555-5678",
        "email": "accounts@smith.com"
      },
      "rental_end_date": "2024-07-13",
      "days_overdue": 3,
      "rental_value": 1850.00,
      "late_fees_accrued": 150.00,
      "items_count": 5,
      "contact_attempts": [
        {
          "date": "2024-07-14",
          "method": "EMAIL",
          "status": "SENT"
        },
        {
          "date": "2024-07-15",
          "method": "PHONE",
          "status": "NO_ANSWER"
        }
      ]
    }
  ]
}
```

---

## Rental Agreements

### Generate Rental Agreement

Generates a rental agreement PDF.

**Endpoint**: `POST /rentals/{rental_id}/agreement/generate`

**Request Body**:
```json
{
  "template_id": "standard_rental_v2",
  "include_terms": true,
  "include_insurance": true,
  "custom_terms": [],
  "signatory_name": "John Doe",
  "signatory_title": "Events Manager"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "agreement_id": "AGR-20240716-0089",
  "document_url": "/api/rentals/agreements/AGR-20240716-0089/download",
  "preview_url": "/api/rentals/agreements/AGR-20240716-0089/preview",
  "expires_at": "2024-07-17T10:30:00Z"
}
```

---

### Get Agreement Template

Retrieves available agreement templates.

**Endpoint**: `GET /rentals/agreement-templates`

---

## Error Handling

### Common Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `INSUFFICIENT_AVAILABILITY` | Not enough items | Requested quantity exceeds available |
| `INVALID_RENTAL_PERIOD` | Date error | Invalid start/end dates |
| `CUSTOMER_BLOCKED` | Customer issue | Customer blocked from rentals |
| `ITEM_NOT_RENTABLE` | Item configuration | Item not set up for rental |
| `OVERDUE_LIMIT_EXCEEDED` | Too many overdue | Customer has too many overdue rentals |
| `CREDIT_LIMIT_EXCEEDED` | Credit issue | Customer exceeded credit limit |
| `INVALID_RETURN_QUANTITY` | Return error | Returning more than rented |
| `RENTAL_NOT_ACTIVE` | Status error | Rental not in active status |

### Error Response Examples

**Insufficient Availability**:
```json
{
  "detail": "Insufficient availability for requested items",
  "error_code": "INSUFFICIENT_AVAILABILITY",
  "errors": [
    {
      "item_id": "8b4a9c13-7892-4562-a3fc-1d963f77bcd5",
      "item_name": "Professional Speaker 15\"",
      "requested": 15,
      "available": 12,
      "alternatives": ["9b5a8d14-8903-5673-b4fd-2e074f88cde7"]
    }
  ]
}
```

**Customer Blocked**:
```json
{
  "detail": "Customer is blocked from new rentals",
  "error_code": "CUSTOMER_BLOCKED",
  "reason": "OVERDUE_RENTALS",
  "blocked_until": "2024-07-20",
  "outstanding_rentals": 3,
  "total_overdue_amount": 3450.00
}
```

---

## Best Practices

### 1. Availability Checking
```javascript
// Always check availability before showing rental form
const checkAvailability = async (items, startDate, endDate) => {
  const response = await api.post('/rentals/check-availability', {
    items: items.map(item => ({
      item_id: item.id,
      quantity: item.quantity,
      start_date: startDate,
      end_date: endDate
    })),
    check_alternative_locations: true
  });
  
  return response.availability.every(item => item.availability_status === 'AVAILABLE');
};
```

### 2. Rental Period Validation
```javascript
// Validate rental periods on frontend
const validateRentalPeriod = (startDate, endDate) => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const today = new Date();
  
  if (start < today) {
    return { valid: false, error: 'Start date cannot be in the past' };
  }
  
  if (end <= start) {
    return { valid: false, error: 'End date must be after start date' };
  }
  
  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
  if (days > 365) {
    return { valid: false, error: 'Rental period cannot exceed 365 days' };
  }
  
  return { valid: true, days };
};
```

### 3. Price Calculation
```javascript
// Calculate rental prices with proper decimal handling
const calculateRentalPrice = (items) => {
  return items.reduce((total, item) => {
    const periods = item.rental_period_value;
    const rate = parseFloat(item.unit_rate);
    const quantity = parseInt(item.quantity);
    const subtotal = periods * rate * quantity;
    
    let discount = 0;
    if (item.discount_type === 'PERCENTAGE') {
      discount = subtotal * (parseFloat(item.discount_value) / 100);
    } else if (item.discount_type === 'FIXED') {
      discount = parseFloat(item.discount_value);
    }
    
    return total + (subtotal - discount);
  }, 0).toFixed(2);
};
```

### 4. Return Processing
```javascript
// Handle partial returns
const processReturn = async (rentalId, returnItems) => {
  // Validate quantities
  for (const item of returnItems) {
    if (item.return_quantity > item.rented_quantity) {
      throw new Error(`Cannot return more than rented for ${item.name}`);
    }
  }
  
  // Check for damage and calculate charges
  const damageCharges = returnItems
    .filter(item => item.damage_assessment?.has_damage)
    .reduce((sum, item) => sum + (item.damage_assessment.damage_charge || 0), 0);
  
  // Submit return
  const response = await api.post(`/rentals/${rentalId}/return`, {
    return_date: new Date().toISOString().split('T')[0],
    return_items: returnItems,
    final_inspection_complete: true
  });
  
  return response;
};
```

### 5. Overdue Management
```javascript
// Monitor overdue rentals
const checkOverdueRentals = async () => {
  const response = await api.get('/rentals/overdue');
  
  if (response.overdue_rentals.length > 0) {
    // Show notification
    showNotification({
      type: 'warning',
      title: 'Overdue Rentals',
      message: `${response.overdue_rentals.length} rentals are overdue`,
      action: {
        label: 'View Details',
        onClick: () => navigateTo('/rentals/overdue')
      }
    });
  }
  
  return response.overdue_rentals;
};

// Set up periodic check
setInterval(checkOverdueRentals, 3600000); // Check every hour
```

### 6. Rental Agreement Handling
```javascript
// Handle agreement signing
const handleAgreementSigning = async (rentalId, signatureData) => {
  // Generate agreement
  const agreement = await api.post(`/rentals/${rentalId}/agreement/generate`, {
    template_id: 'standard_rental_v2',
    include_terms: true,
    include_insurance: true
  });
  
  // Show preview
  showPdfPreview(agreement.preview_url);
  
  // Submit signature
  const signed = await api.post(`/rentals/${rentalId}/agreement/sign`, {
    signature: signatureData,
    agreed_to_terms: true,
    ip_address: await getClientIP()
  });
  
  return signed;
};
```

### 7. Performance Optimization
- Cache available items for quick filtering
- Use virtual scrolling for large rental lists
- Implement incremental search for items
- Batch availability checks when possible
- Preload common rental periods

### 8. Error Recovery
```javascript
// Implement retry logic for critical operations
const createRentalWithRetry = async (rentalData, maxRetries = 3) => {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await api.post('/transactions/new-rental', rentalData);
      return response;
    } catch (error) {
      lastError = error;
      
      // Don't retry on validation errors
      if (error.status === 422) {
        throw error;
      }
      
      // Wait before retry
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  
  throw lastError;
};
```

---

## Appendix

### Rental Status Flow
```
DRAFT → RESERVED → CONFIRMED → PICKED_UP → ACTIVE → OVERDUE
                       ↓            ↓          ↓         ↓
                   CANCELLED    CANCELLED  RETURNED  RETURNED
                                              ↓         ↓
                                          COMPLETED  DISPUTED
```

### Period Types
- `HOURLY` - Minimum 1 hour
- `DAILY` - 24-hour periods
- `WEEKLY` - 7-day periods
- `MONTHLY` - Calendar months

### Condition Ratings
- `EXCELLENT` - Like new
- `GOOD` - Normal wear
- `FAIR` - Noticeable wear
- `POOR` - Significant wear
- `DAMAGED` - Needs repair

### Damage Types
- `COSMETIC` - Surface damage
- `FUNCTIONAL` - Affects operation
- `STRUCTURAL` - Major damage
- `MISSING_PARTS` - Components missing

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 16-07-2025 | Initial comprehensive rental API documentation |

---

**End of Document**