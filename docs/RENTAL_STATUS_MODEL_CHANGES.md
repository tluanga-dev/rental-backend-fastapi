# Rental Status Feature - Model Changes Documentation

## Overview

This document details all the database models affected by the rental status feature implementation, showing the specific changes made to existing models and new models created.

## 📊 Models Affected Summary

| Model | Type | Changes Made | Impact Level |
|-------|------|--------------|--------------|
| `RentalStatusLog` | **NEW** | Complete new model | High |
| `RentalStatusChangeReason` | **NEW** | New enum | Medium |
| `TransactionLine` | **ENHANCED** | Added status field | Medium |
| `RentalLifecycle` | **EXISTING** | Used as-is with relationships | Low |
| `TransactionHeader` | **EXISTING** | Used existing rental status fields | Low |
| `SystemSetting` | **ENHANCED** | New settings added | Low |

## 🆕 New Models Created

### 1. RentalStatusLog Model
**File**: `app/modules/transactions/models/rental_lifecycle.py`

**Purpose**: Historical tracking of all rental status changes for comprehensive audit trails.

```python
class RentalStatusLog(BaseModel):
    """
    Historical log of rental status changes for both headers and line items.
    
    Tracks all status transitions with context about why they occurred,
    enabling comprehensive audit trails and status history reporting.
    """
    
    __tablename__ = "rental_status_logs"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid4, comment="Unique log entry identifier")
    
    # Entity identification
    transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=False, comment="Transaction being tracked")
    transaction_line_id = Column(UUIDType(), ForeignKey("transaction_lines.id"), nullable=True, comment="Specific line item (null for header-level changes)")
    rental_lifecycle_id = Column(UUIDType(), ForeignKey("rental_lifecycles.id"), nullable=True, comment="Associated rental lifecycle")
    
    # Status change details
    old_status = Column(String(30), nullable=True, comment="Previous status (null for initial status)")
    new_status = Column(String(30), nullable=False, comment="New status after change")
    change_reason = Column(String(30), nullable=False, comment="Reason for the status change")
    change_trigger = Column(String(50), nullable=True, comment="What triggered the change (scheduled_job, return_event_id, etc.)")
    
    # Change context
    changed_by = Column(UUIDType(), nullable=True, comment="User who initiated the change (null for system changes)")
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="When the change occurred")
    
    # Additional context
    notes = Column(Text, nullable=True, comment="Additional notes about the status change")
    status_metadata = Column(JSON, nullable=True, comment="Additional context data (overdue days, return quantities, etc.)")
    
    # System tracking
    system_generated = Column(Boolean, nullable=False, default=False, comment="Whether this change was system-generated")
    batch_id = Column(String(50), nullable=True, comment="Batch ID for scheduled updates")
    
    # Relationships
    transaction = relationship("TransactionHeader", lazy="select")
    transaction_line = relationship("TransactionLine", lazy="select")
    rental_lifecycle = relationship("RentalLifecycle", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index("idx_status_log_transaction", "transaction_id"),
        Index("idx_status_log_line", "transaction_line_id"),
        Index("idx_status_log_changed_at", "changed_at"),
        Index("idx_status_log_reason", "change_reason"),
        Index("idx_status_log_batch", "batch_id"),
        Index("idx_status_log_system", "system_generated"),
    )
```

**Database Table Structure**:
```sql
CREATE TABLE rental_status_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES transaction_headers(id),
    transaction_line_id UUID REFERENCES transaction_lines(id),
    rental_lifecycle_id UUID REFERENCES rental_lifecycles(id),
    old_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    change_reason VARCHAR(30) NOT NULL,
    change_trigger VARCHAR(50),
    changed_by UUID,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    status_metadata JSONB,
    system_generated BOOLEAN NOT NULL DEFAULT FALSE,
    batch_id VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX idx_status_log_transaction ON rental_status_logs(transaction_id);
CREATE INDEX idx_status_log_line ON rental_status_logs(transaction_line_id);
CREATE INDEX idx_status_log_changed_at ON rental_status_logs(changed_at);
CREATE INDEX idx_status_log_reason ON rental_status_logs(change_reason);
CREATE INDEX idx_status_log_batch ON rental_status_logs(batch_id);
CREATE INDEX idx_status_log_system ON rental_status_logs(system_generated);
```

### 2. RentalStatusChangeReason Enum
**File**: `app/modules/transactions/models/rental_lifecycle.py`

```python
class RentalStatusChangeReason(PyEnum):
    """Reasons for rental status changes."""
    SCHEDULED_UPDATE = "SCHEDULED_UPDATE"      # Daily automated status check
    RETURN_EVENT = "RETURN_EVENT"              # Status change due to return processing
    MANUAL_UPDATE = "MANUAL_UPDATE"            # Manual status change by user
    EXTENSION = "EXTENSION"                    # Rental period extension
    LATE_FEE_APPLIED = "LATE_FEE_APPLIED"     # Late fee application
    DAMAGE_ASSESSMENT = "DAMAGE_ASSESSMENT"    # Damage assessment during return
```

