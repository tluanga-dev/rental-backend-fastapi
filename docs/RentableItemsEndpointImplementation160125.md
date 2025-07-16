# Rentable Items Endpoint Implementation Guide for Frontend Developers

**Document Version:** 1.0  
**Date:** January 16, 2025  
**Author:** Backend Development Team  

## Overview

The Rentable Items endpoint provides frontend developers with a comprehensive API to retrieve items that are available for rent along with their current stock positions across all locations. This endpoint is specifically designed to support rental transaction forms and inventory management interfaces.

## Base URL

All requests should be made to: `/api/transactions/rentable-items`

## Authentication

All requests require authentication. Include the Bearer token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoint Details

### Get Rentable Items with Availability

**Method:** `GET`  
**URL:** `/api/transactions/rentable-items`

**Description:** Returns a list of items that are marked as rentable and have available quantity > 0 in at least one location.

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location_id` | UUID | No | null | Filter items by specific location |
| `category_id` | UUID | No | null | Filter items by category |
| `skip` | Integer | No | 0 | Number of items to skip (pagination) |
| `limit` | Integer | No | 100 | Maximum items to return (1-1000) |

## Response Format

### Success Response (200 OK)

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "sku": "REN-PROJ-001",
    "item_name": "HD Projector 1080p",
    "rental_rate_per_period": 500.00,
    "rental_period": "1",
    "security_deposit": 1000.00,
    "total_available_quantity": 5,
    "brand": {
      "id": "brand-uuid-123",
      "name": "Sony"
    },
    "category": {
      "id": "category-uuid-456",
      "name": "Electronics"
    },
    "unit_of_measurement": {
      "id": "uom-uuid-789",
      "name": "Unit",
      "code": "UN"
    },
    "location_availability": [
      {
        "location_id": "location-uuid-111",
        "location_name": "Main Warehouse",
        "available_quantity": 3
      },
      {
        "location_id": "location-uuid-222",
        "location_name": "Branch Office",
        "available_quantity": 2
      }
    ]
  }
]
```

### Response Schema

#### Root Array Item

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique item identifier |
| `sku` | String | Stock Keeping Unit code |
| `item_name` | String | Human-readable item name |
| `rental_rate_per_period` | Decimal | Rental cost per period |
| `rental_period` | String | Duration of rental period (e.g., "1" for 1 day) |
| `security_deposit` | Decimal | Required security deposit amount |
| `total_available_quantity` | Float | Total available quantity across all locations |
| `brand` | Object/null | Brand information (can be null) |
| `category` | Object/null | Category information (can be null) |
| `unit_of_measurement` | Object | Unit of measurement details |
| `location_availability` | Array | Availability breakdown by location |

#### Brand Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Brand identifier |
| `name` | String | Brand name |

#### Category Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Category identifier |
| `name` | String | Category name |

#### Unit of Measurement Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unit identifier |
| `name` | String | Unit name (e.g., "Unit", "Piece") |
| `code` | String/null | Unit abbreviation (e.g., "UN", "PC") |

#### Location Availability Object

| Field | Type | Description |
|-------|------|-------------|
| `location_id` | UUID | Location identifier |
| `location_name` | String | Human-readable location name |
| `available_quantity` | Float | Available quantity at this location |

## Example API Calls

### 1. Get All Rentable Items

```bash
curl -X GET "https://api.example.com/api/transactions/rentable-items" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### 2. Get Items with Pagination

```bash
curl -X GET "https://api.example.com/api/transactions/rentable-items?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### 3. Filter by Location

```bash
curl -X GET "https://api.example.com/api/transactions/rentable-items?location_id=123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### 4. Filter by Category

```bash
curl -X GET "https://api.example.com/api/transactions/rentable-items?category_id=456e7890-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### 5. Combined Filters

```bash
curl -X GET "https://api.example.com/api/transactions/rentable-items?location_id=123e4567-e89b-12d3-a456-426614174000&category_id=456e7890-e89b-12d3-a456-426614174000&skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## Frontend Implementation Examples

### React/TypeScript Example

```typescript
// Types
interface LocationAvailability {
  location_id: string;
  location_name: string;
  available_quantity: number;
}

interface Brand {
  id: string;
  name: string;
}

interface Category {
  id: string;
  name: string;
}

interface UnitOfMeasurement {
  id: string;
  name: string;
  code?: string;
}

