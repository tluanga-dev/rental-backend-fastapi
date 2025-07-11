# Frontend Implementation Prompt: Units of Measurement Feature

## Overview
Implement a complete Units of Measurement management interface in the frontend application. This feature allows users to create, read, update, and delete units of measurement that will be used throughout the inventory system.

## API Base URL
```
BASE_URL: http://localhost:8000/api/master-data/units-of-measurement
```

## Authentication
All endpoints require JWT Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Feature Requirements

### 1. Units List Page
Create a paginated table view showing all units of measurement with the following features:

#### API Endpoint
```
GET /api/master-data/units-of-measurement/
```

#### Query Parameters
```typescript
interface UnitsListParams {
  page?: number;          // Default: 1
  page_size?: number;     // Default: 20, Max: 100
  name?: string;          // Filter by name (partial match)
  abbreviation?: string;  // Filter by abbreviation (partial match)
  is_active?: boolean;    // Filter by active status
  search?: string;        // Search in name and abbreviation
  sort_field?: string;    // Default: "name", Options: "name", "abbreviation", "created_at", "updated_at", "is_active"
  sort_direction?: string; // Default: "asc", Options: "asc", "desc"
  include_inactive?: boolean; // Default: false
}
```

#### Response
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Kilogram",
      "abbreviation": "kg",
      "is_active": true,
      "display_name": "Kilogram (kg)"
    },
    {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "name": "Pieces",
      "abbreviation": "pcs",
      "is_active": true,
      "display_name": "Pieces (pcs)"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20,
  "total_pages": 2,
  "has_next": true,
  "has_previous": false
}
```

#### UI Requirements
- Display units in a table with columns: Name, Abbreviation, Status, Actions
- Add search bar for real-time search
- Add filters for active/inactive status
- Implement pagination controls
- Add sort functionality on Name and Abbreviation columns
- Include "Create New Unit" button
- Show active/inactive badge for status
- Add action buttons: View, Edit, Delete, Activate/Deactivate

### 2. Create Unit Form
Implement a form to create new units of measurement.

#### API Endpoint
```
POST /api/master-data/units-of-measurement/
```

#### Request Payload
```json
{
  "name": "Meter",
  "abbreviation": "m",
  "description": "Standard unit of length measurement"
}
```

#### Response (201 Created)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Meter",
  "abbreviation": "m",
  "description": "Standard unit of length measurement",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "created_by": "user-123",
  "updated_by": "user-123",
  "display_name": "Meter (m)",
  "item_count": 0
}
```

#### Form Validation
- Name: Required, max 50 characters, must be unique
- Abbreviation: Optional, max 10 characters, must be unique if provided
- Description: Optional, max 500 characters

#### Error Responses
```json
// 409 Conflict - Duplicate name or abbreviation
{
  "detail": "Unit with name 'Meter' already exists"
}

// 400 Bad Request - Validation error
{
  "detail": "Unit name cannot be empty"
}
```

### 3. View/Edit Unit Details
Implement a detail view with edit capability.

#### Get Unit by ID
```
GET /api/master-data/units-of-measurement/{unit_id}
```

