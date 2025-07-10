"""
Business Rules and Validation Logic for Rental Management System.

This module contains comprehensive business rules that ensure data integrity
and enforce business constraints across all domains.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import re
from uuid import UUID

from app.core.errors import ValidationError, BusinessException


class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []
    
    def add_error(self, field: str, message: str, code: str = None):
        """Add validation error."""
        self.is_valid = False
        self.errors.append({
            "field": field,
            "message": message,
            "code": code,
            "severity": ValidationSeverity.ERROR
        })
    
    def add_warning(self, field: str, message: str, code: str = None):
        """Add validation warning."""
        self.warnings.append({
            "field": field,
            "message": message,
            "code": code,
            "severity": ValidationSeverity.WARNING
        })
    
    def add_info(self, field: str, message: str, code: str = None):
        """Add validation info."""
        self.info.append({
            "field": field,
            "message": message,
            "code": code,
            "severity": ValidationSeverity.INFO
        })
    
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0
    
    def get_all_issues(self) -> List[Dict[str, Any]]:
        """Get all validation issues."""
        return self.errors + self.warnings + self.info
    
    def raise_if_errors(self):
        """Raise ValidationError if there are validation errors."""
        if self.has_errors():
            raise ValidationError(
                "Validation failed",
                {"validation_errors": self.errors}
            )


class BusinessRuleValidator:
    """Base class for business rule validation."""
    
    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """Validate email address format."""
        result = ValidationResult()
        
        if not email:
            result.add_error("email", "Email is required")
            return result
        
        # Basic email format validation
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        if not email_pattern.match(email):
            result.add_error("email", "Invalid email format")
        
        if len(email) > 255:
            result.add_error("email", "Email address too long (max 255 characters)")
        
        # Check for common disposable email domains
        disposable_domains = [
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com'
        ]
        domain = email.split('@')[1] if '@' in email else ''
        if domain.lower() in disposable_domains:
            result.add_warning("email", "Disposable email address detected")
        
        return result
    
    @staticmethod
    def validate_phone_number(phone: str, country_code: str = "US") -> ValidationResult:
        """Validate phone number format."""
        result = ValidationResult()
        
        if not phone:
            result.add_error("phone", "Phone number is required")
            return result
        
        # Remove all non-digit characters for validation
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # US phone number validation
        if country_code == "US":
            if len(digits_only) == 10:
                # Format: (xxx) xxx-xxxx
                pass
            elif len(digits_only) == 11 and digits_only[0] == '1':
                # Format: +1 (xxx) xxx-xxxx
                pass
            else:
                result.add_error("phone", "Invalid US phone number format")
        
        # International phone number (basic validation)
        elif len(digits_only) < 7 or len(digits_only) > 15:
            result.add_error("phone", "Invalid phone number length")
        
        return result
    
    @staticmethod
    def validate_currency_amount(amount: Union[Decimal, float], 
                                min_amount: Decimal = None,
                                max_amount: Decimal = None) -> ValidationResult:
        """Validate currency amount."""
        result = ValidationResult()
        
        if amount is None:
            result.add_error("amount", "Amount is required")
            return result
        
        # Convert to Decimal for precise handling
        if isinstance(amount, float):
            amount = Decimal(str(amount))
        
        if amount < 0:
            result.add_error("amount", "Amount cannot be negative")
        
        if min_amount is not None and amount < min_amount:
            result.add_error("amount", f"Amount must be at least {min_amount}")
        
        if max_amount is not None and amount > max_amount:
            result.add_error("amount", f"Amount cannot exceed {max_amount}")
        
        # Check decimal places (max 2 for currency)
        if amount.as_tuple().exponent < -2:
            result.add_error("amount", "Amount cannot have more than 2 decimal places")
        
        return result
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date, 
                           allow_same_day: bool = True) -> ValidationResult:
        """Validate date range."""
        result = ValidationResult()
        
        if not start_date:
            result.add_error("start_date", "Start date is required")
        
        if not end_date:
            result.add_error("end_date", "End date is required")
        
        if start_date and end_date:
            if start_date > end_date:
                result.add_error("date_range", "Start date cannot be after end date")
            elif start_date == end_date and not allow_same_day:
                result.add_error("date_range", "Start date and end date cannot be the same")
            
            # Check for reasonable date ranges
            max_days = 365 * 2  # 2 years
            if (end_date - start_date).days > max_days:
                result.add_warning("date_range", f"Date range exceeds {max_days} days")
        
        return result
    
    @staticmethod
    def validate_business_hours(time_slot: dict) -> ValidationResult:
        """Validate business hours and time slots."""
        result = ValidationResult()
        
        start_time = time_slot.get('start_time')
        end_time = time_slot.get('end_time')
        
        if not start_time:
            result.add_error("start_time", "Start time is required")
        
        if not end_time:
            result.add_error("end_time", "End time is required")
        
        if start_time and end_time:
            if start_time >= end_time:
                result.add_error("time_range", "Start time must be before end time")
            
            # Check for reasonable business hours
            business_start = "06:00"
            business_end = "23:00"
            
            if start_time < business_start:
                result.add_warning("start_time", "Start time is before typical business hours")
            
            if end_time > business_end:
                result.add_warning("end_time", "End time is after typical business hours")
        
        return result


class CustomerValidator(BusinessRuleValidator):
    """Customer-specific business rules and validation."""
    
    @staticmethod
    def validate_customer_data(customer_data: dict) -> ValidationResult:
        """Validate customer data comprehensively."""
        result = ValidationResult()
        
        # Required fields validation
        required_fields = ["customer_type", "email"]
        for field in required_fields:
            if not customer_data.get(field):
                result.add_error(field, f"{field.replace('_', ' ').title()} is required")
        
        # Customer type specific validation
        customer_type = customer_data.get("customer_type")
        
        if customer_type == "INDIVIDUAL":
            if not customer_data.get("first_name"):
                result.add_error("first_name", "First name is required for individual customers")
            if not customer_data.get("last_name"):
                result.add_error("last_name", "Last name is required for individual customers")
            
            # Validate date of birth for individuals
            dob = customer_data.get("date_of_birth")
            if dob:
                dob_result = CustomerValidator.validate_date_of_birth(dob)
                result.errors.extend(dob_result.errors)
                result.warnings.extend(dob_result.warnings)
        
        elif customer_type == "BUSINESS":
            if not customer_data.get("business_name"):
                result.add_error("business_name", "Business name is required for business customers")
            
            # Validate tax ID for businesses
            tax_id = customer_data.get("tax_id")
            if tax_id:
                tax_result = CustomerValidator.validate_tax_id(tax_id)
                result.errors.extend(tax_result.errors)
        
        # Email validation
        email = customer_data.get("email")
        if email:
            email_result = BusinessRuleValidator.validate_email(email)
            result.errors.extend(email_result.errors)
            result.warnings.extend(email_result.warnings)
        
        # Phone validation
        phone = customer_data.get("phone_number")
        if phone:
            phone_result = BusinessRuleValidator.validate_phone_number(phone)
            result.errors.extend(phone_result.errors)
        
        # Credit limit validation
        credit_limit = customer_data.get("credit_limit")
        if credit_limit is not None:
            credit_result = CustomerValidator.validate_credit_limit(credit_limit)
            result.errors.extend(credit_result.errors)
            result.warnings.extend(credit_result.warnings)
        
        return result
    
    @staticmethod
    def validate_date_of_birth(dob: Union[date, str]) -> ValidationResult:
        """Validate date of birth."""
        result = ValidationResult()
        
        if isinstance(dob, str):
            try:
                dob = datetime.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                result.add_error("date_of_birth", "Invalid date format (use YYYY-MM-DD)")
                return result
        
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if dob > today:
            result.add_error("date_of_birth", "Date of birth cannot be in the future")
        elif age < 18:
            result.add_warning("date_of_birth", "Customer is under 18 years old")
        elif age > 120:
            result.add_error("date_of_birth", "Invalid date of birth (age > 120)")
        
        return result
    
    @staticmethod
    def validate_tax_id(tax_id: str) -> ValidationResult:
        """Validate tax identification number."""
        result = ValidationResult()
        
        # Basic format validation (can be extended for different countries)
        if len(tax_id) < 9:
            result.add_error("tax_id", "Tax ID too short")
        elif len(tax_id) > 20:
            result.add_error("tax_id", "Tax ID too long")
        
        # Check for valid characters (alphanumeric and hyphens)
        if not re.match(r'^[A-Za-z0-9\-]+$', tax_id):
            result.add_error("tax_id", "Tax ID contains invalid characters")
        
        return result
    
    @staticmethod
    def validate_credit_limit(credit_limit: Union[Decimal, float]) -> ValidationResult:
        """Validate customer credit limit."""
        result = ValidationResult()
        
        # Convert to Decimal
        if isinstance(credit_limit, float):
            credit_limit = Decimal(str(credit_limit))
        
        min_limit = Decimal('0')
        max_limit = Decimal('1000000')  # $1M max
        
        amount_result = BusinessRuleValidator.validate_currency_amount(
            credit_limit, min_limit, max_limit
        )
        result.errors.extend(amount_result.errors)
        
        # Warning for high credit limits
        if credit_limit > Decimal('100000'):
            result.add_warning("credit_limit", "High credit limit requires approval")
        
        return result


class InventoryValidator(BusinessRuleValidator):
    """Inventory-specific business rules and validation."""
    
    @staticmethod
    def validate_item_data(item_data: dict) -> ValidationResult:
        """Validate inventory item data."""
        result = ValidationResult()
        
        # Required fields
        required_fields = ["name", "sku", "rental_price_per_day"]
        for field in required_fields:
            if not item_data.get(field):
                result.add_error(field, f"{field.replace('_', ' ').title()} is required")
        
        # SKU validation
        sku = item_data.get("sku")
        if sku:
            sku_result = InventoryValidator.validate_sku(sku)
            result.errors.extend(sku_result.errors)
        
        # Price validation
        rental_price = item_data.get("rental_price_per_day")
        if rental_price is not None:
            price_result = BusinessRuleValidator.validate_currency_amount(
                rental_price, Decimal('0.01'), Decimal('10000')
            )
            result.errors.extend(price_result.errors)
        
        purchase_price = item_data.get("purchase_price")
        if purchase_price is not None:
            purchase_result = BusinessRuleValidator.validate_currency_amount(
                purchase_price, Decimal('0'), Decimal('1000000')
            )
            result.errors.extend(purchase_result.errors)
            
            # Business rule: rental price should be reasonable % of purchase price
            if rental_price and purchase_price:
                daily_rate_percentage = (rental_price / purchase_price) * 100
                if daily_rate_percentage > 10:  # More than 10% per day
                    result.add_warning("rental_price", "Rental price seems high relative to purchase price")
                elif daily_rate_percentage < 0.1:  # Less than 0.1% per day
                    result.add_warning("rental_price", "Rental price seems low relative to purchase price")
        
        # Stock validation
        stock_quantity = item_data.get("stock_quantity")
        if stock_quantity is not None:
            stock_result = InventoryValidator.validate_stock_quantity(stock_quantity)
            result.errors.extend(stock_result.errors)
            result.warnings.extend(stock_result.warnings)
        
        return result
    
    @staticmethod
    def validate_sku(sku: str) -> ValidationResult:
        """Validate SKU format."""
        result = ValidationResult()
        
        if len(sku) < 3:
            result.add_error("sku", "SKU too short (minimum 3 characters)")
        elif len(sku) > 50:
            result.add_error("sku", "SKU too long (maximum 50 characters)")
        
        # SKU should be alphanumeric with hyphens/underscores
        if not re.match(r'^[A-Za-z0-9\-_]+$', sku):
            result.add_error("sku", "SKU contains invalid characters")
        
        return result
    
    @staticmethod
    def validate_stock_quantity(quantity: int) -> ValidationResult:
        """Validate stock quantity."""
        result = ValidationResult()
        
        if quantity < 0:
            result.add_error("stock_quantity", "Stock quantity cannot be negative")
        elif quantity == 0:
            result.add_warning("stock_quantity", "Item is out of stock")
        elif quantity > 10000:
            result.add_warning("stock_quantity", "Very large stock quantity")
        
        return result


class RentalValidator(BusinessRuleValidator):
    """Rental-specific business rules and validation."""
    
    @staticmethod
    def validate_rental_data(rental_data: dict) -> ValidationResult:
        """Validate rental booking data."""
        result = ValidationResult()
        
        # Required fields
        required_fields = ["customer_id", "item_id", "start_date", "end_date"]
        for field in required_fields:
            if not rental_data.get(field):
                result.add_error(field, f"{field.replace('_', ' ').title()} is required")
        
        # Date validation
        start_date = rental_data.get("start_date")
        end_date = rental_data.get("end_date")
        
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            date_result = BusinessRuleValidator.validate_date_range(start_date, end_date)
            result.errors.extend(date_result.errors)
            result.warnings.extend(date_result.warnings)
            
            # Business rules for rental dates
            today = date.today()
            if start_date < today:
                result.add_error("start_date", "Rental start date cannot be in the past")
            
            # Maximum rental period
            max_rental_days = 90
            if (end_date - start_date).days > max_rental_days:
                result.add_error("date_range", f"Rental period cannot exceed {max_rental_days} days")
            
            # Advance booking limit
            max_advance_days = 365
            if (start_date - today).days > max_advance_days:
                result.add_warning("start_date", f"Booking more than {max_advance_days} days in advance")
        
        # Quantity validation
        quantity = rental_data.get("quantity", 1)
        if quantity <= 0:
            result.add_error("quantity", "Rental quantity must be at least 1")
        elif quantity > 10:
            result.add_warning("quantity", "Large quantity rental requires verification")
        
        return result
    
    @staticmethod
    def validate_rental_return(return_data: dict) -> ValidationResult:
        """Validate rental return data."""
        result = ValidationResult()
        
        # Return date validation
        return_date = return_data.get("return_date")
        if return_date:
            if isinstance(return_date, str):
                return_date = datetime.strptime(return_date, "%Y-%m-%d").date()
            
            today = date.today()
            if return_date > today:
                result.add_error("return_date", "Return date cannot be in the future")
        
        # Condition validation
        condition = return_data.get("condition")
        if condition:
            valid_conditions = ["EXCELLENT", "GOOD", "FAIR", "POOR", "DAMAGED"]
            if condition not in valid_conditions:
                result.add_error("condition", f"Invalid condition. Must be one of: {valid_conditions}")
        
        # Damage assessment
        damage_cost = return_data.get("damage_cost")
        if damage_cost is not None:
            damage_result = BusinessRuleValidator.validate_currency_amount(
                damage_cost, Decimal('0'), Decimal('100000')
            )
            result.errors.extend(damage_result.errors)
            
            if damage_cost > 0 and not return_data.get("damage_description"):
                result.add_error("damage_description", "Damage description required when damage cost > 0")
        
        return result


class TransactionValidator(BusinessRuleValidator):
    """Transaction-specific business rules and validation."""
    
    @staticmethod
    def validate_transaction_data(transaction_data: dict) -> ValidationResult:
        """Validate transaction data."""
        result = ValidationResult()
        
        # Required fields
        required_fields = ["customer_id", "transaction_type", "total_amount"]
        for field in required_fields:
            if not transaction_data.get(field):
                result.add_error(field, f"{field.replace('_', ' ').title()} is required")
        
        # Transaction type validation
        transaction_type = transaction_data.get("transaction_type")
        valid_types = ["RENTAL", "SALE", "DEPOSIT", "REFUND", "ADJUSTMENT"]
        if transaction_type and transaction_type not in valid_types:
            result.add_error("transaction_type", f"Invalid transaction type. Must be one of: {valid_types}")
        
        # Amount validation
        total_amount = transaction_data.get("total_amount")
        if total_amount is not None:
            amount_result = BusinessRuleValidator.validate_currency_amount(
                total_amount, Decimal('0'), Decimal('1000000')
            )
            result.errors.extend(amount_result.errors)
        
        # Payment validation
        payment_method = transaction_data.get("payment_method")
        if payment_method:
            payment_result = TransactionValidator.validate_payment_method(payment_method)
            result.errors.extend(payment_result.errors)
        
        return result
    
    @staticmethod
    def validate_payment_method(payment_method: str) -> ValidationResult:
        """Validate payment method."""
        result = ValidationResult()
        
        valid_methods = ["CASH", "CREDIT_CARD", "DEBIT_CARD", "BANK_TRANSFER", "CHECK", "DIGITAL_WALLET"]
        if payment_method not in valid_methods:
            result.add_error("payment_method", f"Invalid payment method. Must be one of: {valid_methods}")
        
        return result


def validate_comprehensive_data(data: dict, domain: str) -> ValidationResult:
    """
    Comprehensive validation for different domains.
    
    Args:
        data: Data to validate
        domain: Domain type ('customer', 'inventory', 'rental', 'transaction')
    
    Returns:
        ValidationResult with all validation issues
    """
    validators = {
        'customer': CustomerValidator.validate_customer_data,
        'inventory': InventoryValidator.validate_item_data,
        'rental': RentalValidator.validate_rental_data,
        'transaction': TransactionValidator.validate_transaction_data,
    }
    
    validator = validators.get(domain)
    if not validator:
        result = ValidationResult()
        result.add_error("domain", f"Unknown validation domain: {domain}")
        return result
    
    return validator(data)


def apply_business_rules(data: dict, domain: str, operation: str = "create") -> ValidationResult:
    """
    Apply business rules for specific operations.
    
    Args:
        data: Data to validate
        domain: Domain type
        operation: Operation type ('create', 'update', 'delete')
    
    Returns:
        ValidationResult with business rule validations
    """
    result = validate_comprehensive_data(data, domain)
    
    # Additional business rules based on operation
    if operation == "update":
        # For updates, some fields might be optional
        pass
    elif operation == "delete":
        # For deletes, check if deletion is allowed
        if domain == "customer" and data.get("has_active_rentals"):
            result.add_error("delete", "Cannot delete customer with active rentals")
        elif domain == "inventory" and data.get("is_rented"):
            result.add_error("delete", "Cannot delete item that is currently rented")
    
    return result