# System Module Implementation Guide for Frontend Developers

**Document Version:** 1.0  
**Date:** January 16, 2025  
**Author:** System Architecture Team  

## Overview

The System Module provides comprehensive system management functionality including settings management, company information, backup operations, audit logging, and system maintenance. This document outlines all available endpoints, request/response formats, and implementation examples for frontend developers.

## Base URL

All system module endpoints are prefixed with `/api/system`

## Authentication

All endpoints require authentication. Include the Bearer token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Core Endpoints

### 1. System Settings Management

#### 1.1 Get All Settings

**Endpoint:** `GET /api/system/settings`

**Query Parameters:**
- `category` (optional): Filter by setting category
- `include_system` (optional, default: true): Include system settings

**Response:**
```json
[
  {
    "id": "uuid",
    "setting_key": "company_name",
    "setting_name": "Company Name",
    "setting_type": "STRING",
    "setting_category": "BUSINESS",
    "setting_value": "Your Company",
    "default_value": "Your Company",
    "description": "Name of the company using the system",
    "is_system": false,
    "is_sensitive": false,
    "validation_rules": {},
    "display_order": "1",
    "is_active": true,
    "created_at": "2025-01-16T10:00:00Z",
    "updated_at": "2025-01-16T10:00:00Z"
  }
]
```

#### 1.2 Get Setting by Key

**Endpoint:** `GET /api/system/settings/{setting_key}`

**Response:**
```json
{
  "id": "uuid",
  "setting_key": "company_name",
  "setting_name": "Company Name",
  "setting_type": "STRING",
  "setting_category": "BUSINESS",
  "setting_value": "Your Company",
  "default_value": "Your Company",
  "description": "Name of the company using the system",
  "is_system": false,
  "is_sensitive": false,
  "validation_rules": {},
  "display_order": "1",
  "is_active": true,
  "created_at": "2025-01-16T10:00:00Z",
  "updated_at": "2025-01-16T10:00:00Z"
}
```

#### 1.3 Get Setting Value Only

**Endpoint:** `GET /api/system/settings/{setting_key}/value`

**Response:**
```json
{
  "setting_key": "company_name",
  "value": "Your Company"
}
```

#### 1.4 Update Setting Value

**Endpoint:** `PUT /api/system/settings/{setting_key}?updated_by={user_id}`

**Request Body:**
```json
{
  "setting_value": "New Company Name"
}
```

**Response:**
```json
{
  "id": "uuid",
  "setting_key": "company_name",
  "setting_name": "Company Name",
  "setting_type": "STRING",
  "setting_category": "BUSINESS",
  "setting_value": "New Company Name",
  "default_value": "Your Company",
  "description": "Name of the company using the system",
  "is_system": false,
  "is_sensitive": false,
  "validation_rules": {},
  "display_order": "1",
  "is_active": true,
  "created_at": "2025-01-16T10:00:00Z",
  "updated_at": "2025-01-16T10:30:00Z"
}
```

#### 1.5 Reset Setting to Default

**Endpoint:** `POST /api/system/settings/{setting_key}/reset?updated_by={user_id}`

**Response:** Same as update setting response with `setting_value` reset to `default_value`

#### 1.6 Get Settings by Category

**Endpoint:** `GET /api/system/settings/categories/{category}`

**Available Categories:**
- `GENERAL`
- `BUSINESS`
- `FINANCIAL`
- `INVENTORY`
- `RENTAL`
- `NOTIFICATION`
- `SECURITY`
- `INTEGRATION`
- `REPORTING`
- `SYSTEM`

**Response:** Array of settings (same format as Get All Settings)

### 2. Company Information Management

#### 2.1 Get Company Information

**Endpoint:** `GET /api/system/company`

**Response:**
```json
{
  "company_name": "Your Company",
  "company_address": "123 Main Street, City, State 12345",
  "company_email": "info@company.com",
  "company_phone": "+1-555-123-4567",
  "company_gst_no": "GST123456789",
  "company_registration_number": "REG987654321"
}
```

#### 2.2 Update Company Information

**Endpoint:** `PUT /api/system/company?updated_by={user_id}`

**Request Body (all fields optional):**
```json
{
  "company_name": "Updated Company Name",
  "company_address": "456 New Street, New City, State 67890",
  "company_email": "contact@newcompany.com",
  "company_phone": "+1-555-987-6543",
  "company_gst_no": "GST987654321",
  "company_registration_number": "REG123456789"
}
```

**Response:**
```json
{
  "company_name": "Updated Company Name",
  "company_address": "456 New Street, New City, State 67890",
  "company_email": "contact@newcompany.com",
  "company_phone": "+1-555-987-6543",
  "company_gst_no": "GST987654321",
  "company_registration_number": "REG123456789"
}
```

### 3. System Backup Management

#### 3.1 Create Backup

**Endpoint:** `POST /api/system/backups?started_by={user_id}`

