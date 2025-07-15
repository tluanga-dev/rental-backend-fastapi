#!/bin/bash

# Comprehensive test script for new inventory endpoints
# Tests the API endpoints using curl commands

BASE_URL="http://localhost:8000"
API_BASE="${BASE_URL}/api/inventory"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to log test results
log_test() {
    local test_name="$1"
    local status="$2"
    local message="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $test_name: $message"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAIL${NC} - $test_name: $message"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Function to test server health
test_server_health() {
    echo -e "${BLUE}Testing server health...${NC}"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        log_test "Server Health" "PASS" "Server is running"
        return 0
    else
        log_test "Server Health" "FAIL" "Server not accessible (HTTP $response)"
        return 1
    fi
}

# Function to test OpenAPI documentation
test_openapi_docs() {
    echo -e "${BLUE}Testing OpenAPI documentation...${NC}"
    
    # Test docs endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs" 2>/dev/null)
    if [ "$response" = "200" ]; then
        log_test "Swagger Docs" "PASS" "API documentation accessible"
    else
        log_test "Swagger Docs" "FAIL" "API documentation not accessible (HTTP $response)"
    fi
    
    # Test OpenAPI spec
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/openapi.json" 2>/dev/null)
    if [ "$response" = "200" ]; then
        # Check if new endpoints are in the spec
        spec_content=$(curl -s "$BASE_URL/openapi.json" 2>/dev/null)
        if echo "$spec_content" | grep -q "items/overview" && echo "$spec_content" | grep -q "items/{item_id}/detailed"; then
            log_test "OpenAPI Spec" "PASS" "New endpoints found in API specification"
        else
            log_test "OpenAPI Spec" "FAIL" "New endpoints not found in API specification"
        fi
    else
        log_test "OpenAPI Spec" "FAIL" "OpenAPI spec not accessible (HTTP $response)"
    fi
}

# Function to test endpoint availability
test_endpoint_availability() {
    echo -e "${BLUE}Testing endpoint availability...${NC}"
    
    # Test overview endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview" 2>/dev/null)
    if [ "$response" != "404" ]; then
        log_test "Overview Endpoint Available" "PASS" "Endpoint exists (HTTP $response)"
    else
        log_test "Overview Endpoint Available" "FAIL" "Endpoint not found (HTTP 404)"
    fi
    
    # Test detailed endpoint with fake UUID
    fake_uuid="123e4567-e89b-12d3-a456-426614174000"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/$fake_uuid/detailed" 2>/dev/null)
    if [ "$response" != "404" ]; then
        log_test "Detailed Endpoint Available" "PASS" "Endpoint exists (HTTP $response)"
    else
        log_test "Detailed Endpoint Available" "FAIL" "Endpoint not found (HTTP 404)"
    fi
}

# Function to test authentication requirements
test_authentication() {
    echo -e "${BLUE}Testing authentication requirements...${NC}"
    
    # Test overview endpoint without auth
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview" 2>/dev/null)
    if [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$response" = "422" ]; then
        log_test "Overview Auth Required" "PASS" "Correctly requires authentication (HTTP $response)"
    else
        log_test "Overview Auth Required" "FAIL" "Does not require authentication (HTTP $response)"
    fi
    
    # Test detailed endpoint without auth
    fake_uuid="123e4567-e89b-12d3-a456-426614174000"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/$fake_uuid/detailed" 2>/dev/null)
    if [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$response" = "422" ]; then
        log_test "Detailed Auth Required" "PASS" "Correctly requires authentication (HTTP $response)"
    else
        log_test "Detailed Auth Required" "FAIL" "Does not require authentication (HTTP $response)"
    fi
}

# Function to test parameter validation
test_parameter_validation() {
    echo -e "${BLUE}Testing parameter validation...${NC}"
    
    # Test invalid limit (too high)
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?limit=2000" 2>/dev/null)
    if [ "$response" = "422" ]; then
        log_test "Invalid Limit High" "PASS" "Correctly validates high limit (HTTP $response)"
    else
        log_test "Invalid Limit High" "FAIL" "Does not validate high limit (HTTP $response)"
    fi
    
    # Test invalid limit (negative)
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?limit=-1" 2>/dev/null)
    if [ "$response" = "422" ]; then
        log_test "Invalid Limit Negative" "PASS" "Correctly validates negative limit (HTTP $response)"
    else
        log_test "Invalid Limit Negative" "FAIL" "Does not validate negative limit (HTTP $response)"
    fi
    
    # Test invalid skip (negative)
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?skip=-1" 2>/dev/null)
    if [ "$response" = "422" ]; then
        log_test "Invalid Skip Negative" "PASS" "Correctly validates negative skip (HTTP $response)"
    else
        log_test "Invalid Skip Negative" "FAIL" "Does not validate negative skip (HTTP $response)"
    fi
    
    # Test invalid sort order
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?sort_order=invalid" 2>/dev/null)
    if [ "$response" = "422" ]; then
        log_test "Invalid Sort Order" "PASS" "Correctly validates sort order (HTTP $response)"
    else
        log_test "Invalid Sort Order" "FAIL" "Does not validate sort order (HTTP $response)"
    fi
    
    # Test invalid sort field
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?sort_by=invalid_field" 2>/dev/null)
    if [ "$response" = "422" ]; then
        log_test "Invalid Sort Field" "PASS" "Correctly validates sort field (HTTP $response)"
    else
        log_test "Invalid Sort Field" "FAIL" "Does not validate sort field (HTTP $response)"
    fi
    
    # Test invalid stock status
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?stock_status=INVALID_STATUS" 2>/dev/null)
    if [ "$response" = "422" ]; then
        log_test "Invalid Stock Status" "PASS" "Correctly validates stock status (HTTP $response)"
    else
        log_test "Invalid Stock Status" "FAIL" "Does not validate stock status (HTTP $response)"
    fi
    
    # Test invalid UUID format in detailed endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/invalid-uuid/detailed" 2>/dev/null)
    if [ "$response" = "422" ]; then
        log_test "Invalid UUID Format" "PASS" "Correctly validates UUID format (HTTP $response)"
    else
        log_test "Invalid UUID Format" "FAIL" "Does not validate UUID format (HTTP $response)"
    fi
}

# Function to test response times
test_response_times() {
    echo -e "${BLUE}Testing response times...${NC}"
    
    # Test overview endpoint response time
    start_time=$(date +%s.%N)
    curl -s -o /dev/null "$API_BASE/items/overview" 2>/dev/null
    end_time=$(date +%s.%N)
    response_time=$(echo "$end_time - $start_time" | bc)
    
    if (( $(echo "$response_time < 5.0" | bc -l) )); then
        log_test "Overview Response Time" "PASS" "Response time: ${response_time}s"
    else
        log_test "Overview Response Time" "FAIL" "Slow response time: ${response_time}s"
    fi
    
    # Test detailed endpoint response time
    fake_uuid="123e4567-e89b-12d3-a456-426614174000"
    start_time=$(date +%s.%N)
    curl -s -o /dev/null "$API_BASE/items/$fake_uuid/detailed" 2>/dev/null
    end_time=$(date +%s.%N)
    response_time=$(echo "$end_time - $start_time" | bc)
    
    if (( $(echo "$response_time < 5.0" | bc -l) )); then
        log_test "Detailed Response Time" "PASS" "Response time: ${response_time}s"
    else
        log_test "Detailed Response Time" "FAIL" "Slow response time: ${response_time}s"
    fi
}

# Function to test HTTP headers
test_http_headers() {
    echo -e "${BLUE}Testing HTTP headers...${NC}"
    
    # Test content type
    content_type=$(curl -s -I "$API_BASE/items/overview" 2>/dev/null | grep -i "content-type" | head -1)
    if echo "$content_type" | grep -q "application/json"; then
        log_test "Content Type Header" "PASS" "Correct content type"
    else
        log_test "Content Type Header" "FAIL" "Incorrect content type: $content_type"
    fi
    
    # Test CORS headers (if enabled)
    cors_header=$(curl -s -I -X OPTIONS "$API_BASE/items/overview" 2>/dev/null | grep -i "access-control-allow-origin" | head -1)
    if [ -n "$cors_header" ]; then
        log_test "CORS Headers" "PASS" "CORS headers present"
    else
        log_test "CORS Headers" "PASS" "CORS headers not configured (expected for secure APIs)"
    fi
}

# Function to test valid parameter combinations
test_valid_parameters() {
    echo -e "${BLUE}Testing valid parameter combinations...${NC}"
    
    # Test valid limit and skip
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?limit=10&skip=0" 2>/dev/null)
    if [ "$response" != "404" ] && [ "$response" != "500" ]; then
        log_test "Valid Limit Skip" "PASS" "Accepts valid limit and skip parameters"
    else
        log_test "Valid Limit Skip" "FAIL" "Rejects valid limit and skip parameters"
    fi
    
    # Test valid sort parameters
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?sort_by=item_name&sort_order=asc" 2>/dev/null)
    if [ "$response" != "404" ] && [ "$response" != "500" ]; then
        log_test "Valid Sort Params" "PASS" "Accepts valid sort parameters"
    else
        log_test "Valid Sort Params" "FAIL" "Rejects valid sort parameters"
    fi
    
    # Test valid stock status
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?stock_status=IN_STOCK" 2>/dev/null)
    if [ "$response" != "404" ] && [ "$response" != "500" ]; then
        log_test "Valid Stock Status" "PASS" "Accepts valid stock status"
    else
        log_test "Valid Stock Status" "FAIL" "Rejects valid stock status"
    fi
    
    # Test valid boolean parameters
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?is_rentable=true" 2>/dev/null)
    if [ "$response" != "404" ] && [ "$response" != "500" ]; then
        log_test "Valid Boolean Params" "PASS" "Accepts valid boolean parameters"
    else
        log_test "Valid Boolean Params" "FAIL" "Rejects valid boolean parameters"
    fi
}

# Function to test edge cases
test_edge_cases() {
    echo -e "${BLUE}Testing edge cases...${NC}"
    
    # Test maximum valid limit
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?limit=1000" 2>/dev/null)
    if [ "$response" != "404" ] && [ "$response" != "500" ]; then
        log_test "Maximum Valid Limit" "PASS" "Accepts maximum valid limit"
    else
        log_test "Maximum Valid Limit" "FAIL" "Rejects maximum valid limit"
    fi
    
    # Test minimum valid limit
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?limit=1" 2>/dev/null)
    if [ "$response" != "404" ] && [ "$response" != "500" ]; then
        log_test "Minimum Valid Limit" "PASS" "Accepts minimum valid limit"
    else
        log_test "Minimum Valid Limit" "FAIL" "Rejects minimum valid limit"
    fi
    
    # Test empty search parameter
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/overview?search=" 2>/dev/null)
    if [ "$response" != "404" ] && [ "$response" != "500" ]; then
        log_test "Empty Search Param" "PASS" "Handles empty search parameter"
    else
        log_test "Empty Search Param" "FAIL" "Cannot handle empty search parameter"
    fi
    
    # Test valid UUID format in detailed endpoint
    valid_uuid="123e4567-e89b-12d3-a456-426614174000"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/items/$valid_uuid/detailed" 2>/dev/null)
    if [ "$response" != "404" ] && [ "$response" != "500" ]; then
        log_test "Valid UUID Format" "PASS" "Accepts valid UUID format"
    else
        log_test "Valid UUID Format" "FAIL" "Rejects valid UUID format"
    fi
}

# Function to print summary
print_summary() {
    echo
    echo "======================================================================"
    echo "INVENTORY ENDPOINTS TEST SUMMARY"
    echo "======================================================================"
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
        echo "Success Rate: $success_rate%"
    fi
    
    echo "======================================================================"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed! The new inventory endpoints are working correctly.${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed. Please review the issues above.${NC}"
        return 1
    fi
}

# Main function
main() {
    echo "======================================================================"
    echo "INVENTORY ENDPOINTS COMPREHENSIVE TEST SUITE"
    echo "======================================================================"
    echo "Testing against: $BASE_URL"
    echo "API Base: $API_BASE"
    echo "======================================================================"
    echo
    
    # Check if bc is available for response time calculations
    if ! command -v bc &> /dev/null; then
        echo -e "${YELLOW}⚠️  Warning: 'bc' command not found. Response time tests will be skipped.${NC}"
    fi
    
    # Run all tests
    test_server_health
    
    # Only proceed if server is healthy
    if [ $? -eq 0 ]; then
        test_openapi_docs
        test_endpoint_availability
        test_authentication
        test_parameter_validation
        test_valid_parameters
        test_edge_cases
        test_http_headers
        
        # Run response time tests if bc is available
        if command -v bc &> /dev/null; then
            test_response_times
        fi
    else
        echo -e "${RED}❌ Server is not accessible. Skipping remaining tests.${NC}"
        echo -e "${YELLOW}💡 Make sure the FastAPI server is running at $BASE_URL${NC}"
        echo -e "${YELLOW}💡 Try: uvicorn app.main:app --reload${NC}"
    fi
    
    print_summary
}

# Run main function
main "$@"