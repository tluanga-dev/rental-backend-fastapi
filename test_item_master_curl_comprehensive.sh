#!/bin/bash

# Comprehensive Item Master API Tests
# This script tests all Item Master endpoints with various scenarios
# including success cases, validation errors, and edge cases

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8000/api"
MASTER_DATA_URL="${BASE_URL}/master-data"
ITEM_URL="${MASTER_DATA_URL}/item-master"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_section() {
    echo -e "\n${YELLOW}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
}

# Function to check HTTP status code
check_status() {
    local expected=$1
    local actual=$2
    local test_name=$3
    
    if [ "$actual" = "$expected" ]; then
        print_success "$test_name (Status: $actual)"
        return 0
    else
        print_error "$test_name (Expected: $expected, Got: $actual)"
        return 1
    fi
}

# Store test data
declare -A TEST_DATA

# 1. AUTHENTICATION
print_section "1. AUTHENTICATION"

print_info "Logging in to get JWT token..."
AUTH_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "admin@example.com",
        "password": "admin123"
    }')

TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    print_success "Login successful - Token obtained"
    AUTH_HEADER="Authorization: Bearer $TOKEN"
else
    print_error "Login failed - Could not obtain token"
    echo "Response: $AUTH_RESPONSE"
    exit 1
fi

# 2. SETUP TEST DATA
print_section "2. SETTING UP TEST DATA"

# Create test unit of measurement
print_info "Creating test unit of measurement..."
UNIT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${MASTER_DATA_URL}/units" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Pieces",
        "abbreviation": "pcs",
        "description": "Individual pieces"
    }')

UNIT_BODY=$(echo "$UNIT_RESPONSE" | head -n -1)
UNIT_STATUS=$(echo "$UNIT_RESPONSE" | tail -n 1)

