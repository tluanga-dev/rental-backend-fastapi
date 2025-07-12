# Item Master API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Base Information](#base-information)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
5. [Error Handling](#error-handling)
6. [Examples and Use Cases](#examples-and-use-cases)

## Overview

The Item Master API provides comprehensive functionality for managing items in the rental management system. This API supports creating, reading, updating, and deleting items with advanced search, filtering, and SKU generation capabilities.

### Key Features
- Full CRUD operations for items
- Advanced search and filtering
- Automatic SKU generation
- Support for rental, sale, and dual-purpose items
- Relationship management with brands, categories, and suppliers
- Inventory tracking integration
- Pagination and count endpoints

## Base Information

### Base URL
```
http://localhost:8000/api/master-data/item-master
```

### Authentication
All endpoints require JWT Bearer token authentication.

### Headers
```json
{
  "Authorization": "Bearer <your-jwt-token>",
  "Content-Type": "application/json"
}
```

## Data Models

### Item Types (Enum)
```typescript
enum ItemType {
  RENTAL = "RENTAL",    // Item available for rent only
  SALE = "SALE",        // Item available for sale only
  BOTH = "BOTH"         // Item available for both rent and sale
}
```

### Item Status (Enum)
```typescript
enum ItemStatus {
  ACTIVE = "ACTIVE",              // Item is active and available
  INACTIVE = "INACTIVE",          // Item is temporarily unavailable
  DISCONTINUED = "DISCONTINUED"   // Item is permanently discontinued
}
```

### ItemCreate (Request Schema)
```typescript
interface ItemCreate {
  // Required fields
  item_code: string;              // Unique item code (max 50 chars)
  item_name: string;              // Item name (max 200 chars)
  item_type: ItemType;            // Type of item
  
  // Optional fields
  item_status?: ItemStatus;       // Default: ACTIVE
  brand_id?: string;              // UUID of associated brand
  category_id?: string;           // UUID of associated category
  unit_of_measurement_id?: string; // UUID of unit of measurement// Pricing fields (required based on item_type)
  rental_price_per_day?: number;  // Required if item_type is RENTAL or BOTH
  rental_price_per_week?: number; // Weekly rental price
  rental_price_per_month?: number; // Monthly rental price
  sale_price?: number;            // Required if item_type is SALE or BOTH
  
  // Rental configuration
  minimum_rental_days?: string;   // Minimum rental period in days
  maximum_rental_days?: string;   // Maximum rental period in days
  security_deposit?: number;      // Security deposit amount
  
  // Item details
  description?: string;           // Item description (max 1000 chars)
  specifications?: string;        // Technical specifications
  model_number?: string;          // Model number (max 100 chars)
  serial_number_required?: boolean; // Whether serial number tracking is required
  warranty_period_days?: string;  // Warranty period in days
  
  // Inventory management
  reorder_level?: string;         // Minimum stock level for reordering
  reorder_quantity?: string;      // Quantity to reorder
}
```

### ItemUpdate (Request Schema)
```typescript
interface ItemUpdate {
  // All fields are optional
  item_name?: string;
  item_type?: ItemType;
  item_status?: ItemStatus;
  brand_id?: string;
  category_id?: string;
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

### ItemResponse (Response Schema)
```typescript
interface ItemResponse {
  // System fields
  id: string;                     // UUID
  created_at: string;             // ISO 8601 datetime
  updated_at: string;             // ISO 8601 datetime
  is_active: boolean;             // Soft delete flag
  
  // Item fields
  item_code: string;
  sku: string;                    // Auto-generated SKU
  item_name: string;
  item_type: string;
  item_status: string;
  
  // Optional fields (null if not set)
  brand_id?: string | null;
  category_id?: string | null;
  unit_of_measurement_id?: string | null;rental_price_per_day?: string | null;
  rental_price_per_week?: string | null;
  rental_price_per_month?: string | null;
  sale_price?: string | null;
  minimum_rental_days?: string | null;
  maximum_rental_days?: string | null;
  security_deposit?: string | null;
  description?: string | null;
  specifications?: string | null;
  model_number?: string | null;
  serial_number_required?: boolean;
  warranty_period_days?: string | null;
  reorder_level?: string | null;
  reorder_quantity?: string | null;
  
  // Computed fields
  display_name: string;           // Format: "Item Name (ITEM_CODE)"
}
```

### ItemListResponse (Response Schema for List Operations)
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

### SKUGenerationRequest
```typescript
interface SKUGenerationRequest {
  category_id?: string;           // UUID of category
  item_name: string;              // Item name for SKU generation
  item_type: string;              // ItemType enum value
}
```

### SKUGenerationResponse
```typescript
interface SKUGenerationResponse {
  sku: string;                    // Generated SKU
  category_code: string;          // Category part of SKU
  subcategory_code: string;       // Subcategory part of SKU
  product_code: string;           // Product abbreviation
  attributes_code: string;        // R/S/B based on item type
  sequence_number: number;        // Sequential number
  format_description: string;     // Human-readable format explanation
}
```

## API Endpoints

### 1. Create Item
**Endpoint:** `POST /`

**Description:** Creates a new item with automatic SKU generation based on category, item name, and type.

**Request Body:**
```json
{
  "item_code": "PWR001",
  "item_name": "DeWalt 20V Max Cordless Drill",
  "item_type": "RENTAL""rental_price_per_day": 15.00,
  "rental_price_per_week": 75.00,
  "rental_price_per_month": 250.00,
  "security_deposit": 50.00,
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "brand_id": "987e6543-e21b-12d3-a456-426614174000",
  "description": "Professional-grade cordless drill with brushless motor",
  "specifications": "Voltage: 20V, Chuck Size: 1/2\", Max Torque: 820 in-lbs",
  "model_number": "DCD999B",
  "minimum_rental_days": "1",
  "maximum_rental_days": "30"
}
```

**Success Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_active": true,
  "item_code": "PWR001",
  "sku": "TOOL-PWR-DWLT-R-001",
  "item_name": "DeWalt 20V Max Cordless Drill",
  "item_type": "RENTAL",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
  "item_status": "ACTIVE",
  "rental_price_per_day": "15.00",
  "rental_price_per_week": "75.00",
  "rental_price_per_month": "250.00",
  "sale_price": null,
  "security_deposit": "50.00",
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "brand_id": "987e6543-e21b-12d3-a456-426614174000",
  "description": "Professional-grade cordless drill with brushless motor",
  "specifications": "Voltage: 20V, Chuck Size: 1/2\", Max Torque: 820 in-lbs",
  "model_number": "DCD999B",
  "minimum_rental_days": "1",
  "maximum_rental_days": "30",
  "display_name": "DeWalt 20V Max Cordless Drill (PWR001)"
}
```

**Error Responses:**
- `409 Conflict`: Item code already exists
- `422 Unprocessable Entity`: Validation error (e.g., missing required pricing for item type)

### 2. Get All Items with Search and Filters
**Endpoint:** `GET /`

**Description:** Retrieves a paginated list of items with optional search and filtering capabilities.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| skip | integer | No | 0 | Number of items to skip for pagination |
| limit | integer | No | 100 | Maximum items to return (1-1000) |
| search | string | No | null | Search term for item name, code, SKU, or description |
| item_type | ItemType | No | null | Filter by item type |
| item_status | ItemStatus | No | null | Filter by item status |
| brand_id | UUID | No | null | Filter by brand ID |
| category_id | UUID | No | null | Filter by category ID |
| active_only | boolean | No | true | Show only active (non-deleted) items |

**Example Request:**
```
GET /api/master-data/item-master/?search=drill&item_type=RENTAL&limit=10
```

**Success Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "item_code": "PWR001",
    "item_name": "DeWalt 20V Max Cordless Drill",
    "item_type": "RENTAL",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
    "item_status": "ACTIVE",
    "rental_price_per_day": "15.00",
    "sale_price": null,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "display_name": "DeWalt 20V Max Cordless Drill (PWR001)"
  },
  {
    "id": "660e8500-e29b-41d4-a716-446655440001",
    "item_code": "PWR002",
    "item_name": "Makita 18V Hammer Drill",
    "item_type": "RENTAL",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
    "item_status": "ACTIVE",
    "rental_price_per_day": "18.00",
    "sale_price": null,
    "is_active": true,
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z",
    "display_name": "Makita 18V Hammer Drill (PWR002)"
  }
]
```

### 3. Get Item by ID
**Endpoint:** `GET /{item_id}`

**Description:** Retrieves a single item by its UUID.

**Path Parameters:**
- `item_id` (UUID): The unique identifier of the item

**Example Request:**
```
GET /api/master-data/item-master/550e8400-e29b-41d4-a716-446655440000
```

**Success Response:** `200 OK`
(Returns full ItemResponse object as shown in Create Item response)

**Error Response:**
- `404 Not Found`: Item not found

### 4. Get Item by Code
**Endpoint:** `GET /code/{item_code}`

**Description:** Retrieves a single item by its unique item code.

**Path Parameters:**
- `item_code` (string): The unique item code

**Example Request:**
```
GET /api/master-data/item-master/code/PWR001
```

**Success Response:** `200 OK`
(Returns full ItemResponse object)

### 5. Get Item by SKU
**Endpoint:** `GET /sku/{sku}`

**Description:** Retrieves a single item by its SKU.

**Path Parameters:**
- `sku` (string): The Stock Keeping Unit

**Example Request:**
```
GET /api/master-data/item-master/sku/TOOL-PWR-DWLT-R-001
```

**Success Response:** `200 OK`
(Returns full ItemResponse object)

### 6. Search Items
**Endpoint:** `GET /search/{search_term}`

**Description:** Search items by name, code, or description.

**Path Parameters:**
- `search_term` (string): The search term

**Query Parameters:**
- `skip` (integer): Pagination offset
- `limit` (integer): Page size
- `active_only` (boolean): Filter active items only

**Example Request:**
```
GET /api/master-data/item-master/search/dewalt?limit=5
```

**Success Response:** `200 OK`
(Returns array of ItemListResponse objects)

### 7. Update Item
**Endpoint:** `PUT /{item_id}`

**Description:** Updates an existing item. All fields are optional - only provided fields will be updated.

**Path Parameters:**
- `item_id` (UUID): The item to update

**Request Body:**
```json
{
  "rental_price_per_day": 17.50,
  "rental_price_per_week": 85.00,
  "description": "Updated description with new features highlighted"
}
```

**Success Response:** `200 OK`
(Returns updated ItemResponse object)

**Error Responses:**
- `404 Not Found`: Item not found
- `422 Unprocessable Entity`: Validation error

### 8. Delete Item
**Endpoint:** `DELETE /{item_id}`

**Description:** Soft deletes an item (sets is_active to false).

**Path Parameters:**
- `item_id` (UUID): The item to delete

**Success Response:** `204 No Content`

**Error Response:**
- `404 Not Found`: Item not found

### 9. Get Rental Items
**Endpoint:** `GET /types/rental`

**Description:** Retrieves all items available for rental (item_type = RENTAL or BOTH).

**Query Parameters:**
- `active_only` (boolean): Show only active items

**Success Response:** `200 OK`
(Returns array of ItemListResponse objects)

### 10. Get Sale Items
**Endpoint:** `GET /types/sale`

**Description:** Retrieves all items available for sale (item_type = SALE or BOTH).

**Query Parameters:**
- `active_only` (boolean): Show only active items

**Success Response:** `200 OK`
(Returns array of ItemListResponse objects)

### 11. Get Items by Category
**Endpoint:** `GET /category/{category_id}`

**Description:** Retrieves all items in a specific category.

**Path Parameters:**
- `category_id` (UUID): The category ID

**Query Parameters:**
- `active_only` (boolean): Show only active items

**Success Response:** `200 OK`
(Returns array of ItemListResponse objects)

### 12. Get Items by Brand
**Endpoint:** `GET /brand/{brand_id}`

**Description:** Retrieves all items for a specific brand.

**Path Parameters:**
- `brand_id` (UUID): The brand ID

**Query Parameters:**
- `active_only` (boolean): Show only active items

**Success Response:** `200 OK`
(Returns array of ItemListResponse objects)

### 13. Get Low Stock Items
**Endpoint:** `GET /low-stock/`

**Description:** Retrieves items that need reordering based on their reorder level.

**Query Parameters:**
- `active_only` (boolean): Show only active items

**Success Response:** `200 OK`
(Returns array of ItemListResponse objects)

### 14. Generate SKU Preview
**Endpoint:** `POST /skus/generate`

**Description:** Generates a preview of what SKU would be created for given parameters without creating an item.

**Request Body:**
```json
{
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "item_name": "Milwaukee Impact Driver",
  "item_type": "RENTAL"
}
```

**Success Response:** `200 OK`
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

### 15. Bulk Generate SKUs
**Endpoint:** `POST /skus/bulk-generate`

**Description:** Generates SKUs for all existing items that don't have them.

**Success Response:** `200 OK`
```json
{
  "total_items": 50,
  "items_with_sku": 45,
  "items_without_sku": 5,
  "skus_generated": 5,
  "failed": 0,
  "results": [
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440000",
      "item_code": "OLD001",
      "generated_sku": "MISC-ITEM-OLD0-R-001",
      "success": true
    }
  ]
}
```

### 16. Count Items
**Endpoint:** `GET /count/total`

**Description:** Returns the total count of items matching the given filters.

**Query Parameters:**
- `search` (string): Search term
- `item_type` (ItemType): Filter by type
- `item_status` (ItemStatus): Filter by status
- `brand_id` (UUID): Filter by brand
- `category_id` (UUID): Filter by category
- `active_only` (boolean): Count only active items

**Example Request:**
```
GET /api/master-data/item-master/count/total?item_type=RENTAL&active_only=true
```

**Success Response:** `200 OK`
```json
{
  "count": 42
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes
| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Item, brand, or category not found |
| 409 | Conflict | Item code already exists |
| 422 | Unprocessable Entity | Validation errors |
| 500 | Internal Server Error | Server-side error |

### Validation Error Examples

**Missing Required Field:**
```json
{
  "detail": [
    {
      "loc": ["body", "item_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Invalid Enum Value:**
```json
{
  "detail": [
    {
      "loc": ["body", "item_type"],
      "msg": "value is not a valid enumeration member; permitted: 'RENTAL', 'SALE', 'BOTH'",
      "type": "type_error.enum"
    }
  ]
}
```

**Business Rule Violation:**
```json
{
  "detail": "Rental items must have rental_price_per_day"
}
```

## Examples and Use Cases

### Example 1: Creating a Rental Item
```bash
curl -X POST "http://localhost:8000/api/master-data/item-master/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "GEN001",
    "item_name": "Honda EU2200i Generator",
    "item_type": "RENTAL""rental_price_per_day": 75.00,
    "rental_price_per_week": 350.00,
    "rental_price_per_month": 1200.00,
    "security_deposit": 200.00,
    "category_id": "456e7890-e89b-12d3-a456-426614174000",
    "brand_id": "789e0123-e21b-12d3-a456-426614174000",
    "description": "Quiet, lightweight, and fuel-efficient generator",
    "specifications": "2200W max, 1800W rated, 48dB noise level",
    "minimum_rental_days": "1",
    "maximum_rental_days": "90"
  }'