**Request Body:**
```json
{
  "backup_name": "Daily Backup 2025-01-16",
  "backup_type": "FULL",
  "description": "Daily full system backup",
  "retention_days": "30"
}
```

**Backup Types:**
- `FULL`: Complete system backup
- `INCREMENTAL`: Changes since last backup
- `DIFFERENTIAL`: Changes since last full backup

**Response:**
```json
{
  "id": "uuid",
  "backup_name": "Daily Backup 2025-01-16",
  "backup_type": "FULL",
  "backup_status": "PENDING",
  "backup_path": null,
  "backup_size": null,
  "started_by": "uuid",
  "started_at": "2025-01-16T10:00:00Z",
  "completed_at": null,
  "error_message": null,
  "retention_days": "30",
  "description": "Daily full system backup",
  "backup_metadata": {},
  "is_active": true,
  "created_at": "2025-01-16T10:00:00Z",
  "updated_at": "2025-01-16T10:00:00Z"
}
```

#### 3.2 Get All Backups

**Endpoint:** `GET /api/system/backups`

**Query Parameters:**
- `skip` (optional, default: 0): Records to skip
- `limit` (optional, default: 100): Maximum records to return
- `backup_type` (optional): Filter by backup type
- `backup_status` (optional): Filter by backup status
- `started_by` (optional): Filter by user who started backup

**Backup Statuses:**
- `PENDING`: Backup queued
- `RUNNING`: Backup in progress
- `COMPLETED`: Backup finished successfully
- `FAILED`: Backup failed
- `CANCELLED`: Backup cancelled

**Response:** Array of backup objects (same format as Create Backup response)

#### 3.3 Get Backup by ID

**Endpoint:** `GET /api/system/backups/{backup_id}`

**Response:** Single backup object (same format as Create Backup response)

#### 3.4 Start Backup

**Endpoint:** `POST /api/system/backups/{backup_id}/start`

**Response:** Updated backup object with status "RUNNING"

#### 3.5 Complete Backup

**Endpoint:** `POST /api/system/backups/{backup_id}/complete?backup_path={path}&backup_size={size}`

**Response:** Updated backup object with status "COMPLETED"

#### 3.6 Fail Backup

**Endpoint:** `POST /api/system/backups/{backup_id}/fail?error_message={message}`

**Response:** Updated backup object with status "FAILED"

### 4. Audit Log Management

#### 4.1 Get Audit Logs

**Endpoint:** `GET /api/system/audit-logs`

**Query Parameters:**
- `skip` (optional, default: 0): Records to skip
- `limit` (optional, default: 100): Maximum records to return
- `user_id` (optional): Filter by user ID
- `action` (optional): Filter by action type
- `entity_type` (optional): Filter by entity type
- `entity_id` (optional): Filter by entity ID
- `success` (optional): Filter by success status
- `start_date` (optional): Filter by start date (ISO format)
- `end_date` (optional): Filter by end date (ISO format)

**Response:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "action": "UPDATE",
    "entity_type": "SystemSetting",
    "entity_id": "uuid",
    "old_values": {
      "setting_value": "Old Value"
    },
    "new_values": {
      "setting_value": "New Value"
    },
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "session_id": "session-uuid",
    "success": true,
    "error_message": null,
    "audit_metadata": {},
    "is_active": true,
    "created_at": "2025-01-16T10:00:00Z",
    "updated_at": "2025-01-16T10:00:00Z"
  }
]
```

#### 4.2 Get Audit Log by ID

**Endpoint:** `GET /api/system/audit-logs/{audit_log_id}`

**Response:** Single audit log object (same format as Get Audit Logs response)

### 5. System Information and Maintenance

#### 5.1 Get System Information

**Endpoint:** `GET /api/system/info`

**Response:**
```json
{
  "system_name": "Rental Management System",
  "system_version": "2.0.0",
  "company_name": "Your Company",
  "timezone": "UTC",
  "settings_count": 25,
  "backups_count": 10,
  "recent_activity_count": 5,
  "last_backup": {
    "backup_name": "Daily Backup 2025-01-15",
    "backup_type": "FULL",
    "backup_status": "COMPLETED",
    "started_at": "2025-01-15T22:00:00Z",
    "completed_at": "2025-01-15T22:30:00Z"
  },
  "system_health": {
    "status": "healthy",
    "uptime": "99.9%",
    "response_time": "120ms",
    "memory_usage": "68%",
    "cpu_usage": "25%",
    "disk_usage": "42%"
  }
}
```

#### 5.2 Perform System Maintenance

**Endpoint:** `POST /api/system/maintenance?user_id={user_id}`

**Response:**
```json
{
  "message": "System maintenance completed",
  "results": {
    "expired_backups_cleaned": 3,
    "old_audit_logs_cleaned": 150
  }
}
```

### 6. Currency Management

#### 6.1 Get Current Currency

**Endpoint:** `GET /api/system/currency`

**Response:**
```json
{
  "currency_code": "USD",
  "symbol": "$",
  "description": "US Dollar",
  "is_default": true
}
```

#### 6.2 Update Currency

**Endpoint:** `PUT /api/system/currency`

**Request Body:**
```json
{
  "currency_code": "EUR",
  "description": "Euro Currency"
}
```

**Response:**
```json
{
  "currency_code": "EUR",
  "symbol": "€",
  "description": "Euro Currency",
  "is_default": true
}
```

#### 6.3 Get Supported Currencies

**Endpoint:** `GET /api/system/currency/supported`

**Response:**
```json
[
  {
    "code": "USD",
    "name": "US Dollar",
    "symbol": "$"
  },
  {
    "code": "EUR",
    "name": "Euro",
    "symbol": "€"
  },
  {
    "code": "GBP",
    "name": "British Pound",
    "symbol": "£"
  }
]
```

## Frontend Implementation Examples

### React/TypeScript Example

```typescript
// Types
interface CompanyInfo {
  company_name: string;
  company_address?: string;
  company_email?: string;
  company_phone?: string;
  company_gst_no?: string;
  company_registration_number?: string;
}

