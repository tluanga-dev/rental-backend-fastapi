# Purchase Transaction Debugging Guide

## 🔍 Comprehensive Logging System

I've implemented a comprehensive logging system to debug the purchase transaction + stock level integration issue. This will help identify exactly what's happening during purchase transactions.

## 📁 Log Files Location

All logs are saved in the `logs/` directory:

- **Markdown Logs**: `logs/purchase_transactions_YYYYMMDD_HHMMSS.md`
- **Standard Logs**: `logs/purchase_transactions_YYYYMMDD_HHMMSS.log`

## 📋 What Gets Logged

### 1. **Purchase Transaction Start**
- Complete purchase request data
- Items count, supplier ID, location ID
- Timestamp with milliseconds

### 2. **Validation Steps**
- Supplier validation (✅ PASSED / ❌ FAILED)
- Location validation (✅ PASSED / ❌ FAILED)  
- Items validation (✅ PASSED / ❌ FAILED)
- Details about what was found/not found

### 3. **Transaction Creation**
- Generated transaction number
- Transaction header details (ID, type, status, total)
- Database session operations

### 4. **Stock Level Processing**
- Each item processing step
- Existing stock checks
- Stock level creation/updates
- Session operations

### 5. **Database Operations**
- Transaction flush operations
- Stock level additions to session
- Final commit operations
- Rollback operations (on errors)

### 6. **Completion/Errors**
- Success/failure status
- Final response data
- Complete error traces with context

## 🧪 How to Use for Debugging

### Step 1: Make a Purchase Transaction
```bash
curl -X POST "http://localhost:8000/api/transactions/new-purchase" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @sample_purchase_data.json
```

### Step 2: Check the Latest Log File
```bash
# Find the latest log file
ls -la logs/purchase_transactions_*.md | tail -1

# View the log content
cat logs/purchase_transactions_YYYYMMDD_HHMMSS.md
```

### Step 3: Look for Key Indicators

#### ✅ **Success Indicators:**
- All validation steps show "✅ PASSED"
- "📝 Transaction Header Created" appears
- "📦 Stock Level Processing Started" appears
- Each item shows "📈 Stock Update" or "➕ Stock Creation"
- "💾 Transaction Commit" shows "✅ SUCCESS"
- "🎯 Purchase Transaction Completed" shows "✅ COMPLETED"

#### ❌ **Failure Indicators:**
- Any validation shows "❌ FAILED"
- "💥 ERROR OCCURRED" section appears
- "💾 Transaction Commit" shows "❌ FAILED"
- Missing stock level processing logs

## 📊 Common Issues to Look For

### 1. **Validation Failures**
**Look for:**
```markdown
#### 🔍 Validation: Supplier Validation
**Status:** ❌ FAILED
**Details:** Supplier ID 550e8400-e29b-41d4-a716-446655440001 not found
```

**Solution:** Create the supplier/location/items first.

### 2. **Stock Level Creation Issues**
**Look for:**
```markdown
##### ➕ Stock Creation (New Stock)
**Item ID:** 550e8400-e29b-41d4-a716-446655440010
**Action:** CREATE NEW
```

If this appears but stock levels are still empty, there's a database issue.

### 3. **Transaction Rollback**
**Look for:**
```markdown
#### 💾 Transaction Commit
**Status:** ❌ FAILED
**Error:** [error details]
```

This indicates the entire transaction was rolled back.

### 4. **Missing Stock Processing**
If you don't see "📦 Stock Level Processing Started", the stock integration isn't being called.

## 🔧 Real-Time Debugging

### Console Logs
The system also outputs to console in real-time:
```
INFO - 🛒 PURCHASE TRANSACTION STARTED - ID: uuid
INFO - 🔍 VALIDATION - Supplier Validation: ✅ PASSED
INFO - 📝 TRANSACTION CREATED - Number: PUR-20240714-1234
INFO - 📦 STOCK LEVEL PROCESSING STARTED - 3 items
INFO - ➕ STOCK CREATE - Item: uuid, Quantity: 10
INFO - 💾 TRANSACTION COMMITTED SUCCESSFULLY
```

### Log File Structure
```markdown
# Purchase Transaction Debug Log

### 🛒 Purchase Transaction Started
**Timestamp:** 2025-07-14 16:43:33.826
**Transaction ID:** Not yet assigned

**Purchase Data:**
```json
{
  "supplier_id": "550e8400-e29b-41d4-a716-446655440001",
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "items": [...]
}
```

#### 🔍 Validation: Supplier Validation
**Status:** ✅ PASSED
**Details:** Supplier found: Test Tech Supplier

#### 📝 Transaction Header Created
**Transaction Details:**
- **ID:** 550e8400-e29b-41d4-a716-446655440003
- **Number:** PUR-20240714-1234
- **Type:** PURCHASE
- **Status:** COMPLETED
- **Total Amount:** $1234.56

#### 📦 Stock Level Processing Started
**Items to Process:** 3

##### ➕ Stock Creation (New Stock)
**Item ID:** 550e8400-e29b-41d4-a716-446655440010
**Action:** CREATE NEW
**Initial Quantity:** 10 units

#### 💾 Transaction Commit
**Status:** ✅ SUCCESS
**Result:** All changes committed to database

### 🎯 Purchase Transaction Completed
**Status:** ✅ COMPLETED
**Transaction ID:** 550e8400-e29b-41d4-a716-446655440003
```

## 🎯 Next Steps

1. **Create a purchase transaction** using your API
2. **Check the latest log file** in the `logs/` directory
3. **Identify the issue** from the detailed logs
4. **Fix the root cause** based on what you find
5. **Verify the fix** by checking stock levels again

The logs will show you **exactly** where the process is failing and why stock levels aren't being created! 🔍