# FastAPI Rental Management System - API Documentation

This document provides comprehensive documentation for all working API endpoints in the rental management system.

## Base URL
- **Development**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Authentication

All endpoints (except health check and authentication endpoints) require JWT authentication.

### Headers Required
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Authentication Endpoints

### 1. User Registration
**POST** `/api/auth/register`

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

### 2. User Login
**POST** `/api/auth/login`

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
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "email": "admin@admin.com",
    "full_name": "System Administrator",
    "is_active": true,
    "is_verified": true
  }
}
```

### 3. Get Current User
**GET** `/api/auth/me`

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "admin",
  "email": "admin@admin.com",
  "full_name": "System Administrator",
  "is_active": true,
  "is_verified": true,
  "is_superuser": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### 4. Refresh Token
**POST** `/api/auth/refresh`

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

## User Management Endpoints

**Note:** Requires admin/superuser permissions

### 1. List Users
**GET** `/api/users/`

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "email": "admin@admin.com",
    "full_name": "System Administrator",
    "is_active": true,
    "is_verified": true,
    "is_superuser": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

### 2. Create User
**POST** `/api/users/`

**Request Body:**
```json
{
  "username": "new_user",
  "email": "newuser@example.com",
  "password": "SecurePass123",
  "full_name": "New User",
  "is_active": true
}
```

### 3. Get User by ID
**GET** `/api/users/{user_id}`

**Response (200):** Same as user object above

### 4. Update User
**PUT** `/api/users/{user_id}`

**Request Body:**
```json
{
  "full_name": "Updated Full Name",
  "email": "updated@example.com"
}
```

### 5. Delete User
**DELETE** `/api/users/{user_id}`

**Response (200):**
```json
{
  "message": "User deleted successfully"
}
```

## Role Management Endpoints

### 1. Create Role
**POST** `/api/users/roles/`

**Request Body:**
```json
{
  "name": "Manager",
  "description": "Manager role with limited permissions",
  "permissions": [
    "read:customers",
    "write:customers",
    "read:inventory",
    "write:inventory",
    "read:transactions"
  ]
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Manager",
  "description": "Manager role with limited permissions",
  "permissions": [
    "read:customers",
    "write:customers",
    "read:inventory",
    "write:inventory",
    "read:transactions"
  ],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 2. Assign Role to User
**POST** `/api/users/{user_id}/roles/{role_id}`

**Response (200):**
```json
{
  "message": "Role assigned successfully"
}
```

## Customer Management Endpoints

### 1. List Customers
**GET** `/api/customers/customers/`

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `customer_type`: str (optional)
- `active_only`: bool (default: true)

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_code": "CUST001",
    "customer_name": "John Smith",
    "customer_type": "INDIVIDUAL",
    "business_name": null,
    "contact_person": "John Smith",
    "email": "john.smith@email.com",
    "phone": "+1234567890",
    "address_line1": "123 Main St",
    "address_line2": null,
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "credit_limit": 5000.00,
    "current_balance": 0.00,
    "payment_terms": 30,
    "tax_number": "TAX123456",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

### 2. Create Customer
**POST** `/api/customers/customers/`

**Request Body:**
```json
{
  "customer_code": "CUST002",
  "customer_name": "Jane Doe",
  "customer_type": "INDIVIDUAL",
  "contact_person": "Jane Doe",
  "email": "jane.doe@email.com",
  "phone": "+1987654321",
  "address_line1": "456 Oak Ave",
  "city": "Los Angeles",
  "state": "CA",
  "postal_code": "90210",
  "country": "USA",
  "credit_limit": 3000.00,
  "payment_terms": 15
}
```

**Response (201):** Same structure as customer object above

### 3. Get Customer by ID
**GET** `/api/customers/customers/{customer_id}`

### 4. Update Customer
**PUT** `/api/customers/customers/{customer_id}`

### 5. Delete Customer
**DELETE** `/api/customers/customers/{customer_id}`

## Supplier Management Endpoints

### 1. List Suppliers
**GET** `/api/suppliers/suppliers/`

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "supplier_code": "SUP001",
    "supplier_name": "ABC Rentals Inc",
    "contact_person": "Mike Johnson",
    "email": "mike@abcrentals.com",
    "phone": "+1234567890",
    "address_line1": "789 Business Blvd",
    "city": "Chicago",
    "state": "IL",
    "postal_code": "60601",
    "country": "USA",
    "payment_terms": 30,
    "tax_number": "TAX789012",
    "rating": 5,
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

### 2. Create Supplier
**POST** `/api/suppliers/suppliers/`

**Request Body:**
```json
{
  "supplier_code": "SUP002",
  "supplier_name": "XYZ Equipment Supply",
  "contact_person": "Sarah Wilson",
  "email": "sarah@xyzequip.com",
  "phone": "+1987654321",
  "address_line1": "321 Industrial Way",
  "city": "Detroit",
  "state": "MI",
  "postal_code": "48201",
  "country": "USA",
  "payment_terms": 45,
  "tax_number": "TAX345678",
  "rating": 4
}
```

## Master Data Endpoints

### 1. Brands

#### List Brands
**GET** `/api/master-data/brands/`

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "brand_code": "CATERPILLAR",
    "brand_name": "Caterpillar",
    "description": "Heavy machinery and equipment",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

#### Create Brand
**POST** `/api/master-data/brands/`

**Request Body:**
```json
{
  "brand_code": "JOHN_DEERE",
  "brand_name": "John Deere",
  "description": "Agricultural and construction equipment"
}
```

### 2. Categories

#### List Categories
**GET** `/api/master-data/categories/`

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "category_code": "EXCAVATORS",
    "category_name": "Excavators",
    "parent_category_id": null,
    "description": "Heavy excavation equipment",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

#### Create Category
**POST** `/api/master-data/categories/`

**Request Body:**
```json
{
  "category_code": "BULLDOZERS",
  "category_name": "Bulldozers",
  "description": "Heavy earthmoving equipment"
}
```

### 3. Locations

#### List Locations
**GET** `/api/master-data/locations/`

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "location_code": "NYC_MAIN",
    "location_name": "New York Main Warehouse",
    "location_type": "WAREHOUSE",
    "address_line1": "123 Storage Street",
    "address_line2": null,
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "phone": "+1234567890",
    "email": "nyc.main@company.com",
    "manager_user_id": null,
    "operating_hours": null,
    "capacity": null,
    "description": null,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "is_active": true
  }
]
```

#### Create Location
**POST** `/api/master-data/locations/`

**Request Body:**
```json
{
  "location_code": "LA_BRANCH",
  "location_name": "Los Angeles Branch",
  "location_type": "BRANCH",
  "address_line1": "456 Pacific Ave",
  "city": "Los Angeles",
  "state": "CA",
  "postal_code": "90210",
  "country": "USA",
  "phone": "+1987654321",
  "email": "la.branch@company.com"
}
```

## Inventory Management Endpoints

### 1. List Items
**GET** `/api/inventory/items/`

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `category_id`: UUID (optional)
- `brand_id`: UUID (optional)
- `active_only`: bool (default: true)

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "item_code": "EXC001",
    "item_name": "Caterpillar 320D Excavator",
    "description": "Medium-sized hydraulic excavator",
    "category_id": "550e8400-e29b-41d4-a716-446655440001",
    "brand_id": "550e8400-e29b-41d4-a716-446655440002",
    "item_type": "EQUIPMENT",
    "unit_of_measure": "UNIT",
    "rental_rate_daily": 450.00,
    "rental_rate_weekly": 2500.00,
    "rental_rate_monthly": 9000.00,
    "sale_price": 125000.00,
    "cost_price": 100000.00,
    "minimum_rental_period": 1,
    "maximum_rental_period": 365,
    "requires_operator": true,
    "requires_training": true,
    "weight_kg": 22000.0,
    "dimensions": "9.5m x 3.2m x 3.1m",
    "power_requirements": "Diesel Engine",
    "item_status": "ACTIVE",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

### 2. Create Item
**POST** `/api/inventory/items/`

**Request Body:**
```json
{
  "item_code": "BULL001",
  "item_name": "John Deere 850K Bulldozer",
  "description": "Heavy-duty track bulldozer",
  "category_id": "550e8400-e29b-41d4-a716-446655440001",
  "brand_id": "550e8400-e29b-41d4-a716-446655440002",
  "item_type": "EQUIPMENT",
  "unit_of_measure": "UNIT",
  "rental_rate_daily": 650.00,
  "rental_rate_weekly": 3500.00,
  "rental_rate_monthly": 12000.00,
  "sale_price": 180000.00,
  "cost_price": 145000.00,
  "minimum_rental_period": 1,
  "maximum_rental_period": 365,
  "requires_operator": true,
  "requires_training": true,
  "weight_kg": 28000.0
}
```

### 3. List Inventory Units
**GET** `/api/inventory/units/`

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "item_id": "550e8400-e29b-41d4-a716-446655440001",
    "unit_number": "EXC001-001",
    "serial_number": "CAT320D2024001",
    "location_id": "550e8400-e29b-41d4-a716-446655440002",
    "condition": "EXCELLENT",
    "availability_status": "AVAILABLE",
    "last_maintenance_date": "2024-01-01",
    "next_maintenance_date": "2024-04-01",
    "hours_used": 1250.5,
    "purchase_date": "2023-01-15",
    "purchase_price": 125000.00,
    "depreciation_rate": 15.0,
    "insurance_value": 110000.00,
    "notes": "Recently serviced and inspected",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

### 4. Create Inventory Unit
**POST** `/api/inventory/units/`

**Request Body:**
```json
{
  "item_id": "550e8400-e29b-41d4-a716-446655440001",
  "unit_number": "BULL001-001",
  "serial_number": "JD850K2024001",
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "condition": "EXCELLENT",
  "availability_status": "AVAILABLE",
  "purchase_date": "2024-01-01",
  "purchase_price": 180000.00,
  "depreciation_rate": 12.0,
  "insurance_value": 165000.00
}
```

## Transaction Management Endpoints

### 1. List Transactions
**GET** `/api/transactions/headers/`

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `transaction_type`: TransactionType (optional)
- `status`: TransactionStatus (optional)

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "transaction_number": "TXN-2024-001",
    "transaction_type": "RENTAL",
    "transaction_date": "2024-01-01T12:00:00Z",
    "customer_id": "550e8400-e29b-41d4-a716-446655440001",
    "location_id": "550e8400-e29b-41d4-a716-446655440002",
    "status": "CONFIRMED",
    "payment_status": "PAID",
    "total_amount": 1350.00,
    "paid_amount": 1350.00,
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

### 2. Create Transaction
**POST** `/api/transactions/headers/`

**Request Body:**
```json
{
  "transaction_number": "TXN-2024-002",
  "transaction_type": "RENTAL",
  "transaction_date": "2024-01-02T10:00:00",
  "customer_id": "550e8400-e29b-41d4-a716-446655440001",
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "rental_start_date": "2024-01-03",
  "rental_end_date": "2024-01-10",
  "notes": "Weekly excavator rental for construction project"
}
```

### 3. Get Transaction with Lines
**GET** `/api/transactions/headers/{transaction_id}`

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "transaction_number": "TXN-2024-001",
  "transaction_type": "RENTAL",
  "transaction_date": "2024-01-01T12:00:00Z",
  "customer_id": "550e8400-e29b-41d4-a716-446655440001",
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "CONFIRMED",
  "payment_status": "PAID",
  "subtotal": 1250.00,
  "discount_amount": 0.00,
  "tax_amount": 100.00,
  "total_amount": 1350.00,
  "paid_amount": 1350.00,
  "deposit_amount": 500.00,
  "rental_start_date": "2024-01-01",
  "rental_end_date": "2024-01-03",
  "transaction_lines": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
      "line_number": 1,
      "line_type": "PRODUCT",
      "item_id": "550e8400-e29b-41d4-a716-446655440003",
      "inventory_unit_id": "550e8400-e29b-41d4-a716-446655440004",
      "description": "Caterpillar 320D Excavator - 3 day rental",
      "quantity": 1.0,
      "unit_price": 450.00,
      "discount_percentage": 0.0,
      "discount_amount": 0.0,
      "tax_rate": 8.0,
      "tax_amount": 100.00,
      "line_total": 1250.00,
      "rental_start_date": "2024-01-01",
      "rental_end_date": "2024-01-03",
      "returned_quantity": 0.0,
      "is_active": true,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 4. Add Transaction Line
**POST** `/api/transactions/headers/{transaction_id}/lines/`

**Request Body:**
```json
{
  "line_number": 1,
  "line_type": "PRODUCT",
  "description": "Caterpillar 320D Excavator - Weekly rental",
  "quantity": 1.0,
  "unit_price": 450.00,
  "item_id": "550e8400-e29b-41d4-a716-446655440003",
  "inventory_unit_id": "550e8400-e29b-41d4-a716-446655440004",
  "tax_rate": 8.0,
  "rental_start_date": "2024-01-03",
  "rental_end_date": "2024-01-10"
}
```

### 5. Create New Rental Transaction
**POST** `/api/transactions/new-rental`

**Description:** Create a new rental transaction with a simplified format that matches the frontend JSON structure exactly. The endpoint automatically fetches rental rates from item master data and calculates totals based on quantity and rental period.

**Request Body:**
```json
{
  "transaction_date": "2024-01-15",
  "customer_id": "550e8400-e29b-41d4-a716-446655440001",
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "payment_method": "CASH",
  "payment_reference": "REF-2024-001",
  "notes": "Five-day excavator rental for construction project",
  "items": [
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440003",
      "quantity": 1,
      "rental_period_value": 5,
      "tax_rate": 8.5,
      "discount_amount": 0.00,
      "rental_start_date": "2024-01-15",
      "rental_end_date": "2024-01-20",
      "notes": "Caterpillar 320D excavator"
    }
  ]
}
```

**Request Fields:**
- `transaction_date`: string (YYYY-MM-DD, required) - Transaction date used for transaction number generation
- `customer_id`: string (UUID, required) - Customer ID (must exist and be able to transact)
- `location_id`: string (UUID, required) - Location ID where rental originates (must exist)
- `payment_method`: string (required) - Payment method (CASH, CARD, BANK_TRANSFER, CHECK, ONLINE)
- `payment_reference`: string (optional) - Payment reference number or transaction ID
- `notes`: string (optional) - Additional notes for the rental transaction
- `items`: array (required, min 1) - Array of rental items

**Item Fields:**
- `item_id`: string (UUID, required) - Item ID (must exist and be rentable)
- `quantity`: integer (required, ≥0) - Quantity to rent (0 allowed for reservations)
- `rental_period_value`: integer (required, ≥0) - Rental period in days (0 allowed for immediate returns)
- `tax_rate`: decimal (optional, 0-100) - Tax rate percentage (default: 0)
- `discount_amount`: decimal (optional, ≥0) - Fixed discount amount (default: 0)
- `rental_start_date`: string (YYYY-MM-DD, required) - Item-specific rental start date
- `rental_end_date`: string (YYYY-MM-DD, required) - Item-specific rental end date (must be after start date)
- `notes`: string (optional) - Additional notes for this specific item

**Key Features:**
- Automatic rental rate lookup from item master data
- Item-level rental date management (different items can have different rental periods)
- Automatic transaction number generation (format: REN-YYYYMMDD-XXXX)
- Tax and discount calculations per line item
- Comprehensive validation at both header and line levels

**Response (201):**
```json
{
  "success": true,
  "message": "Rental transaction created successfully",
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "transaction_number": "REN-20240115-1234",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "transaction_number": "REN-20240115-1234",
    "transaction_type": "RENTAL",
    "transaction_date": "2024-01-15T00:00:00Z",
    "customer_id": "550e8400-e29b-41d4-a716-446655440001",
    "location_id": "550e8400-e29b-41d4-a716-446655440002",
    "status": "CONFIRMED",
    "payment_status": "PENDING",
    "subtotal": 2062.50,
    "discount_amount": 0.00,
    "tax_amount": 187.50,
    "total_amount": 2250.00,
    "paid_amount": 0.00,
    "deposit_amount": 0.00,
    "payment_method": "CASH",
    "payment_reference": "REF-2024-001",
    "notes": "Five-day excavator rental for construction project",
    "transaction_lines": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440010",
        "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "line_number": 1,
        "line_type": "PRODUCT",
        "item_id": "550e8400-e29b-41d4-a716-446655440003",
        "description": "Rental: 550e8400-e29b-41d4-a716-446655440003 (5 days)",
        "quantity": 1.0,
        "unit_price": 450.00,
        "discount_amount": 0.00,
        "tax_rate": 8.5,
        "tax_amount": 187.50,
        "line_total": 2250.00,
        "rental_period_value": 5,
        "rental_period_unit": "DAYS",
        "rental_start_date": "2024-01-15",
        "rental_end_date": "2024-01-20",
        "notes": "Caterpillar 320D excavator"
      }
    ],
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

