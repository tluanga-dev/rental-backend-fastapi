import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.models import Company


@pytest.mark.asyncio
class TestCompanyModel:
    """Test cases for company model validation."""
    
    async def test_create_company_valid(self, db_session: AsyncSession):
        """Test creating a valid company."""
        # Arrange & Act
        company = Company(
            company_name="Model Test Company",
            address="123 Model Street",
            email="model@test.com",
            phone="+91-1234567890",
            gst_no="29ABCDE1234F1Z5",
            registration_number="REG123456789"
        )
        
        # Assert
        assert company.company_name == "Model Test Company"
        assert company.email == "model@test.com"
        assert company.gst_no == "29ABCDE1234F1Z5"
        assert company.registration_number == "REG123456789"
        assert company.is_active is True
    
    async def test_company_name_required(self, db_session: AsyncSession):
        """Test that company name is required."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Company(
                company_name="",  # Empty name
                email="test@test.com"
            )
        
        assert "Company name cannot be empty" in str(exc_info.value)
    
    async def test_company_name_whitespace(self, db_session: AsyncSession):
        """Test that company name cannot be only whitespace."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Company(
                company_name="   ",  # Only whitespace
                email="test@test.com"
            )
        
        assert "Company name cannot be empty" in str(exc_info.value)
    
    async def test_company_name_too_long(self, db_session: AsyncSession):
        """Test that company name cannot exceed max length."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Company(
                company_name="A" * 256,  # Too long
                email="test@test.com"
            )
        
        assert "cannot exceed 255 characters" in str(exc_info.value)
    
    async def test_email_validation_invalid_format(self, db_session: AsyncSession):
        """Test email format validation."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Company(
                company_name="Test Company",
                email="invalid-email"  # Missing @ and domain
            )
        
        assert "Invalid email format" in str(exc_info.value)
    
    async def test_email_validation_empty(self, db_session: AsyncSession):
        """Test that empty email is rejected if provided."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Company(
                company_name="Test Company",
                email=""  # Empty email
            )
        
        assert "Email cannot be empty if provided" in str(exc_info.value)
    
    async def test_email_optional(self, db_session: AsyncSession):
        """Test that email is optional."""
        # Act
        company = Company(
            company_name="No Email Company"
            # No email provided
        )
        
        # Assert
        assert company.email is None
    
    async def test_gst_no_uppercase(self, db_session: AsyncSession):
        """Test that GST number is converted to uppercase."""
        # Act
        company = Company(
            company_name="Test Company",
            gst_no="29abcde1234f1z5"  # Lowercase
        )
        
        # Assert
        assert company.gst_no == "29ABCDE1234F1Z5"
    
    async def test_gst_no_empty(self, db_session: AsyncSession):
        """Test that empty GST number is rejected if provided."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Company(
                company_name="Test Company",
                gst_no=""  # Empty GST
            )
        
        assert "GST number cannot be empty if provided" in str(exc_info.value)
    
    async def test_registration_number_uppercase(self, db_session: AsyncSession):
        """Test that registration number is converted to uppercase."""
        # Act
        company = Company(
            company_name="Test Company",
            registration_number="reg123abc"  # Lowercase
        )
        
        # Assert
        assert company.registration_number == "REG123ABC"
    
    async def test_phone_validation_empty(self, db_session: AsyncSession):
        """Test that empty phone is rejected if provided."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Company(
                company_name="Test Company",
                phone=""  # Empty phone
            )
        
        assert "Phone cannot be empty if provided" in str(exc_info.value)
    
    async def test_phone_too_long(self, db_session: AsyncSession):
        """Test that phone cannot exceed max length."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Company(
                company_name="Test Company",
                phone="+" + "1" * 50  # Too long
            )
        
        assert "cannot exceed 50 characters" in str(exc_info.value)
    
    async def test_update_info_method(self, db_session: AsyncSession):
        """Test the update_info method."""
        # Arrange
        company = Company(
            company_name="Original Company",
            email="original@company.com",
            phone="+91-1111111111"
        )
        
        # Act
        company.update_info(
            company_name="Updated Company",
            email="updated@company.com",
            phone="+91-2222222222",
            updated_by="updater"
        )
        
        # Assert
        assert company.company_name == "Updated Company"
        assert company.email == "updated@company.com"
        assert company.phone == "+91-2222222222"
        assert company.updated_by == "updater"
    
    async def test_update_info_validation(self, db_session: AsyncSession):
        """Test that update_info validates data."""
        # Arrange
        company = Company(
            company_name="Test Company",
            email="test@company.com"
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            company.update_info(
                email="invalid-email"  # Invalid format
            )
        
        assert "Invalid email format" in str(exc_info.value)
    
    async def test_update_info_partial(self, db_session: AsyncSession):
        """Test partial update with update_info."""
        # Arrange
        company = Company(
            company_name="Test Company",
            email="test@company.com",
            phone="+91-1111111111",
            gst_no="12ABCDE3456F7G8"
        )
        
        # Act - Update only phone
        company.update_info(
            phone="+91-9999999999",
            updated_by="partial_updater"
        )
        
        # Assert - Only phone should be updated
        assert company.phone == "+91-9999999999"
        assert company.company_name == "Test Company"  # Unchanged
        assert company.email == "test@company.com"  # Unchanged
        assert company.gst_no == "12ABCDE3456F7G8"  # Unchanged
        assert company.updated_by == "partial_updater"
    
    async def test_display_name_property(self, db_session: AsyncSession):
        """Test the display_name property."""
        # Act
        company = Company(
            company_name="Display Test Company"
        )
        
        # Assert
        assert company.display_name == "Display Test Company"
    
    async def test_str_representation(self, db_session: AsyncSession):
        """Test string representation."""
        # Act
        company = Company(
            company_name="String Test Company"
        )
        
        # Assert
        assert str(company) == "String Test Company"
    
    async def test_repr_representation(self, db_session: AsyncSession):
        """Test developer representation."""
        # Act
        company = Company(
            company_name="Repr Test Company"
        )
        
        # Assert
        repr_str = repr(company)
        assert "Company" in repr_str
        assert "Repr Test Company" in repr_str
        assert "active=True" in repr_str