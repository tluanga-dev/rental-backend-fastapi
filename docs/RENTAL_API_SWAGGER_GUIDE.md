# Rental Filtering API - Swagger UI Visual Guide

## Step-by-Step Guide to Access Rental API in Swagger UI

### 1. Access Swagger UI
Open your browser and navigate to:
```
http://localhost:8000/docs
```

### 2. Authenticate (Important!)
1. Look for the **"Authorize"** button at the top right
2. Click it to open the authentication dialog
3. In the "Value" field, enter your token:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
4. Click **"Authorize"** then **"Close"**

### 3. Find the Rental Endpoint
1. Scroll down to the **"Transactions"** section
2. Look for the green **GET** badge next to `/api/transactions/rentals`
3. The description reads: "Get Rental Transactions"

### 4. Expand the Endpoint
Click on the endpoint bar to expand it. You'll see:
- Full endpoint description
- All available parameters
- Response information

### 5. Test the Endpoint
1. Click the **"Try it out"** button (top right of the expanded section)
2. The parameter fields become editable
3. Fill in any filters you want to test:
   - `limit`: Set to 10 for quick testing
   - `overdue_only`: Toggle to true/false
   - `rental_status`: Select from dropdown (ACTIVE, LATE, etc.)
   - Leave other fields empty for no filtering

### 6. Execute the Request
1. Click the blue **"Execute"** button
2. Swagger UI sends the request with your authentication token

### 7. View the Results
Below the Execute button, you'll see:
- **Curl command**: The exact curl command that was executed
- **Request URL**: The full URL with query parameters
- **Response status**: 200 for success
- **Response body**: The JSON array of rental transactions
- **Response headers**: Including processing time

## Common Test Scenarios

### Test 1: Get All Rentals
- Leave all parameters at default
- Click Execute

### Test 2: Get Active Rentals Only
- Set `rental_status` = ACTIVE
- Click Execute

### Test 3: Get Overdue Rentals
- Set `overdue_only` = true
- Click Execute

### Test 4: Filter by Date Range
- Set `date_from` = 2025-01-01
- Set `date_to` = 2025-01-31
- Click Execute

### Test 5: Pagination Test
- Set `skip` = 0
- Set `limit` = 5
- Click Execute

## Understanding the Response

The response is a JSON array where each item contains:
```json
[
  {
    "id": "uuid",
    "transaction_number": "REN-20250101-001",
    "transaction_date": "2025-01-01T10:00:00",
    "customer_id": "uuid",
    "location_id": "uuid",
    "status": "CONFIRMED",
    "current_rental_status": "ACTIVE",
    "rental_start_date": "2025-01-01",
    "rental_end_date": "2025-01-15",
    "total_amount": 500.00,
    "paid_amount": 250.00,
    "lifecycle": {
      "id": "uuid",
      "current_status": "ACTIVE",
      "last_status_change": "2025-01-01T10:00:00",
      "expected_return_date": "2025-01-15"
    }
  }
]
```

## Troubleshooting

### 401 Unauthorized
- Your token has expired
- Click "Authorize" again and enter a fresh token

### 422 Unprocessable Entity
- Invalid parameter format (e.g., invalid UUID)
- Check the error detail in the response

### 500 Internal Server Error
- Server-side issue
- Check the error message for details

## Export Options

### Copy as cURL
After executing, click "Copy" next to the Curl command to get:
```bash
curl -X 'GET' \
  'http://localhost:8000/api/transactions/rentals?limit=10' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Download OpenAPI Spec
Click on the `/openapi.json` link at the top of the page to download the full API specification.

## Tips
- Use the "Schema" tab to see the exact structure of request/response objects
- The "Example Value" shows a sample response format
- You can click "Clear" to reset all parameters
- The lock icon 🔒 indicates endpoints that require authentication