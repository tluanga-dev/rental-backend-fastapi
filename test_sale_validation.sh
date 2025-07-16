#!/bin/bash

# Test script to validate the new sale endpoint validation

BASE_URL="http://localhost:8000"
ENDPOINT="${BASE_URL}/api/transactions/new-sale"

echo "Testing new sale endpoint validation..."

# Test 1: Missing required fields
echo "Test 1: Missing required fields"
curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
echo ""

# Test 2: Invalid customer_id format
echo "Test 2: Invalid customer_id format"
curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "invalid-uuid",
    "transaction_date": "2024-07-15",
    "items": [{"item_id": "123e4567-e89b-12d3-a456-426614174001", "quantity": 1, "unit_cost": 10.0}]
  }' | python3 -m json.tool
echo ""

# Test 3: Invalid date format
echo "Test 3: Invalid date format"
curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "transaction_date": "invalid-date",
    "items": [{"item_id": "123e4567-e89b-12d3-a456-426614174001", "quantity": 1, "unit_cost": 10.0}]
  }' | python3 -m json.tool
echo ""

# Test 4: Valid request format (will fail on business logic)
echo "Test 4: Valid request format (will fail on business logic)"
curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "transaction_date": "2024-07-15",
    "notes": "Test sale",
    "reference_number": "REF-001",
    "items": [
      {
        "item_id": "123e4567-e89b-12d3-a456-426614174001",
        "quantity": 1,
        "unit_cost": 10.0,
        "tax_rate": 8.5,
        "discount_amount": 1.0,
        "notes": "Test item"
      }
    ]
  }' | python3 -m json.tool
echo ""

echo "Validation testing completed."