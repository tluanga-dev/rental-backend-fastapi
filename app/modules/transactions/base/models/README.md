# Transaction Models Organization

This directory contains the transaction models organized into meaningful, maintainable files.

## File Structure

```
models/
├── __init__.py              # Public API - imports all models
├── transaction_headers.py   # TransactionHeader model and related enums
├── transaction_lines.py     # TransactionLine model and related enums
├── rental_lifecycle.py      # Rental operational models
├── metadata.py              # Transaction metadata models
├── inspections.py           # Inspection and credit memo models
└── README.md               # This file
```

## Core Models

### 📄 transaction_headers.py
**Primary Model:** `TransactionHeader`

The main financial record for all transactions (sales, purchases, rentals).

**Key Features:**
- Financial tracking (amounts, payments, deposits)
- Rental-specific fields (dates, status, advance payments)
- Status management and payment tracking
- Helpful properties for rental operations

**Enums Included:**
- `TransactionType` - SALE, PURCHASE, RENTAL, RETURN, ADJUSTMENT
- `TransactionStatus` - PENDING, PROCESSING, COMPLETED, etc.
- `PaymentMethod` - CASH, CREDIT_CARD, BANK_TRANSFER, etc.
- `PaymentStatus` - PENDING, PAID, PARTIAL, FAILED, REFUNDED
- `RentalPeriodUnit` - HOUR, DAY, WEEK, MONTH
- `RentalStatus` - ACTIVE, LATE, EXTENDED, PARTIAL_RETURN, etc.

### 📄 transaction_lines.py
**Primary Model:** `TransactionLine`

Individual line items within transactions - products, services, fees, etc.

**Key Features:**
- Item identification and pricing
- Rental-specific tracking per line
- Return quantity tracking
- Inventory and fulfillment status
- Helpful properties for rental calculations

**Enums Included:**
- `LineItemType` - PRODUCT, SERVICE, DISCOUNT, TAX, SHIPPING, FEE

### 📄 rental_lifecycle.py
**Primary Models:** `RentalLifecycle`, `RentalReturnEvent`, `RentalItemInspection`

Operational tracking for rental workflows - separate from financial data.

**Key Features:**
- Rental status management
- Return event tracking (multiple returns per rental)
- Per-item inspection with damage assessment
- Fee accumulation and payment tracking

## Design Principles

### 1. **Separation of Concerns**
- **Financial Data** → `transaction_headers.py` & `transaction_lines.py`
- **Operational Data** → `rental_lifecycle.py`
- **Metadata** → `metadata.py` & `inspections.py`

### 2. **Backward Compatibility**
The `__init__.py` file re-exports all models, so existing imports continue to work:

```python
# Still works
from app.modules.transactions.models import TransactionHeader, TransactionLine

# New explicit imports also work
from app.modules.transactions.models.transaction_headers import TransactionHeader
from app.modules.transactions.models.transaction_lines import TransactionLine
```

### 3. **Clear Relationships**
```
TransactionHeader (1) ←→ (Many) TransactionLine
      ↓
RentalLifecycle (1) ←→ (Many) RentalReturnEvent
      ↓
RentalItemInspection (per line item)
```

## Enhanced Features

### TransactionHeader Properties
- `is_rental` - Check if transaction is a rental
- `is_overdue` - Check if rental is past due
- `days_overdue` - Calculate days past due
- `rental_duration_days` - Total rental period in days

### TransactionLine Properties
- `remaining_quantity` - Quantity not yet returned
- `is_fully_returned` - All quantity returned
- `is_partially_returned` - Some but not all returned
- `return_percentage` - Percentage of quantity returned
- `is_rental_overdue` - Line-specific overdue check

### Rental Lifecycle Features
- Multi-stage return process
- Per-item inspection tracking
- Fee calculation and accumulation
- Payment and refund processing
- Status transition management

## Usage Examples

### Creating a Rental Transaction
```python
from app.modules.transactions.models import TransactionHeader, TransactionType, RentalStatus

transaction = TransactionHeader(
    transaction_number="R-2025-001",
    transaction_type=TransactionType.RENTAL,
    rental_start_date=date.today(),
    rental_end_date=date.today() + timedelta(days=7),
    current_rental_status=RentalStatus.ACTIVE,
    deposit_amount=100.00,
    deposit_paid=True
)
```

### Managing Rental Returns
```python
from app.modules.transactions.models import RentalLifecycle, RentalReturnEvent, ReturnEventType

# Create lifecycle tracking
lifecycle = RentalLifecycle(
    transaction_id=transaction.id,
    current_status=RentalStatus.ACTIVE.value
)

# Record return event
return_event = RentalReturnEvent(
    rental_lifecycle_id=lifecycle.id,
    event_type=ReturnEventType.PARTIAL_RETURN.value,
    event_date=date.today(),
    total_quantity_returned=2
)
```

## Migration Notes

- Database schema remains unchanged - only code organization improved
- All existing functionality preserved
- New helpful properties and methods added
- Enhanced rental status tracking capabilities
- Better separation for future maintenance

This reorganization makes the codebase more maintainable while preserving all existing functionality and adding powerful new rental management capabilities.