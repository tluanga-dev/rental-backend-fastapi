# System Settings API Documentation

**Document Version**: 1.0  
**Date**: 18/01/25  
**API Version**: v1  
**Base URL**: `/api/system`

---

## Overview

The System Settings API provides endpoints for managing application configuration settings. These settings control various aspects of the application including business rules, system behavior, and scheduled tasks.

### Authentication
All system settings endpoints require authentication. Users must have appropriate permissions to view or modify system settings.

---

## API Endpoints

### 1. Get All Settings

Retrieve all system settings with optional filtering.

**Endpoint:** `GET /api/system/settings`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category (GENERAL, BUSINESS, FINANCIAL, RENTAL, SYSTEM) |
| `include_system` | boolean | No | Include system settings (default: true) |

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "setting_key": "rental_status_check_enabled",
    "setting_name": "Rental Status Check Enabled",
    "setting_type": "BOOLEAN",
    "setting_category": "SYSTEM",
    "setting_value": "true",
    "default_value": "true",
    "description": "Enable automated rental status checking",
    "is_system": true,
    "is_sensitive": false,
    "validation_rules": null,
    "display_order": "4",
    "is_active": true,
    "created_at": "2025-01-18T00:00:00Z",
    "updated_at": "2025-01-18T00:00:00Z"
  }
]
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Server error

---

### 2. Get Setting by Key

Retrieve a specific system setting by its key.

**Endpoint:** `GET /api/system/settings/{setting_key}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `setting_key` | string | Yes | The unique key of the setting |

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "setting_key": "rental_status_check_time",
  "setting_name": "Rental Status Check Time",
  "setting_type": "STRING",
  "setting_category": "SYSTEM",
  "setting_value": "00:00",
  "default_value": "00:00",
  "description": "Time to run daily rental status check (HH:MM format)",
  "is_system": true,
  "is_sensitive": false,
  "validation_rules": null,
  "display_order": "5",
  "is_active": true,
  "created_at": "2025-01-18T00:00:00Z",
  "updated_at": "2025-01-18T00:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Setting not found
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Server error

---

### 3. Get Setting Value Only

Retrieve only the value of a specific setting.

**Endpoint:** `GET /api/system/settings/{setting_key}/value`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `setting_key` | string | Yes | The unique key of the setting |

**Response:** `200 OK`
```json
{
  "setting_key": "rental_status_log_retention_days",
  "value": "365"
}
```

**Error Responses:**
- `404 Not Found` - Setting not found
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Server error

---

### 4. Update Setting

Update the value of a system setting.

**Endpoint:** `PUT /api/system/settings/{setting_key}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `setting_key` | string | Yes | The unique key of the setting |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `updated_by` | UUID | Yes | User ID making the update |