```

### Example 2: Creating a Sale Item
```bash
curl -X POST "http://localhost:8000/api/master-data/item-master/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "ACC001",
    "item_name": "Safety Helmet - Yellow",
    "item_type": "SALE""sale_price": 29.99,
    "category_id": "567e8901-e89b-12d3-a456-426614174000",
    "description": "ANSI Z89.1 compliant hard hat",
    "reorder_level": "10",
    "reorder_quantity": "50"
  }'
```

### Example 3: Creating a Dual-Purpose Item (Rent & Sale)
```bash
curl -X POST "http://localhost:8000/api/master-data/item-master/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "LAD001",
    "item_name": "Werner 6ft Fiberglass Ladder",
    "item_type": "BOTH""rental_price_per_day": 15.00,
    "rental_price_per_week": 60.00,
    "sale_price": 249.99,
    "category_id": "678e9012-e89b-12d3-a456-426614174000",
    "description": "Type IA duty rating, 300 lb capacity",
    "model_number": "FS106"
  }'
```

### Example 4: Advanced Search with Multiple Filters
```bash
# Search for active rental items containing "drill" in the power tools category
curl -X GET "http://localhost:8000/api/master-data/item-master/?\
search=drill&\
item_type=RENTAL&\
category_id=123e4567-e89b-12d3-a456-426614174000&\
active_only=true&\
limit=20" \
  -H "Authorization: Bearer <token>"
