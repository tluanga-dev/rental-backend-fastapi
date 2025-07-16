-- Clear Only Transaction Headers and Lines
-- This script preserves inventory data (stock levels, inventory units)

BEGIN;

-- First, clear dependent tables that reference transaction_headers
DELETE FROM rental_return_lines;
DELETE FROM rental_returns;
DELETE FROM rental_return_events;
DELETE FROM rental_lifecycles;
DELETE FROM transaction_metadata;

-- Then clear transaction lines and headers
DELETE FROM transaction_lines;
DELETE FROM transaction_headers;

COMMIT;

-- Verify what was cleared
SELECT 
    'transaction_headers' as table_name, COUNT(*) as record_count FROM transaction_headers
UNION ALL
SELECT 'transaction_lines', COUNT(*) FROM transaction_lines
UNION ALL
SELECT 'rental_returns', COUNT(*) FROM rental_returns
UNION ALL
SELECT 'rental_lifecycles', COUNT(*) FROM rental_lifecycles
UNION ALL
SELECT 'transaction_metadata', COUNT(*) FROM transaction_metadata
ORDER BY table_name;

-- Show that inventory data is preserved
SELECT 
    'inventory_units' as table_name, COUNT(*) as record_count FROM inventory_units
UNION ALL
SELECT 'stock_levels', COUNT(*) FROM stock_levels
UNION ALL
SELECT 'stock_movements', COUNT(*) FROM stock_movements
ORDER BY table_name;