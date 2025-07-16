#!/usr/bin/env python3
"""
Unified script to seed all master data from a single CSV file.
This script parses the master_seed_data.csv file and loads all entities
in the correct dependency order.
"""

import asyncio
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime
import re

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.database import async_session_maker, engine
from app.modules.suppliers.models import Supplier, SupplierType, SupplierTier, SupplierStatus, PaymentTerms
from app.modules.customers.models import Customer, CustomerType, CustomerTier, CustomerStatus, BlacklistStatus, CreditRating
from app.modules.master_data.units.models import UnitOfMeasurement
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.categories.models import Category
from app.modules.master_data.locations.models import Location, LocationType
from app.modules.master_data.item_master.models import Item, ItemStatus

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class SeedDataParser:
    """Parser for master seed data CSV file."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.sections = {}
        self.errors = []
        self.warnings = []
        
    def parse_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """Parse the master CSV file into sections."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            current_section = None
            current_headers = None
            current_data = []
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Skip comment lines
                if line.startswith('#'):
                    continue
                
                # Check for section headers
                if line.startswith('## '):
                    # Save previous section if exists
                    if current_section and current_data:
                        self.sections[current_section] = current_data
                    
                    # Start new section
                    current_section = line[3:].strip()
                    current_headers = None
                    current_data = []
                    continue
                
                # Skip if no current section
                if not current_section:
                    continue
                
                # Parse CSV line
                try:
                    csv_reader = csv.reader([line])
                    row = next(csv_reader)
                    
                    # First non-comment line after section header is headers
                    if current_headers is None:
                        current_headers = row
                        continue
                    
                    # Convert row to dictionary
                    if len(row) >= len(current_headers):
                        row_dict = {}
                        for i, header in enumerate(current_headers):
                            value = row[i] if i < len(row) else ''
                            # Convert empty strings to None
                            row_dict[header] = value.strip() if value.strip() else None
                        current_data.append(row_dict)
                    else:
                        self.warnings.append(f"Line {line_num}: Row has fewer columns than headers")
                        
                except Exception as e:
                    self.errors.append(f"Line {line_num}: Error parsing CSV: {e}")
            
            # Save last section
            if current_section and current_data:
                self.sections[current_section] = current_data
                
            return self.sections
            
        except FileNotFoundError:
            self.errors.append(f"File not found: {self.file_path}")
            return {}
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return {}


