#!/bin/bash

# Set variables
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVzZXJfaWQiOjEsInNjb3BlcyI6WyJyZWFkIiwid3JpdGUiXSwiZXhwIjoxNzUyODE1MTU0LCJ0eXBlIjoiYWNjZXNzIn0.upljvIFqjhVSAKawYokE8M9gBC9oEZC4CpX4OZWLgvU"
BASE_URL="http://localhost:8000"

# Get required IDs
echo "Getting customer ID..."
CUSTOMER_ID=$(curl -s -X GET "$BASE_URL/api/customers/?limit=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq -r '.[0].id')

echo "Customer ID: $CUSTOMER_ID"

echo "Getting location ID..."
LOCATION_ID=$(curl -s -X GET "$BASE_URL/api/master-data/locations/?limit=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq -r '.[0].id')

echo "Location ID: $LOCATION_ID"

echo "Getting rental item ID..."
ITEM_ID=$(curl -s -X GET "$BASE_URL/api/inventory/items/rental?active_only=true&limit=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq -r '.[0].id')

echo "Item ID: $ITEM_ID"

# Create rental payload
TODAY=$(date +%Y-%m-%d)
END_DATE=$(date -v+7d +%Y-%m-%d 2>/dev/null || date -d "+7 days" +%Y-%m-%d)

RENTAL_PAYLOAD=$(cat <<EOF
{
  "transaction_date": "$TODAY",
  "customer_id": "$CUSTOMER_ID",
  "location_id": "$LOCATION_ID",
  "payment_method": "CASH",
  "payment_reference": "TEST-001",
  "notes": "Test rental for API verification",
  "items": [
    {
      "item_id": "$ITEM_ID",
      "quantity": 1,
      "rental_period_value": 7,
      "tax_rate": 0,
      "discount_amount": 0,
      "rental_start_date": "$TODAY",
      "rental_end_date": "$END_DATE",
      "notes": "Test item"
    }
  ],
  "delivery_required": false,
  "pickup_required": false
}
EOF
)

echo -e "\nCreating rental with payload:"
echo "$RENTAL_PAYLOAD" | jq '.'

echo -e "\nSending request..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/transactions/new-rental" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$RENTAL_PAYLOAD" \
  --max-time 30)

echo -e "\nResponse:"
echo "$RESPONSE" | jq '.'

# Extract transaction ID if successful
TRANSACTION_ID=$(echo "$RESPONSE" | jq -r '.transaction.id // empty')

if [ -n "$TRANSACTION_ID" ]; then
    echo -e "\nRental created successfully with ID: $TRANSACTION_ID"
    
    echo -e "\nTesting /api/transactions/rentals endpoint..."
    RENTALS=$(curl -s -X GET "$BASE_URL/api/transactions/rentals" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/json")
    
    RENTAL_COUNT=$(echo "$RENTALS" | jq '. | length')
    echo "Found $RENTAL_COUNT rental(s)"
    
    if [ "$RENTAL_COUNT" -gt 0 ]; then
        echo -e "\nFirst rental:"
        echo "$RENTALS" | jq '.[0]'
        
        # Check if our rental is in the list
        FOUND=$(echo "$RENTALS" | jq --arg id "$TRANSACTION_ID" '.[] | select(.id == $id)')
        if [ -n "$FOUND" ]; then
            echo -e "\n✅ SUCCESS: Our created rental is returned by the rentals endpoint!"
        else
            echo -e "\n❌ ERROR: Our created rental was not found in the rentals list"
        fi
    fi
else
    echo -e "\n❌ Failed to create rental. Checking if there are any existing rentals..."
    
    RENTALS=$(curl -s -X GET "$BASE_URL/api/transactions/rentals" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/json")
    
    RENTAL_COUNT=$(echo "$RENTALS" | jq '. | length')
    echo "Found $RENTAL_COUNT existing rental(s)"
    
    if [ "$RENTAL_COUNT" -gt 0 ]; then
        echo -e "\nFirst rental:"
        echo "$RENTALS" | jq '.[0]'
    fi
fi