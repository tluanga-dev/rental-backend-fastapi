# Master Data Seeding Guide

## Overview

This system provides a unified approach to seeding all master data entities from a single CSV file. The system handles dependencies, validation, and provides comprehensive reporting.

## File Structure

```
data/seed_data/
├── master_seed_data.csv          # Main seed data file
└── README.md                     # Data format documentation

scripts/
├── seed_all_data.py              # Main seeding script
├── export_master_data.py         # Export current data to CSV
└── validate_master_data.py       # Validate CSV before import
```

## Master Data Entities

The system seeds the following entities in dependency order:

1. **Units of Measurement** (no dependencies)
2. **Brands** (no dependencies) 
3. **Locations** (no dependencies)
4. **Categories** (hierarchical, self-referential)
5. **Suppliers** (no dependencies)
6. **Customers** (no dependencies)
7. **Items** (depends on units, brands, categories)

## CSV File Format

### File Structure

The `master_seed_data.csv` file uses section markers to separate different entity types:

```csv
## SUPPLIERS
# Comments explaining field constraints
supplier_code,company_name,supplier_type,...
[supplier data rows]

## CUSTOMERS
customer_code,customer_type,business_name,...
[customer data rows]

## UNITS_OF_MEASUREMENT
name,abbreviation,description
[unit data rows]

...and so on
```

### Section Markers

- Section headers start with `## ` (e.g., `## SUPPLIERS`)
- Comments start with `#` and are ignored
- Empty lines are ignored
- First non-comment line after section header contains column headers

### Supported Sections

#### SUPPLIERS
**Required Fields:**
- `supplier_code` (unique, max 50 chars)
- `company_name` (max 255 chars)
- `supplier_type` (MANUFACTURER, DISTRIBUTOR, WHOLESALER, RETAILER, INVENTORY, SERVICE, DIRECT)

**Optional Fields:**
- `contact_person`, `email`, `phone`, `mobile`
- `address_line1`, `address_line2`, `city`, `state`, `postal_code`, `country`
- `tax_id`, `website`, `account_manager`, `notes`, `certifications`
- `payment_terms` (IMMEDIATE, NET15, NET30, NET45, NET60, NET90, COD)
- `credit_limit` (decimal, default: 0)
- `supplier_tier` (PREMIUM, STANDARD, BASIC, TRIAL)
- `status` (ACTIVE, INACTIVE, PENDING, APPROVED, SUSPENDED, BLACKLISTED)
- `quality_rating`, `delivery_rating` (0-5)

#### CUSTOMERS
**Required Fields:**
- `customer_code` (unique, max 20 chars)
- `customer_type` (INDIVIDUAL, BUSINESS)
- For INDIVIDUAL: `first_name` + `last_name`
- For BUSINESS: `business_name`

**Optional Fields:**
- `email`, `phone`, `mobile`
- `address_line1`, `address_line2`, `city`, `state`, `country`, `postal_code`
- `tax_number`, `payment_terms`, `notes`
- `customer_tier` (BRONZE, SILVER, GOLD, PLATINUM)
- `credit_limit` (decimal, default: 0)
- `status` (ACTIVE, INACTIVE, SUSPENDED, PENDING)
- `blacklist_status` (CLEAR, WARNING, BLACKLISTED)
- `credit_rating` (EXCELLENT, GOOD, FAIR, POOR, NO_RATING)

#### UNITS_OF_MEASUREMENT
**Required Fields:**
- `name` (unique, max 50 chars)

**Optional Fields:**
- `abbreviation` (unique, max 10 chars)
- `description` (max 500 chars)

#### BRANDS
**Required Fields:**
- `name` (unique, max 100 chars)

**Optional Fields:**
- `code` (unique, max 20 chars, auto-uppercased)
- `description` (max 1000 chars)

#### CATEGORIES
**Required Fields:**
- `name` (max 100 chars)

**Optional Fields:**
- `parent_category_name` (name of parent category)
- `display_order` (integer, default: 0)
- `is_leaf` (TRUE/FALSE, default: TRUE)

**Hierarchy Rules:**
- Root categories: leave `parent_category_name` empty
- Child categories: specify `parent_category_name`
- Parent categories are processed before child categories

#### LOCATIONS
**Required Fields:**
- `location_code` (unique, max 20 chars, auto-uppercased)
- `location_name` (max 100 chars)
- `location_type` (STORE, WAREHOUSE, SERVICE_CENTER)
- `address`, `city`, `state`, `country`

**Optional Fields:**
- `postal_code`, `contact_number`, `email`
- `manager_email` (for reference only)

#### ITEMS
**Required Fields:**
- `item_name` (max 200 chars)
- `unit_name` (must exist in UNITS_OF_MEASUREMENT)
- `reorder_point` (integer, >= 0)