## 🔄 Enhanced Existing Models

### 1. TransactionLine Model
**File**: `app/modules/transactions/models/transaction_lines.py`

**Changes Made**:
```python
# ADDED: Line-level rental status tracking
current_rental_status = Column(String(30), nullable=True, comment="Current rental status for this line item")
```

**Impact**: 
- Enables individual line item status tracking as required by PRD
- Allows granular status management per rental item
- Supports partial return scenarios

**Before/After Comparison**:
```python
# BEFORE: No line-level status tracking
class TransactionLine(BaseModel):
    # ... existing fields ...
    returned_quantity = Column(Numeric(10, 2), nullable=True, default=0)
    return_date = Column(Date, nullable=True)
    # No status field

# AFTER: Line-level status tracking added
class TransactionLine(BaseModel):
    # ... existing fields ...
    returned_quantity = Column(Numeric(10, 2), nullable=True, default=0)
    return_date = Column(Date, nullable=True)
    current_rental_status = Column(String(30), nullable=True, comment="Current rental status for this line item")  # NEW
```

### 2. SystemSetting Model
**File**: `app/modules/system/service.py`

**Changes Made**: Added new system settings for task scheduling configuration.

```python
# NEW SETTINGS ADDED:
{
    "setting_key": "rental_status_check_enabled",
    "setting_name": "Rental Status Check Enabled",
    "setting_type": SettingType.BOOLEAN,
    "setting_category": SettingCategory.SYSTEM,
    "setting_value": "true",
    "default_value": "true",
    "description": "Enable automated rental status checking",
    "is_system": True,
    "display_order": "4"
},
{
    "setting_key": "rental_status_check_time",
    "setting_name": "Rental Status Check Time",
    "setting_type": SettingType.STRING,
    "setting_category": SettingCategory.SYSTEM,
    "setting_value": "00:00",
    "default_value": "00:00",
    "description": "Time to run daily rental status check (HH:MM format)",
    "is_system": True,
    "display_order": "5"
},
{
    "setting_key": "rental_status_log_retention_days",
    "setting_name": "Rental Status Log Retention Days",
    "setting_type": SettingType.INTEGER,
    "setting_category": SettingCategory.SYSTEM,
    "setting_value": "365",
    "default_value": "365",
    "description": "Number of days to retain rental status change logs",
    "is_system": True,
    "display_order": "6"
},
{
    "setting_key": "task_scheduler_timezone",
    "setting_name": "Task Scheduler Timezone",
    "setting_type": SettingType.STRING,
    "setting_category": SettingCategory.SYSTEM,
    "setting_value": "UTC",
    "default_value": "UTC",
    "description": "Timezone for scheduled tasks",
    "is_system": True,
    "display_order": "7"
}
```

## ✅ Existing Models Used (No Changes Required)

### 1. TransactionHeader Model
**File**: `app/modules/transactions/models/transaction_headers.py`

**Existing Fields Used**:
```python
# These existing fields are used by the status system:
current_rental_status = Column(String(30), nullable=True)  # Already existed
rental_start_date = Column(Date, nullable=True)           # Already existed  
rental_end_date = Column(Date, nullable=True)             # Already existed
transaction_type = Column(String(20), nullable=False)     # Already existed
```

**Why No Changes**: The header model already had all necessary fields for status tracking.

### 2. RentalLifecycle Model
**File**: `app/modules/transactions/models/rental_lifecycle.py`

**Existing Fields Used**:
```python
# These existing fields are used by the status system:
current_status = Column(String(30), nullable=False)           # Already existed
last_status_change = Column(DateTime, nullable=False)         # Already existed
status_changed_by = Column(UUIDType(), nullable=True)         # Already existed
expected_return_date = Column(Date, nullable=True)            # Already existed
total_returned_quantity = Column(Numeric(10, 2), nullable=False, default=0)  # Already existed
```

**Why No Changes**: The lifecycle model already provided all necessary operational tracking.

### 3. RentalStatus Enum
**File**: `app/modules/transactions/models/transaction_headers.py`

**Existing Enum Used**:
```python
class RentalStatus(PyEnum):
    """Rental transaction status enum - already existed"""
    ACTIVE = "ACTIVE"
    LATE = "LATE"
    EXTENDED = "EXTENDED"
    PARTIAL_RETURN = "PARTIAL_RETURN"
    LATE_PARTIAL_RETURN = "LATE_PARTIAL_RETURN"
    COMPLETED = "COMPLETED"
```

**Why No Changes**: The existing enum already matched PRD requirements perfectly.

## 🔗 Model Relationships

### New Relationships Added

