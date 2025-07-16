-- Clear All Inventory and Transaction Data
-- WARNING: This script will delete all transaction and inventory data
-- Run with caution!

-- Start transaction
BEGIN;

-- Disable foreign key checks temporarily (if using PostgreSQL)
-- For PostgreSQL, we'll handle this differently by deleting in correct order

-- 1. Clear Inspection Reports (depends on rental returns and inventory units)
DELETE FROM inspection_reports;

-- 2. Clear Rental Return Lines (depends on rental returns and inventory units)
DELETE FROM rental_return_lines;

-- 3. Clear Rental Returns (depends on transaction headers)
DELETE FROM rental_returns;

-- 4. Clear Rental Return Events (depends on rental lifecycles)
DELETE FROM rental_return_events;

-- 5. Clear Rental Lifecycles (depends on transaction headers)
DELETE FROM rental_lifecycles;

-- 6. Clear Transaction Metadata (depends on transaction headers)
DELETE FROM transaction_metadata;

-- 7. Clear Transaction Lines (depends on transaction headers)
DELETE FROM transaction_lines;

-- 8. Clear Transaction Headers
DELETE FROM transaction_headers;

-- 9. Clear Stock Movements (audit trail - depends on stock levels and items)
DELETE FROM stock_movements;

-- 10. Clear Stock Levels (depends on items)
DELETE FROM stock_levels;

-- 11. Clear Inventory Units (depends on items)
DELETE FROM inventory_units;

-- Reset sequences if needed (PostgreSQL specific)
-- Uncomment and adjust table names as needed
/*
ALTER SEQUENCE transaction_headers_id_seq RESTART WITH 1;
ALTER SEQUENCE transaction_lines_id_seq RESTART WITH 1;
ALTER SEQUENCE rental_returns_id_seq RESTART WITH 1;
ALTER SEQUENCE rental_return_lines_id_seq RESTART WITH 1;
ALTER SEQUENCE rental_lifecycles_id_seq RESTART WITH 1;
ALTER SEQUENCE rental_return_events_id_seq RESTART WITH 1;
ALTER SEQUENCE inspection_reports_id_seq RESTART WITH 1;
ALTER SEQUENCE transaction_metadata_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_movements_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_levels_id_seq RESTART WITH 1;
ALTER SEQUENCE inventory_units_id_seq RESTART WITH 1;
*/

-- Commit transaction
COMMIT;

-- Verify data has been cleared
SELECT 
    'transaction_headers' as table_name, COUNT(*) as record_count FROM transaction_headers
UNION ALL
SELECT 'transaction_lines', COUNT(*) FROM transaction_lines
UNION ALL
SELECT 'rental_returns', COUNT(*) FROM rental_returns
UNION ALL
SELECT 'rental_return_lines', COUNT(*) FROM rental_return_lines
UNION ALL
SELECT 'rental_lifecycles', COUNT(*) FROM rental_lifecycles
UNION ALL
SELECT 'rental_return_events', COUNT(*) FROM rental_return_events
UNION ALL
SELECT 'inspection_reports', COUNT(*) FROM inspection_reports
UNION ALL
SELECT 'transaction_metadata', COUNT(*) FROM transaction_metadata
UNION ALL
SELECT 'stock_movements', COUNT(*) FROM stock_movements
UNION ALL
SELECT 'stock_levels', COUNT(*) FROM stock_levels
UNION ALL
SELECT 'inventory_units', COUNT(*) FROM inventory_units
ORDER BY table_name;