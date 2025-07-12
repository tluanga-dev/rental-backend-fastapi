# Item Master API - LLM Quick Reference

## Context
This API manages items in a rental management system. Items can be rented, sold, or both. Each item has a unique code and an auto-generated SKU.

## Base Configuration
- Base URL: `http://localhost:8000/api/master-data/item-master`
- Authentication: Bearer token required in headers
- Content-Type: application/json

## Critical Enums
```
ItemType: RENTAL | SALE | BOTH
ItemStatus: ACTIVE | INACTIVE | DISCONTINUED
```

## Essential Endpoints

### 1. Create Item - POST /
Creates new item with auto-generated SKU.

**Minimal Rental Item:**
```json
{
  "item_code": "PWR001",
  "item_name": "DeWalt Drill",
  "item_type": "RENTAL""rental_price_per_day": 15.00
}
```

**Minimal Sale Item:**
```json
{
  "item_code": "ACC001",
  "item_name": "Safety Helmet",
  "item_type": "SALE""sale_price": 29.99
}
```

**Full Example with All Common Fields:**
```json
{
  "item_code": "GEN001",
  "item_name": "Honda Generator EU2200i",
  "item_type": "RENTAL""rental_price_per_day": 75.00,
  "rental_price_per_week": 350.00,
  "rental_price_per_month": 1200.00,
  "security_deposit": 200.00,
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "brand_id": "987e6543-e21b-12d3-a456-426614174000",
  "description": "Quiet portable generator",
  "minimum_rental_days": "1",
  "maximum_rental_days": "90"
}
```

**Response includes:** id, sku (auto-generated), created_at, display_name

### 2. Search & List Items - GET /
Supports simultaneous search and filtering.

**Parameters:**
- `search`: Text search in name/code/sku/description
- `item_type`: Filter by RENTAL/SALE/BOTH
- `item_status`: Filter by ACTIVE/INACTIVE/DISCONTINUED
- `category_id`: Filter by category UUID
- `brand_id`: Filter by brand UUID
- `skip`: Offset for pagination (default: 0)
- `limit`: Items per page (default: 100, max: 1000)
- `active_only`: Exclude soft-deleted (default: true)

**Examples:**
```
GET /?search=drill
GET /?item_type=RENTAL&limit=20
GET /?search=honda&category_id=123e4567-e89b-12d3-a456-426614174000
GET /?skip=20&limit=20  # Page 2
```

### 3. Get Single Item
```
GET /{item_id}          # By UUID
GET /code/{item_code}   # By item code
GET /sku/{sku}          # By SKU
```

### 4. Update Item - PUT /{item_id}
All fields optional - only send what needs updating.

```json
{
  "rental_price_per_day": 18.00,
  "description": "Updated description"
}
```

### 5. Delete Item - DELETE /{item_id}
Soft delete (sets is_active=false). Returns 204 on success.

### 6. Specialized Queries
```
GET /types/rental       # Only rental items (RENTAL or BOTH)
GET /types/sale         # Only sale items (SALE or BOTH)
GET /category/{uuid}    # Items in specific category
GET /brand/{uuid}       # Items from specific brand
GET /count/total        # Count with same filters as search
```

### 7. SKU Operations
**Preview SKU without creating item:**
```json
POST /skus/generate
{
  "category_id": "123e4567-e89b-12d3-a456-426614174000",
  "item_name": "Milwaukee Impact Driver",
  "item_type": "RENTAL"
}
```

**Response:**
```json
{
  "sku": "TOOL-PWR-MLWK-R-001",
  "category_code": "TOOL",
  "subcategory_code": "PWR",
  "product_code": "MLWK",
  "attributes_code": "R",
  "sequence_number": 1
}
```

## Response Formats

### List Response (Simplified)
```json
{
  "id": "uuid",
  "item_code": "PWR001",
  "item_name": "DeWalt Drill",
  "item_type": "RENTAL",
  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",
  "item_status": "ACTIVE",
  "rental_price_per_day": "15.00",
  "display_name": "DeWalt Drill (PWR001)"
}
```

### Full Item Response
Includes all fields from create request plus:
- `id`: UUID
- `sku`: Auto-generated
- `created_at`, `updated_at`: ISO timestamps
- `is_active`: Boolean
- `display_name`: "Name (CODE)" format

## Validation Rules
1. **Item codes** must be unique
2. **RENTAL items** must have rental_price_per_day
3. **SALE items** must have sale_price
4. **BOTH items** must have both prices
5. All prices must be >= 0
6. SKU format: CATEGORY-SUBCATEGORY-PRODUCT-TYPE-SEQUENCE

## Common Error Patterns
- `404`: Item/category/brand not found
- `409`: Item code already exists
- `422`: Validation failed (missing required field, invalid enum)

## Quick Integration Examples

### JavaScript/TypeScript
```javascript
// Search items
const items = await fetch('/api/master-data/item-master/?search=drill&item_type=RENTAL', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Create item
const newItem = await fetch('/api/master-data/item-master/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    item_code: 'NEW001',
    item_name: 'New Item',
    item_type: 'RENTAL',
    rental_price_per_day: 10
  })
}).then(r => r.json());
```

### Python
```python
import requests

# Search items
response = requests.get(
    'http://localhost:8000/api/master-data/item-master/',
    params={'search': 'drill', 'item_type': 'RENTAL'},
    headers={'Authorization': f'Bearer {token}'}
)
items = response.json()

# Create item
new_item = requests.post(
    'http://localhost:8000/api/master-data/item-master/',
    json={
        'item_code': 'NEW001',
        'item_name': 'New Item',
        'item_type': 'RENTAL',
        'rental_price_per_day': 10
    },
    headers={'Authorization': f'Bearer {token}'}
).json()
```

## Key Implementation Notes
1. Always include Bearer token in Authorization header
2. Use pagination for large datasets (default limit: 100)
3. Search is case-insensitive and searches multiple fields
4. SKUs are auto-generated - never manually set
5. Soft delete preserves data - use is_active flag
6. Prices are returned as strings to preserve decimal precision
7. UUIDs are strings in JSON
8. All datetime fields use ISO 8601 format