```python
# RentalStatusLog relationships to existing models
class RentalStatusLog(BaseModel):
    # Foreign Key Relationships
    transaction_id → TransactionHeader.id
    transaction_line_id → TransactionLine.id (optional)
    rental_lifecycle_id → RentalLifecycle.id (optional)
    
    # Object Relationships
    transaction = relationship("TransactionHeader", lazy="select")
    transaction_line = relationship("TransactionLine", lazy="select")
    rental_lifecycle = relationship("RentalLifecycle", lazy="select")
```

### Relationship Diagram

```
TransactionHeader (existing)
    ├── TransactionLine (enhanced with current_rental_status)
    ├── RentalLifecycle (existing)
    └── RentalStatusLog (new) ──┐
                                ├── Links to TransactionHeader
                                ├── Links to TransactionLine (optional)
                                └── Links to RentalLifecycle (optional)
```

## 📁 Model Files Modified

### Files with Changes:
1. **`app/modules/transactions/models/rental_lifecycle.py`** - Added `RentalStatusLog` and `RentalStatusChangeReason`
2. **`app/modules/transactions/models/__init__.py`** - Added imports for new models
3. **`app/modules/system/service.py`** - Added new system settings
4. **`app/main.py`** - Added imports for new models

### Files with No Changes (Used As-Is):
1. **`app/modules/transactions/models/transaction_headers.py`** - Used existing fields
2. **`app/modules/transactions/models/transaction_lines.py`** - Only added one field
3. **`app/modules/transactions/models/events.py`** - Used for audit trail integration

## 🗄️ Database Migration Required

### Migration File Created:
**File**: `alembic/versions/add_rental_status_log_models.py`

**Key Changes**:
```sql
-- Create new rental_status_logs table
CREATE TABLE rental_status_logs (
    -- All fields as defined in model
);

-- Add indexes for performance
CREATE INDEX idx_status_log_transaction ON rental_status_logs(transaction_id);
CREATE INDEX idx_status_log_line ON rental_status_logs(transaction_line_id);
-- ... additional indexes

-- Add current_rental_status to transaction_lines if not exists
ALTER TABLE transaction_lines 
ADD COLUMN current_rental_status VARCHAR(30) 
COMMENT 'Current rental status for this line item';

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column() ...
CREATE TRIGGER update_rental_status_logs_updated_at ...
```

## 📊 Data Flow Between Models

### Status Change Flow:
```
1. RentalStatusCalculator calculates new status
2. RentalStatusUpdater updates TransactionHeader.current_rental_status
3. RentalStatusUpdater updates TransactionLine.current_rental_status  
4. RentalStatusUpdater updates RentalLifecycle.current_status
5. RentalStatusUpdater creates RentalStatusLog entry with full context
6. All changes committed atomically
```

### Query Patterns:
```python
# Get current status
current_status = transaction.current_rental_status

# Get line item statuses  
line_statuses = [line.current_rental_status for line in transaction.transaction_lines]

# Get status history
status_history = session.query(RentalStatusLog).filter(
    RentalStatusLog.transaction_id == transaction_id
).order_by(RentalStatusLog.changed_at.desc()).all()

# Get status changes for specific reason
scheduled_changes = session.query(RentalStatusLog).filter(
    RentalStatusLog.change_reason == RentalStatusChangeReason.SCHEDULED_UPDATE.value
).all()
```

## 🔒 Data Integrity Considerations

### Foreign Key Constraints:
- `rental_status_logs.transaction_id` → `transaction_headers.id` (NOT NULL)
- `rental_status_logs.transaction_line_id` → `transaction_lines.id` (NULLABLE)
- `rental_status_logs.rental_lifecycle_id` → `rental_lifecycles.id` (NULLABLE)

### Data Validation:
- Status values must match enum definitions
- Timestamps are automatically managed
- JSON metadata is validated before storage
- Batch IDs follow specific format patterns

## 🎯 Impact Assessment

### Low Impact:
- **SystemSetting**: Only new settings added, no breaking changes
- **TransactionHeader**: No changes, used existing fields
- **RentalLifecycle**: No changes, used existing fields

### Medium Impact:
- **TransactionLine**: Added one new field, backward compatible
- **RentalStatusChangeReason**: New enum, additive change

### High Impact:
- **RentalStatusLog**: Completely new model requiring migration
- **Database**: New table with indexes and triggers

### Breaking Changes: **NONE**
All changes are additive and maintain backward compatibility with existing code.

---

## Summary

The rental status feature implementation was designed to minimize changes to existing models while providing comprehensive status tracking capabilities. The approach was:

1. **Leverage Existing Models**: Used existing `TransactionHeader`, `RentalLifecycle`, and `RentalStatus` enum without changes
2. **Minimal Enhancements**: Added only one field to `TransactionLine` for line-level status tracking  
3. **New Dedicated Model**: Created `RentalStatusLog` for comprehensive audit trails
4. **Configuration Extension**: Added system settings for scheduling configuration
5. **Zero Breaking Changes**: All modifications are backward compatible

This approach ensures the feature is fully functional while maintaining system stability and requiring minimal migration effort.