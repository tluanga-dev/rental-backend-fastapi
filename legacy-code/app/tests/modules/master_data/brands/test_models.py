import pytest
from uuid import uuid4
from datetime import datetime

from app.modules.master_data.brands.models import Brand
from app.core.errors import ValidationError


class TestBrandModel:
    """Tests for Brand model."""
    
    def test_brand_creation_valid(self):
        """Test creating a valid brand."""
        brand = Brand(
            name="Test Brand",
            code="TST",
            description="Test brand description"
        )
        
        assert brand.name == "Test Brand"
        assert brand.code == "TST"
        assert brand.description == "Test brand description"
        assert brand.is_active is True
        assert brand.id is not None
        assert brand.created_at is not None
        assert brand.updated_at is None  # Not updated yet
    
    def test_brand_creation_no_code(self):
        """Test creating a brand without code."""
        brand = Brand(
            name="Test Brand",
            description="Test brand description"
        )
        
        assert brand.name == "Test Brand"
        assert brand.code is None
        assert brand.description == "Test brand description"
        assert brand.is_active is True
    
    def test_brand_creation_no_description(self):
        """Test creating a brand without description."""
        brand = Brand(
            name="Test Brand",
            code="TST"
        )
        
        assert brand.name == "Test Brand"
        assert brand.code == "TST"
        assert brand.description is None
        assert brand.is_active is True
    
    def test_brand_creation_minimal(self):
        """Test creating a brand with minimal data."""
        brand = Brand(name="Test Brand")
        
        assert brand.name == "Test Brand"
        assert brand.code is None
        assert brand.description is None
        assert brand.is_active is True
    
    def test_brand_validation_empty_name(self):
        """Test validation fails for empty name."""
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            Brand(name="")
    
    def test_brand_validation_whitespace_name(self):
        """Test validation fails for whitespace-only name."""
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            Brand(name="   ")
    
    def test_brand_validation_long_name(self):
        """Test validation fails for name too long."""
        long_name = "a" * 101
        with pytest.raises(ValueError, match="Brand name cannot exceed 100 characters"):
            Brand(name=long_name)
    
    def test_brand_validation_empty_code(self):
        """Test validation fails for empty code."""
        with pytest.raises(ValueError, match="Brand code cannot be empty if provided"):
            Brand(name="Test Brand", code="")
    
    def test_brand_validation_whitespace_code(self):
        """Test validation fails for whitespace-only code."""
        with pytest.raises(ValueError, match="Brand code cannot be empty if provided"):
            Brand(name="Test Brand", code="   ")
    
    def test_brand_validation_long_code(self):
        """Test validation fails for code too long."""
        long_code = "a" * 21
        with pytest.raises(ValueError, match="Brand code cannot exceed 20 characters"):
            Brand(name="Test Brand", code=long_code)
    
    def test_brand_validation_invalid_code_characters(self):
        """Test validation fails for invalid code characters."""
        with pytest.raises(ValueError, match="Brand code must contain only letters, numbers, hyphens, and underscores"):
            Brand(name="Test Brand", code="TST@123")
    
    def test_brand_validation_code_auto_uppercase(self):
        """Test that code is automatically converted to uppercase."""
        brand = Brand(name="Test Brand", code="tst")
        assert brand.code == "TST"
    
    def test_brand_validation_long_description(self):
        """Test validation fails for description too long."""
        long_description = "a" * 1001
        with pytest.raises(ValueError, match="Brand description cannot exceed 1000 characters"):
            Brand(name="Test Brand", description=long_description)
    
    def test_brand_update_info_name(self):
        """Test updating brand name."""
        brand = Brand(name="Original Name")
        
        brand.update_info(name="Updated Name", updated_by="user123")
        
        assert brand.name == "Updated Name"
        assert brand.updated_by == "user123"
        assert brand.updated_at is not None
    
    def test_brand_update_info_code(self):
        """Test updating brand code."""
        brand = Brand(name="Test Brand", code="OLD")
        
        brand.update_info(code="NEW", updated_by="user123")
        
        assert brand.code == "NEW"
        assert brand.updated_by == "user123"
        assert brand.updated_at is not None
    
    def test_brand_update_info_description(self):
        """Test updating brand description."""
        brand = Brand(name="Test Brand", description="Old description")
        
        brand.update_info(description="New description", updated_by="user123")
        
        assert brand.description == "New description"
        assert brand.updated_by == "user123"
        assert brand.updated_at is not None
    
    def test_brand_update_info_validation(self):
        """Test update info validation."""
        brand = Brand(name="Test Brand")
        
        # Test empty name validation
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            brand.update_info(name="")
        
        # Test long name validation
        with pytest.raises(ValueError, match="Brand name cannot exceed 100 characters"):
            brand.update_info(name="a" * 101)
        
        # Test empty code validation
        with pytest.raises(ValueError, match="Brand code cannot be empty if provided"):
            brand.update_info(code="")
        
        # Test invalid code characters
        with pytest.raises(ValueError, match="Brand code must contain only letters, numbers, hyphens, and underscores"):
            brand.update_info(code="TST@123")
        
        # Test long description validation
        with pytest.raises(ValueError, match="Brand description cannot exceed 1000 characters"):
            brand.update_info(description="a" * 1001)
    
    def test_brand_display_name_with_code(self):
        """Test display name with code."""
        brand = Brand(name="Test Brand", code="TST")
        assert brand.display_name == "Test Brand (TST)"
    
    def test_brand_display_name_without_code(self):
        """Test display name without code."""
        brand = Brand(name="Test Brand")
        assert brand.display_name == "Test Brand"
    
    def test_brand_has_items_property(self):
        """Test has_items property."""
        brand = Brand(name="Test Brand")
        # Without items relationship loaded, this should be False
        assert brand.has_items is False
    
    def test_brand_can_delete(self):
        """Test can_delete method."""
        brand = Brand(name="Test Brand")
        # Without items, should be able to delete
        assert brand.can_delete() is True
        
        # If inactive, cannot delete
        brand.is_active = False
        assert brand.can_delete() is False
    
    def test_brand_str_representation(self):
        """Test string representation."""
        brand = Brand(name="Test Brand", code="TST")
        assert str(brand) == "Test Brand (TST)"
        
        brand_no_code = Brand(name="Test Brand")
        assert str(brand_no_code) == "Test Brand"
    
    def test_brand_repr_representation(self):
        """Test repr representation."""
        brand = Brand(name="Test Brand", code="TST")
        repr_str = repr(brand)
        
        assert "Brand(" in repr_str
        assert "name='Test Brand'" in repr_str
        assert "code='TST'" in repr_str
        assert "active=True" in repr_str
    
    def test_brand_code_with_hyphens_and_underscores(self):
        """Test that codes with hyphens and underscores are valid."""
        brand1 = Brand(name="Test Brand", code="TST-123")
        assert brand1.code == "TST-123"
        
        brand2 = Brand(name="Test Brand", code="TST_123")
        assert brand2.code == "TST_123"
        
        brand3 = Brand(name="Test Brand", code="TST-123_ABC")
        assert brand3.code == "TST-123_ABC"
    
    def test_brand_code_alphanumeric(self):
        """Test that alphanumeric codes are valid."""
        brand = Brand(name="Test Brand", code="TST123")
        assert brand.code == "TST123"
    
    def test_brand_created_at_timestamp(self):
        """Test that created_at is set on creation."""
        brand = Brand(name="Test Brand")
        assert brand.created_at is not None
        assert isinstance(brand.created_at, datetime)
    
    def test_brand_updated_at_initially_none(self):
        """Test that updated_at is initially None."""
        brand = Brand(name="Test Brand")
        assert brand.updated_at is None
    
    def test_brand_updated_at_set_on_update(self):
        """Test that updated_at is set when updated."""
        brand = Brand(name="Test Brand")
        original_updated_at = brand.updated_at
        
        brand.update_info(name="Updated Name")
        
        assert brand.updated_at is not None
        assert brand.updated_at != original_updated_at
    
    def test_brand_id_is_uuid(self):
        """Test that brand ID is a valid UUID."""
        brand = Brand(name="Test Brand")
        assert brand.id is not None
        # Check that it's a valid UUID format
        assert str(brand.id).count("-") == 4  # Basic UUID format check
    
    def test_brand_audit_fields(self):
        """Test audit fields are set correctly."""
        brand = Brand(
            name="Test Brand",
            created_by="creator123",
            updated_by="updater123"
        )
        
        assert brand.created_by == "creator123"
        assert brand.updated_by == "updater123"
    
    def test_brand_is_active_default(self):
        """Test that is_active defaults to True."""
        brand = Brand(name="Test Brand")
        assert brand.is_active is True
    
    def test_brand_is_active_can_be_set(self):
        """Test that is_active can be set to False."""
        brand = Brand(name="Test Brand", is_active=False)
        assert brand.is_active is False