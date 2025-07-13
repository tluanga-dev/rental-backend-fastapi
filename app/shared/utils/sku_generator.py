"""
SKU Generation Utility.

This module provides intelligent SKU generation for inventory items based on
category hierarchy, product names, and automatic sequence numbering.
"""

import re
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.modules.inventory.models import SKUSequence
from app.modules.master_data.categories.models import Category
from app.core.errors import ValidationError


class SKUGenerator:
    """
    SKU generation service for creating unique Stock Keeping Units.
    
    Generates SKUs in the format: {CATEGORY}-{SUBCATEGORY}-{PRODUCT_NAME}-{ATTRIBUTES}-{SEQUENCE}
    Examples:
    - ELEC-CAM-DSLR-R-001 (Electronics > Cameras > DSLR Camera, Rental)
    - FURN-CHR-OFFI-B-001 (Furniture > Chairs > Office Chair, Both)
    - TOOL-PWR-DRIL-R-001 (Tools > Power Tools > Drill, Rental)
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize SKU generator with database session."""
        self.session = session
        self._category_cache = {}  # Cache for category lookups
    
    async def generate_sku(
        self,
        category_id: Optional[UUID] = None,
        item_name: str = "",
        is_rentable: bool = True,
        is_saleable: bool = False
    ) -> str:
        """
        Generate a unique SKU for an item.
        
        Args:
            category_id: Category UUID for the item
            item_name: Name of the item for product abbreviation
            is_rentable: Whether item can be rented
            is_saleable: Whether item can be sold
            
        Returns:
            Generated unique SKU string in format: CATEGORY-SUBCATEGORY-PRODUCT-ATTRIBUTES-SEQUENCE
            
        Raises:
            ValidationError: If SKU generation fails
        """
        # Extract category components
        category_code, subcategory_code = await self._get_category_components(category_id)
        
        # Generate product name abbreviation (first 4 letters)
        product_code = self._get_product_code(item_name)
        
        # Generate attributes code from boolean fields
        attributes_code = self._get_attributes_code_from_booleans(is_rentable, is_saleable)
        
        # Create composite key for sequence tracking
        sku_key = f"{category_code}-{subcategory_code}-{product_code}-{attributes_code}"
        
        # Get next sequence number
        sequence_number = await self._get_next_sequence(sku_key)
        
        # Format final SKU
        sku = f"{category_code}-{subcategory_code}-{product_code}-{attributes_code}-{sequence_number:03d}"
        
        # Validate uniqueness (safety check)
        await self._validate_sku_uniqueness(sku)
        
        return sku
    
    async def preview_sku(
        self,
        category_id: Optional[UUID] = None,
        item_name: str = "",
        is_rentable: bool = True,
        is_saleable: bool = False
    ) -> str:
        """
        Preview what SKU would be generated without actually generating it.
        
        Args:
            category_id: Category UUID for the item
            item_name: Name of the item for product abbreviation
            is_rentable: Whether item can be rented
            is_saleable: Whether item can be sold
            
        Returns:
            Preview SKU string
        """
        # Extract category components
        category_code, subcategory_code = await self._get_category_components(category_id)
        
        # Generate product name abbreviation (first 4 letters)
        product_code = self._get_product_code(item_name)
        
        # Generate attributes code from boolean fields
        attributes_code = self._get_attributes_code_from_booleans(is_rentable, is_saleable)
        
        # Create composite key for sequence tracking
        sku_key = f"{category_code}-{subcategory_code}-{product_code}-{attributes_code}"
        
        # Get current sequence (without incrementing)
        sequence_record = await self._get_sequence_record(sku_key)
        sequence_number = sequence_record.get_next_sequence_number() if sequence_record else 1
        
        return f"{category_code}-{subcategory_code}-{product_code}-{attributes_code}-{sequence_number:03d}"
    
    async def _get_category_components(self, category_id: Optional[UUID]) -> Tuple[str, str]:
        """
        Extract category and subcategory codes from category hierarchy.
        
        Args:
            category_id: Category UUID
            
        Returns:
            Tuple of (category_code, subcategory_code)
        """
        if not category_id:
            return "MISC", "ITEM"
        
        # Check cache first
        cache_key = str(category_id)
        if cache_key in self._category_cache:
            return self._category_cache[cache_key]
        
        query = select(Category).where(Category.id == category_id, Category.is_active == True)
        result = await self.session.execute(query)
        category = result.scalar_one_or_none()
        
        if not category:
            result = "MISC", "ITEM"
            self._category_cache[cache_key] = result
            return result
        
        # Parse category path to extract hierarchy
        category_path = category.category_path or category.name
        path_parts = [part.strip() for part in category_path.split('/')]
        
        if len(path_parts) >= 2:
            # We have at least root and subcategory
            category_code = self._generate_code_from_name(path_parts[0], max_length=4)
            subcategory_code = self._generate_code_from_name(path_parts[1], max_length=3)
        elif len(path_parts) == 1:
            # Only root category available
            category_code = self._generate_code_from_name(path_parts[0], max_length=4)
            subcategory_code = "GEN"  # Generic subcategory
        else:
            # Fallback
            category_code = "MISC"
            subcategory_code = "ITEM"
        
        result = category_code, subcategory_code
        # Cache the result for future use
        self._category_cache[cache_key] = result
        return result
    
    def _get_product_code(self, item_name: str) -> str:
        """
        Generate product code from item name (first 4 letters).
        
        Args:
            item_name: Name of the item
            
        Returns:
            4-character product code
        """
        if not item_name:
            return "PROD"
        
        # Remove special characters and get only alphanumeric
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', item_name.upper())
        
        if len(clean_name) >= 4:
            return clean_name[:4]
        elif len(clean_name) > 0:
            # Pad with zeros if less than 4 characters
            return clean_name.ljust(4, '0')
        else:
            return "PROD"
    
    def _get_attributes_code_from_booleans(self, is_rentable: bool, is_saleable: bool) -> str:
        """
        Generate attributes code from boolean fields.
        
        Args:
            is_rentable: Whether item can be rented
            is_saleable: Whether item can be sold
            
        Returns:
            1-character attributes code
        """
        if is_rentable and not is_saleable:
            return "R"
        elif is_saleable and not is_rentable:
            return "S"
        else:
            # This shouldn't happen due to validation, but default to R
            return "R"
    
    def _generate_code_from_name(self, name: str, max_length: int = 8) -> str:
        """
        Generate a code from a name by extracting key characters.
        
        Args:
            name: Name to generate code from
            max_length: Maximum length of generated code
            
        Returns:
            Generated code string
        """
        if not name:
            return ""
        
        # Remove special characters and split into words
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        words = clean_name.upper().split()
        
        if not words:
            return ""
        
        # Strategy 1: First letter of each word
        if len(words) > 1:
            code = ''.join(word[0] for word in words if word)
            if len(code) <= max_length:
                return code
        
        # Strategy 2: First word with vowels removed
        first_word = words[0]
        code = re.sub(r'[AEIOU]', '', first_word)
        if len(code) >= 2 and len(code) <= max_length:
            return code
        
        # Strategy 3: First few characters of first word
        return first_word[:max_length]
    
    async def _get_next_sequence(self, sku_key: str) -> int:
        """
        Get next sequence number for SKU key combination.
        
        Args:
            sku_key: Composite SKU key for sequence tracking
            
        Returns:
            Next sequence number
        """
        # Use SELECT FOR UPDATE to prevent race conditions
        from sqlalchemy import text
        
        sequence_record = await self._get_sequence_record_for_update(sku_key)
        
        if sequence_record:
            # Increment existing sequence
            next_seq = sequence_record.get_next_sequence_number()
            sequence_record.increment_sequence()
            # Flush to ensure the update is made but don't commit yet
            await self.session.flush()
            return next_seq
        else:
            # Create new sequence record using the composite key as brand_code
            new_sequence = SKUSequence(
                brand_code=sku_key,  # Using composite key as identifier
                category_code=None,  # Not used in new format
                next_sequence="2"  # Start at 2 since we're returning 1
            )
            self.session.add(new_sequence)
            # Flush to ensure the insert is made but don't commit yet
            await self.session.flush()
            return 1
    
    async def _get_sequence_record(self, sku_key: str) -> Optional[SKUSequence]:
        """Get existing sequence record for SKU key."""
        query = select(SKUSequence).where(
            SKUSequence.brand_code == sku_key,
            SKUSequence.category_code.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_sequence_record_for_update(self, sku_key: str) -> Optional[SKUSequence]:
        """Get existing sequence record for SKU key with row locking."""
        query = select(SKUSequence).where(
            SKUSequence.brand_code == sku_key,
            SKUSequence.category_code.is_(None)
        ).with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    
    def _validate_sku_format(self, sku: str) -> str:
        """
        Validate SKU format for the new 5-component structure.
        
        Args:
            sku: SKU string to validate
            
        Returns:
            Normalized SKU string
            
        Raises:
            ValidationError: If SKU format is invalid
        """
        if not sku:
            raise ValidationError("SKU cannot be empty")
        
        # Normalize to uppercase and strip whitespace
        normalized_sku = sku.upper().strip()
        
        # Check length
        if len(normalized_sku) < 10 or len(normalized_sku) > 50:
            raise ValidationError("SKU must be between 10 and 50 characters")
        
        # Check format: should have 5 parts separated by hyphens
        parts = normalized_sku.split('-')
        if len(parts) != 5:
            raise ValidationError("SKU must have exactly 5 parts separated by hyphens")
        
        # Validate each part
        category_code, subcategory_code, product_code, attributes_code, sequence = parts
        
        if len(category_code) > 4 or not category_code.isalnum():
            raise ValidationError("Category code must be 1-4 alphanumeric characters")
        
        if len(subcategory_code) > 4 or not subcategory_code.isalnum():
            raise ValidationError("Subcategory code must be 1-4 alphanumeric characters")
        
        if len(product_code) != 4 or not product_code.isalnum():
            raise ValidationError("Product code must be exactly 4 alphanumeric characters")
        
        if len(attributes_code) != 1 or attributes_code not in ['R', 'S', 'B']:
            raise ValidationError("Attributes code must be R (Rental), S (Sale), or B (Both)")
        
        if len(sequence) != 3 or not sequence.isdigit():
            raise ValidationError("Sequence must be exactly 3 digits")
        
        return normalized_sku
    
    async def _validate_sku_uniqueness(self, sku: str) -> None:
        """
        Validate that SKU is unique.
        
        Args:
            sku: SKU string to check
            
        Raises:
            ValidationError: If SKU already exists
        """
        # Import here to avoid circular import
        from app.modules.master_data.item_master.models import Item
        
        query = select(Item).where(Item.sku == sku)
        result = await self.session.execute(query)
        existing_item = result.scalar_one_or_none()
        
        if existing_item:
            raise ValidationError(f"SKU '{sku}' already exists")
    
    async def bulk_generate_skus_for_existing_items(self) -> dict:
        """
        Generate SKUs for existing items that don't have them.
        
        Returns:
            Dictionary with generation statistics
        """
        # Import here to avoid circular import
        from app.modules.master_data.item_master.models import Item
        
        # Find items without SKUs
        query = select(Item).where(Item.sku.is_(None))
        result = await self.session.execute(query)
        items_without_skus = result.scalars().all()
        
        if not items_without_skus:
            return {
                "total_processed": 0,
                "successful_generations": 0,
                "failed_generations": 0,
                "errors": []
            }
        
        successful = 0
        failed = 0
        errors = []
        
        for item in items_without_skus:
            try:
                # Generate SKU based on item's category, name, and boolean fields
                sku = await self.generate_sku(
                    category_id=item.category_id,
                    item_name=item.item_name,
                    is_rentable=item.is_rentable,
                    is_saleable=item.is_saleable
                )
                
                # Update item with generated SKU
                item.sku = sku
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    "item_id": str(item.id),
                    "sku": item.sku,
                    "error": str(e)
                })
        
        # Commit all changes
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            return {
                "total_processed": len(items_without_skus),
                "successful_generations": 0,
                "failed_generations": len(items_without_skus),
                "errors": [{"error": f"Failed to commit changes: {str(e)}"}]
            }
        
        return {
            "total_processed": len(items_without_skus),
            "successful_generations": successful,
            "failed_generations": failed,
            "errors": errors
        }