if [ "$UNIT_STATUS" = "201" ] || [ "$UNIT_STATUS" = "409" ]; then
    if [ "$UNIT_STATUS" = "201" ]; then
        UNIT_ID=$(echo $UNIT_BODY | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        TEST_DATA["unit_id"]=$UNIT_ID
        print_success "Unit of measurement created"
    else
        # Get existing unit
        UNITS_RESPONSE=$(curl -s -X GET "${MASTER_DATA_URL}/units?name=Pieces" -H "$AUTH_HEADER")
        UNIT_ID=$(echo $UNITS_RESPONSE | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
        TEST_DATA["unit_id"]=$UNIT_ID
        print_info "Using existing unit of measurement"
    fi
else
    print_error "Failed to create unit of measurement (Status: $UNIT_STATUS)"
fi

# Create test brand
print_info "Creating test brand..."
BRAND_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${MASTER_DATA_URL}/brands" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Brand",
        "description": "Brand for testing"
    }')

BRAND_BODY=$(echo "$BRAND_RESPONSE" | head -n -1)
BRAND_STATUS=$(echo "$BRAND_RESPONSE" | tail -n 1)

if [ "$BRAND_STATUS" = "201" ] || [ "$BRAND_STATUS" = "409" ]; then
    if [ "$BRAND_STATUS" = "201" ]; then
        BRAND_ID=$(echo $BRAND_BODY | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        TEST_DATA["brand_id"]=$BRAND_ID
        print_success "Brand created"
    else
        # Get existing brand
        BRANDS_RESPONSE=$(curl -s -X GET "${MASTER_DATA_URL}/brands?name=Test%20Brand" -H "$AUTH_HEADER")
        BRAND_ID=$(echo $BRANDS_RESPONSE | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
        TEST_DATA["brand_id"]=$BRAND_ID
        print_info "Using existing brand"
    fi
else
    print_error "Failed to create brand (Status: $BRAND_STATUS)"
fi

# Create test category
print_info "Creating test category..."
CATEGORY_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${MASTER_DATA_URL}/categories" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Category",
        "description": "Category for testing"
    }')

CATEGORY_BODY=$(echo "$CATEGORY_RESPONSE" | head -n -1)
CATEGORY_STATUS=$(echo "$CATEGORY_RESPONSE" | tail -n 1)

if [ "$CATEGORY_STATUS" = "201" ] || [ "$CATEGORY_STATUS" = "409" ]; then
    if [ "$CATEGORY_STATUS" = "201" ]; then
        CATEGORY_ID=$(echo $CATEGORY_BODY | grep -o '"id":"[^"]*' | cut -d'"' -f4)
        TEST_DATA["category_id"]=$CATEGORY_ID
        print_success "Category created"
    else
        # Get existing category
        CATEGORIES_RESPONSE=$(curl -s -X GET "${MASTER_DATA_URL}/categories?name=Test%20Category" -H "$AUTH_HEADER")
        CATEGORY_ID=$(echo $CATEGORIES_RESPONSE | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
        TEST_DATA["category_id"]=$CATEGORY_ID
        print_info "Using existing category"
    fi
else
    print_error "Failed to create category (Status: $CATEGORY_STATUS)"
fi

# 3. CREATE ITEM TESTS
print_section "3. CREATE ITEM TESTS"

# Test 3.1: Create valid rental item with all fields
print_info "Test 3.1: Creating rental item with all fields..."
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"Professional Camera\",
        \"item_status\": \"ACTIVE\",
        \"brand_id\": \"${TEST_DATA[brand_id]}\",
        \"category_id\": \"${TEST_DATA[category_id]}\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"rental_rate_per_period\": 150.00,
        \"rental_period\": \"1\",
        \"security_deposit\": 500.00,
        \"description\": \"High-end professional DSLR camera\",
        \"specifications\": \"24MP, Full Frame, 4K Video\",
        \"model_number\": \"CAM-PRO-2024\",
        \"serial_number_required\": true,
        \"warranty_period_days\": \"365\",
        \"reorder_level\": \"2\",
        \"reorder_quantity\": \"5\",
        \"is_rentable\": true,
        \"is_saleable\": false
    }")

CREATE_BODY=$(echo "$CREATE_RESPONSE" | head -n -1)
CREATE_STATUS=$(echo "$CREATE_RESPONSE" | tail -n 1)

if check_status "201" "$CREATE_STATUS" "Create rental item with all fields"; then
    ITEM_ID=$(echo $CREATE_BODY | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    ITEM_SKU=$(echo $CREATE_BODY | grep -o '"sku":"[^"]*' | cut -d'"' -f4)
    TEST_DATA["rental_item_id"]=$ITEM_ID
    TEST_DATA["rental_item_sku"]=$ITEM_SKU
    print_info "Created item ID: $ITEM_ID, SKU: $ITEM_SKU"
fi

# Test 3.2: Create valid sale item with minimal fields
print_info "Test 3.2: Creating sale item with minimal fields..."
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"Camera Battery\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"sale_price\": 45.99,
        \"is_rentable\": false,
        \"is_saleable\": true
    }")

CREATE_STATUS=$(echo "$CREATE_RESPONSE" | tail -n 1)
CREATE_BODY=$(echo "$CREATE_RESPONSE" | head -n -1)

if check_status "201" "$CREATE_STATUS" "Create sale item with minimal fields"; then
    SALE_ITEM_ID=$(echo $CREATE_BODY | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    TEST_DATA["sale_item_id"]=$SALE_ITEM_ID
fi

# Test 3.3: Create item with validation error - missing required field
print_info "Test 3.3: Testing validation - missing required field..."
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "item_name": "Invalid Item"
    }')

CREATE_STATUS=$(echo "$CREATE_RESPONSE" | tail -n 1)
check_status "422" "$CREATE_STATUS" "Validation error - missing unit_of_measurement_id"

# Test 3.4: Create item with business rule violation - both rentable and saleable
print_info "Test 3.4: Testing business rule - both rentable and saleable..."
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"Invalid Item Type\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"is_rentable\": true,
        \"is_saleable\": true
    }")

CREATE_STATUS=$(echo "$CREATE_RESPONSE" | tail -n 1)
check_status "422" "$CREATE_STATUS" "Business rule violation - item cannot be both rentable and saleable"

# Test 3.5: Create item with business rule violation - neither rentable nor saleable
print_info "Test 3.5: Testing business rule - neither rentable nor saleable..."
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"Invalid Item Type 2\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"is_rentable\": false,
        \"is_saleable\": false
    }")