#### Response
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Kilogram",
  "abbreviation": "kg",
  "description": "Standard unit of mass",
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T11:30:00Z",
  "created_by": "user-123",
  "updated_by": "user-456",
  "display_name": "Kilogram (kg)",
  "item_count": 42
}
```

#### Update Unit
```
PUT /api/master-data/units-of-measurement/{unit_id}
```

#### Update Payload
```json
{
  "name": "Kilogram",
  "abbreviation": "KG",
  "description": "Updated description for kilogram",
  "is_active": true
}
```

### 4. Delete Unit
Implement soft delete functionality.

#### API Endpoint
```
DELETE /api/master-data/units-of-measurement/{unit_id}
```

#### Response
- 204 No Content on success
- 404 Not Found if unit doesn't exist
- 400 Bad Request if unit has associated items

### 5. Search Units
Implement a search feature for quick unit lookup.

#### API Endpoint
```
GET /api/master-data/units-of-measurement/search/?q={searchTerm}&limit=10&include_inactive=false
```

#### Response
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

### 6. Bulk Operations
Implement bulk activate/deactivate functionality.

#### API Endpoint
```
POST /api/master-data/units-of-measurement/bulk-operation
```

#### Request Payload
```json
{
  "unit_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ],
  "operation": "deactivate"  // Options: "activate", "deactivate"
}
```

#### Response
```json
{
  "success_count": 2,
  "failure_count": 0,
  "errors": []
}
```

### 7. Import/Export Features

#### Export Units
```
GET /api/master-data/units-of-measurement/export/?include_inactive=true
```

Response: Array of all unit objects with complete details

#### Import Units
```
POST /api/master-data/units-of-measurement/import/
```

#### Import Payload
```json
[
  {
    "name": "Liter",
    "abbreviation": "L",
    "description": "Unit of volume",
    "is_active": true
  },
  {
    "name": "Gram",
    "abbreviation": "g",
    "description": "Unit of mass",
    "is_active": true
  }
]
```

#### Import Response
```json
{
  "total_processed": 2,
  "successful_imports": 2,
  "failed_imports": 0,
  "skipped_imports": 0,
  "errors": []
}
```

### 8. Statistics Dashboard
Display unit usage statistics.

#### API Endpoint
```
GET /api/master-data/units-of-measurement/stats/
```

#### Response
```json
{
  "total_units": 25,
  "active_units": 20,
  "inactive_units": 5,
  "units_with_items": 15,
  "units_without_items": 10,
  "most_used_units": [
    {
      "name": "Pieces",
      "item_count": 150
    },
    {
      "name": "Kilogram",
      "item_count": 89
    }
  ]
}
```

## Additional Features to Implement

### 1. Quick Actions
- **Activate Unit**: `POST /api/master-data/units-of-measurement/{unit_id}/activate`
- **Deactivate Unit**: `POST /api/master-data/units-of-measurement/{unit_id}/deactivate`

### 2. Lookup by Name/Abbreviation
- **By Name**: `GET /api/master-data/units-of-measurement/by-name/{unit_name}`
- **By Abbreviation**: `GET /api/master-data/units-of-measurement/by-abbreviation/{unit_abbreviation}`

### 3. Active Units Dropdown
For use in other forms (e.g., inventory items):
```
GET /api/master-data/units-of-measurement/active/
```

Returns array of unit summaries for dropdown/select components.

## UI/UX Guidelines

1. **List View**
   - Use data tables with sorting and filtering
   - Implement debounced search (300ms delay)
   - Show loading states during API calls
   - Display success/error toast notifications

2. **Forms**
   - Use modal dialogs or dedicated pages
   - Implement client-side validation matching backend rules
   - Show field-level error messages
   - Disable submit button during API calls

3. **Confirmations**
   - Require confirmation for delete operations
   - Show warning if unit has associated items
   - Require confirmation for bulk operations

4. **Status Indicators**
   - Active: Green badge/chip
   - Inactive: Red/gray badge/chip
   - Show item count where applicable

5. **Responsive Design**
   - Mobile-friendly table with horizontal scroll
   - Collapsible filters on mobile
   - Touch-friendly action buttons

## Error Handling

Handle these common error responses:
- **400**: Validation errors - show field-specific messages
- **401**: Unauthorized - redirect to login
- **404**: Not found - show appropriate message
- **409**: Conflict - show duplicate error message
- **500**: Server error - show generic error message

## State Management

Recommended state structure:
```typescript
interface UnitsState {
  units: Unit[];
  selectedUnit: Unit | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  filters: {
    search: string;
    isActive: boolean | null;
    sortField: string;
    sortDirection: 'asc' | 'desc';
  };
  statistics: UnitStats | null;
}
```

## Performance Considerations

1. Implement pagination to handle large datasets
2. Use debounced search to reduce API calls
3. Cache active units list for dropdowns
4. Implement optimistic updates for better UX
5. Use lazy loading for statistics

## Testing Requirements

1. Test CRUD operations
2. Test validation rules
3. Test error scenarios
4. Test pagination and filtering
5. Test bulk operations
6. Test import/export functionality
7. Test responsive behavior

This implementation should provide a complete, user-friendly interface for managing units of measurement in the rental management system.