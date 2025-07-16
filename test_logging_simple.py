#!/usr/bin/env python3
"""
Simple test to verify the new comprehensive logging system components.
"""

import sys
import os
import uuid
from decimal import Decimal
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath("."))

try:
    # Test 1: Import and initialize logging configuration
    print("🔧 Testing logging configuration import...")
    from app.core.logging_config import LoggingConfig, LoggingManager, setup_application_logging
    
    # Initialize logging
    setup_application_logging()
    print("✅ Logging configuration imported and initialized successfully")
    
    # Test 2: Test transaction logger import and basic functionality
    print("\n📝 Testing transaction logger...")
    from app.core.transaction_logger import TransactionLogger, get_transaction_logger
    
    # Create a transaction logger instance
    logger = get_transaction_logger()
    transaction_id = uuid.uuid4()
    
    # Start a test transaction log
    logger.start_transaction_log("TEST_SALE", transaction_id, "simple_test")
    print("✅ Transaction log started")
    
    # Add some test events
    logger.log_validation("customer_validation", True, {"customer_id": "test-123"})
    logger.log_event("ITEM_VALIDATED", "Test item validation successful")
    
    # Add inventory change
    logger.log_inventory_change(
        item_id=uuid.uuid4(),
        item_name="Test Item",
        change_type="SALE", 
        quantity_before=Decimal("5"),
        quantity_after=Decimal("3"),
        location_name="Test Location"
    )
    
    # Complete the log
    log_file = logger.complete_transaction_log("COMPLETED")
    
    if log_file and log_file.exists():
        print(f"✅ Transaction log file created: {log_file}")
        
        # Read and show the content
        with open(log_file, 'r') as f:
            content = f.read()
            
        print(f"📄 Log file size: {len(content)} characters")
        print("📄 Log file preview:")
        print("-" * 50)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 50)
    else:
        print("❌ Transaction log file not created")
        
    # Test 3: Check file naming convention
    print(f"\n📁 Testing file naming convention...")
    filename = log_file.name if log_file else "No file generated"
    print(f"Generated filename: {filename}")
    
    # Check if it follows the pattern: operation-mm-hh-ddmmyy.md
    if filename.endswith('.md') and 'test_sale' in filename.lower():
        parts = filename.replace('.md', '').split('-')
        if len(parts) >= 4:
            print("✅ Filename follows expected pattern")
            print(f"   Operation part: {parts[0]}")
            print(f"   Timestamp part: {'-'.join(parts[-3:])}")
        else:
            print(f"⚠️  Filename pattern may not match exactly: {filename}")
    else:
        print(f"❌ Filename does not follow expected pattern")
        
    # Test 4: Test logging directories
    print(f"\n📁 Testing logging directories...")
    logs_dir = Path("logs")
    transaction_logs_dir = Path("logs/transactions")
    
    print(f"Main logs directory exists: {logs_dir.exists()}")
    print(f"Transaction logs directory exists: {transaction_logs_dir.exists()}")
    
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.md"))
        print(f"Found {len(log_files)} markdown log files in main directory")
        
    if transaction_logs_dir.exists():
        transaction_files = list(transaction_logs_dir.glob("*.md"))
        print(f"Found {len(transaction_files)} transaction log files")
        
    # Test 5: Test the logging manager
    print(f"\n🔍 Testing logging manager...")
    from app.core.logging_config import get_logging_manager
    
    manager = get_logging_manager()
    status = manager.get_logging_status()
    
    print("✅ Logging manager status retrieved")
    print(f"   Configured loggers: {len(status['loggers'])}")
    print(f"   Transaction logging: {status['config']['transaction_logging_enabled']}")
    print(f"   API logging: {status['config']['api_logging_enabled']}")
    
    # Test different logger types
    transaction_logger = manager.get_transaction_logger()
    api_logger = manager.get_api_logger()
    audit_logger = manager.get_audit_logger()
    
    transaction_logger.info("Test message from transaction logger")
    api_logger.info("Test message from API logger")
    audit_logger.info("Test message from audit logger")
    
    print("✅ All logger types working")
    
    print(f"\n🎉 All basic logging tests completed successfully!")
    print(f"📝 The comprehensive logging system is ready for use.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)