CREATE_STATUS=$(echo "$CREATE_RESPONSE" | tail -n 1)
check_status "422" "$CREATE_STATUS" "Business rule violation - item must be either rentable or saleable"

# Test 3.6: Create item with invalid numeric string
print_info "Test 3.6: Testing validation - invalid numeric string..."
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"Invalid Numeric\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"rental_period\": \"abc\",
        \"is_rentable\": true,
        \"is_saleable\": false
    }")

CREATE_STATUS=$(echo "$CREATE_RESPONSE" | tail -n 1)
check_status "422" "$CREATE_STATUS" "Validation error - invalid rental_period"

# 4. READ ITEM TESTS
print_section "4. READ ITEM TESTS"

# Test 4.1: Get item by ID
print_info "Test 4.1: Getting item by ID..."
GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/${TEST_DATA[rental_item_id]}" \
    -H "$AUTH_HEADER")

GET_STATUS=$(echo "$GET_RESPONSE" | tail -n 1)
check_status "200" "$GET_STATUS" "Get item by ID"

# Test 4.2: Get item by SKU
print_info "Test 4.2: Getting item by SKU..."
GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/sku/${TEST_DATA[rental_item_sku]}" \
    -H "$AUTH_HEADER")

GET_STATUS=$(echo "$GET_RESPONSE" | tail -n 1)
check_status "200" "$GET_STATUS" "Get item by SKU"

# Test 4.3: Get non-existent item
print_info "Test 4.3: Getting non-existent item..."
GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/00000000-0000-0000-0000-000000000000" \
    -H "$AUTH_HEADER")

GET_STATUS=$(echo "$GET_RESPONSE" | tail -n 1)
check_status "404" "$GET_STATUS" "Get non-existent item returns 404"

# 5. UPDATE ITEM TESTS
print_section "5. UPDATE ITEM TESTS"

# Test 5.1: Partial update - change description only
print_info "Test 5.1: Partial update - changing description..."
UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "$ITEM_URL/${TEST_DATA[rental_item_id]}" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "description": "Updated professional DSLR camera description"
    }')

UPDATE_STATUS=$(echo "$UPDATE_RESPONSE" | tail -n 1)
check_status "200" "$UPDATE_STATUS" "Partial update - description only"

# Test 5.2: Update item status
print_info "Test 5.2: Updating item status to INACTIVE..."
UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "$ITEM_URL/${TEST_DATA[rental_item_id]}" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "item_status": "INACTIVE"
    }')

UPDATE_STATUS=$(echo "$UPDATE_RESPONSE" | tail -n 1)
check_status "200" "$UPDATE_STATUS" "Update item status"

# Test 5.3: Update with validation error
print_info "Test 5.3: Update with validation error - negative price..."
UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "$ITEM_URL/${TEST_DATA[rental_item_id]}" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "rental_rate_per_period": -50.00
    }')

UPDATE_STATUS=$(echo "$UPDATE_RESPONSE" | tail -n 1)
check_status "422" "$UPDATE_STATUS" "Update validation error - negative price"

# Test 5.4: Update with business rule violation
print_info "Test 5.4: Update with business rule violation..."
UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "$ITEM_URL/${TEST_DATA[rental_item_id]}" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{
        "is_rentable": true,
        "is_saleable": true
    }')

UPDATE_STATUS=$(echo "$UPDATE_RESPONSE" | tail -n 1)
check_status "422" "$UPDATE_STATUS" "Update business rule violation"

# 6. LIST AND SEARCH TESTS
print_section "6. LIST AND SEARCH TESTS"

# Test 6.1: List all items with pagination
print_info "Test 6.1: Listing items with pagination..."
LIST_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?skip=0&limit=10" \
    -H "$AUTH_HEADER")

LIST_STATUS=$(echo "$LIST_RESPONSE" | tail -n 1)
check_status "200" "$LIST_STATUS" "List items with pagination"

