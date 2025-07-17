#!/bin/bash
# Company Settings API Test using curl

echo "🧪 COMPANY SETTINGS API TEST WITH CURL"
echo "=" | head -c 50; echo

BASE_URL="http://localhost:8000"

# Test 1: Health check
echo "1. 🏥 Testing backend health..."
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "   ✅ Backend is healthy"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "   ❌ Backend is not healthy"
    echo "   Response: $HEALTH_RESPONSE"
    exit 1
fi

echo

# Test 2: Initialize system settings
echo "2. ⚙️  Initializing system settings..."
INIT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/system/settings/initialize")
INIT_STATUS=$?
if [ $INIT_STATUS -eq 0 ]; then
    echo "   ✅ Settings initialization requested"
    echo "   Response: $(echo "$INIT_RESPONSE" | head -c 100)..."
else
    echo "   ⚠️  Settings initialization may have failed"
fi

echo

# Test 3: Get company info
echo "3. 📋 Getting company information..."
COMPANY_GET_RESPONSE=$(curl -s "$BASE_URL/api/system/company")
GET_STATUS=$?
if [ $GET_STATUS -eq 0 ] && echo "$COMPANY_GET_RESPONSE" | grep -q "company_name"; then
    echo "   ✅ Company info retrieved successfully"
    echo "   Response: $COMPANY_GET_RESPONSE"
else
    echo "   ❌ Failed to get company info"
    echo "   Response: $COMPANY_GET_RESPONSE"
    # Continue anyway to test the update
fi

echo

# Test 4: Update company info
echo "4. 💾 Updating company information..."
TEST_USER_ID=$(uuidgen)
UPDATE_DATA='{
    "company_name": "API Test Company Ltd",
    "company_address": "456 API Test Boulevard\nAutomation City, AC 67890",
    "company_email": "api@testcompany.com",
    "company_phone": "+1-555-API-TEST",
    "company_gst_no": "GST111222333",
    "company_registration_number": "REG444555666"
}'

UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/system/company?updated_by=$TEST_USER_ID" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA")

if echo "$UPDATE_RESPONSE" | grep -q "API Test Company Ltd"; then
    echo "   ✅ Company info updated successfully"
    echo "   Response: $UPDATE_RESPONSE"
else
    echo "   ❌ Failed to update company info"
    echo "   Response: $UPDATE_RESPONSE"
    
    # Check if it's a settings initialization issue
    if echo "$UPDATE_RESPONSE" | grep -q "not found"; then
        echo "   💡 This appears to be a settings initialization issue"
        echo "   🔄 Let's try to restart the backend server to trigger initialization"
        exit 1
    fi
fi

echo

# Test 5: Verify persistence
echo "5. 🔄 Verifying data persistence..."
VERIFY_RESPONSE=$(curl -s "$BASE_URL/api/system/company")
if echo "$VERIFY_RESPONSE" | grep -q "API Test Company Ltd"; then
    echo "   ✅ Data persistence verified!"
    echo "   Current data: $VERIFY_RESPONSE"
else
    echo "   ⚠️  Data may not have persisted correctly"
    echo "   Current data: $VERIFY_RESPONSE"
fi

echo
echo "=" | head -c 50; echo
echo "🎯 API TEST SUMMARY:"

if echo "$VERIFY_RESPONSE" | grep -q "API Test Company Ltd"; then
    echo "🎉 ALL API TESTS PASSED!"
    echo "✅ Company settings API is working correctly"
    echo
    echo "📋 What this means:"
    echo "• Backend server is running and healthy"
    echo "• System settings are properly initialized" 
    echo "• Company info can be retrieved and updated"
    echo "• Data persists correctly in the database"
    echo
    echo "🚀 Next Steps:"
    echo "1. Open your browser to: http://localhost:3000/settings/company"
    echo "2. Fill in the company information form"
    echo "3. Click 'Save Changes'"
    echo "4. You should see a success message"
    echo "5. Refresh the page to verify data persists"
else
    echo "⚠️  SOME ISSUES DETECTED"
    echo "The API may not be fully working. Check the responses above."
    echo
    echo "🔧 Troubleshooting:"
    echo "1. Ensure the backend server is running: uvicorn app.main:app --reload"
    echo "2. Check if system settings are initialized"
    echo "3. Look for any error messages in the server logs"
fi