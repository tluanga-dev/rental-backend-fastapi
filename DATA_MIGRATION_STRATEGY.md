# Data Migration Strategy: Boolean Fields Implementation

## Overview

This document outlines the strategy for migrating existing items from the `item_type` enum system to the new `is_rentable` and `is_saleable` boolean fields while maintaining data integrity and business logic consistency.

## Current State vs Target State

### Current State (item_type enum)
- `RENTAL`: Item available for rent only
- `SALE`: Item available for sale only  
- `BOTH`: Item available for both rent and sale

### Target State (boolean fields)
- `is_rentable`: Boolean indicating if item can be rented
- `is_saleable`: Boolean indicating if item can be sold
- **Constraint**: Both fields cannot be `true` simultaneously (mutual exclusion)

## Migration Challenge

The main challenge is handling items with `item_type = "BOTH"`, which violates the new mutual exclusion constraint where both `is_rentable` and `is_saleable` cannot be `true`.

## Migration Options

### Option 1: Split BOTH Items (Recommended)

**Strategy**: Create duplicate items for each `BOTH` type item
- Original item becomes rental-only: `is_rentable=true, is_saleable=false`
- New duplicate item becomes sale-only: `is_rentable=false, is_saleable=true`
- Append suffix to item codes to differentiate (e.g., `ITEM001-R` and `ITEM001-S`)

**Advantages**:
- Maintains all existing data
- Clear separation of business functions
- No data loss
- Supports inventory tracking separately

**Implementation**:
```sql
-- Step 1: Update simple mappings
UPDATE items SET is_rentable = true, is_saleable = false WHERE item_type = 'RENTAL';
UPDATE items SET is_rentable = false, is_saleable = true WHERE item_type = 'SALE';

-- Step 2: Handle BOTH items (requires application logic for duplicates)
-- This will be done via Python script
```

### Option 2: Force User Decision

**Strategy**: Require business users to decide the primary use case for each `BOTH` item
- Present list of `BOTH` items to administrators
- Allow them to choose rental vs sale for each item
- Update accordingly

**Advantages**:
- Business-driven decisions
- No duplicate data
- Clean migration

**Disadvantages**:
- Requires manual intervention
- May delay deployment
- Potential business disruption

### Option 3: Default Based on Pricing

**Strategy**: Use existing pricing data to determine primary function
- If `rental_price_per_day` exists and `sale_price` doesn't → Rental
- If `sale_price` exists and `rental_price_per_day` doesn't → Sale
- If both exist → Use higher revenue potential or default to rental

**Advantages**:
- Automated decision making
- Based on business data
- No manual intervention

**Disadvantages**:
- May not reflect actual business intent
- Could lead to incorrect categorization

## Recommended Implementation Plan

### Phase 1: Pre-Migration Analysis

1. **Analyze existing data**:
   ```sql
   SELECT 
     item_type,
     COUNT(*) as count,
     COUNT(CASE WHEN rental_price_per_day IS NOT NULL THEN 1 END) as has_rental_price,
     COUNT(CASE WHEN sale_price IS NOT NULL THEN 1 END) as has_sale_price
   FROM items 
   GROUP BY item_type;
   ```

2. **Identify problematic records**:
   ```sql
   SELECT id, item_code, item_name, item_type, rental_price_per_day, sale_price
   FROM items 
   WHERE item_type = 'BOTH'
   ORDER BY item_code;
   ```

### Phase 2: Migration Script

Create Python migration script:

```python
async def migrate_item_types():
    """Migrate existing items to boolean fields."""
    
    # Simple mappings
    await session.execute(
        update(Item)
        .where(Item.item_type == 'RENTAL')
        .values(is_rentable=True, is_saleable=False)
    )
    
    await session.execute(
        update(Item)
        .where(Item.item_type == 'SALE')
        .values(is_rentable=False, is_saleable=True)
    )
    
    # Handle BOTH items - Option 1 (Split)
    both_items = await session.execute(
        select(Item).where(Item.item_type == 'BOTH')
    )
    
    for item in both_items.scalars():
        # Update original to rental-only
        item.is_rentable = True
        item.is_saleable = False
        item.item_code = f"{item.item_code}-R"
        
        # Create sale-only duplicate
        sale_item = Item(
            item_code=f"{item.item_code.replace('-R', '')}-S",
            sku=f"{item.sku}-S",
            item_name=f"{item.item_name} (Sale)",
            item_type="SALE",
            is_rentable=False,
            is_saleable=True,
            # Copy other relevant fields
        )
        session.add(sale_item)
    
    await session.commit()
```

### Phase 3: Data Validation

1. **Verify migration results**:
   ```sql
   -- Check that all items have valid boolean combinations
   SELECT 
     is_rentable, 
     is_saleable, 
     COUNT(*) 
   FROM items 
   GROUP BY is_rentable, is_saleable;
   
   -- Should show:
   -- true, false (rental items)
   -- false, true (sale items)
   -- No true, true or false, false combinations
   ```

2. **Business validation**:
   - Verify total item count matches expectations
   - Check that pricing fields align with boolean flags
   - Confirm inventory relationships are maintained

### Phase 4: Cleanup

1. **Update item_type field** (optional):
   ```sql
   UPDATE items 
   SET item_type = CASE 
     WHEN is_rentable THEN 'RENTAL'
     WHEN is_saleable THEN 'SALE'
   END;
   ```

2. **Update related systems**:
   - Inventory management
   - Transaction records
   - Reporting systems

## Rollback Strategy

### Immediate Rollback (Pre-Production)
- Restore database from backup
- Re-run previous migration state

### Production Rollback
```sql
-- Revert boolean fields back to item_type enum
UPDATE items 
SET item_type = CASE 
  WHEN is_rentable = true AND is_saleable = false THEN 'RENTAL'
  WHEN is_rentable = false AND is_saleable = true THEN 'SALE'
END;

-- Handle duplicated items (requires business logic)
```

## Testing Strategy

### Unit Tests
- ✅ Schema validation (completed)
- ✅ Business logic validation (completed)
- Migration script testing

### Integration Tests
- Full migration on test database
- API endpoint testing with new fields
- Performance impact assessment

### User Acceptance Testing
- Business user validation of migrated data
- Workflow testing with new boolean fields
- Inventory management testing

## Timeline

1. **Week 1**: Analysis and migration script development
2. **Week 2**: Testing on development/staging environments
3. **Week 3**: User acceptance testing and validation
4. **Week 4**: Production migration during maintenance window

## Risk Mitigation

### High Risk: Data Loss
- **Mitigation**: Full database backup before migration
- **Monitoring**: Row count verification before/after

### Medium Risk: Business Disruption
- **Mitigation**: Off-hours deployment, communication plan
- **Monitoring**: Real-time error tracking

### Low Risk: Performance Impact
- **Mitigation**: Index optimization, query performance testing
- **Monitoring**: Database performance metrics

## Success Criteria

- ✅ All existing items successfully migrated
- ✅ No data loss or corruption
- ✅ All API endpoints working with new boolean fields
- ✅ Business workflows functioning correctly
- ✅ Performance maintained or improved
- ✅ Zero critical bugs in production

---

**Note**: This migration strategy prioritizes data integrity and business continuity while implementing the new mutual exclusion constraint. The recommended approach (Option 1) may create additional items but ensures no business data is lost during the transition.