# Test 6.2: Search items by term
print_info "Test 6.2: Searching items by term 'Camera'..."
SEARCH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?search=Camera" \
    -H "$AUTH_HEADER")

SEARCH_STATUS=$(echo "$SEARCH_RESPONSE" | tail -n 1)
check_status "200" "$SEARCH_STATUS" "Search items by term"

# Test 6.3: Filter by status
print_info "Test 6.3: Filtering items by status ACTIVE..."
FILTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?item_status=ACTIVE" \
    -H "$AUTH_HEADER")

FILTER_STATUS=$(echo "$FILTER_RESPONSE" | tail -n 1)
check_status "200" "$FILTER_STATUS" "Filter items by status"

# Test 6.4: Filter by rentable
print_info "Test 6.4: Filtering rentable items..."
FILTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?is_rentable=true" \
    -H "$AUTH_HEADER")

FILTER_STATUS=$(echo "$FILTER_RESPONSE" | tail -n 1)
check_status "200" "$FILTER_STATUS" "Filter rentable items"

# Test 6.5: Filter by saleable
print_info "Test 6.5: Filtering saleable items..."
FILTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?is_saleable=true" \
    -H "$AUTH_HEADER")

FILTER_STATUS=$(echo "$FILTER_RESPONSE" | tail -n 1)
check_status "200" "$FILTER_STATUS" "Filter saleable items"

# Test 6.6: Combined filters
print_info "Test 6.6: Combined filters - ACTIVE + rentable + search..."
FILTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?item_status=ACTIVE&is_rentable=true&search=Camera" \
    -H "$AUTH_HEADER")

FILTER_STATUS=$(echo "$FILTER_RESPONSE" | tail -n 1)
check_status "200" "$FILTER_STATUS" "Combined filters"

# Test 6.7: Filter by brand
print_info "Test 6.7: Filtering items by brand..."
FILTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?brand_id=${TEST_DATA[brand_id]}" \
    -H "$AUTH_HEADER")

FILTER_STATUS=$(echo "$FILTER_RESPONSE" | tail -n 1)
check_status "200" "$FILTER_STATUS" "Filter items by brand"

# Test 6.8: Filter by category
print_info "Test 6.8: Filtering items by category..."
FILTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?category_id=${TEST_DATA[category_id]}" \
    -H "$AUTH_HEADER")

FILTER_STATUS=$(echo "$FILTER_RESPONSE" | tail -n 1)
check_status "200" "$FILTER_STATUS" "Filter items by category"

# 7. SPECIALIZED ENDPOINTS
print_section "7. SPECIALIZED ENDPOINTS"

# Test 7.1: Get rental items only
print_info "Test 7.1: Getting rental items only..."
RENTAL_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/types/rental" \
    -H "$AUTH_HEADER")

RENTAL_STATUS=$(echo "$RENTAL_RESPONSE" | tail -n 1)
check_status "200" "$RENTAL_STATUS" "Get rental items only"

# Test 7.2: Get sale items only
print_info "Test 7.2: Getting sale items only..."
SALE_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/types/sale" \
    -H "$AUTH_HEADER")

SALE_STATUS=$(echo "$SALE_RESPONSE" | tail -n 1)
check_status "200" "$SALE_STATUS" "Get sale items only"

# Test 7.3: Get items by category endpoint
print_info "Test 7.3: Getting items by category endpoint..."
CATEGORY_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/category/${TEST_DATA[category_id]}" \
    -H "$AUTH_HEADER")

CATEGORY_STATUS=$(echo "$CATEGORY_RESPONSE" | tail -n 1)
check_status "200" "$CATEGORY_STATUS" "Get items by category"

# Test 7.4: Get items by brand endpoint
print_info "Test 7.4: Getting items by brand endpoint..."
BRAND_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/brand/${TEST_DATA[brand_id]}" \
    -H "$AUTH_HEADER")

BRAND_STATUS=$(echo "$BRAND_RESPONSE" | tail -n 1)
check_status "200" "$BRAND_STATUS" "Get items by brand"

