#!/usr/bin/env python3
"""
Test rental aggregation logic and backward compatibility.
"""

import sys
import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

sys.path.append('/app')

async def test_rental_aggregation():
    """Test rental status aggregation logic."""
    print("🧪 TESTING RENTAL AGGREGATION LOGIC")
    print("===================================")
    
    try:
        from app.modules.transactions.models.transaction_headers import (
            TransactionHeader, TransactionType, TransactionStatus, RentalStatus
        )
        from app.modules.transactions.models.transaction_lines import (
            TransactionLine, LineItemType, RentalPeriodUnit
        )
        
        print("✅ Models imported successfully")
        
        # Create a mock transaction header
        header = TransactionHeader()
        header.id = uuid4()
        header.transaction_number = "TEST-001"
        header.transaction_type = TransactionType.RENTAL
        header.status = TransactionStatus.PENDING
        header.transaction_date = datetime.now()
        header.customer_id = str(uuid4())
        header.location_id = str(uuid4())
        
        # Create mock transaction lines with different rental statuses
        line1 = TransactionLine()
        line1.id = uuid4()
        line1.transaction_id = header.id
        line1.line_number = 1
        line1.line_type = LineItemType.PRODUCT
        line1.description = "Test Item 1"
        line1.quantity = Decimal("1")
        line1.unit_price = Decimal("100.00")
        line1.rental_start_date = date.today()
        line1.rental_end_date = date.today() + timedelta(days=7)
        line1.current_rental_status = RentalStatus.ACTIVE
        line1.rental_period_unit = RentalPeriodUnit.DAY
        
        line2 = TransactionLine()
        line2.id = uuid4()
        line2.transaction_id = header.id
        line2.line_number = 2
        line2.line_type = LineItemType.PRODUCT
        line2.description = "Test Item 2"
        line2.quantity = Decimal("1")
        line2.unit_price = Decimal("150.00")
        line2.rental_start_date = date.today()
        line2.rental_end_date = date.today() + timedelta(days=5)
        line2.current_rental_status = RentalStatus.LATE
        line2.rental_period_unit = RentalPeriodUnit.DAY
        
        # Mock the relationship
        header.transaction_lines = [line1, line2]
        
        # Test 1: rental_start_date aggregation
        start_date = header.rental_start_date
        print(f"Rental start date: {start_date}")
        assert start_date == date.today(), f"Expected {date.today()}, got {start_date}"
        print("✅ rental_start_date aggregation works")
        
        # Test 2: rental_end_date aggregation  
        end_date = header.rental_end_date
        expected_end = date.today() + timedelta(days=7)
        print(f"Rental end date: {end_date}")
        assert end_date == expected_end, f"Expected {expected_end}, got {end_date}"
        print("✅ rental_end_date aggregation works")
        
        # Test 3: current_rental_status aggregation
        rental_status = header.current_rental_status
        print(f"Aggregated rental status: {rental_status}")
        assert rental_status == RentalStatus.LATE, f"Expected LATE, got {rental_status}"
        print("✅ current_rental_status aggregation works (LATE takes priority)")
        
        # Test 4: Test with all COMPLETED status
        line1.current_rental_status = RentalStatus.COMPLETED
        line2.current_rental_status = RentalStatus.COMPLETED
        rental_status = header.current_rental_status
        print(f"All completed status: {rental_status}")
        assert rental_status == RentalStatus.COMPLETED, f"Expected COMPLETED, got {rental_status}"
        print("✅ current_rental_status aggregation works (all COMPLETED)")
        
        # Test 5: Test with PARTIAL_RETURN
        line1.current_rental_status = RentalStatus.ACTIVE
        line2.current_rental_status = RentalStatus.PARTIAL_RETURN
        rental_status = header.current_rental_status
        print(f"Partial return status: {rental_status}")
        assert rental_status == RentalStatus.PARTIAL_RETURN, f"Expected PARTIAL_RETURN, got {rental_status}"
        print("✅ current_rental_status aggregation works (PARTIAL_RETURN)")
        
        # Test 6: Test rental duration calculation
        duration = header.rental_duration_days
        print(f"Rental duration: {duration} days")
        assert duration == 7, f"Expected 7 days, got {duration}"
        print("✅ rental_duration_days calculation works")
        
        # Test 7: Test is_rental property
        assert header.is_rental == True, "is_rental should be True for RENTAL type"
        print("✅ is_rental property works")
        
        # Test 8: Test with no lines (edge case)
        header.transaction_lines = []
        assert header.rental_start_date is None, "Should be None with no lines"
        assert header.rental_end_date is None, "Should be None with no lines"
        assert header.current_rental_status is None, "Should be None with no lines"
        print("✅ Edge case with no lines handled correctly")
        
        print("\n🎉 ALL RENTAL AGGREGATION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Rental aggregation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enum_functionality():
    """Test enum functionality."""
    print("\n🔧 TESTING ENUM FUNCTIONALITY")
    print("=============================")
    
    try:
        from app.modules.transactions.models.transaction_headers import RentalStatus
        from app.modules.transactions.models.transaction_lines import RentalPeriodUnit
        
        # Test RentalStatus enum
        print("Testing RentalStatus enum...")
        statuses = list(RentalStatus)
        expected_statuses = [
            RentalStatus.ACTIVE,
            RentalStatus.LATE, 
            RentalStatus.EXTENDED,
            RentalStatus.PARTIAL_RETURN,
            RentalStatus.LATE_PARTIAL_RETURN,
            RentalStatus.COMPLETED
        ]
        
        assert len(statuses) == 6, f"Expected 6 statuses, got {len(statuses)}"
        assert set(statuses) == set(expected_statuses), "Status values don't match"
        print(f"✅ RentalStatus has {len(statuses)} values: {[s.value for s in statuses]}")
        
        # Test RentalPeriodUnit enum
        print("Testing RentalPeriodUnit enum...")
        units = list(RentalPeriodUnit)
        expected_units = [
            RentalPeriodUnit.HOUR,
            RentalPeriodUnit.DAY,
            RentalPeriodUnit.WEEK,
            RentalPeriodUnit.MONTH
        ]
        
        assert len(units) == 4, f"Expected 4 units, got {len(units)}"
        assert set(units) == set(expected_units), "Unit values don't match"
        print(f"✅ RentalPeriodUnit has {len(units)} values: {[u.value for u in units]}")
        
        print("\n🎉 ALL ENUM TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Enum test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🚀 STARTING RENTAL LOGIC TESTING")
    print("=================================")
    
    test1_result = await test_rental_aggregation()
    test2_result = await test_enum_functionality()
    
    if test1_result and test2_result:
        print("\n" + "="*50)
        print("🏆 ALL RENTAL LOGIC TESTS PASSED!")
        print("🎯 Migration implementation is robust and working correctly.")
        print("="*50)
        return True
    else:
        print("\n" + "="*50)
        print("❌ SOME TESTS FAILED")
        print("🔧 Please review the implementation.")
        print("="*50)
        return False

if __name__ == "__main__":
    asyncio.run(main())