**Optional Fields:**
- `sku` (auto-generated if empty)
- `brand_name` (must exist in BRANDS)
- `category_name` (must exist in CATEGORIES)
- `item_status` (ACTIVE, INACTIVE, DISCONTINUED)
- `rental_rate_per_period`, `sale_price`, `purchase_price`, `security_deposit` (decimals)
- `rental_period` (string, must be positive integer)
- `description`, `specifications`, `model_number`
- `serial_number_required` (TRUE/FALSE)
- `warranty_period_days` (string, must be valid number)
- `is_rentable`, `is_saleable` (TRUE/FALSE, mutually exclusive)

## Usage

### Basic Usage

```bash
# Seed all data
python scripts/seed_all_data.py

# Specify custom file
python scripts/seed_all_data.py /path/to/custom_seed_data.csv

# Dry run (preview without saving)
python scripts/seed_all_data.py --dry-run

# Seed specific sections only
python scripts/seed_all_data.py --sections SUPPLIERS,CUSTOMERS
```

### Docker Usage

```bash
# Seed data inside container
docker-compose exec app python scripts/seed_all_data.py

# Dry run inside container
docker-compose exec app python scripts/seed_all_data.py --dry-run
```

### Command Line Options

- `--dry-run`: Preview changes without saving to database
- `--sections`: Process only specified sections (comma-separated)
- `--help`: Show help message

## Features

### Data Validation
- Validates all enum values
- Checks required fields
- Validates email and phone formats
- Ensures unique constraints
- Validates foreign key references

### Dependency Handling
- Processes entities in correct dependency order
- Resolves references by name (e.g., items reference units by name)
- Handles hierarchical categories correctly

### Error Handling
- Continues processing after individual record errors
- Provides detailed error messages
- Rollback on serious errors

### Idempotency
- Checks for existing records by unique keys
- Updates existing records or skips them
- Prevents duplicate entries

### Progress Reporting
- Color-coded output for easy reading
- Progress indicators for each entity type
- Detailed summary at completion

## Example Output

```
=== Master Data Seeding Started ===
Mode: LIVE

📏 Seeding Units of Measurement...
  ✓ Created unit: Piece
  ✓ Created unit: Kilogram
  ↻ Updated unit: Meter

🏷️  Seeding Brands...
  ✓ Created brand: Sony
  ✓ Created brand: Canon

📍 Seeding Locations...
  ✓ Created location: MAIN001
  ✓ Created location: WARE001

📂 Seeding Categories...
  ✓ Created category: Electronics
  ✓ Created category: Audio

🏢 Seeding Suppliers...
  ✓ Created supplier: SUP001
  ✓ Created supplier: SUP002

👥 Seeding Customers...
  ✓ Created customer: CUST001
  ✓ Created customer: CUST002

📦 Seeding Items...
  ✓ Created item: Professional Studio Speakers
  ✓ Created item: Wireless Microphone System

✅ All data committed successfully!

=== SEEDING SUMMARY ===
Total Records Created: 125
Total Records Updated: 15
Total Errors: 2

Breakdown by Entity:
  Suppliers: 10 created, 0 updated, 0 errors
  Customers: 10 created, 0 updated, 0 errors
  Units: 20 created, 0 updated, 0 errors
  Brands: 20 created, 0 updated, 0 errors
  Categories: 35 created, 0 updated, 0 errors
  Locations: 7 created, 0 updated, 0 errors
  Items: 23 created, 0 updated, 2 errors
```

## Google Sheets Integration

### Creating Google Sheets Version

1. Import the CSV file into Google Sheets
2. Create separate sheets for each section
3. Add data validation for enum fields
4. Use conditional formatting for required fields

### Exporting from Google Sheets

1. Export each sheet as CSV
2. Use provided utility script to merge into master format
3. Or export as Excel file and convert

## Troubleshooting

### Common Issues

1. **File Not Found**
   - Check file path is correct
   - Ensure file is in `data/seed_data/` directory

2. **Parse Errors**
   - Check CSV format is correct
   - Ensure section headers start with `## `
   - Verify no extra commas in data

3. **Validation Errors**
   - Check enum values match exactly
   - Verify required fields are not empty
   - Check email formats are valid

4. **Reference Errors**
   - Ensure referenced entities exist (units, brands, categories)
   - Check spelling of reference names
   - Verify hierarchy for categories

5. **Permission Errors**
   - Check database is running
   - Verify connection credentials
   - Ensure proper database permissions

### Debug Mode

Use `--dry-run` to validate data without saving:

```bash
python scripts/seed_all_data.py --dry-run
```

This will show:
- What would be created/updated
- All validation errors
- Reference resolution issues

## Best Practices

1. **Always use dry run first**
2. **Backup database before seeding**
3. **Start with small data sets**
4. **Validate required fields**
5. **Use consistent naming conventions**
6. **Keep CSV file under version control**
7. **Test with sample data first**

## Related Scripts

- `export_master_data.py` - Export current data to CSV format
- `validate_master_data.py` - Validate CSV without importing
- `clear_all_data_except_auth.py` - Clear data before re-seeding