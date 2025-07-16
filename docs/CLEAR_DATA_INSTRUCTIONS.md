# Instructions to Clear Inventory and Transaction Data

## ⚠️ WARNING
This will permanently delete ALL inventory and transaction data from your database. This action cannot be undone!

## Method 1: Using SQL Script with Docker

1. Make sure your Docker containers are running:
   ```bash
   docker-compose up -d
   ```

2. Execute the SQL script directly:
   ```bash
   docker-compose exec -T db psql -U postgres -d fastapi_db < scripts/clear_inventory_transaction_data.sql
   ```

## Method 2: Using the Shell Script

1. Make the script executable:
   ```bash
   chmod +x scripts/clear_data_docker.sh
   ```

2. Run the script:
   ```bash
   ./scripts/clear_data_docker.sh
   ```

## Method 3: Using Python Script

1. Activate your virtual environment:
   ```bash
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

2. Run the Python script:
   ```bash
   python scripts/clear_inventory_transaction_data.py
   ```

## Method 4: Manual SQL Execution

1. Connect to your PostgreSQL database:
   ```bash
   docker-compose exec db psql -U postgres -d fastapi_db
   ```

2. Run the following SQL commands in order:
   ```sql
   BEGIN;
   
   -- Clear tables in dependency order
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
   ```

3. Verify the data has been cleared:
   ```sql
   SELECT 
       'transaction_headers' as table_name, COUNT(*) as record_count FROM transaction_headers
   UNION ALL
   SELECT 'transaction_lines', COUNT(*) FROM transaction_lines
   UNION ALL
   SELECT 'inventory_units', COUNT(*) FROM inventory_units
   UNION ALL
   SELECT 'stock_levels', COUNT(*) FROM stock_levels
   UNION ALL
   SELECT 'stock_movements', COUNT(*) FROM stock_movements;
   ```

## Tables Affected

The following tables will be cleared:
- `inspection_reports` - Inspection records for returned items
- `rental_return_lines` - Individual item return details
- `rental_returns` - Rental return headers
- `rental_return_events` - Rental lifecycle events
- `rental_lifecycles` - Rental operational tracking
- `transaction_metadata` - Transaction-specific metadata
- `transaction_lines` - Transaction line items
- `transaction_headers` - Main transaction records
- `stock_movements` - Stock movement audit trail
- `stock_levels` - Current stock levels by location
- `inventory_units` - Individual inventory unit records

## Post-Clearing Notes

After clearing the data:
1. All transaction history will be lost
2. All inventory tracking will be reset
3. Stock levels will be zero
4. You'll need to re-initialize inventory through purchase transactions or manual stock adjustments

## Recovery

If you need to restore the data:
1. Restore from a database backup (if available)
2. Re-import data from external sources
3. Manually recreate critical records