# Test 7.5: Get low stock items
print_info "Test 7.5: Getting low stock items..."
LOW_STOCK_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/low-stock/" \
    -H "$AUTH_HEADER")

LOW_STOCK_STATUS=$(echo "$LOW_STOCK_RESPONSE" | tail -n 1)
check_status "200" "$LOW_STOCK_STATUS" "Get low stock items"

# Test 7.6: Search endpoint
print_info "Test 7.6: Using search endpoint..."
SEARCH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/search/Camera" \
    -H "$AUTH_HEADER")

SEARCH_STATUS=$(echo "$SEARCH_RESPONSE" | tail -n 1)
check_status "200" "$SEARCH_STATUS" "Search endpoint"

# 8. COUNT ENDPOINT
print_section "8. COUNT ENDPOINT"

# Test 8.1: Count all items
print_info "Test 8.1: Counting all items..."
COUNT_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/count/total" \
    -H "$AUTH_HEADER")

COUNT_STATUS=$(echo "$COUNT_RESPONSE" | tail -n 1)
check_status "200" "$COUNT_STATUS" "Count all items"

# Test 8.2: Count with filters
print_info "Test 8.2: Counting with filters..."
COUNT_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/count/total?is_rentable=true&item_status=ACTIVE" \
    -H "$AUTH_HEADER")

COUNT_STATUS=$(echo "$COUNT_RESPONSE" | tail -n 1)
check_status "200" "$COUNT_STATUS" "Count with filters"

# 9. SKU MANAGEMENT
print_section "9. SKU MANAGEMENT"

# Test 9.1: Generate SKU preview
print_info "Test 9.1: Generating SKU preview..."
SKU_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL/skus/generate" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"category_id\": \"${TEST_DATA[category_id]}\",
        \"item_name\": \"Test Product\",
        \"is_rentable\": true,
        \"is_saleable\": false
    }")

SKU_STATUS=$(echo "$SKU_RESPONSE" | tail -n 1)
check_status "200" "$SKU_STATUS" "Generate SKU preview"

# Test 9.2: Bulk generate SKUs
print_info "Test 9.2: Bulk generating SKUs..."
BULK_SKU_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL/skus/bulk-generate" \
    -H "$AUTH_HEADER")

BULK_SKU_STATUS=$(echo "$BULK_SKU_RESPONSE" | tail -n 1)
check_status "200" "$BULK_SKU_STATUS" "Bulk generate SKUs"

# 10. DELETE TESTS
print_section "10. DELETE TESTS"

# Test 10.1: Delete item (soft delete)
print_info "Test 10.1: Deleting item (soft delete)..."
DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$ITEM_URL/${TEST_DATA[rental_item_id]}" \
    -H "$AUTH_HEADER")

DELETE_STATUS=$(echo "$DELETE_RESPONSE" | tail -n 1)
check_status "204" "$DELETE_STATUS" "Delete item"

# Test 10.2: Delete non-existent item
print_info "Test 10.2: Deleting non-existent item..."
DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$ITEM_URL/00000000-0000-0000-0000-000000000000" \
    -H "$AUTH_HEADER")

DELETE_STATUS=$(echo "$DELETE_RESPONSE" | tail -n 1)
check_status "404" "$DELETE_STATUS" "Delete non-existent item returns 404"

# 11. ERROR SCENARIOS
print_section "11. ERROR SCENARIOS"

# Test 11.1: Invalid authentication
print_info "Test 11.1: Testing invalid authentication..."
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL" \
    -H "Authorization: Bearer invalid_token")

UNAUTH_STATUS=$(echo "$UNAUTH_RESPONSE" | tail -n 1)
check_status "401" "$UNAUTH_STATUS" "Invalid authentication"

# Test 11.2: Missing authentication
print_info "Test 11.2: Testing missing authentication..."
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL")

UNAUTH_STATUS=$(echo "$UNAUTH_RESPONSE" | tail -n 1)
check_status "401" "$UNAUTH_STATUS" "Missing authentication"

