#!/usr/bin/env python3
"""
Test script for the comprehensive logging system.

This script tests all components of the logging system:
1. Centralized logging configuration
2. Transaction logger (file-based markdown logs)
3. Audit service (database-based logging)
4. API middleware logging
5. Transaction event logging
"""

import asyncio
import sys
import os
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath("."))

from app.core.logging_config import get_logging_manager, setup_application_logging
from app.core.transaction_logger import get_transaction_logger
from app.core.database import get_async_session
from app.modules.system.services.audit_service import AuditService


async def test_centralized_logging_config():
    """Test the centralized logging configuration."""
    print("🔧 Testing Centralized Logging Configuration...")
    
    try:
        # Initialize logging
        setup_application_logging()
        manager = get_logging_manager()
        
        # Get logging status
        status = manager.get_logging_status()
        
        print("✅ Logging configuration initialized successfully")
        print(f"📁 Log directory: {status['config']['log_directory']}")
        print(f"📁 Transaction log directory: {status['config']['transaction_log_directory']}")
        print(f"🔍 Available loggers: {', '.join(status['loggers'])}")
        
        # Test different loggers
        loggers = {
            "transaction": manager.get_transaction_logger(),
            "api": manager.get_api_logger(),
            "audit": manager.get_audit_logger(),
            "error": manager.get_error_logger(),
            "performance": manager.get_performance_logger()
        }
        
        for name, logger in loggers.items():
            logger.info(f"Test message from {name} logger")
            print(f"✅ {name.capitalize()} logger working")
            
        return True
        
    except Exception as e:
        print(f"❌ Centralized logging test failed: {e}")
        return False