interface RentableItem {
  id: string;
  sku: string;
  item_name: string;
  rental_rate_per_period: number;
  rental_period: string;
  security_deposit: number;
  total_available_quantity: number;
  brand?: Brand;
  category?: Category;
  unit_of_measurement: UnitOfMeasurement;
  location_availability: LocationAvailability[];
}

// API Service
class RentableItemsService {
  private baseURL = '/api/transactions/rentable-items';
  
  async getRentableItems(params: {
    location_id?: string;
    category_id?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<RentableItem[]> {
    const searchParams = new URLSearchParams();
    
    if (params.location_id) searchParams.append('location_id', params.location_id);
    if (params.category_id) searchParams.append('category_id', params.category_id);
    if (params.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) searchParams.append('limit', params.limit.toString());
    
    const url = `${this.baseURL}${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
}

// React Hook
const useRentableItems = (filters: {
  location_id?: string;
  category_id?: string;
  skip?: number;
  limit?: number;
} = {}) => {
  const [items, setItems] = useState<RentableItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const service = new RentableItemsService();
  
  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await service.getRentableItems(filters);
        setItems(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    fetchItems();
  }, [filters.location_id, filters.category_id, filters.skip, filters.limit]);
  
  return { items, loading, error };
};

// React Component
const RentableItemsList: React.FC = () => {
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 10;
  
  const { items, loading, error } = useRentableItems({
    location_id: selectedLocation || undefined,
    category_id: selectedCategory || undefined,
    skip: currentPage * pageSize,
    limit: pageSize
  });
  
  if (loading) return <div>Loading rentable items...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <h2>Available Items for Rent</h2>
      
      {/* Filters */}
      <div className="filters">
        <select 
          value={selectedLocation} 
          onChange={(e) => setSelectedLocation(e.target.value)}
        >
          <option value="">All Locations</option>
          {/* Add location options */}
        </select>
        
        <select 
          value={selectedCategory} 
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          {/* Add category options */}
        </select>
      </div>
      
      {/* Items List */}
      <div className="items-grid">
        {items.map((item) => (
          <div key={item.id} className="item-card">
            <h3>{item.item_name}</h3>
            <p>SKU: {item.sku}</p>
            <p>Rental Rate: ${item.rental_rate_per_period}/{item.rental_period} period(s)</p>
            <p>Security Deposit: ${item.security_deposit}</p>
            <p>Total Available: {item.total_available_quantity}</p>
            
            {item.brand && <p>Brand: {item.brand.name}</p>}
            {item.category && <p>Category: {item.category.name}</p>}
            
            <div className="location-availability">
              <h4>Available Locations:</h4>
              {item.location_availability.map((location) => (
                <div key={location.location_id} className="location-item">
                  <span>{location.location_name}: </span>
                  <span>{location.available_quantity} available</span>
                </div>
              ))}
            </div>
            
            <button 
              onClick={() => handleRentItem(item)}
              disabled={item.total_available_quantity === 0}
            >
              Rent This Item
            </button>
          </div>
        ))}
      </div>
      
      {/* Pagination */}
      <div className="pagination">
        <button 
          onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
          disabled={currentPage === 0}
        >
          Previous
        </button>
        <span>Page {currentPage + 1}</span>
        <button 
          onClick={() => setCurrentPage(prev => prev + 1)}
          disabled={items.length < pageSize}
        >
          Next
        </button>
      </div>
    </div>
  );
};
```

### Vue.js Example

```vue
<template>
  <div class="rentable-items">
    <h2>Available Items for Rent</h2>
    
    <!-- Filters -->
    <div class="filters">
      <select v-model="selectedLocation" @change="fetchItems">
        <option value="">All Locations</option>
        <!-- Add location options -->
      </select>
      
      <select v-model="selectedCategory" @change="fetchItems">
        <option value="">All Categories</option>
        <!-- Add category options -->
      </select>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading">Loading...</div>
    
    <!-- Error State -->
    <div v-if="error" class="error">{{ error }}</div>
    
    <!-- Items List -->
    <div v-else class="items-grid">
      <div v-for="item in items" :key="item.id" class="item-card">
        <h3>{{ item.item_name }}</h3>
        <p>SKU: {{ item.sku }}</p>
        <p>Rental Rate: ${{ item.rental_rate_per_period }}/{{ item.rental_period }} period(s)</p>
        <p>Security Deposit: ${{ item.security_deposit }}</p>
        <p>Total Available: {{ item.total_available_quantity }}</p>
        
        <p v-if="item.brand">Brand: {{ item.brand.name }}</p>
        <p v-if="item.category">Category: {{ item.category.name }}</p>
        
        <div class="location-availability">
          <h4>Available Locations:</h4>
          <div v-for="location in item.location_availability" :key="location.location_id">
            {{ location.location_name }}: {{ location.available_quantity }} available
          </div>
        </div>
        
        <button 
          @click="handleRentItem(item)"
          :disabled="item.total_available_quantity === 0"
        >
          Rent This Item
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';

export default {
  name: 'RentableItemsList',
  setup() {
    const items = ref([]);
    const loading = ref(false);
    const error = ref(null);
    const selectedLocation = ref('');
    const selectedCategory = ref('');
    
    const fetchItems = async () => {
      try {
        loading.value = true;
        error.value = null;
        
        const params = new URLSearchParams();
        if (selectedLocation.value) params.append('location_id', selectedLocation.value);
        if (selectedCategory.value) params.append('category_id', selectedCategory.value);
        
        const response = await fetch(`/api/transactions/rentable-items?${params}`, {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        items.value = await response.json();
      } catch (err) {
        error.value = err.message;
      } finally {
        loading.value = false;
      }
    };
    
    const handleRentItem = (item) => {
      // Handle rent item logic
      console.log('Renting item:', item);
    };
    
    onMounted(fetchItems);
    
    return {
      items,
      loading,
      error,
      selectedLocation,
      selectedCategory,
      fetchItems,
      handleRentItem
    };
  }
};
</script>
```

## Error Handling

### Common HTTP Status Codes

| Status Code | Description | Action |
|-------------|-------------|---------|
| 200 | Success | Process the returned data |
| 401 | Unauthorized | Redirect to login or refresh token |
| 403 | Forbidden | Show permission error |
| 422 | Validation Error | Display validation messages |
| 500 | Server Error | Show generic error message |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Error Handling Example

```typescript
try {
  const items = await service.getRentableItems(filters);
  // Handle success
} catch (error) {
  if (error.status === 401) {
    // Handle authentication error
    redirectToLogin();
  } else if (error.status === 403) {
    // Handle permission error
    showPermissionError();
  } else {
    // Handle other errors
    showGenericError(error.message);
  }
}
```

## Performance Considerations

1. **Pagination**: Use `skip` and `limit` parameters for large datasets
2. **Filtering**: Apply filters server-side rather than client-side
3. **Caching**: Consider caching responses for frequently accessed data
4. **Debouncing**: Debounce filter inputs to avoid excessive API calls

## Best Practices

1. **Always include error handling** in your API calls
2. **Use TypeScript interfaces** for better type safety
3. **Implement loading states** to improve user experience
4. **Cache responses** when appropriate to reduce API calls
5. **Validate user inputs** before sending to the API
6. **Handle edge cases** like empty results or network failures
7. **Use pagination** for better performance with large datasets
8. **Implement proper authentication** token management

## Use Cases

### 1. Rental Form Item Selection
Use this endpoint to populate a dropdown or grid of available items when creating a new rental transaction.

### 2. Inventory Dashboard
Display current stock levels and availability across locations for rental items.

### 3. Quick Rental Check
Allow users to quickly check if a specific item is available for rent at their preferred location.

### 4. Category-Based Browsing
Enable users to browse rentable items by category (e.g., Electronics, Furniture, etc.).

### 5. Location-Specific Availability
Show items available at a specific store or warehouse location.

## Integration with Rental Forms

When integrating with rental transaction forms, you can:

1. **Pre-populate item selection**: Use the API to show available items
2. **Real-time availability**: Check stock before finalizing rental
3. **Location-based filtering**: Show items available at user's preferred location
4. **Quantity validation**: Ensure requested quantity doesn't exceed available stock

```typescript
// Example integration with rental form
const validateRentalForm = async (formData: RentalFormData) => {
  const availableItems = await rentableItemsService.getRentableItems({
    location_id: formData.location_id
  });
  
  const selectedItem = availableItems.find(item => item.id === formData.item_id);
  
  if (!selectedItem) {
    throw new Error('Item is not available for rent');
  }
  
  if (formData.quantity > selectedItem.total_available_quantity) {
    throw new Error('Requested quantity exceeds available stock');
  }
  
  return true;
};
```

## Support

For questions or issues with the Rentable Items API, please contact the backend development team or refer to the API documentation at `/docs` when the application is running.

---

**Last Updated:** January 16, 2025  
**API Version:** 2.0.0  
**Endpoint:** `/api/transactions/rentable-items`