class MasterDataSeeder:
    """Seeder for all master data entities."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.session = None
        self.stats = {
            'suppliers': {'created': 0, 'updated': 0, 'errors': 0},
            'customers': {'created': 0, 'updated': 0, 'errors': 0},
            'units': {'created': 0, 'updated': 0, 'errors': 0},
            'brands': {'created': 0, 'updated': 0, 'errors': 0},
            'categories': {'created': 0, 'updated': 0, 'errors': 0},
            'locations': {'created': 0, 'updated': 0, 'errors': 0},
            'items': {'created': 0, 'updated': 0, 'errors': 0},
        }
        
        # Caches for lookups
        self.units_cache = {}
        self.brands_cache = {}
        self.categories_cache = {}
        self.locations_cache = {}
    
    async def seed_all(self, sections: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Seed all data sections in dependency order."""
        async with async_session_maker() as session:
            self.session = session
            
            try:
                if not self.dry_run:
                    await session.begin()
                
                print(f"{Colors.HEADER}=== Master Data Seeding Started ==={Colors.ENDC}")
                print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
                
                # Load in dependency order
                await self._seed_units(sections.get('UNITS_OF_MEASUREMENT', []))
                await self._seed_brands(sections.get('BRANDS', []))
                await self._seed_locations(sections.get('LOCATIONS', []))
                await self._seed_categories(sections.get('CATEGORIES', []))
                await self._seed_suppliers(sections.get('SUPPLIERS', []))
                await self._seed_customers(sections.get('CUSTOMERS', []))
                await self._seed_items(sections.get('ITEMS', []))
                
                if not self.dry_run:
                    await session.commit()
                    print(f"\n{Colors.GREEN}✅ All data committed successfully!{Colors.ENDC}")
                else:
                    print(f"\n{Colors.CYAN}📋 Dry run completed - no data was saved{Colors.ENDC}")
                
                return self.stats
                
            except Exception as e:
                if not self.dry_run:
                    await session.rollback()
                print(f"\n{Colors.FAIL}❌ Error occurred: {e}{Colors.ENDC}")
                raise
    
    async def _seed_units(self, units_data: List[Dict[str, Any]]):
        """Seed units of measurement."""
        print(f"\n{Colors.CYAN}📏 Seeding Units of Measurement...{Colors.ENDC}")
        
        for unit_data in units_data:
            try:
                name = unit_data.get('name')
                if not name:
                    self.stats['units']['errors'] += 1
                    continue
                
                # Check if exists
                if not self.dry_run:
                    result = await self.session.execute(
                        text("SELECT id FROM units_of_measurement WHERE name = :name"),
                        {'name': name}
                    )
                    existing = result.fetchone()
                    
                    if existing:
                        self.stats['units']['updated'] += 1
                        self.units_cache[name] = existing[0]
                        print(f"  {Colors.WARNING}↻{Colors.ENDC} Updated unit: {name}")
                        continue
                
                # Create new unit
                unit = UnitOfMeasurement(
                    name=name,
                    abbreviation=unit_data.get('abbreviation'),
                    description=unit_data.get('description')
                )
                
                if not self.dry_run:
                    self.session.add(unit)
                    await self.session.flush()
                    self.units_cache[name] = unit.id
                
                self.stats['units']['created'] += 1
                print(f"  {Colors.GREEN}✓{Colors.ENDC} Created unit: {name}")
                
            except Exception as e:
                self.stats['units']['errors'] += 1
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Error with unit {unit_data.get('name')}: {e}")
    
    async def _seed_brands(self, brands_data: List[Dict[str, Any]]):
        """Seed brands."""
        print(f"\n{Colors.CYAN}🏷️  Seeding Brands...{Colors.ENDC}")
        
        for brand_data in brands_data:
            try:
                name = brand_data.get('name')
                if not name:
                    self.stats['brands']['errors'] += 1
                    continue
                
                # Check if exists
                if not self.dry_run:
                    result = await self.session.execute(
                        text("SELECT id FROM brands WHERE name = :name"),
                        {'name': name}
                    )
                    existing = result.fetchone()
                    
                    if existing:
                        self.stats['brands']['updated'] += 1
                        self.brands_cache[name] = existing[0]
                        print(f"  {Colors.WARNING}↻{Colors.ENDC} Updated brand: {name}")
                        continue
                
                # Create new brand
                brand = Brand(
                    name=name,
                    code=brand_data.get('code'),
                    description=brand_data.get('description')
                )
                
                if not self.dry_run:
                    self.session.add(brand)
                    await self.session.flush()
                    self.brands_cache[name] = brand.id
                
                self.stats['brands']['created'] += 1
                print(f"  {Colors.GREEN}✓{Colors.ENDC} Created brand: {name}")
                
            except Exception as e:
                self.stats['brands']['errors'] += 1
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Error with brand {brand_data.get('name')}: {e}")
    
    async def _seed_locations(self, locations_data: List[Dict[str, Any]]):
        """Seed locations."""
        print(f"\n{Colors.CYAN}📍 Seeding Locations...{Colors.ENDC}")
        
        for location_data in locations_data:
            try:
                location_code = location_data.get('location_code')
                if not location_code:
                    self.stats['locations']['errors'] += 1
                    continue
                
                # Check if exists
                if not self.dry_run:
                    result = await self.session.execute(
                        text("SELECT id FROM locations WHERE location_code = :code"),
                        {'code': location_code}
                    )
                    existing = result.fetchone()
                    
                    if existing:
                        self.stats['locations']['updated'] += 1
                        self.locations_cache[location_code] = existing[0]
                        print(f"  {Colors.WARNING}↻{Colors.ENDC} Updated location: {location_code}")
                        continue
                
                # Create new location
                location = Location(
                    location_code=location_code,
                    location_name=location_data.get('location_name'),
                    location_type=LocationType(location_data.get('location_type')),
                    address=location_data.get('address'),
                    city=location_data.get('city'),
                    state=location_data.get('state'),
                    country=location_data.get('country'),
                    postal_code=location_data.get('postal_code'),
                    contact_number=location_data.get('contact_number'),
                    email=location_data.get('email')
                )
                
                if not self.dry_run:
                    self.session.add(location)
                    await self.session.flush()
                    self.locations_cache[location_code] = location.id
                
                self.stats['locations']['created'] += 1
                print(f"  {Colors.GREEN}✓{Colors.ENDC} Created location: {location_code}")
                
            except Exception as e:
                self.stats['locations']['errors'] += 1
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Error with location {location_data.get('location_code')}: {e}")
    
    async def _seed_categories(self, categories_data: List[Dict[str, Any]]):
        """Seed categories with hierarchy support."""
        print(f"\n{Colors.CYAN}📂 Seeding Categories...{Colors.ENDC}")
        
        # First pass: create root categories
        for category_data in categories_data:
            try:
                name = category_data.get('name')
                parent_name = category_data.get('parent_category_name')
                
                if not name:
                    self.stats['categories']['errors'] += 1
                    continue
                
                # Skip child categories in first pass
                if parent_name:
                    continue
                
                await self._create_category(category_data)
                
            except Exception as e:
                self.stats['categories']['errors'] += 1
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Error with category {category_data.get('name')}: {e}")
        
        # Second pass: create child categories
        for category_data in categories_data:
            try:
                name = category_data.get('name')
                parent_name = category_data.get('parent_category_name')
                
                if not name or not parent_name:
                    continue
                
                await self._create_category(category_data)
                
            except Exception as e:
                self.stats['categories']['errors'] += 1
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Error with category {category_data.get('name')}: {e}")
    
    async def _create_category(self, category_data: Dict[str, Any]):
        """Create a single category."""
        name = category_data.get('name')
        parent_name = category_data.get('parent_category_name')
        
        # Check if exists
        if not self.dry_run:
            result = await self.session.execute(
                text("SELECT id FROM categories WHERE name = :name"),
                {'name': name}
            )
            existing = result.fetchone()
            
            if existing:
                self.stats['categories']['updated'] += 1
                self.categories_cache[name] = existing[0]
                print(f"  {Colors.WARNING}↻{Colors.ENDC} Updated category: {name}")
                return
        
        # Get parent ID if specified
        parent_id = None
        if parent_name:
            parent_id = self.categories_cache.get(parent_name)
            if not parent_id:
                print(f"  {Colors.WARNING}⚠{Colors.ENDC} Parent category '{parent_name}' not found for '{name}'")
                return
        
        # Create category
        category = Category(
            name=name,
            parent_category_id=parent_id,
            display_order=int(category_data.get('display_order', 0)),
            is_leaf=category_data.get('is_leaf', 'TRUE').upper() == 'TRUE'
        )
        
        if not self.dry_run:
            self.session.add(category)
            await self.session.flush()
            self.categories_cache[name] = category.id
        
        self.stats['categories']['created'] += 1
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Created category: {name}")
    
    async def _seed_suppliers(self, suppliers_data: List[Dict[str, Any]]):
        """Seed suppliers."""
        print(f"\n{Colors.CYAN}🏢 Seeding Suppliers...{Colors.ENDC}")
        
        for supplier_data in suppliers_data:
            try:
                supplier_code = supplier_data.get('supplier_code')
                if not supplier_code:
                    self.stats['suppliers']['errors'] += 1
                    continue
                
                # Check if exists
                if not self.dry_run:
                    result = await self.session.execute(
                        text("SELECT id FROM suppliers WHERE supplier_code = :code"),
                        {'code': supplier_code}
                    )
                    existing = result.fetchone()
                    
                    if existing:
                        self.stats['suppliers']['updated'] += 1
                        print(f"  {Colors.WARNING}↻{Colors.ENDC} Updated supplier: {supplier_code}")
                        continue
                
                # Create supplier
                supplier = Supplier(
                    supplier_code=supplier_code,
                    company_name=supplier_data.get('company_name'),
                    supplier_type=SupplierType(supplier_data.get('supplier_type')),
                    contact_person=supplier_data.get('contact_person'),
                    email=supplier_data.get('email'),
                    phone=supplier_data.get('phone'),
                    mobile=supplier_data.get('mobile'),
                    address_line1=supplier_data.get('address_line1'),
                    address_line2=supplier_data.get('address_line2'),
                    city=supplier_data.get('city'),
                    state=supplier_data.get('state'),
                    postal_code=supplier_data.get('postal_code'),
                    country=supplier_data.get('country'),
                    tax_id=supplier_data.get('tax_id'),
                    payment_terms=PaymentTerms(supplier_data.get('payment_terms', 'NET30')),
                    credit_limit=Decimal(supplier_data.get('credit_limit', '0')),
                    supplier_tier=SupplierTier(supplier_data.get('supplier_tier', 'STANDARD')),
                    status=SupplierStatus(supplier_data.get('status', 'ACTIVE')),
                    notes=supplier_data.get('notes'),
                    website=supplier_data.get('website'),
                    account_manager=supplier_data.get('account_manager'),
                    preferred_payment_method=supplier_data.get('preferred_payment_method'),
                    certifications=supplier_data.get('certifications')
                )
                
                # Update performance metrics if provided
                if supplier_data.get('quality_rating'):
                    supplier.quality_rating = float(supplier_data.get('quality_rating'))
                if supplier_data.get('delivery_rating'):
                    supplier.delivery_rating = float(supplier_data.get('delivery_rating'))
                
                if not self.dry_run:
                    self.session.add(supplier)
                
                self.stats['suppliers']['created'] += 1
                print(f"  {Colors.GREEN}✓{Colors.ENDC} Created supplier: {supplier_code}")
                
            except Exception as e:
                self.stats['suppliers']['errors'] += 1
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Error with supplier {supplier_data.get('supplier_code')}: {e}")
    
    async def _seed_customers(self, customers_data: List[Dict[str, Any]]):
        """Seed customers."""
        print(f"\n{Colors.CYAN}👥 Seeding Customers...{Colors.ENDC}")
        
        for customer_data in customers_data:
            try:
                customer_code = customer_data.get('customer_code')
                if not customer_code:
                    self.stats['customers']['errors'] += 1
                    continue
                
                # Check if exists
                if not self.dry_run:
                    result = await self.session.execute(
                        text("SELECT id FROM customers WHERE customer_code = :code"),
                        {'code': customer_code}
                    )
                    existing = result.fetchone()
                    
                    if existing:
                        self.stats['customers']['updated'] += 1
                        print(f"  {Colors.WARNING}↻{Colors.ENDC} Updated customer: {customer_code}")
                        continue
                
                # Create customer
                customer = Customer(
                    customer_code=customer_code,
                    customer_type=CustomerType(customer_data.get('customer_type')),
                    business_name=customer_data.get('business_name'),
                    first_name=customer_data.get('first_name'),
                    last_name=customer_data.get('last_name'),
                    email=customer_data.get('email'),
                    phone=customer_data.get('phone'),
                    mobile=customer_data.get('mobile'),
                    address_line1=customer_data.get('address_line1'),
                    address_line2=customer_data.get('address_line2'),
                    city=customer_data.get('city'),
                    state=customer_data.get('state'),
                    country=customer_data.get('country'),
                    postal_code=customer_data.get('postal_code'),
                    tax_number=customer_data.get('tax_number'),
                    payment_terms=customer_data.get('payment_terms'),
                    customer_tier=CustomerTier(customer_data.get('customer_tier', 'BRONZE')),
                    credit_limit=Decimal(customer_data.get('credit_limit', '0')),
                    status=CustomerStatus(customer_data.get('status', 'ACTIVE')),
                    blacklist_status=BlacklistStatus(customer_data.get('blacklist_status', 'CLEAR')),
                    credit_rating=CreditRating(customer_data.get('credit_rating', 'GOOD')),
                    notes=customer_data.get('notes')
                )
                
                if not self.dry_run:
                    self.session.add(customer)
                
                self.stats['customers']['created'] += 1
                print(f"  {Colors.GREEN}✓{Colors.ENDC} Created customer: {customer_code}")
                
            except Exception as e:
                self.stats['customers']['errors'] += 1
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Error with customer {customer_data.get('customer_code')}: {e}")
    
    async def _seed_items(self, items_data: List[Dict[str, Any]]):
        """Seed items."""
        print(f"\n{Colors.CYAN}📦 Seeding Items...{Colors.ENDC}")
        
        for item_data in items_data:
            try:
                item_name = item_data.get('item_name')
                if not item_name:
                    self.stats['items']['errors'] += 1
                    continue
                
                # Get unit ID
                unit_name = item_data.get('unit_name')
                unit_id = self.units_cache.get(unit_name)
                if not unit_id:
                    print(f"  {Colors.WARNING}⚠{Colors.ENDC} Unit '{unit_name}' not found for item '{item_name}'")
                    self.stats['items']['errors'] += 1
                    continue
                
                # Get brand ID (optional)
                brand_id = None
                brand_name = item_data.get('brand_name')
                if brand_name:
                    brand_id = self.brands_cache.get(brand_name)
                
                # Get category ID (optional)
                category_id = None
                category_name = item_data.get('category_name')
                if category_name:
                    category_id = self.categories_cache.get(category_name)
                
                # Check if exists by SKU or name
                sku = item_data.get('sku')
                if not self.dry_run:
                    if sku:
                        result = await self.session.execute(
                            text("SELECT id FROM items WHERE sku = :sku"),
                            {'sku': sku}
                        )
                    else:
                        result = await self.session.execute(
                            text("SELECT id FROM items WHERE item_name = :name"),
                            {'name': item_name}
                        )
                    existing = result.fetchone()
                    
                    if existing:
                        self.stats['items']['updated'] += 1
                        print(f"  {Colors.WARNING}↻{Colors.ENDC} Updated item: {item_name}")
                        continue
                
                # Create item
                item = Item(
                    sku=sku,  # Will be auto-generated if None
                    item_name=item_name,
                    unit_of_measurement_id=unit_id,
                    brand_id=brand_id,
                    category_id=category_id,
                    item_status=ItemStatus(item_data.get('item_status', 'ACTIVE')),
                    rental_rate_per_period=Decimal(item_data.get('rental_rate_per_period', '0')),
                    rental_period=item_data.get('rental_period', '1'),
                    sale_price=Decimal(item_data.get('sale_price', '0')),
                    purchase_price=Decimal(item_data.get('purchase_price', '0')),
                    security_deposit=Decimal(item_data.get('security_deposit', '0')),
                    reorder_point=int(item_data.get('reorder_point', '0')),
                    description=item_data.get('description'),
                    specifications=item_data.get('specifications'),
                    model_number=item_data.get('model_number'),
                    serial_number_required=item_data.get('serial_number_required', 'FALSE').upper() == 'TRUE',
                    warranty_period_days=item_data.get('warranty_period_days', '0'),
                    is_rentable=item_data.get('is_rentable', 'TRUE').upper() == 'TRUE',
                    is_saleable=item_data.get('is_saleable', 'FALSE').upper() == 'TRUE'
                )
                
                if not self.dry_run:
                    self.session.add(item)
                
                self.stats['items']['created'] += 1
                print(f"  {Colors.GREEN}✓{Colors.ENDC} Created item: {item_name}")
                
            except Exception as e:
                self.stats['items']['errors'] += 1
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Error with item {item_data.get('item_name')}: {e}")


