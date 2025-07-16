#!/usr/bin/env python3
"""
Script to clear all data from the database except authentication and RBAC tables.
This preserves users, roles, permissions, and their associations.
WARNING: This will permanently delete most business data!
"""

import asyncio
import sys
from typing import List, Dict, Tuple
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import async_session_maker, engine
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Tables to preserve (authentication and RBAC)
PRESERVE_TABLES = [
    "users",
    "user_profiles",
    "roles",
    "permissions",
    "user_roles",
    "role_permissions",
    "user_permissions",
    "refresh_tokens",
    "login_attempts",
    "password_reset_tokens"
]

# Tables to clear in dependency order (most dependent first)
TABLES_TO_CLEAR = [
    # Analytics Module
    ("system_alerts", "System alerts and notifications"),
    ("business_metrics", "Business KPI tracking"),
    ("analytics_reports", "Generated analytics reports"),
    
    # System Module
    ("audit_logs", "System audit trail"),
    ("system_backups", "Backup tracking"),
    ("system_settings", "System configuration"),
    
    # Rentals Module (depends on transactions)
    ("inspection_reports", "Item inspection reports"),
    ("rental_return_lines", "Individual item returns"),
    ("rental_returns", "Rental return headers"),
    
    # Transactions Module
    ("rental_lifecycle", "Rental operational tracking"),
    ("transaction_metadata", "Transaction metadata"),
    ("transaction_events", "Transaction event log"),
    ("transaction_lines", "Transaction line items"),
    ("transaction_headers", "Main transactions"),
    
    # Inventory Module
    ("stock_movements", "Stock movement history"),
    ("stock_levels", "Current stock levels"),
    ("inventory_units", "Individual inventory units"),
    ("sku_sequences", "SKU generation sequences"),
    
    # Master Data Module
    ("items", "Product/item catalog"),
    ("locations", "Physical locations"),
    ("units_of_measurement", "Units of measurement"),
    ("brands", "Product brands"),
    ("categories", "Product categories"),
    
    # Business Partners
    ("suppliers", "Supplier records"),
    ("customers", "Customer records"),
]


async def get_table_counts(session, tables: List[Tuple[str, str]]) -> Dict[str, int]:
    """Get record counts for specified tables."""
    counts = {}
    for table_name, _ in tables:
        try:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            counts[table_name] = result.scalar()
        except Exception:
            counts[table_name] = -1  # Table might not exist
    return counts


async def show_table_preview(dry_run: bool = False):
    """Show current state of all tables."""
    async with async_session_maker() as session:
        print(f"\n{Colors.HEADER}=== DATABASE TABLE PREVIEW ==={Colors.ENDC}")
        
        # Show preserved tables
        print(f"\n{Colors.CYAN}Tables to PRESERVE (Authentication/RBAC):{Colors.ENDC}")
        preserve_counts = {}
        for table in PRESERVE_TABLES:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                preserve_counts[table] = count
                print(f"  {Colors.GREEN}✓{Colors.ENDC} {table:<25} {count:>10,} records")
            except Exception:
                print(f"  {Colors.WARNING}?{Colors.ENDC} {table:<25} {'N/A':>10}")
        
        # Show tables to clear
        print(f"\n{Colors.WARNING}Tables to CLEAR:{Colors.ENDC}")
        clear_counts = await get_table_counts(session, TABLES_TO_CLEAR)
        total_records = 0
        
        for table_name, description in TABLES_TO_CLEAR:
            count = clear_counts.get(table_name, -1)
            if count >= 0:
                total_records += count
                status = f"{Colors.FAIL}✗{Colors.ENDC}" if count > 0 else f"{Colors.GREEN}✓{Colors.ENDC}"
                print(f"  {status} {table_name:<25} {count:>10,} records - {description}")
            else:
                print(f"  {Colors.WARNING}?{Colors.ENDC} {table_name:<25} {'N/A':>10} - {description}")
        
        print(f"\n{Colors.BOLD}Total records to be deleted: {total_records:,}{Colors.ENDC}")
        
        if dry_run:
            print(f"\n{Colors.CYAN}DRY RUN MODE - No data will be deleted{Colors.ENDC}")
        
        return total_records, preserve_counts, clear_counts