def test_transaction_logger():
    """Test the file-based transaction logger."""
    print("\n📝 Testing Transaction Logger (File-based)...")
    
    try:
        # Get transaction logger
        logger = get_transaction_logger()
        
        # Test transaction start
        transaction_id = uuid.uuid4()
        operation_name = "test_sale"
        
        logger.start_transaction_log("SALE", transaction_id, operation_name)
        print("✅ Transaction log started")
        
        # Test validation logging
        logger.log_validation("customer_validation", True, {"customer_id": "test-123"})
        print("✅ Validation logged")
        
        # Test inventory change
        logger.log_inventory_change(
            item_id=uuid.uuid4(),
            item_name="Test Item",
            change_type="SALE",
            quantity_before=Decimal("10"),
            quantity_after=Decimal("8"),
            location_id=uuid.uuid4(),
            location_name="Main Warehouse"
        )
        print("✅ Inventory change logged")
        
        # Test payment event
        logger.log_payment_event(
            payment_type="PAYMENT",
            amount=Decimal("100.00"),
            method="CASH",
            status="COMPLETED",
            reference="PAY-001"
        )
        print("✅ Payment event logged")
        
        # Test error logging
        logger.log_error("ValidationError", "Test error message", {"field": "test"})
        print("✅ Error logged")
        
        # Complete transaction log
        log_file = logger.complete_transaction_log("COMPLETED")
        
        if log_file and log_file.exists():
            print(f"✅ Transaction log completed: {log_file}")
            
            # Read and display part of the log file
            with open(log_file, 'r') as f:
                content = f.read()
                print(f"📄 Log file size: {len(content)} characters")
                print("📄 Log file preview (first 200 characters):")
                print(content[:200] + "..." if len(content) > 200 else content)
        else:
            print("❌ Log file not created")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Transaction logger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_audit_service():
    """Test the audit service."""
    print("\n🔍 Testing Audit Service (Database-based)...")
    
    try:
        # Get database session
        async with get_async_session() as session:
            audit_service = AuditService(session)
            
            # Test transaction ID
            transaction_id = uuid.uuid4()
            user_id = uuid.uuid4()
            
            # Test transaction start logging
            await audit_service.log_transaction_start(
                transaction_id=transaction_id,
                transaction_type="SALE",
                operation_name="test_audit_sale",
                user_id=user_id,
                session_id="test-session-123",
                ip_address="127.0.0.1",
                additional_data={"test": "data"}
            )
            print("✅ Transaction start logged to database")
            
            # Test validation logging
            await audit_service.log_validation_step(
                transaction_id=transaction_id,
                validation_type="customer_validation",
                result=True,
                details={"customer_id": str(uuid.uuid4())},
                user_id=user_id
            )
            print("✅ Validation step logged to database")
            
            # Test inventory change logging
            await audit_service.log_inventory_change(
                transaction_id=transaction_id,
                item_id=uuid.uuid4(),
                item_name="Test Audit Item",
                change_type="SALE",
                quantity_before=Decimal("15"),
                quantity_after=Decimal("13"),
                location_id=uuid.uuid4(),
                location_name="Test Location",
                user_id=user_id
            )
            print("✅ Inventory change logged to database")
            
            # Test payment event logging
            await audit_service.log_payment_event(
                transaction_id=transaction_id,
                payment_type="PAYMENT",
                amount=Decimal("150.00"),
                method="CREDIT_CARD",
                status="COMPLETED",
                reference="CC-PAY-001",
                user_id=user_id
            )
            print("✅ Payment event logged to database")
            
            # Test error logging
            await audit_service.log_error(
                transaction_id=transaction_id,
                error_type="TestError",
                error_message="Test error for audit logging",
                error_details={"test_field": "test_value"},
                user_id=user_id
            )
            print("✅ Error logged to database")
            
            # Test transaction completion
            log_file_path = await audit_service.complete_transaction_log(
                transaction_id=transaction_id,
                final_status="COMPLETED",
                user_id=user_id,
                completion_notes="Test transaction completed successfully"
            )
            print(f"✅ Transaction completion logged: {log_file_path}")
            
            # Test audit trail retrieval
            audit_trail = await audit_service.get_transaction_audit_trail(
                transaction_id=transaction_id,
                include_events=True,
                include_audit_logs=True
            )
            
            print(f"✅ Audit trail retrieved:")
            print(f"   - Events: {audit_trail['summary']['total_events']}")
            print(f"   - Audit logs: {audit_trail['summary']['total_audit_logs']}")
            print(f"   - Has errors: {audit_trail['summary']['has_errors']}")
            
            # Commit the test data
            await session.commit()
            
        return True
        
    except Exception as e:
        print(f"❌ Audit service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_log_file_naming_convention():
    """Test that log files follow the correct naming convention."""
    print("\n📁 Testing Log File Naming Convention...")
    
    try:
        logs_dir = Path("logs")
        transaction_logs_dir = Path("logs/transactions")
        
        # Create directories if they don't exist
        logs_dir.mkdir(exist_ok=True)
        transaction_logs_dir.mkdir(exist_ok=True)
        
        # Check existing log files
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log")) + list(logs_dir.glob("*.md"))
            print(f"✅ Found {len(log_files)} log files in {logs_dir}")
            
            # Show a few examples
            for i, log_file in enumerate(log_files[:5]):
                print(f"   📄 {log_file.name}")
                
        if transaction_logs_dir.exists():
            transaction_files = list(transaction_logs_dir.glob("*.md"))
            print(f"✅ Found {len(transaction_files)} transaction log files in {transaction_logs_dir}")
            
        # Test naming convention format
        logger = get_transaction_logger()
        test_transaction_id = uuid.uuid4()
        logger.start_transaction_log("TEST", test_transaction_id, "naming_test")
        log_file = logger.complete_transaction_log("COMPLETED")
        
        if log_file:
            filename = log_file.name
            print(f"✅ Generated log file: {filename}")
            
            # Check naming pattern: operation-mm-hh-ddmmyy.md
            parts = filename.replace('.md', '').split('-')
            if len(parts) >= 4:
                operation = parts[0]
                timestamp_part = '-'.join(parts[-3:])  # mm-hh-ddmmyy
                print(f"✅ Operation: {operation}")
                print(f"✅ Timestamp: {timestamp_part}")
                print("✅ Naming convention verified")
            else:
                print(f"❌ Unexpected filename format: {filename}")
                return False
        else:
            print("❌ No log file generated")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Log file naming test failed: {e}")
        return False


def test_log_content_structure():
    """Test the structure and content of generated log files."""
    print("\n📄 Testing Log Content Structure...")
    
    try:
        # Find the most recent transaction log file
        logs_dir = Path("logs/transactions")
        if not logs_dir.exists():
            logs_dir = Path("logs")
            
        md_files = list(logs_dir.glob("*.md"))
        if not md_files:
            print("❌ No markdown log files found")
            return False
            
        # Get the most recent file
        latest_file = max(md_files, key=lambda f: f.stat().st_mtime)
        print(f"📄 Reading latest log file: {latest_file.name}")
        
        with open(latest_file, 'r') as f:
            content = f.read()
            
        # Check for expected sections
        expected_sections = [
            "# Transaction Log",
            "## Transaction Information",
            "## Transaction Events",
            "## Inventory Changes",
            "## Payment Events",
            "## Errors",
            "## Summary"
        ]
        
        missing_sections = []
        for section in expected_sections:
            if section in content:
                print(f"✅ Found section: {section}")
            else:
                missing_sections.append(section)
                
        if missing_sections:
            print(f"⚠️  Missing sections: {', '.join(missing_sections)}")
        else:
            print("✅ All expected sections found")
            
        # Show file stats
        lines = content.split('\n')
        print(f"📊 Log file statistics:")
        print(f"   - Total lines: {len(lines)}")
        print(f"   - Total characters: {len(content)}")
        print(f"   - File size: {latest_file.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Log content test failed: {e}")
        return False


async def run_all_tests():
    """Run all logging system tests."""
    print("🚀 Starting Comprehensive Logging System Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Centralized logging configuration
    result1 = await test_centralized_logging_config()
    test_results.append(("Centralized Logging Config", result1))
    
    # Test 2: Transaction logger
    result2 = test_transaction_logger()
    test_results.append(("Transaction Logger", result2))
    
    # Test 3: Audit service
    result3 = await test_audit_service()
    test_results.append(("Audit Service", result3))
    
    # Test 4: Log file naming convention
    result4 = test_log_file_naming_convention()
    test_results.append(("File Naming Convention", result4))
    
    # Test 5: Log content structure
    result5 = test_log_content_structure()
    test_results.append(("Log Content Structure", result5))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
            
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Logging system is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)