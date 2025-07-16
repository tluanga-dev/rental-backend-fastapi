from typing import Optional
from sqlalchemy import Column, String, Text, Index

from app.db.base import BaseModel


class Company(BaseModel):
    """
    Company model for managing company information.
    
    Attributes:
        company_name: Name of the company
        address: Company address
        email: Company email address
        phone: Company phone number
        gst_no: GST registration number
        registration_number: Company registration number
    """
    
    __tablename__ = "companies"
    
    # Basic company information
    company_name = Column(String(255), nullable=False, unique=True, index=True, comment="Company name")
    address = Column(Text, nullable=True, comment="Company address")
    email = Column(String(255), nullable=True, comment="Company email")
    phone = Column(String(50), nullable=True, comment="Company phone number")
    gst_no = Column(String(50), nullable=True, unique=True, index=True, comment="GST registration number")
    registration_number = Column(String(100), nullable=True, unique=True, index=True, comment="Company registration number")
    
    # Additional indexes for performance
    __table_args__ = (
        Index('idx_company_name_active', 'company_name', 'is_active'),
    )
    
    def __init__(
        self,
        company_name: str,
        address: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        gst_no: Optional[str] = None,
        registration_number: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Company.
        
        Args:
            company_name: Company name
            address: Company address
            email: Company email
            phone: Company phone number
            gst_no: GST registration number
            registration_number: Company registration number
            **kwargs: Additional BaseModel fields
        """
        super().__init__(
            company_name=company_name,
            address=address,
            email=email,
            phone=phone,
            gst_no=gst_no,
            registration_number=registration_number,
            **kwargs
        )
        self._validate()
    
    def _validate(self):
        """Validate company business rules."""
        # Company name validation
        if not self.company_name or not self.company_name.strip():
            raise ValueError("Company name cannot be empty")
        
        if len(self.company_name) > 255:
            raise ValueError("Company name cannot exceed 255 characters")
        
        # Email validation
        if self.email:
            if not self.email.strip():
                raise ValueError("Email cannot be empty if provided")
            
            if len(self.email) > 255:
                raise ValueError("Email cannot exceed 255 characters")
            
            # Basic email format validation
            if "@" not in self.email or "." not in self.email.split("@")[-1]:
                raise ValueError("Invalid email format")
        
        # Phone validation
        if self.phone:
            if not self.phone.strip():
                raise ValueError("Phone cannot be empty if provided")
            
            if len(self.phone) > 50:
                raise ValueError("Phone number cannot exceed 50 characters")
        
        # GST number validation
        if self.gst_no:
            if not self.gst_no.strip():
                raise ValueError("GST number cannot be empty if provided")
            
            if len(self.gst_no) > 50:
                raise ValueError("GST number cannot exceed 50 characters")
            
            # Uppercase GST number
            self.gst_no = self.gst_no.upper().strip()
        
        # Registration number validation
        if self.registration_number:
            if not self.registration_number.strip():
                raise ValueError("Registration number cannot be empty if provided")
            
            if len(self.registration_number) > 100:
                raise ValueError("Registration number cannot exceed 100 characters")
            
            # Uppercase registration number
            self.registration_number = self.registration_number.upper().strip()
    
    def update_info(
        self,
        company_name: Optional[str] = None,
        address: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        gst_no: Optional[str] = None,
        registration_number: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """
        Update company information.
        
        Args:
            company_name: New company name
            address: New address
            email: New email
            phone: New phone number
            gst_no: New GST number
            registration_number: New registration number
            updated_by: User making the update
        """
        if company_name is not None:
            if not company_name or not company_name.strip():
                raise ValueError("Company name cannot be empty")
            if len(company_name) > 255:
                raise ValueError("Company name cannot exceed 255 characters")
            self.company_name = company_name.strip()
        
        if address is not None:
            self.address = address.strip() if address else None
        
        if email is not None:
            if email and not email.strip():
                raise ValueError("Email cannot be empty if provided")
            if email and len(email) > 255:
                raise ValueError("Email cannot exceed 255 characters")
            if email and ("@" not in email or "." not in email.split("@")[-1]):
                raise ValueError("Invalid email format")
            self.email = email.strip() if email else None
        
        if phone is not None:
            if phone and not phone.strip():
                raise ValueError("Phone cannot be empty if provided")
            if phone and len(phone) > 50:
                raise ValueError("Phone number cannot exceed 50 characters")
            self.phone = phone.strip() if phone else None
        
        if gst_no is not None:
            if gst_no and not gst_no.strip():
                raise ValueError("GST number cannot be empty if provided")
            if gst_no and len(gst_no) > 50:
                raise ValueError("GST number cannot exceed 50 characters")
            self.gst_no = gst_no.upper().strip() if gst_no else None
        
        if registration_number is not None:
            if registration_number and not registration_number.strip():
                raise ValueError("Registration number cannot be empty if provided")
            if registration_number and len(registration_number) > 100:
                raise ValueError("Registration number cannot exceed 100 characters")
            self.registration_number = registration_number.upper().strip() if registration_number else None
        
        self.updated_by = updated_by
    
    @property
    def display_name(self) -> str:
        """Get display name for the company."""
        return self.company_name
    
    def __str__(self) -> str:
        """String representation of company."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of company."""
        return f"<Company(id={self.id}, name='{self.company_name}', active={self.is_active})>"