```

### Example 5: Updating Item Pricing
```bash
curl -X PUT "http://localhost:8000/api/master-data/item-master/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "rental_price_per_day": 18.00,
    "rental_price_per_week": 90.00,
    "rental_price_per_month": 300.00,
    "security_deposit": 75.00
  }'
```

### Example 6: Pagination Example
```bash
# Get page 2 of items (items 21-40)
curl -X GET "http://localhost:8000/api/master-data/item-master/?skip=20&limit=20" \
  -H "Authorization: Bearer <token>"
```

## Business Rules and Validation

### Item Code Rules
- Must be unique across all items
- Maximum 50 characters
- Cannot be empty
- Recommended format: Category prefix + sequential number (e.g., "PWR001", "GEN002")

### SKU Generation Rules
- Format: `{CATEGORY}-{SUBCATEGORY}-{PRODUCT}-{ATTRIBUTES}-{SEQUENCE}`
- Category: 3-4 character code from category hierarchy
- Subcategory: 3-4 character code from subcategory
- Product: 3-4 character abbreviation from item name
- Attributes: Single character (R=Rental, S=Sale, B=Both)
- Sequence: 3-digit sequential number (001, 002, etc.)
- Example: `TOOL-PWR-DWLT-R-001` (Tools > Power Tools > DeWalt > Rental > #001)

### Pricing Rules
- All prices must be non-negative
- Rental items (type=RENTAL) must have `rental_price_per_day`
- Sale items (type=SALE) must have `sale_price`
- Dual-purpose items (type=BOTH) must have both `rental_price_per_day` and `sale_price`
- Weekly rental price should typically be 4-5x daily rate
- Monthly rental price should typically be 15-20x daily rate

### Status Transitions
- New items default to ACTIVE status
- ACTIVE → INACTIVE: Temporary unavailability
- ACTIVE/INACTIVE → DISCONTINUED: Permanent removal from catalog
- DISCONTINUED items cannot be reactivated

## Performance Considerations

### Pagination
- Default page size: 100 items
- Maximum page size: 1000 items
- Always use pagination for large result sets
- Use `skip` and `limit` parameters efficiently

### Search Optimization
- Search is case-insensitive
- Searches across: item_name, item_code, sku, description
- Use specific filters (category, brand) to narrow results
- Combine search with filters for best performance

### Caching Recommendations
- Cache category and brand lookups (change infrequently)
- Cache item lists with short TTL (5-10 minutes)
- Don't cache individual item details (prices change frequently)

## Integration Best Practices

### Frontend Integration
1. **Error Handling**: Always handle 404, 422, and 409 errors gracefully
2. **Loading States**: Show loading indicators during API calls
3. **Debouncing**: Debounce search inputs (300-500ms recommended)
4. **Pagination**: Implement infinite scroll or traditional pagination
5. **Caching**: Cache search results and filters client-side

### SKU Generation Flow
1. User selects category (provides category_id)
2. User enters item name
3. User selects item type
4. Call SKU preview endpoint to show generated SKU
5. Submit create item request (SKU generated server-side)

### Search Implementation
```typescript
// Example: Debounced search with filters
async function searchItems(params: {
  search?: string;
  itemType?: ItemType;
  categoryId?: string;
  brandId?: string;
  page: number;
  pageSize: number;
}) {
  const queryParams = new URLSearchParams({
    skip: String((params.page - 1) * params.pageSize),
    limit: String(params.pageSize),
    ...(params.search && { search: params.search }),
    ...(params.itemType && { item_type: params.itemType }),
    ...(params.categoryId && { category_id: params.categoryId }),
    ...(params.brandId && { brand_id: params.brandId })
  });

  const response = await fetch(
    `/api/master-data/item-master/?${queryParams}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}
```

### Batch Operations
For bulk operations (e.g., importing items):
1. Use the single create endpoint in a loop
2. Implement retry logic for failed items
3. Show progress to users
4. Consider implementing a bulk import endpoint if needed

## Migration Guide

### From Legacy System
If migrating from an older system:
1. Map old item codes to new format
2. Generate SKUs for existing items using bulk endpoint
3. Validate all required fields based on item type
4. Update related systems with new item IDs

### API Version Changes
This API follows semantic versioning. Breaking changes will result in a new major version with migration period.