# Clear Data Except Authentication Guide

## Overview

The `clear_all_data_except_auth.py` script allows you to clear all business data from your database while preserving authentication and RBAC (Role-Based Access Control) data. This is useful for:

- Resetting the system to a clean state while keeping user accounts
- Testing with fresh data
- Preparing for data migrations
- Clearing test data from production

## What Gets Preserved

The following tables and their data are **PRESERVED**:

### Authentication & RBAC Tables
- `users` - User accounts with login credentials
- `user_profiles` - Extended user profile information
- `roles` - System roles (Admin, Manager, etc.)
- `permissions` - Fine-grained permissions
- `user_roles` - User-to-role assignments
- `role_permissions` - Role-to-permission assignments
- `user_permissions` - Direct user permissions
- `refresh_tokens` - Active JWT refresh tokens
- `login_attempts` - Login security audit trail
- `password_reset_tokens` - Active password reset tokens

## What Gets Cleared

All other tables are **CLEARED**, including:

### Business Data
- All transactions (sales, purchases, rentals)
- All inventory data (stock levels, movements, units)
- All master data (items, categories, brands, locations, units of measurement)
- All customer records
- All supplier records
- All rental returns and inspections
- All analytics and reports
- System settings and configurations
- Audit logs

## Usage

### Basic Usage

```bash
# Navigate to the project directory
cd /path/to/rental-backend-fastapi

# Run the script
python scripts/clear_all_data_except_auth.py
```

### Dry Run Mode

To see what would be deleted without actually deleting anything:

```bash
python scripts/clear_all_data_except_auth.py --dry-run
```

Or using the short option:

```bash
python scripts/clear_all_data_except_auth.py -d
```

### Help

To see available options:

```bash
python scripts/clear_all_data_except_auth.py --help
```

## Script Features

1. **Table Preview**: Shows current record counts for all tables before deletion
2. **Confirmation Prompt**: Requires explicit confirmation before deleting data
3. **Transaction Safety**: Uses database transactions - all or nothing
4. **Progress Indicators**: Shows progress for large table deletions
5. **Color-Coded Output**: Easy to read terminal output
6. **Verification**: Confirms all tables are empty after deletion
7. **Summary Report**: Provides detailed summary of what was deleted

## Example Output

```
=== DATABASE TABLE PREVIEW ===

Tables to PRESERVE (Authentication/RBAC):
  ✓ users                        42 records
  ✓ user_profiles                42 records
  ✓ roles                         4 records
  ✓ permissions                  85 records
  ✓ user_roles                   42 records

Tables to CLEAR:
  ✗ transaction_headers       1,234 records - Main transactions
  ✗ transaction_lines         3,456 records - Transaction line items
  ✗ inventory_units             789 records - Individual inventory units
  ✗ stock_levels                156 records - Current stock levels
  ✗ customers                   234 records - Customer records

Total records to be deleted: 5,869

WARNING: This will DELETE 5,869 records!
This action cannot be undone.
Authentication data (218 records) will be preserved.

Are you sure you want to continue? (yes/no): yes

=== CLEARING DATA ===
  ✓ Cleared 25 records from system_alerts
  ✓ Cleared 150 records from business_metrics
  ⟳ Clearing transaction_headers (1,234 records)...
  ✓ Cleared 1,234 records from transaction_headers

=== VERIFICATION ===
All data cleared successfully!

=== SUMMARY REPORT ===
Timestamp: 2025-01-16 10:30:45
Mode: EXECUTED
Total records deleted: 5,869
Tables cleared: 23
Tables preserved: 10
Records preserved: 218
```

## Docker Usage

If you're using Docker, you can run the script inside the container:

```bash
# Execute in the running container
docker-compose exec app python scripts/clear_all_data_except_auth.py

# Or with dry run
docker-compose exec app python scripts/clear_all_data_except_auth.py --dry-run
```

## Safety Considerations

1. **Backup First**: Always backup your database before running this script in production
2. **Dry Run**: Use `--dry-run` first to see what will be deleted
3. **Transaction Safety**: The script uses transactions, so if any error occurs, no data is deleted
4. **Confirmation Required**: The script requires explicit "yes" confirmation
5. **Preserved Data**: Authentication data is never touched

## Troubleshooting

### Permission Denied
If you get a permission error, make the script executable:
```bash
chmod +x scripts/clear_all_data_except_auth.py
```

### Module Not Found
Ensure you're in the virtual environment:
```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### Database Connection Error
Check your database is running and `DATABASE_URL` is correctly set:
```bash
docker-compose up -d db
```

## Post-Clearing Steps

After clearing data, you may want to:

1. **Re-initialize Master Data**: Create categories, brands, locations, etc.
2. **Import Test Data**: Load sample products and inventory
3. **Verify User Access**: Ensure users can still log in
4. **Check Permissions**: Verify RBAC is still functioning

## Related Scripts

- `clear_inventory_transaction_data.py` - Clears only inventory and transaction data
- `clear_transactions_only.sql` - SQL script to clear only transactions
- `create_admin.py` - Create a new admin user