async def clear_data(dry_run: bool = False):
    """Clear all data except authentication and RBAC tables."""
    
    # Show current state
    total_to_delete, preserve_counts, before_counts = await show_table_preview(dry_run)
    
    if total_to_delete == 0 and not dry_run:
        print(f"\n{Colors.GREEN}No data to clear. All tables are already empty.{Colors.ENDC}")
        return
    
    # Confirmation prompt
    if not dry_run:
        print(f"\n{Colors.WARNING}WARNING: This will DELETE {total_to_delete:,} records!{Colors.ENDC}")
        print("This action cannot be undone.")
        print(f"Authentication data ({sum(preserve_counts.values()):,} records) will be preserved.")
        
        response = input(f"\n{Colors.BOLD}Are you sure you want to continue? (yes/no): {Colors.ENDC}")
        
        if response.lower() != 'yes':
            print(f"{Colors.CYAN}Operation cancelled.{Colors.ENDC}")
            return
    
    async with async_session_maker() as session:
        try:
            # Start transaction
            await session.begin()
            
            print(f"\n{Colors.HEADER}=== CLEARING DATA ==={Colors.ENDC}")
            
            deleted_counts = {}
            total_deleted = 0
            
            # Clear each table
            for table_name, description in TABLES_TO_CLEAR:
                if dry_run:
                    # In dry run, just show what would be deleted
                    count = before_counts.get(table_name, 0)
                    if count > 0:
                        print(f"  {Colors.CYAN}[DRY RUN]{Colors.ENDC} Would delete {count:,} records from {table_name}")
                    deleted_counts[table_name] = count
                else:
                    try:
                        # Show progress for large tables
                        before_count = before_counts.get(table_name, 0)
                        if before_count > 10000:
                            print(f"  {Colors.CYAN}⟳{Colors.ENDC} Clearing {table_name} ({before_count:,} records)...", end='', flush=True)
                        
                        result = await session.execute(text(f"DELETE FROM {table_name}"))
                        deleted_count = result.rowcount
                        deleted_counts[table_name] = deleted_count
                        total_deleted += deleted_count
                        
                        if before_count > 10000:
                            print(f"\r  {Colors.GREEN}✓{Colors.ENDC} Cleared {deleted_count:,} records from {table_name:<25}")
                        else:
                            print(f"  {Colors.GREEN}✓{Colors.ENDC} Cleared {deleted_count:,} records from {table_name}")
                    
                    except Exception as e:
                        print(f"  {Colors.FAIL}✗{Colors.ENDC} Error clearing {table_name}: {str(e)}")
                        deleted_counts[table_name] = 0
            
            if not dry_run:
                # Commit the transaction
                await session.commit()
                print(f"\n{Colors.GREEN}✅ Transaction committed successfully!{Colors.ENDC}")
            
            # Verification
            print(f"\n{Colors.HEADER}=== VERIFICATION ==={Colors.ENDC}")
            
            if not dry_run:
                # Get after counts
                after_counts = await get_table_counts(session, TABLES_TO_CLEAR)
                
                print(f"\n{Colors.CYAN}Cleared tables (should be 0):{Colors.ENDC}")
                all_clear = True
                for table_name, _ in TABLES_TO_CLEAR:
                    count = after_counts.get(table_name, -1)
                    if count > 0:
                        all_clear = False
                        print(f"  {Colors.FAIL}✗{Colors.ENDC} {table_name:<25} {count:>10,} records remaining")
                    elif count == 0:
                        print(f"  {Colors.GREEN}✓{Colors.ENDC} {table_name:<25} {count:>10,} records")
                
                # Check preserved tables
                print(f"\n{Colors.CYAN}Preserved tables (authentication/RBAC):{Colors.ENDC}")
                for table in PRESERVE_TABLES[:5]:  # Show first 5 preserved tables
                    try:
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        print(f"  {Colors.GREEN}✓{Colors.ENDC} {table:<25} {count:>10,} records preserved")
                    except Exception:
                        pass
                
                if all_clear:
                    print(f"\n{Colors.GREEN}✅ All data cleared successfully!{Colors.ENDC}")
                else:
                    print(f"\n{Colors.WARNING}⚠️  Some tables still contain data{Colors.ENDC}")
            
            # Summary report
            print(f"\n{Colors.HEADER}=== SUMMARY REPORT ==={Colors.ENDC}")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTED'}")
            print(f"Total records deleted: {total_deleted:,}")
            print(f"Tables cleared: {len([c for c in deleted_counts.values() if c > 0])}")
            print(f"Tables preserved: {len(PRESERVE_TABLES)}")
            print(f"Records preserved: {sum(preserve_counts.values()):,}")
            
            # Top 5 tables by deletion count
            if deleted_counts:
                sorted_deletions = sorted(deleted_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                print(f"\n{Colors.CYAN}Top tables by deletion count:{Colors.ENDC}")
                for table, count in sorted_deletions:
                    if count > 0:
                        print(f"  • {table}: {count:,} records")
                
        except Exception as e:
            await session.rollback()
            print(f"\n{Colors.FAIL}❌ Error occurred: {e}{Colors.ENDC}")
            print("Transaction rolled back. No data was deleted.")
            raise


async def main():
    """Main function."""
    print(f"{Colors.HEADER}{Colors.BOLD}=== Clear All Data Except Authentication ==={Colors.ENDC}")
    print(f"Database: {os.getenv('DATABASE_URL', 'Not configured')}")
    
    # Check for command line arguments
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    if dry_run:
        print(f"\n{Colors.CYAN}Running in DRY RUN mode - no data will be deleted{Colors.ENDC}")
    
    try:
        await clear_data(dry_run=dry_run)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Operation cancelled by user.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}")
        sys.exit(1)
    finally:
        # Close the engine
        await engine.dispose()


if __name__ == "__main__":
    # Show help if requested
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python clear_all_data_except_auth.py [OPTIONS]")
        print("\nOptions:")
        print("  --dry-run, -d    Show what would be deleted without actually deleting")
        print("  --help, -h       Show this help message")
        print("\nThis script clears all data except authentication and RBAC tables.")
        sys.exit(0)
    
    asyncio.run(main())