**Response Fields:**
- `success`: boolean - Operation success status (always true for 201 responses)
- `message`: string - Human-readable success message
- `transaction_id`: UUID - Created transaction ID for reference
- `transaction_number`: string - Generated transaction number (REN-YYYYMMDD-XXXX format)
- `data`: object - Complete transaction object with all details and line items

**Business Logic:**
- Unit prices are automatically fetched from item master data (`rental_rate_per_period`)
- Line totals calculated as: `(unit_price * quantity * rental_period_value) + tax_amount - discount_amount`
- Tax amount calculated as: `(subtotal * tax_rate) / 100`
- Transaction totals are sum of all line totals
- All monetary values are in decimal format with 2 decimal places

**Validation Rules:**

**Header Level:**
- `transaction_date`: Must be valid YYYY-MM-DD format
- `customer_id`: Must be valid UUID format and customer must exist and be able to transact (not blacklisted)
- `location_id`: Must be valid UUID format and location must exist
- `payment_method`: Must be one of: CASH, CARD, BANK_TRANSFER, CHECK, ONLINE
- `items`: Array must contain at least 1 item

**Item Level:**
- `item_id`: Must be valid UUID format, item must exist and be rentable (`is_rentable: true`)
- `quantity`: Must be integer >= 0 (0 allowed for reservations)
- `rental_period_value`: Must be integer >= 0 (0 allowed for immediate returns)
- `tax_rate`: Must be decimal between 0-100 (if provided)
- `discount_amount`: Must be decimal >= 0 (if provided)
- `rental_start_date`: Must be valid YYYY-MM-DD format
- `rental_end_date`: Must be valid YYYY-MM-DD format and after start date
- Date range validation performed per item independently

