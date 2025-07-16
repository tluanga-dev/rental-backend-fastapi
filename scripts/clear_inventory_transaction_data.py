#!/usr/bin/env python3
"""
Script to clear all inventory and transaction data from the database.
WARNING: This will permanently delete all transaction and inventory data!
"""

import asyncio
import sys
from sqlalchemy import text
from app.core.database import async_session_maker, engine
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def clear_data():
    """Clear all inventory and transaction data."""
    
    # Confirmation prompt
    print("WARNING: This script will DELETE ALL inventory and transaction data!")
    print("This action cannot be undone.")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Tables to clear in order (respecting foreign key constraints)
    tables_to_clear = [
        "inspection_reports",
        "rental_return_lines", 
        "rental_returns",
        "rental_return_events",
        "rental_lifecycles",
        "transaction_metadata",
        "transaction_lines",
        "transaction_headers",
        "stock_movements",
        "stock_levels",
        "inventory_units"
    ]
    
    async with async_session_maker() as session:
        try:
            # Start transaction
            await session.begin()
            
            print("\nClearing data from tables...")
            
            # Clear each table
            for table in tables_to_clear:
                result = await session.execute(text(f"DELETE FROM {table}"))
                print(f"✓ Cleared {result.rowcount} records from {table}")
            
            # Commit the transaction
            await session.commit()
            print("\n✅ All data cleared successfully!")
            
            # Verify by counting records
            print("\nVerifying tables are empty:")
            for table in tables_to_clear:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count} records")
                
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error occurred: {e}")
            print("Transaction rolled back. No data was deleted.")
            raise


async def main():
    """Main function."""
    print("=== Clear Inventory and Transaction Data ===")
    print(f"Database: {os.getenv('DATABASE_URL', 'Not configured')}")
    
    try:
        await clear_data()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        # Close the engine
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())