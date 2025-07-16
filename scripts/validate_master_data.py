#!/usr/bin/env python3
"""
Script to validate master seed data CSV file without importing to database.
This script checks format, required fields, and data consistency.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
import re
from decimal import Decimal, InvalidOperation

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the parser from the main seeding script
from seed_all_data import SeedDataParser, Colors


class DataValidator:
    """Validator for master seed data."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
        # Valid enum values
        self.valid_enums = {
            'supplier_type': ['MANUFACTURER', 'DISTRIBUTOR', 'WHOLESALER', 'RETAILER', 'INVENTORY', 'SERVICE', 'DIRECT'],
            'payment_terms': ['IMMEDIATE', 'NET15', 'NET30', 'NET45', 'NET60', 'NET90', 'COD'],
            'supplier_tier': ['PREMIUM', 'STANDARD', 'BASIC', 'TRIAL'],
            'supplier_status': ['ACTIVE', 'INACTIVE', 'PENDING', 'APPROVED', 'SUSPENDED', 'BLACKLISTED'],
            'customer_type': ['INDIVIDUAL', 'BUSINESS'],
            'customer_tier': ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM'],
            'customer_status': ['ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING'],
            'blacklist_status': ['CLEAR', 'WARNING', 'BLACKLISTED'],
            'credit_rating': ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'NO_RATING'],
            'location_type': ['STORE', 'WAREHOUSE', 'SERVICE_CENTER'],
            'item_status': ['ACTIVE', 'INACTIVE', 'DISCONTINUED'],
            'boolean': ['TRUE', 'FALSE']
        }
    
    def validate_all(self, sections: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Validate all sections."""
        valid = True
        
        print(f"{Colors.HEADER}=== Data Validation Started ==={Colors.ENDC}")
        
        # Validate each section
        for section_name, data in sections.items():
            section_valid = self._validate_section(section_name, data)
            if not section_valid:
                valid = False
        
        # Cross-reference validation
        self._validate_references(sections)
        
        return valid
    
    def _validate_section(self, section_name: str, data: List[Dict[str, Any]]) -> bool:
        """Validate a single section."""
        print(f"\n{Colors.CYAN}Validating {section_name}...{Colors.ENDC}")
        
        if not data:
            self.warnings.append(f"{section_name}: No data found")
            return True
        
        valid = True
        
        for i, row in enumerate(data, 1):
            row_valid = True
            
            if section_name == 'SUPPLIERS':
                row_valid = self._validate_supplier(row, i)
            elif section_name == 'CUSTOMERS':
                row_valid = self._validate_customer(row, i)
            elif section_name == 'UNITS_OF_MEASUREMENT':
                row_valid = self._validate_unit(row, i)
            elif section_name == 'BRANDS':
                row_valid = self._validate_brand(row, i)
            elif section_name == 'CATEGORIES':
                row_valid = self._validate_category(row, i)
            elif section_name == 'LOCATIONS':
                row_valid = self._validate_location(row, i)
            elif section_name == 'ITEMS':
                row_valid = self._validate_item(row, i)
            
            if not row_valid:
                valid = False
        
        if valid:
            print(f"  {Colors.GREEN}✓{Colors.ENDC} {len(data)} records validated")
        else:
            print(f"  {Colors.FAIL}✗{Colors.ENDC} Validation errors found")
        
        return valid
    
    def _validate_supplier(self, row: Dict[str, Any], row_num: int) -> bool:
        """Validate supplier row."""
        valid = True
        
        # Required fields
        if not row.get('supplier_code'):
            self.errors.append(f"SUPPLIERS row {row_num}: supplier_code is required")
            valid = False
        
        if not row.get('company_name'):
            self.errors.append(f"SUPPLIERS row {row_num}: company_name is required")
            valid = False
        
        if not row.get('supplier_type'):
            self.errors.append(f"SUPPLIERS row {row_num}: supplier_type is required")
            valid = False
        elif row['supplier_type'] not in self.valid_enums['supplier_type']:
            self.errors.append(f"SUPPLIERS row {row_num}: invalid supplier_type '{row['supplier_type']}'")
            valid = False
        
        # Optional enum fields
        if row.get('payment_terms') and row['payment_terms'] not in self.valid_enums['payment_terms']:
            self.errors.append(f"SUPPLIERS row {row_num}: invalid payment_terms '{row['payment_terms']}'")
            valid = False
        
        if row.get('supplier_tier') and row['supplier_tier'] not in self.valid_enums['supplier_tier']:
            self.errors.append(f"SUPPLIERS row {row_num}: invalid supplier_tier '{row['supplier_tier']}'")
            valid = False
        
        if row.get('status') and row['status'] not in self.valid_enums['supplier_status']:
            self.errors.append(f"SUPPLIERS row {row_num}: invalid status '{row['status']}'")
            valid = False
        
        # Email validation
        if row.get('email') and not self._is_valid_email(row['email']):
            self.errors.append(f"SUPPLIERS row {row_num}: invalid email format")
            valid = False
        
        # Numeric fields
        if row.get('credit_limit') and not self._is_valid_decimal(row['credit_limit']):
            self.errors.append(f"SUPPLIERS row {row_num}: invalid credit_limit")
            valid = False
        
        if row.get('quality_rating') and not self._is_valid_rating(row['quality_rating']):
            self.errors.append(f"SUPPLIERS row {row_num}: invalid quality_rating (must be 0-5)")
            valid = False
        
        if row.get('delivery_rating') and not self._is_valid_rating(row['delivery_rating']):
            self.errors.append(f"SUPPLIERS row {row_num}: invalid delivery_rating (must be 0-5)")
            valid = False
        
        return valid
    
    def _validate_customer(self, row: Dict[str, Any], row_num: int) -> bool:
        """Validate customer row."""
        valid = True
        
        # Required fields
        if not row.get('customer_code'):
            self.errors.append(f"CUSTOMERS row {row_num}: customer_code is required")
            valid = False
        
        if not row.get('customer_type'):
            self.errors.append(f"CUSTOMERS row {row_num}: customer_type is required")
            valid = False
        elif row['customer_type'] not in self.valid_enums['customer_type']:
            self.errors.append(f"CUSTOMERS row {row_num}: invalid customer_type '{row['customer_type']}'")
            valid = False
        
        # Type-specific validation
        if row.get('customer_type') == 'INDIVIDUAL':
            if not row.get('first_name'):
                self.errors.append(f"CUSTOMERS row {row_num}: first_name is required for INDIVIDUAL customers")
                valid = False
            if not row.get('last_name'):
                self.errors.append(f"CUSTOMERS row {row_num}: last_name is required for INDIVIDUAL customers")
                valid = False
        elif row.get('customer_type') == 'BUSINESS':
            if not row.get('business_name'):
                self.errors.append(f"CUSTOMERS row {row_num}: business_name is required for BUSINESS customers")
                valid = False
        
        # Optional enum fields
        if row.get('customer_tier') and row['customer_tier'] not in self.valid_enums['customer_tier']:
            self.errors.append(f"CUSTOMERS row {row_num}: invalid customer_tier '{row['customer_tier']}'")
            valid = False
        
        if row.get('status') and row['status'] not in self.valid_enums['customer_status']:
            self.errors.append(f"CUSTOMERS row {row_num}: invalid status '{row['status']}'")
            valid = False
        
        if row.get('blacklist_status') and row['blacklist_status'] not in self.valid_enums['blacklist_status']:
            self.errors.append(f"CUSTOMERS row {row_num}: invalid blacklist_status '{row['blacklist_status']}'")
            valid = False
        
        if row.get('credit_rating') and row['credit_rating'] not in self.valid_enums['credit_rating']:
            self.errors.append(f"CUSTOMERS row {row_num}: invalid credit_rating '{row['credit_rating']}'")
            valid = False
        
        # Email validation
        if row.get('email') and not self._is_valid_email(row['email']):
            self.errors.append(f"CUSTOMERS row {row_num}: invalid email format")
            valid = False
        
        # Numeric fields
        if row.get('credit_limit') and not self._is_valid_decimal(row['credit_limit']):
            self.errors.append(f"CUSTOMERS row {row_num}: invalid credit_limit")
            valid = False
        
        return valid
    
    def _validate_unit(self, row: Dict[str, Any], row_num: int) -> bool:
        """Validate unit row."""
        valid = True
        
        if not row.get('name'):
            self.errors.append(f"UNITS_OF_MEASUREMENT row {row_num}: name is required")
            valid = False
        
        return valid
    
    def _validate_brand(self, row: Dict[str, Any], row_num: int) -> bool:
        """Validate brand row."""
        valid = True
        
        if not row.get('name'):
            self.errors.append(f"BRANDS row {row_num}: name is required")
            valid = False
        
        return valid
    
    def _validate_category(self, row: Dict[str, Any], row_num: int) -> bool:
        """Validate category row."""
        valid = True
        
        if not row.get('name'):
            self.errors.append(f"CATEGORIES row {row_num}: name is required")
            valid = False
        
        # Boolean validation
        if row.get('is_leaf') and row['is_leaf'] not in self.valid_enums['boolean']:
            self.errors.append(f"CATEGORIES row {row_num}: invalid is_leaf value '{row['is_leaf']}'")
            valid = False
        
        # Numeric validation
        if row.get('display_order') and not self._is_valid_integer(row['display_order']):
            self.errors.append(f"CATEGORIES row {row_num}: invalid display_order")
            valid = False
        
        return valid
    
    def _validate_location(self, row: Dict[str, Any], row_num: int) -> bool:
        """Validate location row."""
        valid = True
        
        # Required fields
        required_fields = ['location_code', 'location_name', 'location_type', 'address', 'city', 'state', 'country']
        for field in required_fields:
            if not row.get(field):
                self.errors.append(f"LOCATIONS row {row_num}: {field} is required")
                valid = False
        
        # Enum validation
        if row.get('location_type') and row['location_type'] not in self.valid_enums['location_type']:
            self.errors.append(f"LOCATIONS row {row_num}: invalid location_type '{row['location_type']}'")
            valid = False
        
        # Email validation
        if row.get('email') and not self._is_valid_email(row['email']):
            self.errors.append(f"LOCATIONS row {row_num}: invalid email format")
            valid = False
        
        return valid
    
    def _validate_item(self, row: Dict[str, Any], row_num: int) -> bool:
        """Validate item row."""
        valid = True
        
        # Required fields
        if not row.get('item_name'):
            self.errors.append(f"ITEMS row {row_num}: item_name is required")
            valid = False
        
        if not row.get('unit_name'):
            self.errors.append(f"ITEMS row {row_num}: unit_name is required")
            valid = False
        
        if not row.get('reorder_point'):
            self.errors.append(f"ITEMS row {row_num}: reorder_point is required")
            valid = False
        elif not self._is_valid_integer(row['reorder_point']):
            self.errors.append(f"ITEMS row {row_num}: invalid reorder_point")
            valid = False
        
        # Enum validation
        if row.get('item_status') and row['item_status'] not in self.valid_enums['item_status']:
            self.errors.append(f"ITEMS row {row_num}: invalid item_status '{row['item_status']}'")
            valid = False
        
        # Boolean validation
        boolean_fields = ['serial_number_required', 'is_rentable', 'is_saleable']
        for field in boolean_fields:
            if row.get(field) and row[field] not in self.valid_enums['boolean']:
                self.errors.append(f"ITEMS row {row_num}: invalid {field} value '{row[field]}'")
                valid = False
        
        # Numeric validation
        decimal_fields = ['rental_rate_per_period', 'sale_price', 'purchase_price', 'security_deposit']
        for field in decimal_fields:
            if row.get(field) and not self._is_valid_decimal(row[field]):
                self.errors.append(f"ITEMS row {row_num}: invalid {field}")
                valid = False
        
        # Business logic validation
        is_rentable = row.get('is_rentable', 'TRUE').upper() == 'TRUE'
        is_saleable = row.get('is_saleable', 'FALSE').upper() == 'TRUE'
        
        if not is_rentable and not is_saleable:
            self.errors.append(f"ITEMS row {row_num}: item must be either rentable or saleable")
            valid = False
        
        return valid
    
    def _validate_references(self, sections: Dict[str, List[Dict[str, Any]]]):
        """Validate cross-references between sections."""
        print(f"\n{Colors.CYAN}Validating references...{Colors.ENDC}")
        
        # Build reference sets
        units = {row['name'] for row in sections.get('UNITS_OF_MEASUREMENT', []) if row.get('name')}
        brands = {row['name'] for row in sections.get('BRANDS', []) if row.get('name')}
        categories = {row['name'] for row in sections.get('CATEGORIES', []) if row.get('name')}
        
        # Validate category hierarchy
        for i, cat in enumerate(sections.get('CATEGORIES', []), 1):
            parent = cat.get('parent_category_name')
            if parent and parent not in categories:
                self.errors.append(f"CATEGORIES row {i}: parent category '{parent}' not found")
        
        # Validate item references
        for i, item in enumerate(sections.get('ITEMS', []), 1):
            unit_name = item.get('unit_name')
            if unit_name and unit_name not in units:
                self.errors.append(f"ITEMS row {i}: unit '{unit_name}' not found")
            
            brand_name = item.get('brand_name')
            if brand_name and brand_name not in brands:
                self.errors.append(f"ITEMS row {i}: brand '{brand_name}' not found")
            
            category_name = item.get('category_name')
            if category_name and category_name not in categories:
                self.errors.append(f"ITEMS row {i}: category '{category_name}' not found")
        
        if not self.errors:
            print(f"  {Colors.GREEN}✓{Colors.ENDC} All references validated")
        else:
            print(f"  {Colors.FAIL}✗{Colors.ENDC} Reference errors found")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_decimal(self, value: str) -> bool:
        """Validate decimal value."""
        try:
            Decimal(value)
            return True
        except (InvalidOperation, ValueError):
            return False
    
    def _is_valid_integer(self, value: str) -> bool:
        """Validate integer value."""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_valid_rating(self, value: str) -> bool:
        """Validate rating value (0-5)."""
        try:
            rating = float(value)
            return 0 <= rating <= 5
        except (ValueError, TypeError):
            return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate master seed data CSV file')
    parser.add_argument('file', nargs='?', default='data/seed_data/master_seed_data.csv',
                        help='Path to master seed data CSV file')
    
    args = parser.parse_args()
    
    # Resolve file path
    file_path = Path(args.file)
    if not file_path.is_absolute():
        file_path = Path(__file__).parent.parent / file_path
    
    print(f"{Colors.HEADER}{Colors.BOLD}=== Master Data Validation Tool ==={Colors.ENDC}")
    print(f"File: {file_path}")
    
    # Parse CSV file
    parser = SeedDataParser(str(file_path))
    sections = parser.parse_file()
    
    if parser.errors:
        print(f"\n{Colors.FAIL}Parse errors occurred:{Colors.ENDC}")
        for error in parser.errors:
            print(f"  • {error}")
        return False
    
    if not sections:
        print(f"\n{Colors.FAIL}No data sections found in file{Colors.ENDC}")
        return False
    
    print(f"\n{Colors.CYAN}Found sections:{Colors.ENDC}")
    for section, data in sections.items():
        print(f"  • {section}: {len(data)} records")
    
    # Validate data
    validator = DataValidator()
    valid = validator.validate_all(sections)
    
    # Print summary
    print(f"\n{Colors.HEADER}=== VALIDATION SUMMARY ==={Colors.ENDC}")
    
    if valid:
        print(f"{Colors.GREEN}✅ All validation checks passed!{Colors.ENDC}")
        print(f"File is ready for import.")
    else:
        print(f"{Colors.FAIL}❌ Validation failed with {len(validator.errors)} errors{Colors.ENDC}")
    
    if validator.warnings:
        print(f"\n{Colors.WARNING}Warnings ({len(validator.warnings)}):{Colors.ENDC}")
        for warning in validator.warnings:
            print(f"  • {warning}")
    
    if validator.errors:
        print(f"\n{Colors.FAIL}Errors ({len(validator.errors)}):{Colors.ENDC}")
        for error in validator.errors:
            print(f"  • {error}")
    
    return valid


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)