interface SystemSetting {
  id: string;
  setting_key: string;
  setting_name: string;
  setting_type: string;
  setting_category: string;
  setting_value: string;
  default_value: string;
  description: string;
  is_system: boolean;
  is_sensitive: boolean;
  validation_rules: Record<string, any>;
  display_order: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// API Service
class SystemService {
  private baseURL = '/api/system';
  
  async getCompanyInfo(): Promise<CompanyInfo> {
    const response = await fetch(`${this.baseURL}/company`, {
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
  
  async updateCompanyInfo(data: Partial<CompanyInfo>, userId: string): Promise<CompanyInfo> {
    const response = await fetch(`${this.baseURL}/company?updated_by=${userId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
  
  async getSettings(category?: string): Promise<SystemSetting[]> {
    const url = category 
      ? `${this.baseURL}/settings/categories/${category}`
      : `${this.baseURL}/settings`;
    
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
  
  async updateSetting(key: string, value: any, userId: string): Promise<SystemSetting> {
    const response = await fetch(`${this.baseURL}/settings/${key}?updated_by=${userId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ setting_value: value })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
}

// React Component Example
const CompanySettingsForm: React.FC = () => {
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const systemService = new SystemService();
  
  useEffect(() => {
    loadCompanyInfo();
  }, []);
  
  const loadCompanyInfo = async () => {
    try {
      setLoading(true);
      const data = await systemService.getCompanyInfo();
      setCompanyInfo(data);
    } catch (error) {
      console.error('Failed to load company info:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSubmit = async (formData: Partial<CompanyInfo>) => {
    try {
      setLoading(true);
      const userId = getCurrentUserId(); // Implement this function
      const updatedData = await systemService.updateCompanyInfo(formData, userId);
      setCompanyInfo(updatedData);
      // Show success message
    } catch (error) {
      console.error('Failed to update company info:', error);
      // Show error message
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) return <div>Loading...</div>;
  if (!companyInfo) return <div>No company information available</div>;
  
  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      const formData = new FormData(e.target as HTMLFormElement);
      handleSubmit(Object.fromEntries(formData.entries()));
    }}>
      <input
        name="company_name"
        defaultValue={companyInfo.company_name}
        placeholder="Company Name"
        required
      />
      <textarea
        name="company_address"
        defaultValue={companyInfo.company_address || ''}
        placeholder="Company Address"
      />
      <input
        name="company_email"
        type="email"
        defaultValue={companyInfo.company_email || ''}
        placeholder="Company Email"
      />
      <input
        name="company_phone"
        defaultValue={companyInfo.company_phone || ''}
        placeholder="Company Phone"
      />
      <input
        name="company_gst_no"
        defaultValue={companyInfo.company_gst_no || ''}
        placeholder="GST Number"
      />
      <input
        name="company_registration_number"
        defaultValue={companyInfo.company_registration_number || ''}
        placeholder="Registration Number"
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Saving...' : 'Save Changes'}
      </button>
    </form>
  );
};
```

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK**: Success
- **201 Created**: Resource created successfully
- **204 No Content**: Success with no response body
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

Error responses include a `detail` field with error description:

```json
{
  "detail": "Setting with key 'invalid_key' not found"
}
```

## Best Practices

1. **Always include error handling** in your API calls
2. **Cache settings data** when appropriate to reduce API calls
3. **Use the correct user ID** in update operations for audit trails
4. **Validate user input** before sending to the API
5. **Handle loading states** appropriately in your UI
6. **Use TypeScript interfaces** for better type safety
7. **Implement proper authentication** token management
8. **Test with different user roles** to ensure proper access control

## Support

For questions or issues with the System Module API, please contact the backend development team or refer to the API documentation at `/docs` when the application is running.

---

**Last Updated:** January 16, 2025  
**API Version:** 2.0.0