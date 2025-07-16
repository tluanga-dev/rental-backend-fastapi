#!/bin/bash

# Script to clear inventory and transaction data using Docker

echo "WARNING: This will DELETE ALL inventory and transaction data!"
echo "This action cannot be undone."
read -p "Are you sure you want to continue? (yes/no): " response

if [ "$response" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo "Clearing data..."

# Execute SQL commands via docker-compose
docker-compose exec -T db psql -U postgres -d fastapi_db << EOF
BEGIN;

-- Clear tables in order
DELETE FROM inspection_reports;
DELETE FROM rental_return_lines;
DELETE FROM rental_returns;
DELETE FROM rental_return_events;
DELETE FROM rental_lifecycles;
DELETE FROM transaction_metadata;
DELETE FROM transaction_lines;
DELETE FROM transaction_headers;
DELETE FROM stock_movements;
DELETE FROM stock_levels;
DELETE FROM inventory_units;

COMMIT;

-- Show counts
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
EOF

echo "✅ Data cleared successfully!"