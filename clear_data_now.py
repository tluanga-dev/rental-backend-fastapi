import psycopg2
from psycopg2 import sql
import os

# Database connection parameters
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'fastapi_db',
    'user': 'postgres',
    'password': 'postgres'
}

def clear_data():
    """Clear all inventory and transaction data."""
    
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
    
    conn = None
    cursor = None
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Start transaction
        conn.autocommit = False
        
        print("\nClearing data from tables...")
        
        # Clear each table
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            print(f"✓ Cleared {cursor.rowcount} records from {table}")
        
        # Commit the transaction
        conn.commit()
        print("\n✅ All data cleared successfully!")
        
        # Verify by counting records
        print("\nVerifying tables are empty:")
        for table in tables_to_clear:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\n❌ Error occurred: {e}")
        print("Transaction rolled back. No data was deleted.")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    print("=== Clear Inventory and Transaction Data ===")
    print("WARNING: This will DELETE ALL inventory and transaction data!")
    print("This action cannot be undone.")
    
    response = input("Are you sure you want to continue? (type 'yes' to confirm): ")
    
    if response.lower() == 'yes':
        clear_data()
    else:
        print("Operation cancelled.")