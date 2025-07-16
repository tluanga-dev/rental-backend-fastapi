#!/bin/bash

# Test script for the new sale endpoint using curl
BASE_URL="http://localhost:8000"
SALE_ENDPOINT="${BASE_URL}/api/transactions/new-sale"

# Sample sale data
SALE_DATA='{
  "customer_id": "123e4567-e89b-12d3-a456-426614174000",
  "transaction_date": "2024-07-15",
  "notes": "Test sale transaction",
  "reference_number": "REF-TEST-001",
  "items": [
    {
      "item_id": "123e4567-e89b-12d3-a456-426614174001",
      "quantity": 2,
      "unit_cost": 25.50,
      "tax_rate": 8.5,
      "discount_amount": 5.00,
      "notes": "Test item 1"
    },
    {
      "item_id": "123e4567-e89b-12d3-a456-426614174002",
      "quantity": 1,
      "unit_cost": 100.00,
      "tax_rate": 8.5,
      "discount_amount": 0.00,
      "notes": "Test item 2"
    }
  ]
}'

echo "Testing new sale endpoint..."
echo "URL: ${SALE_ENDPOINT}"
echo "Data: ${SALE_DATA}"
echo ""

# Test if server is running
echo "Checking if server is running..."
curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health"
if [ $? -eq 0 ]; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running or not accessible"
    exit 1
fi

echo ""
echo "Testing new sale endpoint..."

# Make the request
curl -X POST "${SALE_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${SALE_DATA}" \
  -v

echo ""
echo "Test completed."