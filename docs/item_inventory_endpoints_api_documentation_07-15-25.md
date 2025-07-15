# Item Inventory Endpoints API Documentation

**Document Version:** 1.0  
**Created:** July 15, 2025  
**Last Updated:** July 15, 2025  
**Author:** System Development Team

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL](#base-url)
4. [Endpoints](#endpoints)
   - [Items Inventory Overview](#items-inventory-overview)
   - [Item Inventory Detailed](#item-inventory-detailed)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)
9. [Integration Guide](#integration-guide)
10. [Changelog](#changelog)

## Overview

The Item Inventory Endpoints provide comprehensive access to inventory information for rental management systems. These endpoints offer two complementary views:

- **Overview Endpoint**: Optimized for table displays and dashboards with aggregated data
- **Detailed Endpoint**: Complete item inventory information for detailed views and reports

### Key Features

- **Performance Optimized**: Efficient database queries with proper indexing
- **Flexible Filtering**: Multiple filter options for precise data retrieval
- **Pagination Support**: Handle large datasets efficiently
- **Real-time Data**: Current inventory status with accurate stock levels
- **Comprehensive Data**: Complete item lifecycle information

## Authentication

All endpoints require authentication using JWT Bearer tokens.

```http
Authorization: Bearer <your-jwt-token>
```

**Required Permissions:**
- `inventory:read` - Read inventory data
- `items:read` - Read item master data

## Base URL

```
https://your-domain.com/api/inventory
```

## Endpoints

### Items Inventory Overview

**GET** `/items/overview`

Retrieve inventory overview for multiple items, optimized for table displays and dashboards.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip (pagination) |
| `limit` | integer | 100 | Maximum records to return (1-1000) |
| `item_status` | string | null | Filter by item status (`ACTIVE`, `INACTIVE`, `DISCONTINUED`) |
| `brand_id` | UUID | null | Filter by brand ID |
| `category_id` | UUID | null | Filter by category ID |
| `stock_status` | string | null | Filter by stock status (`IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`) |
| `is_rentable` | boolean | null | Filter by rentable items |
| `is_saleable` | boolean | null | Filter by saleable items |
| `search` | string | null | Search by item name or SKU |
| `sort_by` | string | `item_name` | Sort field (`item_name`, `sku`, `created_at`, `total_units`, `stock_status`) |
| `sort_order` | string | `asc` | Sort order (`asc`, `desc`) |

#### Response Format

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "sku": "CAT-BRD-001",
    "item_name": "Professional Drill",
    "item_status": "ACTIVE",
    "brand_name": "DeWalt",
    "category_name": "Power Tools",
    "rental_rate_per_period": 25.00,
    "sale_price": 299.99,
    "is_rentable": true,
    "is_saleable": false,
    "total_units": 15,
    "units_by_status": {
      "available": 10,
      "rented": 4,
      "sold": 0,
      "maintenance": 1,
      "damaged": 0,
      "retired": 0
    },
    "total_quantity_on_hand": 15.00,
    "total_quantity_available": 10.00,
    "total_quantity_on_rent": 4.00,
    "stock_status": "IN_STOCK",
    "reorder_point": 5,
    "is_low_stock": false,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-07-15T14:20:00Z"
  }
]
```

#### Status Codes

- **200 OK**: Success
- **400 Bad Request**: Invalid query parameters
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **422 Unprocessable Entity**: Validation errors

### Item Inventory Detailed

**GET** `/items/{item_id}/detailed`

Retrieve comprehensive inventory information for a single item.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | UUID | Yes | Unique identifier of the item |

#### Response Format

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "sku": "CAT-BRD-001",
  "item_name": "Professional Drill",
  "item_status": "ACTIVE",
  "brand_id": "987fcdeb-51a2-43d7-8902-123456789abc",
  "brand_name": "DeWalt",
  "category_id": "456e7890-1234-5678-9abc-def012345678",
  "category_name": "Power Tools",
  "unit_of_measurement_id": "789abcde-5678-90ab-cdef-123456789012",
  "unit_of_measurement_name": "Each",
  "description": "High-performance cordless drill with variable speed",
  "specifications": "18V, 2.0Ah battery, 13mm chuck",
  "model_number": "DCD771C2",
  "serial_number_required": true,
  "warranty_period_days": "365",
  "rental_rate_per_period": 25.00,
  "rental_period": "1",
  "sale_price": 299.99,
  "purchase_price": 180.00,
  "security_deposit": 50.00,
  "is_rentable": true,
  "is_saleable": false,
  "total_units": 15,
  "units_by_status": {
    "available": 10,
    "rented": 4,
    "sold": 0,
    "maintenance": 1,
    "damaged": 0,
    "retired": 0
  },
  "inventory_units": [
    {
      "id": "unit-123e4567-e89b-12d3-a456-426614174001",
      "unit_code": "DRL-001",
      "serial_number": "SN123456789",
      "status": "AVAILABLE",
      "condition": "EXCELLENT",
      "location_id": "loc-456e7890-1234-5678-9abc-def012345678",
      "location_name": "Main Warehouse",
      "purchase_date": "2025-01-15T00:00:00Z",
      "purchase_price": 180.00,
      "warranty_expiry": "2026-01-15T00:00:00Z",
      "last_maintenance_date": "2025-06-15T00:00:00Z",
      "next_maintenance_date": "2025-12-15T00:00:00Z",
      "notes": "Regular maintenance completed",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-07-15T14:20:00Z"
    }
  ],
  "stock_by_location": [
    {
      "location_id": "loc-456e7890-1234-5678-9abc-def012345678",
      "location_name": "Main Warehouse",
      "quantity_on_hand": 12.00,
      "quantity_available": 8.00,
      "quantity_on_rent": 4.00
    },
    {
      "location_id": "loc-789abcde-5678-90ab-cdef-123456789012",
      "location_name": "Branch Office",
      "quantity_on_hand": 3.00,
      "quantity_available": 2.00,
      "quantity_on_rent": 0.00
    }
  ],
  "total_quantity_on_hand": 15.00,
  "total_quantity_available": 10.00,
  "total_quantity_on_rent": 4.00,
  "reorder_point": 5,
  "stock_status": "IN_STOCK",
  "is_low_stock": false,
  "recent_movements": [
    {
      "id": "mov-123e4567-e89b-12d3-a456-426614174002",
      "movement_type": "RENTAL_OUT",
      "quantity_change": -2.00,
      "reason": "Rented out 2 units",
      "reference_type": "TRANSACTION",
      "reference_id": "TXN-20250715-001",
      "location_name": "Main Warehouse",
      "created_at": "2025-07-15T09:30:00Z",
      "created_by_name": "john.doe@company.com"
    }
  ],
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-07-15T14:20:00Z",
  "created_by": "user-123e4567-e89b-12d3-a456-426614174003",
  "updated_by": "user-456e7890-1234-5678-9abc-def012345678"
}
```

#### Status Codes

- **200 OK**: Success
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Item not found
- **422 Unprocessable Entity**: Validation errors

## Data Models

### ItemInventoryOverview

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique item identifier |
| `sku` | string | Stock Keeping Unit |
| `item_name` | string | Item name |
| `item_status` | enum | Item status (`ACTIVE`, `INACTIVE`, `DISCONTINUED`) |
| `brand_name` | string | Brand name (nullable) |
| `category_name` | string | Category name (nullable) |
| `rental_rate_per_period` | decimal | Rental rate per period (nullable) |
| `sale_price` | decimal | Sale price (nullable) |
| `is_rentable` | boolean | Whether item can be rented |
| `is_saleable` | boolean | Whether item can be sold |
| `total_units` | integer | Total inventory units |
| `units_by_status` | object | Unit counts by status |
| `total_quantity_on_hand` | decimal | Total quantity on hand |
| `total_quantity_available` | decimal | Total available quantity |
| `total_quantity_on_rent` | decimal | Total quantity on rent |
| `stock_status` | enum | Stock status (`IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`) |
| `reorder_point` | integer | Reorder point threshold |
| `is_low_stock` | boolean | Whether stock is below reorder point |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### UnitsByStatus

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `available` | integer | 0 | Available units |
| `rented` | integer | 0 | Rented units |
| `sold` | integer | 0 | Sold units |
| `maintenance` | integer | 0 | Units in maintenance |
| `damaged` | integer | 0 | Damaged units |
| `retired` | integer | 0 | Retired units |

### InventoryUnitDetail

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unit identifier |
| `unit_code` | string | Unit code |
| `serial_number` | string | Serial number (nullable) |
| `status` | enum | Unit status |
| `condition` | enum | Unit condition |
| `location_id` | UUID | Location identifier |
| `location_name` | string | Location name |
| `purchase_date` | datetime | Purchase date (nullable) |
| `purchase_price` | decimal | Purchase price |
| `warranty_expiry` | datetime | Warranty expiry (nullable) |
| `last_maintenance_date` | datetime | Last maintenance date (nullable) |
| `next_maintenance_date` | datetime | Next maintenance date (nullable) |
| `notes` | string | Additional notes (nullable) |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### LocationStockInfo

| Field | Type | Description |
|-------|------|-------------|
| `location_id` | UUID | Location identifier |
| `location_name` | string | Location name |
| `quantity_on_hand` | decimal | Quantity on hand |
| `quantity_available` | decimal | Available quantity |
| `quantity_on_rent` | decimal | Quantity on rent |

### RecentMovement

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Movement identifier |
| `movement_type` | enum | Movement type |
| `quantity_change` | decimal | Quantity change |
| `reason` | string | Movement reason |
| `reference_type` | enum | Reference type |
| `reference_id` | string | Reference ID (nullable) |
| `location_name` | string | Location name |
| `created_at` | datetime | Creation timestamp |
| `created_by_name` | string | Created by user name (nullable) |

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-07-15T14:20:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `ITEM_NOT_FOUND` | Requested item not found |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

## Rate Limiting

- **Overview Endpoint**: 1000 requests per hour per user
- **Detailed Endpoint**: 500 requests per hour per user

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time (Unix timestamp)

## Examples

### Basic Overview Request

```bash
curl -X GET "https://your-domain.com/api/inventory/items/overview?limit=10&sort_by=item_name" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json"
```

### Filtered Overview Request

```bash
curl -X GET "https://your-domain.com/api/inventory/items/overview?stock_status=LOW_STOCK&is_rentable=true&limit=50" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json"
```

### Search Request

```bash
curl -X GET "https://your-domain.com/api/inventory/items/overview?search=drill&sort_by=stock_status&sort_order=desc" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json"
```

### Detailed Item Request

```bash
curl -X GET "https://your-domain.com/api/inventory/items/123e4567-e89b-12d3-a456-426614174000/detailed" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json"
```

### Pagination Example

```bash
# Get first page
curl -X GET "https://your-domain.com/api/inventory/items/overview?skip=0&limit=25" \
  -H "Authorization: Bearer your-jwt-token"

# Get second page
curl -X GET "https://your-domain.com/api/inventory/items/overview?skip=25&limit=25" \
  -H "Authorization: Bearer your-jwt-token"
```

## Integration Guide

### Frontend Integration

#### React/JavaScript Example

```javascript
// Fetch inventory overview
const fetchInventoryOverview = async (params = {}) => {
  const queryParams = new URLSearchParams(params).toString();
  const response = await fetch(`/api/inventory/items/overview?${queryParams}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Fetch detailed item
const fetchItemDetails = async (itemId) => {
  const response = await fetch(`/api/inventory/items/${itemId}/detailed`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Usage example
const loadInventoryData = async () => {
  try {
    const overview = await fetchInventoryOverview({
      limit: 50,
      sort_by: 'item_name',
      stock_status: 'IN_STOCK'
    });
    console.log('Inventory overview:', overview);
  } catch (error) {
    console.error('Error loading inventory:', error);
  }
};
```

#### Table Component Example

```javascript
const InventoryTable = () => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    skip: 0,
    limit: 50,
    sort_by: 'item_name',
    sort_order: 'asc'
  });

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const data = await fetchInventoryOverview(filters);
        setInventory(data);
      } catch (error) {
        console.error('Error loading inventory:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [filters]);

  const handleSort = (field) => {
    setFilters(prev => ({
      ...prev,
      sort_by: field,
      sort_order: prev.sort_by === field && prev.sort_order === 'asc' ? 'desc' : 'asc'
    }));
  };

  if (loading) return <div>Loading...</div>;

  return (
    <table>
      <thead>
        <tr>
          <th onClick={() => handleSort('item_name')}>Item Name</th>
          <th onClick={() => handleSort('sku')}>SKU</th>
          <th onClick={() => handleSort('stock_status')}>Stock Status</th>
          <th onClick={() => handleSort('total_units')}>Total Units</th>
          <th>Available</th>
          <th>On Rent</th>
        </tr>
      </thead>
      <tbody>
        {inventory.map(item => (
          <tr key={item.id}>
            <td>{item.item_name}</td>
            <td>{item.sku}</td>
            <td>{item.stock_status}</td>
            <td>{item.total_units}</td>
            <td>{item.units_by_status.available}</td>
            <td>{item.units_by_status.rented}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

### Backend Integration

#### Python Example

```python
import requests
from typing import List, Dict, Optional

class InventoryClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_inventory_overview(self, **params) -> List[Dict]:
        """Get inventory overview with optional filtering."""
        response = requests.get(
            f"{self.base_url}/api/inventory/items/overview",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_item_details(self, item_id: str) -> Dict:
        """Get detailed information for a specific item."""
        response = requests.get(
            f"{self.base_url}/api/inventory/items/{item_id}/detailed",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_low_stock_items(self) -> List[Dict]:
        """Get items with low stock."""
        return self.get_inventory_overview(stock_status='LOW_STOCK')
    
    def search_items(self, query: str, limit: int = 50) -> List[Dict]:
        """Search items by name or SKU."""
        return self.get_inventory_overview(search=query, limit=limit)

# Usage
client = InventoryClient('https://your-domain.com', 'your-jwt-token')
low_stock_items = client.get_low_stock_items()
```

### Common Integration Patterns

#### 1. Dashboard Widget

```javascript
const StockStatusWidget = () => {
  const [stats, setStats] = useState({
    in_stock: 0,
    low_stock: 0,
    out_of_stock: 0
  });

  useEffect(() => {
    const loadStats = async () => {
      const [inStock, lowStock, outOfStock] = await Promise.all([
        fetchInventoryOverview({ stock_status: 'IN_STOCK', limit: 1 }),
        fetchInventoryOverview({ stock_status: 'LOW_STOCK', limit: 1000 }),
        fetchInventoryOverview({ stock_status: 'OUT_OF_STOCK', limit: 1000 })
      ]);
      
      setStats({
        in_stock: inStock.length,
        low_stock: lowStock.length,
        out_of_stock: outOfStock.length
      });
    };
    loadStats();
  }, []);

  return (
    <div className="stock-status-widget">
      <div className="stat">
        <h3>In Stock</h3>
        <p>{stats.in_stock}</p>
      </div>
      <div className="stat">
        <h3>Low Stock</h3>
        <p>{stats.low_stock}</p>
      </div>
      <div className="stat">
        <h3>Out of Stock</h3>
        <p>{stats.out_of_stock}</p>
      </div>
    </div>
  );
};
```

#### 2. Reorder Alert System

```javascript
const ReorderAlerts = () => {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const checkReorderAlerts = async () => {
      const lowStockItems = await fetchInventoryOverview({
        stock_status: 'LOW_STOCK',
        limit: 100
      });
      
      const reorderAlerts = lowStockItems.filter(item => item.is_low_stock);
      setAlerts(reorderAlerts);
    };
    
    checkReorderAlerts();
    const interval = setInterval(checkReorderAlerts, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="reorder-alerts">
      {alerts.map(item => (
        <div key={item.id} className="alert">
          <strong>{item.item_name}</strong> is below reorder point ({item.reorder_point})
        </div>
      ))}
    </div>
  );
};
```

#### 3. Inventory Export

```javascript
const exportInventoryData = async (format = 'csv') => {
  const allItems = [];
  let skip = 0;
  const limit = 1000;
  
  while (true) {
    const batch = await fetchInventoryOverview({ skip, limit });
    if (batch.length === 0) break;
    
    allItems.push(...batch);
    skip += limit;
  }
  
  if (format === 'csv') {
    const csv = convertToCSV(allItems);
    downloadFile(csv, 'inventory-export.csv', 'text/csv');
  } else if (format === 'json') {
    const json = JSON.stringify(allItems, null, 2);
    downloadFile(json, 'inventory-export.json', 'application/json');
  }
};
```

## Best Practices

### Performance Optimization

1. **Use Overview Endpoint for Lists**: Always use the overview endpoint for table displays and lists
2. **Implement Pagination**: Don't load all items at once; use pagination
3. **Cache Data**: Cache overview data for short periods (1-2 minutes)
4. **Use Appropriate Filters**: Apply filters server-side rather than client-side

### Error Handling

1. **Handle Network Errors**: Implement retry logic for network failures
2. **Validate Responses**: Check response status codes and structure
3. **User Feedback**: Show meaningful error messages to users
4. **Logging**: Log errors for debugging purposes

### Security

1. **Token Management**: Securely store and refresh JWT tokens
2. **Input Validation**: Validate all user inputs before sending requests
3. **Rate Limiting**: Respect rate limits and implement exponential backoff
4. **HTTPS Only**: Always use HTTPS in production

## Testing

### Unit Tests

```javascript
describe('Inventory API', () => {
  test('should fetch inventory overview', async () => {
    const mockResponse = [
      { id: '123', item_name: 'Test Item', total_units: 10 }
    ];
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });
    
    const result = await fetchInventoryOverview();
    expect(result).toEqual(mockResponse);
  });
  
  test('should handle errors gracefully', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' })
    });
    
    await expect(fetchInventoryOverview()).rejects.toThrow();
  });
});
```

### Integration Tests

```bash
# Test overview endpoint
curl -X GET "http://localhost:8000/api/inventory/items/overview?limit=5" \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json"

# Test detailed endpoint
curl -X GET "http://localhost:8000/api/inventory/items/123e4567-e89b-12d3-a456-426614174000/detailed" \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json"
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check JWT token validity and expiration
2. **403 Forbidden**: Verify user has required permissions
3. **404 Not Found**: Confirm item ID exists in the system
4. **422 Validation Error**: Check query parameter format and values
5. **500 Internal Server Error**: Check server logs for detailed error information

### Performance Issues

1. **Slow Response Times**: 
   - Check database indexes
   - Optimize query parameters
   - Use pagination for large datasets

2. **Memory Usage**: 
   - Reduce limit parameter
   - Use streaming for large exports
   - Implement client-side caching

### Debugging Tips

1. **Enable Logging**: Set appropriate log levels for debugging
2. **Check Network**: Verify network connectivity and DNS resolution
3. **Validate Tokens**: Ensure JWT tokens are properly formatted
4. **Test Locally**: Use local development environment for debugging

## Changelog

### Version 1.0 (July 15, 2025)

**Added:**
- Initial release of Item Inventory Endpoints
- Items inventory overview endpoint with filtering and pagination
- Item inventory detailed endpoint with comprehensive data
- Complete API documentation and examples
- Authentication and authorization support
- Error handling and rate limiting
- Integration examples for frontend and backend

**Features:**
- Real-time inventory status tracking
- Multi-location stock level support
- Inventory unit lifecycle management
- Stock movement history
- Reorder point alerts
- Performance-optimized queries

**Supported Platforms:**
- Web browsers (Chrome, Firefox, Safari, Edge)
- Mobile applications (iOS, Android)
- Server-side integrations (Python, Node.js, Java)
- REST API clients

---

## Support

For technical support and questions:
- **Email**: api-support@company.com
- **Documentation**: https://docs.company.com/api
- **Issues**: https://github.com/company/rental-api/issues
- **Slack**: #api-support

## License

This API documentation is proprietary and confidential. Unauthorized use is prohibited.

---

*This documentation was generated on July 15, 2025. For the most up-to-date information, please refer to the interactive API documentation at https://your-domain.com/docs*