def print_summary(stats: Dict[str, Any], errors: List[str], warnings: List[str]):
    """Print seeding summary."""
    print(f"\n{Colors.HEADER}=== SEEDING SUMMARY ==={Colors.ENDC}")
    
    total_created = sum(stat['created'] for stat in stats.values())
    total_updated = sum(stat['updated'] for stat in stats.values())
    total_errors = sum(stat['errors'] for stat in stats.values())
    
    print(f"Total Records Created: {Colors.GREEN}{total_created}{Colors.ENDC}")
    print(f"Total Records Updated: {Colors.WARNING}{total_updated}{Colors.ENDC}")
    print(f"Total Errors: {Colors.FAIL}{total_errors}{Colors.ENDC}")
    
    print(f"\n{Colors.CYAN}Breakdown by Entity:{Colors.ENDC}")
    for entity, stat in stats.items():
        print(f"  {entity.capitalize()}: {Colors.GREEN}{stat['created']} created{Colors.ENDC}, "
              f"{Colors.WARNING}{stat['updated']} updated{Colors.ENDC}, "
              f"{Colors.FAIL}{stat['errors']} errors{Colors.ENDC}")
    
    if warnings:
        print(f"\n{Colors.WARNING}Warnings:{Colors.ENDC}")
        for warning in warnings:
            print(f"  • {warning}")
    
    if errors:
        print(f"\n{Colors.FAIL}Errors:{Colors.ENDC}")
        for error in errors:
            print(f"  • {error}")


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed all master data from CSV file')
    parser.add_argument('file', nargs='?', default='data/seed_data/master_seed_data.csv',
                        help='Path to master seed data CSV file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without saving to database')
    parser.add_argument('--sections', 
                        help='Comma-separated list of sections to process (e.g., SUPPLIERS,CUSTOMERS)')
    
    args = parser.parse_args()
    
    # Resolve file path
    file_path = Path(args.file)
    if not file_path.is_absolute():
        file_path = Path(__file__).parent.parent / file_path
    
    print(f"{Colors.HEADER}{Colors.BOLD}=== Master Data Seeding Tool ==={Colors.ENDC}")
    print(f"File: {file_path}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    
    # Parse CSV file
    parser = SeedDataParser(str(file_path))
    sections = parser.parse_file()
    
    if parser.errors:
        print(f"\n{Colors.FAIL}Parse errors occurred:{Colors.ENDC}")
        for error in parser.errors:
            print(f"  • {error}")
        return
    
    if not sections:
        print(f"\n{Colors.FAIL}No data sections found in file{Colors.ENDC}")
        return
    
    # Filter sections if specified
    if args.sections:
        section_names = [s.strip().upper() for s in args.sections.split(',')]
        sections = {k: v for k, v in sections.items() if k in section_names}
    
    print(f"\n{Colors.CYAN}Found sections:{Colors.ENDC}")
    for section, data in sections.items():
        print(f"  • {section}: {len(data)} records")
    
    # Seed data
    try:
        seeder = MasterDataSeeder(dry_run=args.dry_run)
        stats = await seeder.seed_all(sections)
        
        print_summary(stats, parser.errors, parser.warnings)
        
    except Exception as e:
        print(f"\n{Colors.FAIL}Seeding failed: {e}{Colors.ENDC}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())