**Request Body:**
```json
{
  "setting_value": "true"
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "setting_key": "rental_status_check_enabled",
  "setting_name": "Rental Status Check Enabled",
  "setting_type": "BOOLEAN",
  "setting_category": "SYSTEM",
  "setting_value": "true",
  "default_value": "true",
  "description": "Enable automated rental status checking",
  "is_system": true,
  "is_sensitive": false,
  "validation_rules": null,
  "display_order": "4",
  "is_active": true,
  "created_at": "2025-01-18T00:00:00Z",
  "updated_at": "2025-01-18T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Setting not found
- `400 Bad Request` - Invalid value or validation failed
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - User lacks permission to modify system settings
- `500 Internal Server Error` - Server error

---

### 5. Reset Setting to Default

Reset a system setting to its default value.

**Endpoint:** `POST /api/system/settings/{setting_key}/reset`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `setting_key` | string | Yes | The unique key of the setting |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `updated_by` | UUID | Yes | User ID making the reset |

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "setting_key": "rental_status_check_time",
  "setting_name": "Rental Status Check Time",
  "setting_type": "STRING",
  "setting_category": "SYSTEM",
  "setting_value": "00:00",
  "default_value": "00:00",
  "description": "Time to run daily rental status check (HH:MM format)",
  "is_system": true,
  "is_sensitive": false,
  "validation_rules": null,
  "display_order": "5",
  "is_active": true,
  "created_at": "2025-01-18T00:00:00Z",
  "updated_at": "2025-01-18T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Setting not found
- `400 Bad Request` - Setting cannot be modified
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - User lacks permission
- `500 Internal Server Error` - Server error

---

## Rental Status Related Settings

The following system settings specifically control the rental status feature:

### 1. rental_status_check_enabled
- **Type**: BOOLEAN
- **Category**: SYSTEM
- **Default**: "true"
- **Description**: Enable automated rental status checking
- **Values**: "true" | "false"
- **Example Update**:
  ```json
  PUT /api/system/settings/rental_status_check_enabled?updated_by=user-uuid
  {
    "setting_value": "false"
  }
  ```

### 2. rental_status_check_time
- **Type**: STRING
- **Category**: SYSTEM
- **Default**: "00:00"
- **Description**: Time to run daily rental status check (HH:MM format)
- **Format**: 24-hour time format (HH:MM)
- **Example Update**:
  ```json
  PUT /api/system/settings/rental_status_check_time?updated_by=user-uuid
  {
    "setting_value": "02:30"
  }
  ```

### 3. rental_status_log_retention_days
- **Type**: INTEGER
- **Category**: SYSTEM
- **Default**: "365"
- **Description**: Number of days to retain rental status change logs
- **Min Value**: 30
- **Max Value**: 3650 (10 years)
- **Example Update**:
  ```json
  PUT /api/system/settings/rental_status_log_retention_days?updated_by=user-uuid
  {
    "setting_value": "180"
  }
  ```

### 4. task_scheduler_timezone
- **Type**: STRING
- **Category**: SYSTEM
- **Default**: "UTC"
- **Description**: Timezone for scheduled tasks
- **Valid Values**: IANA timezone identifiers (e.g., "UTC", "America/New_York", "Europe/London")
- **Example Update**:
  ```json
  PUT /api/system/settings/task_scheduler_timezone?updated_by=user-uuid
  {
    "setting_value": "America/Chicago"
  }
  ```

---

## Setting Types

The API supports the following setting types:

| Type | Description | Example Values |
|------|-------------|----------------|
| STRING | Text values | "Hello", "00:00", "UTC" |
| INTEGER | Whole numbers | "365", "30", "100" |
| DECIMAL | Decimal numbers | "10.50", "0.08", "99.99" |
| BOOLEAN | True/False values | "true", "false" |
| JSON | JSON objects/arrays | "{\"key\": \"value\"}", "[1,2,3]" |
| DATE | Date values | "2025-01-18" |
| TIME | Time values | "14:30:00" |
| DATETIME | Date and time | "2025-01-18T14:30:00Z" |

---

## Setting Categories

Settings are organized into the following categories:

| Category | Description | Example Settings |
|----------|-------------|------------------|
| GENERAL | General application settings | app_name, timezone |
| BUSINESS | Business-related settings | company_name, business_hours |
| FINANCIAL | Financial settings | tax_rate, late_fee_rate |
| RENTAL | Rental-specific settings | minimum_rental_days, security_deposit |
| SYSTEM | System configuration | rental_status_check_enabled, backup_retention |

---

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common error scenarios:

1. **Authentication Error (401)**
   ```json
   {
     "detail": "Authentication required"
   }
   ```

2. **Permission Error (403)**
   ```json
   {
     "detail": "You do not have permission to modify system settings"
   }
   ```

3. **Validation Error (400)**
   ```json
   {
     "detail": "Invalid value for setting 'rental_status_check_time': must be in HH:MM format"
   }
   ```

4. **Not Found Error (404)**
   ```json
   {
     "detail": "Setting 'non_existent_key' not found"
   }
   ```

---

## Usage Examples

### Example 1: Enable Rental Status Checking
```bash
curl -X PUT "https://api.example.com/api/system/settings/rental_status_check_enabled?updated_by=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer your-auth-token" \
  -H "Content-Type: application/json" \
  -d '{"setting_value": "true"}'
```

### Example 2: Configure Check Time
```bash
curl -X PUT "https://api.example.com/api/system/settings/rental_status_check_time?updated_by=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer your-auth-token" \
  -H "Content-Type: application/json" \
  -d '{"setting_value": "03:00"}'
```

### Example 3: Get All System Category Settings
```bash
curl -X GET "https://api.example.com/api/system/settings?category=SYSTEM" \
  -H "Authorization: Bearer your-auth-token"
```

### Example 4: Reset Setting to Default
```bash
curl -X POST "https://api.example.com/api/system/settings/rental_status_log_retention_days/reset?updated_by=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer your-auth-token"
```

---

## Best Practices

1. **Authentication**: Always include valid authentication tokens
2. **Validation**: Validate setting values on the client side before sending
3. **Error Handling**: Implement proper error handling for all response codes
4. **Caching**: Cache settings that don't change frequently
5. **Batch Updates**: Update multiple related settings in sequence
6. **Audit Trail**: The `updated_by` parameter ensures all changes are tracked
7. **Permission Checks**: Verify user permissions before showing setting UI

---

## Notes

- System settings marked with `is_system: true` are critical settings that should be modified with caution
- Some settings may require application restart to take effect
- Setting changes are audited and can be tracked through the audit log system
- The scheduler will automatically pick up timezone and time changes on the next run
- Boolean values must be sent as strings: "true" or "false"
- All timestamps are in UTC unless otherwise specified

For additional support or questions about system settings, contact the backend team.