# Test 11.3: Malformed JSON
print_info "Test 11.3: Testing malformed JSON..."
MALFORMED_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{invalid json}')

MALFORMED_STATUS=$(echo "$MALFORMED_RESPONSE" | tail -n 1)
check_status "422" "$MALFORMED_STATUS" "Malformed JSON"

# Test 11.4: Invalid UUID format
print_info "Test 11.4: Testing invalid UUID format..."
INVALID_UUID_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL/not-a-uuid" \
    -H "$AUTH_HEADER")

INVALID_UUID_STATUS=$(echo "$INVALID_UUID_RESPONSE" | tail -n 1)
check_status "422" "$INVALID_UUID_STATUS" "Invalid UUID format"

# Test 11.5: Invalid enum value
print_info "Test 11.5: Testing invalid enum value..."
INVALID_ENUM_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"Invalid Status Item\",
        \"item_status\": \"INVALID_STATUS\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"is_rentable\": true,
        \"is_saleable\": false
    }")

INVALID_ENUM_STATUS=$(echo "$INVALID_ENUM_RESPONSE" | tail -n 1)
check_status "422" "$INVALID_ENUM_STATUS" "Invalid enum value"

# 12. EDGE CASES
print_section "12. EDGE CASES"

# Test 12.1: Very long item name
print_info "Test 12.1: Testing very long item name..."
LONG_NAME=$(python3 -c "print('A' * 201)")  # 201 characters (exceeds 200 limit)
LONG_NAME_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"$LONG_NAME\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"is_rentable\": true,
        \"is_saleable\": false
    }")

LONG_NAME_STATUS=$(echo "$LONG_NAME_RESPONSE" | tail -n 1)
check_status "422" "$LONG_NAME_STATUS" "Item name too long"

# Test 12.2: Empty item name
print_info "Test 12.2: Testing empty item name..."
EMPTY_NAME_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"is_rentable\": true,
        \"is_saleable\": false
    }")

EMPTY_NAME_STATUS=$(echo "$EMPTY_NAME_RESPONSE" | tail -n 1)
check_status "422" "$EMPTY_NAME_STATUS" "Empty item name"

# Test 12.3: Zero rental period
print_info "Test 12.3: Testing zero rental period..."
ZERO_PERIOD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ITEM_URL" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
        \"item_name\": \"Zero Period Item\",
        \"unit_of_measurement_id\": \"${TEST_DATA[unit_id]}\",
        \"rental_period\": \"0\",
        \"is_rentable\": true,
        \"is_saleable\": false
    }")

ZERO_PERIOD_STATUS=$(echo "$ZERO_PERIOD_RESPONSE" | tail -n 1)
check_status "422" "$ZERO_PERIOD_STATUS" "Zero rental period"

# Test 12.4: Large pagination limit
print_info "Test 12.4: Testing large pagination limit..."
LARGE_LIMIT_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?limit=1001" \
    -H "$AUTH_HEADER")

LARGE_LIMIT_STATUS=$(echo "$LARGE_LIMIT_RESPONSE" | tail -n 1)
check_status "422" "$LARGE_LIMIT_STATUS" "Pagination limit too large"

# Test 12.5: Negative pagination skip
print_info "Test 12.5: Testing negative pagination skip..."
NEGATIVE_SKIP_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$ITEM_URL?skip=-1" \
    -H "$AUTH_HEADER")

NEGATIVE_SKIP_STATUS=$(echo "$NEGATIVE_SKIP_RESPONSE" | tail -n 1)
check_status "422" "$NEGATIVE_SKIP_STATUS" "Negative pagination skip"

# CLEANUP
print_section "CLEANUP"

# Clean up sale item
if [ -n "${TEST_DATA[sale_item_id]}" ]; then
    curl -s -X DELETE "$ITEM_URL/${TEST_DATA[sale_item_id]}" -H "$AUTH_HEADER" > /dev/null
    print_info "Cleaned up sale item"
fi

# Note: rental item already deleted in test 10.1

# SUMMARY
print_section "TEST SUMMARY"

echo -e "\nTotal Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed! ✨${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi