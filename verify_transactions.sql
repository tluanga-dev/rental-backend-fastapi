-- Check if transaction data exists
SELECT 
    'transaction_headers' as table_name, 
    COUNT(*) as total_count,
    COUNT(CASE WHEN transaction_type = 'PURCHASE' THEN 1 END) as purchase_count,
    COUNT(CASE WHEN transaction_type = 'SALE' THEN 1 END) as sale_count,
    COUNT(CASE WHEN transaction_type = 'RENTAL' THEN 1 END) as rental_count
FROM transaction_headers;

-- Show sample of transaction headers
SELECT id, transaction_number, transaction_type, status, created_at 
FROM transaction_headers 
LIMIT 5;

-- Count transaction lines
SELECT COUNT(*) as transaction_lines_count FROM transaction_lines;

-- Check related tables
SELECT 
    'rental_returns' as table_name, COUNT(*) as count FROM rental_returns
UNION ALL
SELECT 'rental_lifecycles', COUNT(*) FROM rental_lifecycles
UNION ALL
SELECT 'transaction_metadata', COUNT(*) FROM transaction_metadata
ORDER BY table_name;