#!/usr/bin/env python3
"""
Script to update API documentation files to reflect schema changes:
- Remove purchase_price and supplier_id references
- Update unit_of_measurement_id to be required
"""

import re
import os

def update_file(file_path):
    """Update a single file to remove purchase_price and supplier_id references."""
    print(f"Updating {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove purchase_price from JSON examples
    content = re.sub(r'[,\s]*"purchase_price":\s*[\d.]+,?\s*', '', content)
    
    # Remove supplier_id from JSON examples and schema definitions
    content = re.sub(r'[,\s]*"?supplier_id"?\??:\s*[^,\n]+,?\s*', '', content)
    
    # Update unit_of_measurement_id to be required in TypeScript interfaces
    content = re.sub(
        r'unit_of_measurement_id\?\?:\s*string\s*\|\s*null;.*',
        'unit_of_measurement_id: string;  // REQUIRED - UUID reference to units table',
        content
    )
    
    # Fix ItemListResponse to remove purchase_price line
    content = re.sub(r'.*purchase_price.*\n', '', content)
    
    # Update examples to include unit_of_measurement_id where needed
    # Pattern for JSON objects that have item_type but no unit_of_measurement_id
    def add_uom_to_json(match):
        json_obj = match.group(0)
        if '"unit_of_measurement_id"' not in json_obj and '"item_type"' in json_obj:
            # Add unit_of_measurement_id after item_type
            json_obj = re.sub(
                r'("item_type":\s*"[^"]+"),',
                r'\1,\n  "unit_of_measurement_id": "12345678-1234-1234-1234-123456789012",',
                json_obj
            )
        return json_obj
    
    # Apply to JSON blocks
    content = re.sub(r'\{[^}]*"item_code"[^}]*\}', add_uom_to_json, content, flags=re.DOTALL)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Updated {file_path}")
        return True
    else:
        print(f"  ℹ️  No changes needed for {file_path}")
        return False

def main():
    """Update all documentation files."""
    doc_files = [
        'ITEM_MASTER_API_COMPLETE_GUIDE.md',
        'ITEM_MASTER_API_LLM_REFERENCE.md', 
        'ITEM_MASTER_API_DOCUMENTATION.md',
        'API_REFERENCE.md'
    ]
    
    updated_count = 0
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            if update_file(doc_file):
                updated_count += 1
        else:
            print(f"  ⚠️  File not found: {doc_file}")
    
    print(f"\n🎉 Updated {updated_count} documentation files")
    print("\nSchema changes applied:")
    print("  ✅ Removed purchase_price field references")  
    print("  ✅ Removed supplier_id field references")
    print("  ✅ Made unit_of_measurement_id required")

if __name__ == "__main__":
    main()