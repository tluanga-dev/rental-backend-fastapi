# FastAPI Rental Management System - API Reference

## Overview

This document provides a comprehensive reference for all API endpoints in the FastAPI Rental Management System. This guide is designed for frontend developers to understand and integrate with the backend API.

## Base Information

- **Base URL**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Content-Type**: `application/json`
- **Authentication**: JWT Bearer Token

## Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Master Data](#master-data)
   - [Brands](#brands)
   - [Categories](#categories)
   - [Locations](#locations)
   - [Units of Measurement](#units-of-measurement)
4. [Customer Management](#customer-management)
5. [Supplier Management](#supplier-management)
6. [Inventory Management](#inventory-management)
7. [Transaction Processing](#transaction-processing)
8. [Rental Operations](#rental-operations)
9. [Analytics & Reporting](#analytics--reporting)
10. [System Management](#system-management)

---

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2025-01-10T10:00:00Z"
  }
}
```

### POST /api/auth/login
Login and receive access tokens.

**Request Body:**
```json
{
  "username": "admin",
  "password": "Admin@123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "System Administrator"
  }
}
```

### POST /api/auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### GET /api/auth/me
Get current user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "System Administrator",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### POST /api/auth/logout
Logout and invalidate refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

## User Management

### GET /api/users/
Get all users (admin only).

**Query Parameters:**
- `search` (optional): Search users by email or name
- `page` (optional): Page number (default: 1)
- `size` (optional): Items per page (default: 20)

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "System Administrator",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### POST /api/users/
Create a new user (admin only).

**Request Body:**
```json
{
  "username": "new_user",
  "email": "newuser@example.com",
  "password": "SecurePassword123",
  "full_name": "New User",
  "is_active": true
}
```

**Response (201):**
```json
{
  "id": 2,
  "username": "new_user",
  "email": "newuser@example.com",
  "full_name": "New User",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z"
}
```

---

## Master Data

### Brands

#### GET /api/master-data/brands/brands/
Get all brands with pagination and filtering.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `name` (optional): Filter by brand name
- `code` (optional): Filter by brand code
- `is_active` (optional): Filter by active status
- `search` (optional): Search in name and code
- `sort_field` (optional): Field to sort by (default: "name")
- `sort_direction` (optional): Sort direction "asc" or "desc" (default: "asc")
- `include_inactive` (optional): Include inactive brands (default: false)

**Response (200):**
```json
{
  "items": [
    {
      "id": "b28ccd93-d61b-437d-81ef-d909a0eae5f8",
      "name": "Apple",
      "code": "APPLE",
      "description": "Apple Inc. brand",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "display_name": "Apple (APPLE)"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

#### POST /api/master-data/brands/brands/
Create a new brand.

**Request Body:**
```json
{
  "name": "Samsung",
  "code": "SAMSUNG",
  "description": "Samsung Electronics brand",
  "is_active": true
}
```

**Response (201):**
```json
{
  "id": "new-brand-uuid",
  "name": "Samsung",
  "code": "SAMSUNG",
  "description": "Samsung Electronics brand",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "display_name": "Samsung (SAMSUNG)"
}
```

#### GET /api/master-data/brands/brands/{brand_id}
Get brand by ID.

**Response (200):**
```json
{
  "id": "b28ccd93-d61b-437d-81ef-d909a0eae5f8",
  "name": "Apple",
  "code": "APPLE",
  "description": "Apple Inc. brand",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "display_name": "Apple (APPLE)"
}
```

#### PUT /api/master-data/brands/brands/{brand_id}
Update an existing brand.

**Request Body:**
```json
{
  "name": "Apple Inc.",
  "description": "Updated Apple Inc. brand description"
}
```

**Response (200):**
```json
{
  "id": "b28ccd93-d61b-437d-81ef-d909a0eae5f8",
  "name": "Apple Inc.",
  "code": "APPLE",
  "description": "Updated Apple Inc. brand description",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "display_name": "Apple Inc. (APPLE)"
}
```

### Categories

#### GET /api/master-data/categories/categories/
Get all categories with pagination and filtering.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `name` (optional): Filter by category name
- `parent_id` (optional): Filter by parent category ID
- `level` (optional): Filter by category level
- `is_leaf` (optional): Filter by leaf status
- `is_active` (optional): Filter by active status
- `search` (optional): Search in name and path
- `sort_field` (optional): Field to sort by (default: "name")
- `sort_direction` (optional): Sort direction (default: "asc")
- `include_inactive` (optional): Include inactive categories (default: false)

**Response (200):**
```json
{
  "items": [
    {
      "id": "category-uuid",
      "name": "Electronics",
      "code": "ELEC",
      "category_path": "Electronics",
      "category_level": 1,
      "parent_category_id": null,
      "is_leaf": false,
      "is_active": true,
      "display_order": 1,
      "description": "Electronic devices and components",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

#### POST /api/master-data/categories/categories/
Create a new category.

**Request Body:**
```json
{
  "name": "Smartphones",
  "code": "PHONE",
  "parent_category_id": "electronics-uuid",
  "description": "Mobile phones and smartphones",
  "display_order": 1
}
```

**Response (201):**
```json
{
  "id": "new-category-uuid",
  "name": "Smartphones",
  "code": "PHONE",
  "category_path": "Electronics/Smartphones",
  "category_level": 2,
  "parent_category_id": "electronics-uuid",
  "is_leaf": true,
  "is_active": true,
  "display_order": 1,
  "description": "Mobile phones and smartphones",
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z"
}
```

### Locations

#### GET /api/master-data/locations/
Get all locations.

**Response (200):**
```json
{
  "items": [
    {
      "id": "location-uuid",
      "name": "Main Warehouse",
      "code": "MAIN_WH",
      "location_type": "WAREHOUSE",
      "address": "123 Storage St, City, State 12345",
      "description": "Primary storage facility",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

### Units of Measurement

#### GET /api/master-data/units-of-measurement/
Get all units of measurement with pagination and filtering.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)
- `name` (optional): Filter by unit name (partial match)
- `abbreviation` (optional): Filter by unit abbreviation (partial match)
- `is_active` (optional): Filter by active status
- `search` (optional): Search in name and abbreviation
- `sort_field` (optional): Field to sort by (default: "name")
- `sort_direction` (optional): Sort direction "asc" or "desc" (default: "asc")
- `include_inactive` (optional): Include inactive units (default: false)

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Kilogram",
      "abbreviation": "kg",
      "is_active": true,
      "display_name": "Kilogram (kg)"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

#### POST /api/master-data/units-of-measurement/
Create a new unit of measurement.

**Request Body:**
```json
{
  "name": "Kilogram",
  "abbreviation": "kg",
  "description": "Standard unit of mass"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Kilogram",
  "abbreviation": "kg",
  "description": "Standard unit of mass",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "created_by": "user-uuid",
  "updated_by": "user-uuid",
  "display_name": "Kilogram (kg)",
  "item_count": 0
}
```

#### GET /api/master-data/units-of-measurement/{unit_id}
Get a specific unit of measurement by ID.

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Kilogram",
  "abbreviation": "kg",
  "description": "Standard unit of mass",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "created_by": "user-uuid",
  "updated_by": "user-uuid",
  "display_name": "Kilogram (kg)",
  "item_count": 0
}
```

#### GET /api/master-data/units-of-measurement/by-name/{unit_name}
Get a unit of measurement by name.

**Response (200):** Same as GET by ID

#### GET /api/master-data/units-of-measurement/by-abbreviation/{unit_abbreviation}
Get a unit of measurement by abbreviation.

**Response (200):** Same as GET by ID

#### PUT /api/master-data/units-of-measurement/{unit_id}
Update an existing unit of measurement.

**Request Body:**
```json
{
  "name": "Kilogram",
  "abbreviation": "KG",
  "description": "Updated description",
  "is_active": true
}
```

**Response (200):** Same as GET by ID

#### DELETE /api/master-data/units-of-measurement/{unit_id}
Soft delete a unit of measurement (sets is_active to false).

**Response (204):** No content

#### GET /api/master-data/units-of-measurement/search/
Search units of measurement by name, abbreviation, or description.

**Query Parameters:**
- `q` (required): Search query (min length: 1)
- `limit` (optional): Maximum results (default: 10, max: 50)
- `include_inactive` (optional): Include inactive units (default: false)

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Kilogram",
    "abbreviation": "kg",
    "is_active": true,
    "display_name": "Kilogram (kg)"
  }
]
```

#### GET /api/master-data/units-of-measurement/active/
Get all active units of measurement.

**Response (200):** Array of unit summaries

#### GET /api/master-data/units-of-measurement/stats/
Get unit of measurement statistics.

**Response (200):**
```json
{
  "total_units": 10,
  "active_units": 8,
  "inactive_units": 2,
  "units_with_items": 5,
  "units_without_items": 5,
  "most_used_units": [
    {
      "name": "Pieces",
      "item_count": 150
    }
  ]
}
```

#### POST /api/master-data/units-of-measurement/{unit_id}/activate
Activate a unit of measurement.

**Response (200):** Updated unit object

#### POST /api/master-data/units-of-measurement/{unit_id}/deactivate
Deactivate a unit of measurement.

**Response (200):** Updated unit object

#### POST /api/master-data/units-of-measurement/bulk-operation
Perform bulk operations on multiple units.

**Request Body:**
```json
{
  "unit_ids": ["uuid1", "uuid2", "uuid3"],
  "operation": "activate"
}
```

**Response (200):**
```json
{
  "success_count": 3,
  "failure_count": 0,
  "errors": []
}
```

#### GET /api/master-data/units-of-measurement/export/
Export all units of measurement data.

**Query Parameters:**
- `include_inactive` (optional): Include inactive units (default: false)

**Response (200):** Array of complete unit objects with all fields

#### POST /api/master-data/units-of-measurement/import/
Import units of measurement data.

**Request Body:**
```json
[
  {
    "name": "Meter",
    "abbreviation": "m",
    "description": "Standard unit of length",
    "is_active": true
  }
]
```

**Response (200):**
```json
{
  "total_processed": 1,
  "successful_imports": 1,
  "failed_imports": 0,
  "skipped_imports": 0,
  "errors": []
}
```

---

## Customer Management

### GET /api/customers/customers/
Get all customers with pagination and filtering.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `search` (optional): Search in name, email, phone
- `customer_type` (optional): Filter by customer type
- `status` (optional): Filter by customer status
- `is_active` (optional): Filter by active status

**Response (200):**
```json
{
  "items": [
    {
      "id": "customer-uuid",
      "customer_code": "CUST001",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "+1-555-123-4567",
      "customer_type": "INDIVIDUAL",
      "status": "ACTIVE",
      "credit_limit": "5000.00",
      "credit_rating": "GOOD",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "display_name": "John Doe (CUST001)"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

### POST /api/customers/customers/
Create a new customer.

**Request Body:**
```json
{
  "customer_code": "CUST002",
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@example.com",
  "phone": "+1-555-987-6543",
  "customer_type": "INDIVIDUAL",
  "credit_limit": 3000.00,
  "address": {
    "street": "456 Main St",
    "city": "Anytown",
    "state": "ST",
    "zip_code": "12345",
    "country": "USA"
  }
}
```

**Response (201):**
```json
{
  "id": "new-customer-uuid",
  "customer_code": "CUST002",
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@example.com",
  "phone": "+1-555-987-6543",
  "customer_type": "INDIVIDUAL",
  "status": "ACTIVE",
  "credit_limit": "3000.00",
  "credit_rating": "GOOD",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "display_name": "Jane Smith (CUST002)"
}
```

---

## Supplier Management

### GET /api/suppliers/suppliers/
Get all suppliers.

**Response (200):**
```json
{
  "items": [
    {
      "id": "supplier-uuid",
      "supplier_code": "SUPP001",
      "name": "Tech Supplies Inc",
      "contact_person": "Alice Johnson",
      "email": "alice@techsupplies.com",
      "phone": "+1-555-444-3333",
      "supplier_type": "MANUFACTURER",
      "status": "ACTIVE",
      "credit_terms": "NET_30",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "display_name": "Tech Supplies Inc (SUPP001)"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

### POST /api/suppliers/suppliers/
Create a new supplier.

**Request Body:**
```json
{
  "supplier_code": "SUPP002",
  "name": "Office Equipment Co",
  "contact_person": "Bob Wilson",
  "email": "bob@officeequip.com",
  "phone": "+1-555-222-1111",
  "supplier_type": "DISTRIBUTOR",
  "credit_terms": "NET_15",
  "address": {
    "street": "789 Business Ave",
    "city": "Commerce City",
    "state": "CC",
    "zip_code": "54321",
    "country": "USA"
  }
}
```

**Response (201):**
```json
{
  "id": "new-supplier-uuid",
  "supplier_code": "SUPP002",
  "name": "Office Equipment Co",
  "contact_person": "Bob Wilson",
  "email": "bob@officeequip.com",
  "phone": "+1-555-222-1111",
  "supplier_type": "DISTRIBUTOR",
  "status": "ACTIVE",
  "credit_terms": "NET_15",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "display_name": "Office Equipment Co (SUPP002)"
}
```

---

## Inventory Management

### Items

#### GET /api/inventory/items
Get all inventory items.

**Query Parameters:**
- `skip` (optional): Records to skip (default: 0)
- `limit` (optional): Maximum records (default: 100)
- `item_type` (optional): Filter by item type ("RENTAL", "SALE", "BOTH")
- `item_status` (optional): Filter by item status
- `brand_id` (optional): Filter by brand ID
- `category_id` (optional): Filter by category ID
- `active_only` (optional): Only active items (default: true)

**Response (200):**
```json
[
  {
    "id": "item-uuid",
    "item_code": "ITEM001",
    "sku": "CONS-HM-EXCA-R-001",
    "item_name": "Excavator Caterpillar 320",
    "item_type": "RENTAL",
    "item_status": "ACTIVE",
    "brand_id": null,
    "category_id": "heavy-machinery-uuid",
    "purchase_price": "150000.00",
    "rental_price_per_day": "1200.00",
    "sale_price": null,
    "description": "Heavy duty excavator for construction",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "display_name": "Excavator Caterpillar 320 (ITEM001)"
  }
]
```

#### POST /api/inventory/items
Create a new inventory item with automatic SKU generation.

**Request Body:**
```json
{
  "item_code": "DRILL001",
  "item_name": "Power Drill Makita",
  "item_type": "SALE",
  "category_id": "power-tools-uuid",
  "purchase_price": 120.00,
  "sale_price": 180.00,
  "description": "Professional grade power drill"
}
```

**Response (201):**
```json
{
  "id": "new-item-uuid",
  "item_code": "DRILL001",
  "sku": "TOOL-PWR-POWE-S-001",
  "item_name": "Power Drill Makita",
  "item_type": "SALE",
  "item_status": "ACTIVE",
  "brand_id": null,
  "category_id": "power-tools-uuid",
  "purchase_price": "120.00",
  "rental_price_per_day": null,
  "sale_price": "180.00",
  "description": "Professional grade power drill",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "display_name": "Power Drill Makita (DRILL001)"
}
```

#### GET /api/inventory/items/{item_id}
Get item by ID.

#### GET /api/inventory/items/code/{item_code}
Get item by item code.

#### GET /api/inventory/items/sku/{sku}
Get item by SKU.

**Response (200):** Same as item object above

#### PUT /api/inventory/items/{item_id}
Update an existing item.

#### DELETE /api/inventory/items/{item_id}
Soft delete an item.

#### GET /api/inventory/items/search/{search_term}
Search items by name or code.

#### GET /api/inventory/items/rental
Get all rental items (RENTAL or BOTH types).

#### GET /api/inventory/items/sale
Get all sale items (SALE or BOTH types).

### SKU Management

#### POST /api/inventory/skus/generate
Preview SKU generation for given parameters.

**Request Body:**
```json
{
  "category_id": "e5c46b97-6730-4c07-819c-2ed9014e7feb",
  "item_name": "Excavator Caterpillar",
  "item_type": "RENTAL"
}
```

**Response (200):**
```json
{
  "sku": "CONS-HM-EXCA-R-001",
  "category_code": "CONS",
  "subcategory_code": "HM",
  "product_code": "EXCA",
  "attributes_code": "R",
  "sequence_number": 1
}
```

#### POST /api/inventory/skus/bulk-generate
Generate SKUs for all existing items that don't have them.

**Response (200):**
```json
{
  "total_processed": 10,
  "successful_generations": 9,
  "failed_generations": 1,
  "errors": [
    {
      "item_id": "item-uuid",
      "item_code": "ITEM123",
      "error": "Category not found"
    }
  ]
}
```

### SKU Format Specification

**Format:** `[CATEGORY]-[SUBCATEGORY]-[PRODUCT]-[ATTRIBUTES]-[SEQUENCE]`

- **CATEGORY**: 1-4 character abbreviation of root category (e.g., CONS for Construction)
- **SUBCATEGORY**: 1-4 character abbreviation of subcategory (e.g., HM for Heavy Machinery)
- **PRODUCT**: First 4 letters of product name, uppercase, alphanumeric only (e.g., EXCA for Excavator)
- **ATTRIBUTES**: Single character indicating item type:
  - `R` = Rental only
  - `S` = Sale only
  - `B` = Both rental and sale
- **SEQUENCE**: 3-digit zero-padded sequence number (e.g., 001, 002, 003)

**Examples:**
- `CONS-HM-EXCA-R-001` - Construction > Heavy Machinery > Excavator (Rental)
- `CONS-MAC-GENE-B-001` - Construction > Machinery > Generator (Both)
- `TOOL-PWR-DRIL-S-001` - Tools > Power Tools > Drill (Sale only)
- `MISC-ITEM-PROD-R-001` - Fallback format when category hierarchy is not available

**Notes:**
- SKUs are automatically generated during item creation
- Custom SKU input is not supported
- SKUs must be unique across the system
- The system tracks sequences per unique combination of category, subcategory, product, and attributes

### Inventory Units

#### GET /api/inventory/inventory/units
Get all inventory units.

**Query Parameters:**
- `skip` (optional): Records to skip (default: 0)
- `limit` (optional): Maximum records (default: 100)
- `item_id` (optional): Filter by item ID
- `location_id` (optional): Filter by location ID
- `status` (optional): Filter by unit status
- `condition` (optional): Filter by unit condition
- `active_only` (optional): Only active units (default: true)

**Response (200):**
```json
[
  {
    "id": "unit-uuid",
    "unit_serial": "MBA001",
    "item_id": "item-uuid",
    "location_id": "location-uuid",
    "status": "AVAILABLE",
    "condition": "EXCELLENT",
    "purchase_date": "2025-01-01",
    "warranty_expiry": "2026-01-01",
    "notes": "Brand new unit",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

#### POST /api/inventory/inventory/units
Create a new inventory unit.

**Request Body:**
```json
{
  "unit_serial": "MBA002",
  "item_id": "item-uuid",
  "location_id": "location-uuid",
  "condition": "EXCELLENT",
  "purchase_date": "2025-01-10",
  "warranty_expiry": "2026-01-10",
  "notes": "New unit for rental"
}
```

**Response (201):**
```json
{
  "id": "new-unit-uuid",
  "unit_serial": "MBA002",
  "item_id": "item-uuid",
  "location_id": "location-uuid",
  "status": "AVAILABLE",
  "condition": "EXCELLENT",
  "purchase_date": "2025-01-10",
  "warranty_expiry": "2026-01-10",
  "notes": "New unit for rental",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z"
}
```

---

## Transaction Processing

### GET /api/transactions/transactions/
Get all transactions.

**Query Parameters:**
- `skip` (optional): Records to skip (default: 0)
- `limit` (optional): Maximum records (default: 100)
- `transaction_type` (optional): Filter by transaction type
- `status` (optional): Filter by transaction status
- `payment_status` (optional): Filter by payment status
- `customer_id` (optional): Filter by customer ID
- `location_id` (optional): Filter by location ID
- `date_from` (optional): Filter from date
- `date_to` (optional): Filter to date
- `active_only` (optional): Only active transactions (default: true)

**Response (200):**
```json
[
  {
    "id": "transaction-uuid",
    "transaction_number": "TXN001",
    "transaction_type": "RENTAL",
    "status": "CONFIRMED",
    "payment_status": "PAID",
    "customer_id": "customer-uuid",
    "location_id": "location-uuid",
    "transaction_date": "2025-01-10",
    "due_date": "2025-01-17",
    "total_amount": "455.00",
    "paid_amount": "455.00",
    "discount_amount": "0.00",
    "tax_amount": "35.00",
    "notes": "7-day MacBook rental",
    "created_at": "2025-01-10T10:00:00Z",
    "updated_at": "2025-01-10T10:00:00Z"
  }
]
```

### POST /api/transactions/transactions/
Create a new transaction.

**Request Body:**
```json
{
  "transaction_type": "RENTAL",
  "customer_id": "customer-uuid",
  "location_id": "location-uuid",
  "transaction_date": "2025-01-10",
  "due_date": "2025-01-17",
  "notes": "7-day laptop rental for business trip",
  "lines": [
    {
      "item_id": "item-uuid",
      "inventory_unit_id": "unit-uuid",
      "quantity": 1,
      "unit_price": 65.00,
      "rental_days": 7
    }
  ]
}
```

**Response (201):**
```json
{
  "id": "new-transaction-uuid",
  "transaction_number": "TXN002",
  "transaction_type": "RENTAL",
  "status": "PENDING",
  "payment_status": "PENDING",
  "customer_id": "customer-uuid",
  "location_id": "location-uuid",
  "transaction_date": "2025-01-10",
  "due_date": "2025-01-17",
  "total_amount": "455.00",
  "paid_amount": "0.00",
  "discount_amount": "0.00",
  "tax_amount": "35.00",
  "notes": "7-day laptop rental for business trip",
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z"
}
```

---

## Rental Operations

### GET /api/rentals/rentals/
Get all rental returns.

**Response (200):**
```json
[
  {
    "id": "rental-return-uuid",
    "return_number": "RTN001",
    "transaction_id": "transaction-uuid",
    "return_date": "2025-01-17",
    "return_type": "NORMAL",
    "status": "COMPLETED",
    "total_deposit_refund": "0.00",
    "total_damage_fee": "0.00",
    "total_late_fee": "0.00",
    "notes": "Equipment returned in good condition",
    "processed_by": "staff-user-uuid",
    "created_at": "2025-01-17T14:00:00Z",
    "updated_at": "2025-01-17T14:00:00Z"
  }
]
```

### POST /api/rentals/rentals/
Process a rental return.

**Request Body:**
```json
{
  "transaction_id": "transaction-uuid",
  "return_date": "2025-01-17",
  "return_type": "NORMAL",
  "notes": "All items returned in excellent condition",
  "lines": [
    {
      "transaction_line_id": "transaction-line-uuid",
      "inventory_unit_id": "unit-uuid",
      "returned_quantity": 1,
      "condition_on_return": "EXCELLENT",
      "damage_assessment": {
        "has_damage": false,
        "damage_description": null,
        "damage_fee": 0.00
      }
    }
  ]
}
```

**Response (201):**
```json
{
  "id": "new-rental-return-uuid",
  "return_number": "RTN002",
  "transaction_id": "transaction-uuid",
  "return_date": "2025-01-17",
  "return_type": "NORMAL",
  "status": "COMPLETED",
  "total_deposit_refund": "0.00",
  "total_damage_fee": "0.00",
  "total_late_fee": "0.00",
  "notes": "All items returned in excellent condition",
  "processed_by": "staff-user-uuid",
  "created_at": "2025-01-17T14:00:00Z",
  "updated_at": "2025-01-17T14:00:00Z"
}
```

---

## Analytics & Reporting

### GET /api/analytics/analytics/dashboard
Get analytics dashboard data.

**Response (200):**
```json
{
  "total_reports": 5,
  "pending_reports": 1,
  "completed_reports": 4,
  "failed_reports": 0,
  "active_alerts": 2,
  "critical_alerts": 0,
  "total_metrics": 15,
  "metrics_with_targets": 10,
  "metrics_meeting_targets": 8,
  "recent_reports": [
    {
      "id": "report-uuid",
      "report_name": "Monthly Revenue Report",
      "report_type": "FINANCIAL",
      "status": "COMPLETED",
      "generated_at": "2025-01-10T09:00:00Z"
    }
  ],
  "critical_alerts_list": [],
  "key_metrics": [
    {
      "metric_name": "monthly_revenue",
      "current_value": 25000.00,
      "target_value": 30000.00,
      "percentage": 83.33,
      "trend": "UP"
    }
  ]
}
```

### GET /api/analytics/analytics/reports
Get all analytics reports.

**Query Parameters:**
- `skip` (optional): Records to skip (default: 0)
- `limit` (optional): Maximum records (default: 100)
- `report_type` (optional): Filter by report type
- `report_status` (optional): Filter by report status
- `start_date` (optional): Filter from date
- `end_date` (optional): Filter to date

**Response (200):**
```json
[
  {
    "id": "report-uuid",
    "report_name": "Weekly Inventory Report",
    "report_type": "INVENTORY",
    "status": "COMPLETED",
    "description": "Weekly inventory status and movements",
    "generated_by": "admin-user-uuid",
    "generated_at": "2025-01-10T09:00:00Z",
    "file_path": "/reports/weekly_inventory_20250110.pdf",
    "file_size": 245760,
    "parameters": {
      "week_start": "2025-01-06",
      "week_end": "2025-01-12",
      "include_zero_stock": false
    }
  }
]
```

---

## System Management

### GET /api/system/system/settings
Get system settings.

**Response (200):**
```json
[
  {
    "id": "setting-uuid",
    "setting_key": "default_rental_period",
    "setting_name": "Default Rental Period",
    "setting_type": "INTEGER",
    "setting_category": "RENTAL",
    "setting_value": "7",
    "default_value": "7",
    "description": "Default rental period in days",
    "is_system": false,
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

### PUT /api/system/system/settings/{setting_id}
Update a system setting.

**Request Body:**
```json
{
  "setting_value": "14",
  "description": "Updated default rental period to 14 days"
}
```

**Response (200):**
```json
{
  "id": "setting-uuid",
  "setting_key": "default_rental_period",
  "setting_name": "Default Rental Period",
  "setting_type": "INTEGER",
  "setting_category": "RENTAL",
  "setting_value": "14",
  "default_value": "7",
  "description": "Updated default rental period to 14 days",
  "is_system": false,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z"
}
```

---

## Common Response Formats

### Error Responses

#### 400 Bad Request
```json
{
  "detail": "Validation error message",
  "type": "validation_error"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

#### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

#### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

### Pagination Response Format
Most list endpoints return data in this paginated format:

```json
{
  "items": [], // Array of objects
  "total": 0, // Total number of items
  "page": 1, // Current page number
  "page_size": 20, // Items per page
  "total_pages": 0, // Total number of pages
  "has_next": false, // Whether there's a next page
  "has_previous": false // Whether there's a previous page
}
```

---

## Data Types and Enums

### Customer Types
- `INDIVIDUAL`: Individual customer
- `BUSINESS`: Business customer
- `CORPORATE`: Corporate customer

### Customer Status
- `ACTIVE`: Active customer
- `INACTIVE`: Inactive customer
- `SUSPENDED`: Temporarily suspended
- `BLACKLISTED`: Permanently blacklisted

### Item Types
- `RENTAL`: Only available for rental
- `SALE`: Only available for sale
- `BOTH`: Available for both rental and sale

### Item Status
- `ACTIVE`: Available for use
- `INACTIVE`: Not available
- `DISCONTINUED`: No longer offered
- `MAINTENANCE`: Under maintenance

### Unit Status
- `AVAILABLE`: Available for rental/sale
- `RENTED`: Currently rented out
- `SOLD`: Has been sold
- `MAINTENANCE`: Under maintenance
- `DAMAGED`: Damaged and unavailable
- `LOST`: Lost or stolen

### Unit Condition
- `EXCELLENT`: Like new condition
- `GOOD`: Minor wear
- `FAIR`: Noticeable wear but functional
- `POOR`: Significant wear, may need repair
- `DAMAGED`: Requires repair

### Transaction Types
- `RENTAL`: Rental transaction
- `SALE`: Sale transaction
- `RETURN`: Return transaction
- `PURCHASE`: Purchase from supplier

### Transaction Status
- `PENDING`: Awaiting confirmation
- `CONFIRMED`: Confirmed and active
- `COMPLETED`: Successfully completed
- `CANCELLED`: Cancelled transaction
- `OVERDUE`: Past due date

### Payment Status
- `PENDING`: Payment not yet received
- `PARTIAL`: Partially paid
- `PAID`: Fully paid
- `OVERDUE`: Payment overdue
- `REFUNDED`: Payment refunded

---

## Authentication Flow Example

### Complete Authentication Flow
```javascript
// 1. Login
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'Admin@123'
  })
});

const { access_token, refresh_token } = await loginResponse.json();

// 2. Store tokens securely
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// 3. Use access token for API calls
const apiResponse = await fetch('/api/inventory/inventory/items', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  }
});

// 4. Handle token refresh when needed
if (apiResponse.status === 401) {
  const refreshResponse = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      refresh_token: localStorage.getItem('refresh_token')
    })
  });
  
  const { access_token: newToken } = await refreshResponse.json();
  localStorage.setItem('access_token', newToken);
  
  // Retry original request with new token
}
```

---

## Frontend Integration Notes

### Best Practices

1. **Token Management**: Always store tokens securely and implement automatic refresh
2. **Error Handling**: Implement proper error handling for all API responses
3. **Loading States**: Show loading indicators during API calls
4. **Pagination**: Implement proper pagination controls for list endpoints
5. **Form Validation**: Validate input on the frontend before sending to API
6. **Real-time Updates**: Consider implementing WebSocket connections for real-time updates

### Common Patterns

#### Data Fetching with Error Handling
```javascript
async function fetchItems(filters = {}) {
  try {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/inventory/inventory/items?${params}`, {
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch items:', error);
    throw error;
  }
}
```

#### Form Submission
```javascript
async function createCustomer(customerData) {
  try {
    const response = await fetch('/api/customers/customers/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(customerData)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create customer');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to create customer:', error);
    throw error;
  }
}
```

---

This API reference provides comprehensive documentation for integrating with the FastAPI Rental Management System. For the most up-to-date API documentation, always refer to the interactive Swagger UI at `http://localhost:8000/docs`.