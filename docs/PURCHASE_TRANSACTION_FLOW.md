# Purchase Transaction Flow Documentation

## Table of Contents
1. [Overview](#overview)
2. [Database Models](#database-models)
3. [API Endpoint](#api-endpoint)
4. [Step-by-Step Process Flow](#step-by-step-process-flow)
5. [Sample Data Flow](#sample-data-flow)
6. [Database Tables Hit](#database-tables-hit)
7. [Stock Level Management](#stock-level-management)
8. [Error Handling](#error-handling)
9. [Transaction Logging](#transaction-logging)

## Overview

The purchase transaction flow in the rental management system handles the procurement of inventory items from suppliers. This process involves creating transaction records, updating stock levels, tracking stock movements, and maintaining a complete audit trail.

### Key Features
- Unified transaction model (purchases share the same infrastructure as sales and rentals)
- Automatic stock level updates with movement tracking
- Support for multiple item conditions (A, B, C, D)
- Comprehensive validation and error handling
- Detailed logging for debugging and auditing

## Database Models

### 1. TransactionHeader (transaction_headers table)
The main transaction record that stores purchase information.

```python
class TransactionHeader:
    id: UUID                    # Primary key
    transaction_number: str     # Format: PUR-YYYYMMDD-XXXX
    transaction_type: Enum      # Set to "PURCHASE"
    transaction_date: datetime  # Purchase date and time
    customer_id: str           # Stores supplier_id (reused field)
    location_id: str           # Delivery location
    status: Enum               # Usually "COMPLETED" for purchases
    payment_status: Enum       # Usually "PENDING" initially
    
    # Financial fields
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    
    # Relationships
    transaction_lines: List[TransactionLine]
```

### 2. TransactionLine (transaction_lines table)
Individual line items within a purchase transaction.

```python
class TransactionLine:
    id: UUID
    transaction_id: UUID       # Links to TransactionHeader
    line_number: int          # Sequential line number
    line_type: Enum           # "PRODUCT" for purchase items
    item_id: str              # Links to item master
    
    description: str          # Format: "Purchase: {item_id} (Condition: {A-D})"
    quantity: Decimal
    unit_price: Decimal       # Purchase cost per unit
    tax_rate: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    line_total: Decimal
    
    notes: str               # Additional notes
```

### 3. StockLevel (stock_levels table)
Tracks current inventory quantities at each location.

```python
class StockLevel:
    id: UUID
    item_id: UUID
    location_id: UUID
    quantity_on_hand: Decimal     # Total stock
    quantity_available: Decimal   # Available for sale/rent
    quantity_on_rent: Decimal     # Currently rented out
    
    # Unique constraint on (item_id, location_id)
```

### 4. StockMovement (stock_movements table)
Immutable audit records for all stock changes.

```python
class StockMovement:
    id: UUID
    stock_level_id: UUID
    item_id: UUID
    location_id: UUID
    
    movement_type: str         # "PURCHASE" for purchases
    reference_type: str        # "TRANSACTION"
    reference_id: str          # Transaction ID
    
    quantity_change: Decimal   # Positive for purchases
    quantity_before: Decimal
    quantity_after: Decimal
    
    reason: str               # Human-readable reason
    notes: str                # Additional context
    created_at: datetime      # Timestamp
```

## API Endpoint

### POST /api/transactions/new-purchase

**Request Schema (NewPurchaseRequest):**
```json
{
    "supplier_id": "550e8400-e29b-41d4-a716-446655440001",
    "location_id": "550e8400-e29b-41d4-a716-446655440002",
    "purchase_date": "2024-01-15",
    "notes": "Monthly inventory replenishment",
    "reference_number": "PO-2024-001",
    "items": [
        {
            "item_id": "550e8400-e29b-41d4-a716-446655440003",
            "quantity": 50,
            "unit_cost": 25.99,
            "tax_rate": 8.5,
            "discount_amount": 0,
            "condition": "A",
            "notes": "New stock"
        }
    ]
}
```

**Response Schema (NewPurchaseResponse):**
```json
{
    "success": true,
    "message": "Purchase transaction created successfully",
    "transaction_id": "550e8400-e29b-41d4-a716-446655440004",
    "transaction_number": "PUR-20240115-3847",
    "data": {
        // Full transaction details
    }
}
```

## Step-by-Step Process Flow

### 1. Request Validation
```python
# In create_new_purchase() method
async def create_new_purchase(self, purchase_data: NewPurchaseRequest):
    # Start logging
    self.logger.log_purchase_start(purchase_data.model_dump())
```

### 2. Supplier Validation
```python
# Validate supplier exists
supplier = await supplier_repo.get_by_id(purchase_data.supplier_id)
if not supplier:
    raise NotFoundError(f"Supplier with ID {purchase_data.supplier_id} not found")
```

### 3. Location Validation
```python
# Validate location exists
location = await location_repo.get_by_id(purchase_data.location_id)
if not location:
    raise NotFoundError(f"Location with ID {purchase_data.location_id} not found")
```

### 4. Item Validation
```python
# Validate all items exist
for item in purchase_data.items:
    item_exists = await item_repo.get_by_id(item.item_id)
    if not item_exists:
        raise NotFoundError(f"Item with ID {item.item_id} not found")
```

### 5. Transaction Number Generation
```python
# Generate unique transaction number
transaction_number = f"PUR-{purchase_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

# Ensure uniqueness
while await self.transaction_repository.get_by_number(transaction_number):
    transaction_number = f"PUR-{purchase_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
```

### 6. Create Transaction Header
```python
transaction = TransactionHeader(
    transaction_number=transaction_number,
    transaction_type=TransactionType.PURCHASE,
    transaction_date=datetime.combine(purchase_data.purchase_date, datetime.min.time()),
    customer_id=str(purchase_data.supplier_id),  # Supplier stored in customer_id
    location_id=str(purchase_data.location_id),
    status=TransactionStatus.COMPLETED,
    payment_status=PaymentStatus.PENDING,
    notes=purchase_data.notes or "",
    subtotal=Decimal("0"),
    discount_amount=Decimal("0"),
    tax_amount=Decimal("0"),
    total_amount=Decimal("0"),
    paid_amount=Decimal("0")
)

self.session.add(transaction)
await self.session.flush()  # Get ID without committing
```

### 7. Create Transaction Lines
```python
for idx, item in enumerate(purchase_data.items):
    # Calculate line values
    line_subtotal = item.unit_cost * Decimal(str(item.quantity))
    tax_amount = (line_subtotal * (item.tax_rate or Decimal("0"))) / 100
    discount_amount = item.discount_amount or Decimal("0")
    line_total = line_subtotal + tax_amount - discount_amount

    # Create transaction line
    line = TransactionLine(
        transaction_id=str(transaction.id),
        line_number=idx + 1,
        line_type=LineItemType.PRODUCT,
        item_id=item.item_id,
        description=f"Purchase: {item.item_id} (Condition: {item.condition})",
        quantity=Decimal(str(item.quantity)),
        unit_price=item.unit_cost,
        tax_rate=item.tax_rate or Decimal("0"),
        tax_amount=tax_amount,
        discount_amount=discount_amount,
        line_total=line_total,
        notes=item.notes or ""
    )

    self.session.add(line)
```

### 8. Update Transaction Totals
```python
# Update header with calculated totals
transaction.subtotal = total_amount - tax_total + discount_total
transaction.tax_amount = tax_total
transaction.discount_amount = discount_total
transaction.total_amount = total_amount
```

### 9. Update Stock Levels
```python
async def _update_stock_levels_for_purchase(self, purchase_data, transaction):
    for item in purchase_data.items:
        # Check if stock level exists
        existing_stock = await self.inventory_service.stock_level_repository.get_by_item_location(
            item.item_id, purchase_data.location_id
        )
        
        if existing_stock:
            # Update existing stock level
            await self.inventory_service.adjust_stock_level(
                item_id=item.item_id,
                location_id=purchase_data.location_id,
                quantity_change=item.quantity,
                transaction_type="PURCHASE",
                reference_id=str(transaction.id),
                notes=f"Purchase transaction - Condition: {item.condition}"
            )
        else:
            # Create new stock level
            stock_data = StockLevelCreate(
                item_id=item.item_id,
                location_id=purchase_data.location_id,
                quantity_on_hand=Decimal(str(item.quantity)),
                quantity_available=Decimal(str(item.quantity)),
                quantity_on_rent=Decimal("0")
            )
            
            created_stock = await self.inventory_service.stock_level_repository.create(stock_data)
            
            # Create initial stock movement record
            await self.inventory_service._create_stock_movement_record(
                stock_level_id=created_stock.id,
                movement_type="PURCHASE",
                quantity_change=Decimal(str(item.quantity)),
                quantity_before=Decimal("0"),
                quantity_after=Decimal(str(item.quantity)),
                reference_type=ReferenceType.TRANSACTION,
                reference_id=str(transaction.id),
                reason=f"Initial purchase - Condition: {item.condition}",
                notes=f"Purchase transaction - Condition: {item.condition}"
            )
```

### 10. Commit Transaction
```python
# Commit all changes atomically
await self.session.commit()
await self.session.refresh(transaction)
```

## Sample Data Flow

### Initial Request
```json
{
    "supplier_id": "123e4567-e89b-12d3-a456-426614174000",
    "location_id": "456e7890-e89b-12d3-a456-426614174001",
    "purchase_date": "2024-01-15",
    "notes": "Q1 2024 inventory purchase",
    "reference_number": "PO-2024-Q1-001",
    "items": [
        {
            "item_id": "789e0123-e89b-12d3-a456-426614174002",
            "quantity": 100,
            "unit_cost": 15.50,
            "tax_rate": 8.5,
            "discount_amount": 50.00,
            "condition": "A",
            "notes": "Brand new items"
        },
        {
            "item_id": "012e3456-e89b-12d3-a456-426614174003",
            "quantity": 50,
            "unit_cost": 25.00,
            "tax_rate": 8.5,
            "discount_amount": 0,
            "condition": "B",
            "notes": "Slightly used items"
        }
    ]
}
```

### Created Transaction Header
```sql
INSERT INTO transaction_headers (
    id, transaction_number, transaction_type, transaction_date,
    customer_id, location_id, status, payment_status,
    subtotal, discount_amount, tax_amount, total_amount, paid_amount
) VALUES (
    'abc12345-e89b-12d3-a456-426614174004',
    'PUR-20240115-7823',
    'PURCHASE',
    '2024-01-15 00:00:00',
    '123e4567-e89b-12d3-a456-426614174000',  -- supplier_id
    '456e7890-e89b-12d3-a456-426614174001',
    'COMPLETED',
    'PENDING',
    2750.00,  -- subtotal
    50.00,    -- discount
    237.75,   -- tax
    2937.75,  -- total
    0.00      -- paid
);
```

### Created Transaction Lines
```sql
-- Line 1
INSERT INTO transaction_lines (
    id, transaction_id, line_number, line_type, item_id,
    description, quantity, unit_price, tax_rate, tax_amount,
    discount_amount, line_total
) VALUES (
    'def45678-e89b-12d3-a456-426614174005',
    'abc12345-e89b-12d3-a456-426614174004',
    1,
    'PRODUCT',
    '789e0123-e89b-12d3-a456-426614174002',
    'Purchase: 789e0123-e89b-12d3-a456-426614174002 (Condition: A)',
    100,
    15.50,
    8.5,
    131.75,   -- (1550 * 8.5%)
    50.00,
    1631.75   -- 1550 + 131.75 - 50
);

-- Line 2
INSERT INTO transaction_lines (
    id, transaction_id, line_number, line_type, item_id,
    description, quantity, unit_price, tax_rate, tax_amount,
    discount_amount, line_total
) VALUES (
    'ghi78901-e89b-12d3-a456-426614174006',
    'abc12345-e89b-12d3-a456-426614174004',
    2,
    'PRODUCT',
    '012e3456-e89b-12d3-a456-426614174003',
    'Purchase: 012e3456-e89b-12d3-a456-426614174003 (Condition: B)',
    50,
    25.00,
    8.5,
    106.25,   -- (1250 * 8.5%)
    0.00,
    1356.25   -- 1250 + 106.25
);
```

### Stock Level Updates
```sql
-- For existing stock level (Item 1)
UPDATE stock_levels 
SET 
    quantity_on_hand = quantity_on_hand + 100,
    quantity_available = quantity_available + 100,
    updated_at = CURRENT_TIMESTAMP
WHERE 
    item_id = '789e0123-e89b-12d3-a456-426614174002' 
    AND location_id = '456e7890-e89b-12d3-a456-426614174001';

-- For new stock level (Item 2)
INSERT INTO stock_levels (
    id, item_id, location_id, quantity_on_hand, 
    quantity_available, quantity_on_rent
) VALUES (
    'jkl01234-e89b-12d3-a456-426614174007',
    '012e3456-e89b-12d3-a456-426614174003',
    '456e7890-e89b-12d3-a456-426614174001',
    50,
    50,
    0
);
```

### Stock Movement Records
```sql
-- Movement for Item 1
INSERT INTO stock_movements (
    id, stock_level_id, item_id, location_id,
    movement_type, reference_type, reference_id,
    quantity_change, quantity_before, quantity_after,
    reason, notes
) VALUES (
    'mno34567-e89b-12d3-a456-426614174008',
    'existing-stock-level-id',
    '789e0123-e89b-12d3-a456-426614174002',
    '456e7890-e89b-12d3-a456-426614174001',
    'PURCHASE',
    'TRANSACTION',
    'abc12345-e89b-12d3-a456-426614174004',
    100,
    150,  -- existing quantity
    250,  -- new quantity
    'Purchase transaction',
    'Purchase transaction - Condition: A'
);

-- Movement for Item 2
INSERT INTO stock_movements (
    id, stock_level_id, item_id, location_id,
    movement_type, reference_type, reference_id,
    quantity_change, quantity_before, quantity_after,
    reason, notes
) VALUES (
    'pqr56789-e89b-12d3-a456-426614174009',
    'jkl01234-e89b-12d3-a456-426614174007',
    '012e3456-e89b-12d3-a456-426614174003',
    '456e7890-e89b-12d3-a456-426614174001',
    'PURCHASE',
    'TRANSACTION',
    'abc12345-e89b-12d3-a456-426614174004',
    50,
    0,   -- new stock
    50,  -- after purchase
    'Initial purchase - Condition: B',
    'Purchase transaction - Condition: B'
);
```

## Database Tables Hit

During a purchase transaction, the following database tables are accessed:

1. **suppliers** - Validate supplier exists
2. **locations** - Validate location exists
3. **items** - Validate all items exist
4. **transaction_headers** - Check for duplicate transaction number, create new purchase record
5. **transaction_lines** - Create line items for each purchased item
6. **stock_levels** - Check existing stock, create/update stock levels
7. **stock_movements** - Create audit records for all stock changes

### Query Sequence
```
1. SELECT * FROM suppliers WHERE id = :supplier_id
2. SELECT * FROM locations WHERE id = :location_id
3. SELECT * FROM items WHERE id IN (:item_ids)
4. SELECT * FROM transaction_headers WHERE transaction_number = :number
5. INSERT INTO transaction_headers ...
6. INSERT INTO transaction_lines ... (multiple)
7. SELECT * FROM stock_levels WHERE item_id = :item_id AND location_id = :location_id
8. UPDATE stock_levels ... OR INSERT INTO stock_levels ...
9. INSERT INTO stock_movements ... (one per item)
10. COMMIT
```

## Stock Level Management

### Stock Level Adjustment Logic
When a purchase is made, the system:

1. **Checks for existing stock level** at the specified location
2. **If exists**: Increases quantity_on_hand and quantity_available by purchase quantity
3. **If not exists**: Creates new stock level with purchased quantity
4. **Always creates** a stock movement record for audit trail

### Stock Movement Tracking
Every purchase creates a stock movement record with:
- **movement_type**: "PURCHASE"
- **reference_type**: "TRANSACTION"
- **reference_id**: Transaction ID
- **quantity_change**: Positive value (addition to stock)
- **quantity_before**: Stock level before purchase
- **quantity_after**: Stock level after purchase

## Error Handling

### Validation Errors
```python
# Supplier not found
NotFoundError: "Supplier with ID {supplier_id} not found"

# Location not found
NotFoundError: "Location with ID {location_id} not found"

# Item not found
NotFoundError: "Item with ID {item_id} not found"

# Invalid data format
ValidationError: "Invalid date format. Use YYYY-MM-DD format."
ValidationError: "Invalid UUID format: {value}"
```

### Transaction Rollback
If any error occurs during the process:
```python
except Exception as e:
    await self.session.rollback()
    self.logger.log_error(e, "Purchase Transaction Creation")
    raise e
```

## Transaction Logging

The system uses `PurchaseTransactionLogger` for comprehensive logging:

### Log Points
1. **Purchase Start** - Logs initial request data
2. **Validation Steps** - Logs each validation success/failure
3. **Transaction Creation** - Logs header creation
4. **Stock Processing** - Logs each stock level update
5. **Completion** - Logs final success with transaction details
6. **Errors** - Logs any failures with full context

### Sample Log Output
```
[2024-01-15 10:30:00] Starting Purchase Transaction Processing
[2024-01-15 10:30:00] Supplier Validation: SUCCESS - Supplier found: ABC Supplies Ltd
[2024-01-15 10:30:00] Location Validation: SUCCESS - Location found: Main Warehouse
[2024-01-15 10:30:00] Items Validation: SUCCESS - All 2 items validated successfully
[2024-01-15 10:30:00] Generated Transaction Number: PUR-20240115-7823
[2024-01-15 10:30:00] Transaction Header Created: abc12345-e89b-12d3-a456-426614174004
[2024-01-15 10:30:01] Processing Item 789e0123: quantity=100, existing_stock=150
[2024-01-15 10:30:01] Stock Quantity Adjusted with Movement Tracking
[2024-01-15 10:30:01] Processing Item 012e3456: quantity=50, new stock level created
[2024-01-15 10:30:01] Transaction Commit: SUCCESS
[2024-01-15 10:30:01] Purchase Transaction Completed Successfully: PUR-20240115-7823
```

## Summary

The purchase transaction flow is a comprehensive process that:
1. Validates all entities (supplier, location, items)
2. Creates a transaction header with type "PURCHASE"
3. Creates detailed line items for each purchased item
4. Automatically updates stock levels at the specified location
5. Creates immutable stock movement records for audit trail
6. Provides detailed logging throughout the process
7. Ensures data integrity through atomic transactions

This design ensures accurate inventory tracking, complete audit trails, and seamless integration with the broader transaction management system.