**Error Responses:**

**404 Not Found**
```json
{
  "detail": "Customer with ID 550e8400-e29b-41d4-a716-446655440001 not found"
}
```

**422 Validation Error**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "customer_id"],
      "msg": "Value error, Invalid UUID format: invalid-uuid",
      "input": "invalid-uuid"
    },
    {
      "type": "value_error", 
      "loc": ["body", "items", 0],
      "msg": "Value error, Rental end date must be after start date",
      "input": {...}
    }
  ]
}
```

**Generated Transaction Numbers:**
- Format: `REN-YYYYMMDD-XXXX`
- Example: `REN-20240115-1234`
- Based on transaction date with random 4-digit suffix
- Automatically ensures uniqueness across all rental transactions

**Usage Examples:**

**Single Item Rental:**
```bash
curl -X POST "http://localhost:8000/api/transactions/new-rental" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <token>" \
-d '{
  "transaction_date": "2024-01-15",
  "customer_id": "550e8400-e29b-41d4-a716-446655440001",
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "payment_method": "CASH",
  "payment_reference": "CASH-001",
  "notes": "Construction equipment rental",
  "items": [
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440003",
      "quantity": 1,
      "rental_period_value": 7,
      "tax_rate": 10.0,
      "discount_amount": 50.00,
      "rental_start_date": "2024-01-15",
      "rental_end_date": "2024-01-22",
      "notes": "Weekly excavator rental with discount"
    }
  ]
}'
```

**Multiple Items with Different Rental Periods:**
```json
{
  "transaction_date": "2024-01-15",
  "customer_id": "550e8400-e29b-41d4-a716-446655440001",
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "payment_method": "CARD",
  "payment_reference": "CC-123456",
  "notes": "Multi-equipment rental for construction project",
  "items": [
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440003",
      "quantity": 1,
      "rental_period_value": 7,
      "tax_rate": 8.5,
      "discount_amount": 0.00,
      "rental_start_date": "2024-01-15",
      "rental_end_date": "2024-01-22",
      "notes": "Excavator for foundation work"
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440004",
      "quantity": 2,
      "rental_period_value": 3,
      "tax_rate": 8.5,
      "discount_amount": 25.00,
      "rental_start_date": "2024-01-16",
      "rental_end_date": "2024-01-19",
      "notes": "Two generators for temporary power"
    }
  ]
}
```

## Analytics Endpoints

### 1. Get Revenue Analytics
**GET** `/api/analytics/revenue/`

**Query Parameters:**
- `period`: str (daily, weekly, monthly, yearly)
- `start_date`: date (YYYY-MM-DD)
- `end_date`: date (YYYY-MM-DD)

**Response (200):**
```json
{
  "total_revenue": 45750.00,
  "rental_revenue": 32500.00,
  "sales_revenue": 13250.00,
  "period_breakdown": [
    {
      "period": "2024-01-01",
      "revenue": 15250.00,
      "rental_revenue": 10750.00,
      "sales_revenue": 4500.00
    }
  ],
  "growth_rate": 12.5,
  "compared_to_previous_period": true
}
```

### 2. Get Inventory Analytics
**GET** `/api/analytics/inventory/`

**Response (200):**
```json
{
  "total_items": 150,
  "total_units": 485,
  "available_units": 342,
  "rented_units": 98,
  "maintenance_units": 32,
  "out_of_service_units": 13,
  "utilization_rate": 67.8,
  "top_rented_items": [
    {
      "item_name": "Caterpillar 320D Excavator",
      "rental_count": 45,
      "revenue": 20250.00
    }
  ]
}
```

### 3. Get Customer Analytics
**GET** `/api/analytics/customers/`

**Response (200):**
```json
{
  "total_customers": 125,
  "active_customers": 98,
  "new_customers_this_month": 12,
  "top_customers": [
    {
      "customer_name": "ABC Construction",
      "total_revenue": 87500.00,
      "transaction_count": 23
    }
  ],
  "customer_segments": {
    "INDIVIDUAL": 45,
    "BUSINESS": 80
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 409 Conflict
```json
{
  "detail": "Resource already exists"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "field_name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Common Response Patterns

### Paginated Lists
Most list endpoints support pagination:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

### Filtering
Many endpoints support filtering parameters:
- `active_only`: bool (default: true) - Filter for active records only
- Entity-specific filters (e.g., `customer_type`, `transaction_type`)

### Soft Deletion
All entities support soft deletion via the `is_active` field. Deleted records are marked as `is_active: false` but remain in the database.

### Timestamps
All entities include:
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last modified

### UUID Identifiers
All entities use UUID primary keys for better security and distributed system compatibility.