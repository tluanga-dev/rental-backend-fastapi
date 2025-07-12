# Item Master API - Complete Developer Guide

## Table of Contents
1. [Overview](#overview)
2. [Authentication & Setup](#authentication--setup)
3. [Data Models & Validation](#data-models--validation)
4. [Core CRUD Operations](#core-crud-operations)
5. [Search & Filtering](#search--filtering)
6. [SKU Management](#sku-management)
7. [Specialized Endpoints](#specialized-endpoints)
8. [Error Handling](#error-handling)
9. [Workflow Examples](#workflow-examples)
10. [Frontend Integration Guide](#frontend-integration-guide)

## Overview

The Item Master API is the core system for managing rental and sale items in the rental management platform. It provides comprehensive functionality for creating, managing, and querying items with advanced features like automatic SKU generation, intelligent search, and flexible filtering.

### 🔑 Key Capabilities
- **Full CRUD Operations**: Create, read, update, delete items
- **Intelligent Search**: Multi-field text search across names, codes, SKUs, descriptions
- **Advanced Filtering**: Filter by type, status, brand, category with combinations
- **Automatic SKU Generation**: Smart SKU creation based on category and item properties
- **Business Logic Validation**: Ensures data integrity with type-specific pricing rules
- **Pagination & Performance**: Efficient data loading with configurable page sizes
- **Soft Delete**: Preserves data integrity with recoverable deletions

### 🏗️ Architecture
- **Base URL**: `http://localhost:8000/api/master-data/item-master`
- **Response Format**: JSON with consistent structure
- **Authentication**: JWT Bearer token required
- **Pagination**: Offset-based with configurable limits
- **Search**: Case-insensitive with partial matching

## Authentication & Setup

### 🔐 Authentication Headers
All API requests require authentication via JWT Bearer token:

```http
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

### 🌐 Environment Configuration
```bash
# API Base URL
API_BASE_URL=http://localhost:8000/api/master-data/item-master

# Headers for all requests
HEADERS = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}
```

### 📱 Response Format Standard
All responses follow this consistent structure:
```typescript
// Success Response
{
  data: T,                    // Response data (single object or array)
  status: "success",          // Always "success" for 2xx responses
  message?: string           // Optional success message
}

// Error Response  
{
  detail: string | object,   // Error description or validation details
  status_code: number,       // HTTP status code
  error_type?: string        // Optional error classification
}
```

## Data Models & Validation

### 🏷️ Core Enumerations

#### ItemType
Defines how the item can be used in the business:
```typescript
enum ItemType {
  RENTAL = "RENTAL",    // Item available for rent only
  SALE = "SALE",        // Item available for sale only  
  BOTH = "BOTH"         // Item available for both rent and sale
}
```

#### ItemStatus
Defines the current lifecycle status of the item:
```typescript
enum ItemStatus {
  ACTIVE = "ACTIVE",              // Item is available for business use
  INACTIVE = "INACTIVE",          // Item is temporarily unavailable
  DISCONTINUED = "DISCONTINUED"   // Item is permanently removed from catalog
}
```

### 📝 Request Schemas

#### ItemCreate - Full Schema Definition
```typescript
interface ItemCreate {
  // === REQUIRED FIELDS ===
  item_code: string;              // Unique identifier (max 50 chars, alphanumeric + dash/underscore)
  item_name: string;              // Display name (max 200 chars, min 1 char)
  item_type: ItemType;            // Business usage type
  unit_of_measurement_id: string; // UUID reference to units table (REQUIRED)
  
  // === CONDITIONAL REQUIRED FIELDS (based on item_type) ===
  rental_price_per_day?: number; // Required if item_type = RENTAL or BOTH
  sale_price?: number;            // Required if item_type = SALE or BOTH
  
  // === OPTIONAL SYSTEM FIELDS ===
  item_status?: ItemStatus;       // Default: ACTIVE
  brand_id?: string;              // UUID reference to brands table
  category_id?: string;           // UUID reference to categories table
  
  // === OPTIONAL PRICING FIELDS ===
  rental_price_per_week?: number; // Weekly rental rate (typically 4-5x daily)
  rental_price_per_month?: number; // Monthly rental rate (typically 15-20x daily)
  security_deposit?: number;      // Security deposit amount (>= 0)
  
  // === OPTIONAL RENTAL CONFIGURATION ===
  minimum_rental_days?: string;   // Minimum rental period (integer as string)
  maximum_rental_days?: string;   // Maximum rental period (integer as string)
  
  // === OPTIONAL DESCRIPTIVE FIELDS ===
  description?: string;           // Detailed description (max 1000 chars)
  specifications?: string;        // Technical specifications (max 2000 chars)
  model_number?: string;          // Manufacturer model (max 100 chars)
  serial_number_required?: boolean; // Whether to track serial numbers
  warranty_period_days?: string;  // Warranty duration (integer as string)
  
  // === OPTIONAL INVENTORY FIELDS ===
  reorder_level?: string;         // Minimum stock for reorder alerts (integer as string)
  reorder_quantity?: string;      // Default reorder quantity (integer as string)
}
```

#### ItemUpdate - Partial Update Schema
```typescript
interface ItemUpdate {
  // All fields are optional - only provided fields will be updated
  item_name?: string;
  item_type?: ItemType;           // ⚠️ Changing this may require pricing updates
  item_status?: ItemStatus;
  brand_id?: string | null;       // Set to null to remove association
  category_id?: string | null;
  unit_of_measurement_id?: string;
  rental_price_per_day?: number;
  rental_price_per_week?: number;
  rental_price_per_month?: number;
  sale_price?: number;
  minimum_rental_days?: string;
  maximum_rental_days?: string;
  security_deposit?: number;
  description?: string;
  specifications?: string;
  model_number?: string;
  serial_number_required?: boolean;
  warranty_period_days?: string;
  reorder_level?: string;
  reorder_quantity?: string;
}
```

### 📤 Response Schemas

#### ItemResponse - Complete Item Data
```typescript
interface ItemResponse {
  // === SYSTEM METADATA ===
  id: string;                     // UUID primary key
  created_at: string;             // ISO 8601 datetime (UTC)
  updated_at: string;             // ISO 8601 datetime (UTC)
  is_active: boolean;             // Soft delete flag (false = deleted)
  
  // === CORE ITEM DATA ===
  item_code: string;              // Unique business identifier
  sku: string;                    // Auto-generated Stock Keeping Unit
  item_name: string;              // Display name
  item_type: string;              // ItemType value
  item_status: string;            // ItemStatus value
  
  // === RELATIONSHIP IDS ===
  brand_id?: string | null;
  category_id?: string | null;
  unit_of_measurement_id: string;  // REQUIRED - UUID reference to units table
  
  // === PRICING (nullable) ===
  rental_price_per_day?: string | null;    // Decimal as string
  rental_price_per_week?: string | null;   // Decimal as string
  rental_price_per_month?: string | null;  // Decimal as string
  sale_price?: string | null;              // Decimal as string
  security_deposit?: string | null;        // Decimal as string
  
  // === RENTAL CONFIGURATION (nullable) ===
  minimum_rental_days?: string | null;
  maximum_rental_days?: string | null;
  
  // === DESCRIPTIVE FIELDS (nullable) ===
  description?: string | null;
  specifications?: string | null;
  model_number?: string | null;
  serial_number_required?: boolean;
  warranty_period_days?: string | null;
  
  // === INVENTORY FIELDS (nullable) ===
  reorder_level?: string | null;
  reorder_quantity?: string | null;
  
  // === COMPUTED FIELDS ===
  display_name: string;           // Format: "Item Name (ITEM_CODE)"
}
```

#### ItemListResponse - Simplified for Lists
```typescript
interface ItemListResponse {
  id: string;
  item_code: string;
  item_name: string;
  item_type: string;
  item_status: string;
  rental_price_per_day?: string | null;
  sale_price?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  display_name: string;
}
```

### ✅ Validation Rules & Business Logic

#### Item Code Validation
```typescript
// Rules for item_code field
{
  required: true,
  maxLength: 50,
  pattern: /^[A-Za-z0-9_-]+$/,     // Alphanumeric, underscore, dash only
  unique: true                      // Must be unique across all items
}

// Recommended format: PREFIX + NUMBER
// Examples: "PWR001", "FURN_001", "TOOL-001"
```

#### Pricing Validation by Item Type
```typescript
// RENTAL items
if (item_type === "RENTAL") {
  rental_price_per_day: { required: true, min: 0 }
  sale_price: { forbidden: true }
}

// SALE items  
if (item_type === "SALE") {
  sale_price: { required: true, min: 0 }
  rental_price_per_day: { forbidden: true }
  rental_price_per_week: { forbidden: true }
  rental_price_per_month: { forbidden: true }
}

// BOTH items
if (item_type === "BOTH") {
  rental_price_per_day: { required: true, min: 0 }
  sale_price: { required: true, min: 0 }
}
```

#### Rental Period Validation
```typescript
// Rental days validation
if (minimum_rental_days && maximum_rental_days) {
  assert(parseInt(maximum_rental_days) >= parseInt(minimum_rental_days))
}

// Common rental periods
minimum_rental_days: "1"     // 1 day minimum
maximum_rental_days: "30"    // 30 days maximum (example)
```

## Core CRUD Operations

### 1. Create Item

#### 📤 Endpoint
```http
POST /api/master-data/item-master/
Content-Type: application/json
Authorization: Bearer <token>
```

#### 📝 Request Examples

**Rental Item (Minimum Required)**
```json
{
  "item_code": "DRILL001",
  "item_name": "Cordless Drill",
  "item_type": "RENTAL",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
  "rental_price_per_day": 12.00
}
```

**Sale Item (Minimum Required)**
```json
{
  "item_code": "HELMET001", 
  "item_name": "Safety Helmet",
  "item_type": "SALE",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
  "sale_price": 45.00
}
```

**Dual-Purpose Item (Full Example)**
```json
{
  "item_code": "LADDER001",
  "item_name": "Werner 6ft Fiberglass Ladder",
  "item_type": "BOTH",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
  "rental_price_per_day": 15.00,
  "rental_price_per_week": 75.00,
  "rental_price_per_month": 250.00,
  "sale_price": 279.99,
  "security_deposit": 50.00,
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "brand_id": "987e6543-e21b-12d3-a456-426614174000",
  "description": "Type IA duty rating, 300 lb capacity fiberglass ladder",
  "specifications": "Height: 6ft, Width: 18\", Weight: 15 lbs, ANSI Type IA",
  "model_number": "FS106",
  "minimum_rental_days": "1",
  "maximum_rental_days": "90",
  "warranty_period_days": "365",
  "reorder_level": "5",
  "reorder_quantity": "10"
}
```

#### ✅ Success Response (201 Created)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-01-15T10:30:00.000Z",
  "is_active": true,
  "item_code": "LADDER001",
  "sku": "TOOL-LAD-WRNE-B-001",
  "item_name": "Werner 6ft Fiberglass Ladder",
  "item_type": "BOTH",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
  "item_status": "ACTIVE",
  "rental_price_per_day": "15.00",
  "rental_price_per_week": "75.00",
  "rental_price_per_month": "250.00",
  "sale_price": "279.99",
  "security_deposit": "50.00",
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "brand_id": "987e6543-e21b-12d3-a456-426614174000",
  "description": "Type IA duty rating, 300 lb capacity fiberglass ladder",
  "specifications": "Height: 6ft, Width: 18\", Weight: 15 lbs, ANSI Type IA",
  "model_number": "FS106",
  "minimum_rental_days": "1",
  "maximum_rental_days": "90",
  "warranty_period_days": "365",
  "reorder_level": "5",
  "reorder_quantity": "10",
  "display_name": "Werner 6ft Fiberglass Ladder (LADDER001)"
}
```

#### ❌ Error Responses

**409 Conflict - Duplicate Item Code**
```json
{
  "detail": "Item with code 'LADDER001' already exists",
  "status_code": 409
}
```

**422 Validation Error - Missing Required Field**
```json
{
  "detail": [
    {
      "loc": ["body", "rental_price_per_day"],
      "msg": "Rental items must have rental_price_per_day",
      "type": "value_error"
    }
  ],
  "status_code": 422
}
```

### 2. Get Item by ID

#### 📤 Endpoint
```http
GET /api/master-data/item-master/{item_id}
Authorization: Bearer <token>
```

#### 📝 Request Example
```http
GET /api/master-data/item-master/550e8400-e29b-41d4-a716-446655440000
```

#### ✅ Success Response (200 OK)
Returns complete ItemResponse object (same structure as create response)

#### ❌ Error Response
```json
{
  "detail": "Item with ID 550e8400-e29b-41d4-a716-446655440000 not found",
  "status_code": 404
}
```

### 3. Update Item

#### 📤 Endpoint
```http
PUT /api/master-data/item-master/{item_id}
Content-Type: application/json
Authorization: Bearer <token>
```

#### 📝 Request Examples

**Partial Update (Price Change)**
```json
{
  "rental_price_per_day": 18.00,
  "rental_price_per_week": 90.00,
  "rental_price_per_month": 300.00
}
```

**Status Change**
```json
{
  "item_status": "INACTIVE"
}
```

**Complete Information Update**
```json
{
  "item_name": "Werner 6ft Fiberglass Ladder - Professional Grade",
  "description": "Updated description with enhanced safety features",
  "rental_price_per_day": 20.00,
  "sale_price": 299.99,
  "specifications": "Height: 6ft, Width: 18\", Weight: 15 lbs, ANSI Type IA, Enhanced grip"
}
```

#### ✅ Success Response (200 OK)
Returns updated ItemResponse object with new values

#### ❌ Error Responses

**404 Not Found**
```json
{
  "detail": "Item with ID 550e8400-e29b-41d4-a716-446655440000 not found",
  "status_code": 404
}
```

**422 Validation Error**
```json
{
  "detail": [
    {
      "loc": ["body", "sale_price"],
      "msg": "Sale items must have sale_price",
      "type": "value_error"
    }
  ],
  "status_code": 422
}
```

### 4. Delete Item (Soft Delete)

#### 📤 Endpoint
```http
DELETE /api/master-data/item-master/{item_id}
Authorization: Bearer <token>
```

#### 📝 Request Example
```http
DELETE /api/master-data/item-master/550e8400-e29b-41d4-a716-446655440000
```

#### ✅ Success Response (204 No Content)
No response body. Item is soft-deleted (is_active = false).

#### ❌ Error Response
```json
{
  "detail": "Item with ID 550e8400-e29b-41d4-a716-446655440000 not found",
  "status_code": 404
}
```

## Search & Filtering

### 🔍 Main Search & Filter Endpoint

#### 📤 Endpoint
```http
GET /api/master-data/item-master/
Authorization: Bearer <token>
```

#### 🎛️ Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of items to skip (pagination offset) |
| `limit` | integer | No | 100 | Number of items to return (1-1000) |
| `search` | string | No | null | Search term for name/code/SKU/description |
| `item_type` | enum | No | null | Filter by RENTAL/SALE/BOTH |
| `item_status` | enum | No | null | Filter by ACTIVE/INACTIVE/DISCONTINUED |
| `brand_id` | UUID | No | null | Filter by specific brand |
| `category_id` | UUID | No | null | Filter by specific category |
| `active_only` | boolean | No | true | Include only non-deleted items |

#### 📝 Request Examples

**Basic Search**
```http
GET /api/master-data/item-master/?search=drill
```

**Search with Type Filter**
```http
GET /api/master-data/item-master/?search=ladder&item_type=RENTAL
```

**Multi-Filter Query**
```http
GET /api/master-data/item-master/?search=power&item_type=BOTH&item_status=ACTIVE&limit=20
```

**Pagination Example**
```http
GET /api/master-data/item-master/?skip=20&limit=10
# Returns items 21-30
```

**Category-Specific Search**
```http
GET /api/master-data/item-master/?category_id=123e4567-e89b-12d3-a456-426614174000&search=drill
```

#### ✅ Success Response (200 OK)
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "item_code": "DRILL001",
    "item_name": "DeWalt 20V Max Cordless Drill",
    "item_type": "RENTAL",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
    "item_status": "ACTIVE",
    "rental_price_per_day": "15.00",
    "sale_price": null,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z",
    "display_name": "DeWalt 20V Max Cordless Drill (DRILL001)"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "item_code": "DRILL002",
    "item_name": "Milwaukee M18 Hammer Drill",
    "item_type": "BOTH",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
    "item_status": "ACTIVE",
    "rental_price_per_day": "18.00",
    "sale_price": "249.99",
    "is_active": true,
    "created_at": "2024-01-15T11:00:00.000Z",
    "updated_at": "2024-01-15T11:00:00.000Z",
    "display_name": "Milwaukee M18 Hammer Drill (DRILL002)"
  }
]
```

### 🔢 Count Items

#### 📤 Endpoint
```http
GET /api/master-data/item-master/count/total
Authorization: Bearer <token>
```

#### 🎛️ Query Parameters
Accepts same filter parameters as main search endpoint

#### 📝 Request Examples
```http
GET /api/master-data/item-master/count/total
GET /api/master-data/item-master/count/total?search=drill
GET /api/master-data/item-master/count/total?item_type=RENTAL&active_only=true
```

#### ✅ Success Response (200 OK)
```json
{
  "count": 42
}
```

### 🔍 Dedicated Search Endpoint

#### 📤 Endpoint
```http
GET /api/master-data/item-master/search/{search_term}
Authorization: Bearer <token>
```

#### 📝 Request Example
```http
GET /api/master-data/item-master/search/dewalt?limit=10&active_only=true
```

#### ✅ Success Response (200 OK)
Returns array of ItemListResponse objects matching the search term

## SKU Management

### 🏷️ SKU Format & Generation Rules

#### SKU Structure
```
Format: {CATEGORY}-{SUBCATEGORY}-{PRODUCT}-{TYPE}-{SEQUENCE}

Components:
- CATEGORY: 3-4 char category code (e.g., "TOOL", "FURN")
- SUBCATEGORY: 3-4 char subcategory code (e.g., "PWR", "HAND") 
- PRODUCT: 3-4 char product abbreviation from item name
- TYPE: Single character (R=Rental, S=Sale, B=Both)
- SEQUENCE: 3-digit sequential number (001, 002, etc.)

Examples:
- TOOL-PWR-DWLT-R-001 (Tools > Power Tools > DeWalt > Rental > #001)
- FURN-OFFI-DESK-B-001 (Furniture > Office > Desk > Both > #001)
- MISC-ITEM-UNKN-S-001 (Miscellaneous > Item > Unknown > Sale > #001)
```

### 🔮 Generate SKU Preview

#### 📤 Endpoint
```http
POST /api/master-data/item-master/skus/generate
Content-Type: application/json
Authorization: Bearer <token>
```

#### 📝 Request Schema
```typescript
interface SKUGenerationRequest {
  category_id?: string;           // UUID of category (optional)
  item_name: string;              // Item name for product abbreviation
  item_type: "RENTAL" | "SALE" | "BOTH";  // Type for type code
}
```

#### 📝 Request Examples

**With Category**
```json
{
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "item_name": "Milwaukee M18 Impact Driver",
  "item_type": "RENTAL"
}
```

**Without Category (Uses MISC)**
```json
{
  "item_name": "Custom Tool Set",
  "item_type": "BOTH"
}
```

#### ✅ Success Response (200 OK)
```json
{
  "sku": "TOOL-PWR-MLWK-R-001",
  "category_code": "TOOL",
  "subcategory_code": "PWR", 
  "product_code": "MLWK",
  "attributes_code": "R",
  "sequence_number": 1,
  "format_description": "Format: CATEGORY-SUBCATEGORY-PRODUCT-ATTRIBUTES-SEQUENCE"
}
```

### 🔄 Bulk SKU Generation

#### 📤 Endpoint
```http
POST /api/master-data/item-master/skus/bulk-generate
Authorization: Bearer <token>
```

#### 📝 Request Example
```http
POST /api/master-data/item-master/skus/bulk-generate
# No request body required
```

#### ✅ Success Response (200 OK)
```json
{
  "total_items": 150,
  "items_with_sku": 142,
  "items_without_sku": 8,
  "skus_generated": 8,
  "failed": 0,
  "results": [
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440000",
      "item_code": "OLD001",
      "generated_sku": "MISC-ITEM-OLD0-R-001",
      "success": true,
      "error": null
    },
    {
      "item_id": "660e8400-e29b-41d4-a716-446655440001", 
      "item_code": "OLD002",
      "generated_sku": "TOOL-HAND-OLD0-S-002",
      "success": true,
      "error": null
    }
  ]
}
```

## Specialized Endpoints

### 🎯 Get Items by Business Type

#### Rental Items Only
```http
GET /api/master-data/item-master/types/rental?active_only=true
```
Returns items where `item_type` is "RENTAL" or "BOTH"

#### Sale Items Only  
```http
GET /api/master-data/item-master/types/sale?active_only=true
```
Returns items where `item_type` is "SALE" or "BOTH"

### 🏷️ Get Items by Category
```http
GET /api/master-data/item-master/category/{category_id}?active_only=true
```

### 🏭 Get Items by Brand
```http
GET /api/master-data/item-master/brand/{brand_id}?active_only=true
```

### 📦 Get Low Stock Items
```http
GET /api/master-data/item-master/low-stock/?active_only=true
```
Returns items where current stock is below `reorder_level`

### 🔍 Get Item by Business Code
```http
GET /api/master-data/item-master/code/{item_code}
```

### 🏷️ Get Item by SKU
```http
GET /api/master-data/item-master/sku/{sku}
```

#### 📝 Example Responses
All specialized endpoints return the same data structure as the main search endpoint.

## Error Handling

### 🚨 HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful GET, PUT operations |
| 201 | Created | Successful POST operations |
| 204 | No Content | Successful DELETE operations |
| 400 | Bad Request | Malformed request syntax |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Item, category, or brand not found |
| 409 | Conflict | Duplicate item code or constraint violation |
| 422 | Unprocessable Entity | Validation errors in request data |
| 500 | Internal Server Error | Unexpected server-side error |

### 📋 Error Response Formats

#### Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "item_name"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "rental_price_per_day"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 0}
    }
  ],
  "status_code": 422
}
```

#### Business Logic Errors (409/422)
```json
{
  "detail": "Rental items must have rental_price_per_day",
  "status_code": 422
}

{
  "detail": "Item with code 'DRILL001' already exists", 
  "status_code": 409
}
```

#### Not Found Errors (404)
```json
{
  "detail": "Item with ID 550e8400-e29b-41d4-a716-446655440000 not found",
  "status_code": 404
}
```

### 🛠️ Common Error Scenarios & Solutions

#### Scenario 1: Creating Rental Item Without Rental Price
```json
// ❌ Request
{
  "item_code": "DRILL001",
  "item_name": "Power Drill",
  "item_type": "RENTAL",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012"
  // ❌ Missing rental_price_per_day
}

// ❌ Response (422)
{
  "detail": "Rental items must have rental_price_per_day"
}

// ✅ Corrected Request
{
  "item_code": "DRILL001", 
  "item_name": "Power Drill",
  "item_type": "RENTAL",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
  "rental_price_per_day": 15.00  // ✅ Added required field
}
```

#### Scenario 2: Invalid Item Type Change
```json
// ❌ Request - Changing RENTAL item to SALE without sale_price
{
  "item_type": "SALE"
  // ❌ Missing sale_price for SALE item
}

// ❌ Response (422)
{
  "detail": "Sale items must have sale_price"
}

// ✅ Corrected Request
{
  "item_type": "SALE",
  "sale_price": 299.99  // ✅ Added required pricing
}
```

## Workflow Examples

### 📝 Workflow 1: Complete Item Creation Process

```typescript
// Step 1: Check if item code is available (optional)
const checkResponse = await fetch(`${API_BASE}/code/${itemCode}`, {
  headers: HEADERS
});
if (checkResponse.status === 200) {
  throw new Error('Item code already exists');
}

// Step 2: Preview SKU generation (optional)
const skuPreview = await fetch(`${API_BASE}/skus/generate`, {
  method: 'POST',
  headers: HEADERS,
  body: JSON.stringify({
    category_id: selectedCategoryId,
    item_name: itemName,
    item_type: itemType
  })
});
const { sku } = await skuPreview.json();
console.log('Generated SKU:', sku);

// Step 3: Create the item
const createResponse = await fetch(`${API_BASE}/`, {
  method: 'POST',
  headers: HEADERS,
  body: JSON.stringify({
    item_code: itemCode,
    item_name: itemName,
    item_type: itemType,
    unit_of_measurement_id: selectedUnitId,
    rental_price_per_day: rentalPricePerDay,
    category_id: selectedCategoryId,
    brand_id: selectedBrandId,
    description: description
  })
});

if (createResponse.ok) {
  const newItem = await createResponse.json();
  console.log('Item created successfully:', newItem.display_name);
  console.log('Generated SKU:', newItem.sku);
} else {
  const error = await createResponse.json();
  console.error('Creation failed:', error.detail);
}
```

### 🔍 Workflow 2: Advanced Search with Pagination

```typescript
interface SearchParams {
  search?: string;
  itemType?: string;
  categoryId?: string;
  brandId?: string;
  page: number;
  pageSize: number;
}

async function searchItems(params: SearchParams) {
  const queryParams = new URLSearchParams({
    skip: String((params.page - 1) * params.pageSize),
    limit: String(params.pageSize),
    ...(params.search && { search: params.search }),
    ...(params.itemType && { item_type: params.itemType }),
    ...(params.categoryId && { category_id: params.categoryId }),
    ...(params.brandId && { brand_id: params.brandId })
  });

  // Get items and count in parallel
  const [itemsResponse, countResponse] = await Promise.all([
    fetch(`${API_BASE}/?${queryParams}`, { headers: HEADERS }),
    fetch(`${API_BASE}/count/total?${queryParams}`, { headers: HEADERS })
  ]);

  const items = await itemsResponse.json();
  const { count } = await countResponse.json();

  return {
    items,
    totalCount: count,
    totalPages: Math.ceil(count / params.pageSize),
    currentPage: params.page,
    hasNextPage: (params.page * params.pageSize) < count
  };
}

// Usage example
const searchResults = await searchItems({
  search: 'drill',
  itemType: 'RENTAL',
  page: 1,
  pageSize: 20
});

console.log(`Found ${searchResults.totalCount} items`);
console.log(`Page ${searchResults.currentPage} of ${searchResults.totalPages}`);
```

### 📝 Workflow 3: Bulk Item Management

```typescript
// Example: Update prices for all power tools
async function updateCategoryPricing(categoryId: string, priceIncrease: number) {
  // Step 1: Get all items in category
  const response = await fetch(`${API_BASE}/category/${categoryId}`, {
    headers: HEADERS
  });
  const items = await response.json();

  // Step 2: Update each item
  const updatePromises = items.map(async (item) => {
    const currentPrice = parseFloat(item.rental_price_per_day || '0');
    const newPrice = currentPrice * (1 + priceIncrease);

    return fetch(`${API_BASE}/${item.id}`, {
      method: 'PUT',
      headers: HEADERS,
      body: JSON.stringify({
        rental_price_per_day: newPrice
      })
    });
  });

  // Step 3: Execute all updates
  const results = await Promise.allSettled(updatePromises);
  
  const successful = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;

  console.log(`Price update complete: ${successful} successful, ${failed} failed`);
}
```

## Frontend Integration Guide

### 🎨 React Hook Example

```typescript
// useItems.ts - Custom hook for item management
import { useState, useEffect } from 'react';

interface UseItemsOptions {
  search?: string;
  itemType?: string;
  categoryId?: string;
  pageSize?: number;
  autoRefresh?: boolean;
}

export function useItems(options: UseItemsOptions = {}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);

  const fetchItems = async (pageNum = 1) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        skip: String((pageNum - 1) * (options.pageSize || 20)),
        limit: String(options.pageSize || 20),
        ...(options.search && { search: options.search }),
        ...(options.itemType && { item_type: options.itemType }),
        ...(options.categoryId && { category_id: options.categoryId })
      });

      const [itemsRes, countRes] = await Promise.all([
        fetch(`/api/master-data/item-master/?${params}`, {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }),
        fetch(`/api/master-data/item-master/count/total?${params}`, {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        })
      ]);

      if (!itemsRes.ok || !countRes.ok) {
        throw new Error('Failed to fetch items');
      }

      const itemsData = await itemsRes.json();
      const countData = await countRes.json();

      setItems(itemsData);
      setTotalCount(countData.count);
      setPage(pageNum);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems(1);
  }, [options.search, options.itemType, options.categoryId]);

  return {
    items,
    loading,
    error,
    totalCount,
    page,
    totalPages: Math.ceil(totalCount / (options.pageSize || 20)),
    fetchItems,
    nextPage: () => fetchItems(page + 1),
    prevPage: () => fetchItems(page - 1),
    refresh: () => fetchItems(page)
  };
}
```

### 🎨 Vue.js Composable Example

```typescript
// useItems.js - Vue 3 composable
import { ref, computed, watch } from 'vue';

export function useItems(options = {}) {
  const items = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const totalCount = ref(0);
  const page = ref(1);

  const totalPages = computed(() => 
    Math.ceil(totalCount.value / (options.pageSize || 20))
  );

  const fetchItems = async (pageNum = 1) => {
    loading.value = true;
    error.value = null;

    try {
      const params = new URLSearchParams({
        skip: String((pageNum - 1) * (options.pageSize || 20)),
        limit: String(options.pageSize || 20),
        ...(options.search && { search: options.search }),
        ...(options.itemType && { item_type: options.itemType }),
        ...(options.categoryId && { category_id: options.categoryId })
      });

      const response = await fetch(`/api/master-data/item-master/?${params}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });

      if (!response.ok) throw new Error('Failed to fetch items');

      const data = await response.json();
      items.value = data;
      page.value = pageNum;
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  };

  // Watch for option changes
  watch(() => [options.search, options.itemType, options.categoryId], 
    () => fetchItems(1), 
    { immediate: true }
  );

  return {
    items: readonly(items),
    loading: readonly(loading),
    error: readonly(error),
    totalCount: readonly(totalCount),
    page: readonly(page),
    totalPages,
    fetchItems,
    nextPage: () => fetchItems(page.value + 1),
    prevPage: () => fetchItems(page.value - 1),
    refresh: () => fetchItems(page.value)
  };
}
```

### 🔧 Error Handling Best Practices

```typescript
// apiClient.ts - Centralized API client with error handling
class ItemMasterAPI {
  private baseURL = '/api/master-data/item-master';
  private headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${this.getToken()}`
  };

  async handleResponse(response: Response) {
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Handle unauthorized - redirect to login
          this.redirectToLogin();
          throw new Error('Authentication required');
        
        case 403:
          throw new Error('Insufficient permissions');
        
        case 404:
          throw new Error('Item not found');
        
        case 409:
          throw new Error(error.detail || 'Conflict - item may already exist');
        
        case 422:
          // Handle validation errors
          if (Array.isArray(error.detail)) {
            const validationErrors = error.detail.map(err => 
              `${err.loc.join('.')}: ${err.msg}`
            ).join(', ');
            throw new Error(`Validation errors: ${validationErrors}`);
          } else {
            throw new Error(error.detail || 'Validation error');
          }
        
        default:
          throw new Error('An unexpected error occurred');
      }
    }

    return response.json();
  }

  async createItem(itemData: ItemCreate) {
    const response = await fetch(`${this.baseURL}/`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(itemData)
    });

    return this.handleResponse(response);
  }

  async searchItems(params: SearchParams) {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`${this.baseURL}/?${queryString}`, {
      headers: this.headers
    });

    return this.handleResponse(response);
  }

  // ... other methods
}
```

### 🔄 State Management Integration

```typescript
// Redux Toolkit slice example
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';

export const fetchItems = createAsyncThunk(
  'items/fetchItems',
  async (params: SearchParams, { rejectWithValue }) => {
    try {
      const api = new ItemMasterAPI();
      return await api.searchItems(params);
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const createItem = createAsyncThunk(
  'items/createItem',
  async (itemData: ItemCreate, { rejectWithValue }) => {
    try {
      const api = new ItemMasterAPI();
      return await api.createItem(itemData);
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const itemsSlice = createSlice({
  name: 'items',
  initialState: {
    items: [],
    loading: false,
    error: null,
    totalCount: 0,
    currentPage: 1
  },
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setPage: (state, action) => {
      state.currentPage = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchItems.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchItems.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.totalCount = action.payload.totalCount;
      })
      .addCase(fetchItems.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

export default itemsSlice.reducer;
```

---

## 🎯 Quick Reference Summary

### Essential Endpoints
- **POST** `/` - Create item
- **GET** `/` - Search & list items  
- **GET** `/{id}` - Get item by ID
- **PUT** `/{id}` - Update item
- **DELETE** `/{id}` - Delete item
- **GET** `/count/total` - Count items
- **POST** `/skus/generate` - Preview SKU

### Key Features
- ✅ Smart search across multiple fields
- ✅ Flexible filtering by type, status, brand, category
- ✅ Automatic SKU generation with business rules
- ✅ Comprehensive validation and error handling  
- ✅ Pagination and performance optimization
- ✅ Soft delete with data preservation

### Business Rules
- Item codes must be unique
- Rental items require rental pricing
- Sale items require sale pricing  
- Both items require both pricing types
- SKU format: CATEGORY-SUBCATEGORY-PRODUCT-TYPE-SEQUENCE

This guide provides everything needed to successfully integrate with the Item Master API. For additional support, refer to the OpenAPI documentation at `/docs` for interactive testing.