from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import CustomerRepository
from .models import Customer, CustomerType, CustomerStatus, BlacklistStatus, CreditRating
from .schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerStatusUpdate,
    CustomerBlacklistUpdate, CustomerCreditUpdate, CustomerSearchRequest,
    CustomerStatsResponse, CustomerAddressCreate, CustomerAddressResponse,
    CustomerContactCreate, CustomerContactResponse, CustomerDetailResponse
)
from app.core.errors import ValidationError, NotFoundError, ConflictError
from app.shared.pagination import Page


class CustomerService:
    """Customer service."""
    
    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.repository = CustomerRepository(session)
    
    async def create_customer(self, customer_data: CustomerCreate) -> CustomerResponse:
        """Create a new customer."""
        # Check if customer code already exists
        existing_customer = await self.repository.get_by_code(customer_data.customer_code)
        if existing_customer:
            raise ConflictError(f"Customer with code '{customer_data.customer_code}' already exists")
        
        # Create customer data
        customer_dict = {
            "customer_code": customer_data.customer_code,
            "customer_type": customer_data.customer_type,
            "business_name": customer_data.business_name,
            "first_name": customer_data.first_name,
            "last_name": customer_data.last_name,
            "email": customer_data.email,
            "phone": customer_data.phone,
            "mobile": customer_data.mobile,
            "address_line1": customer_data.address_line1,
            "address_line2": customer_data.address_line2,
            "city": customer_data.city,
            "state": customer_data.state,
            "postal_code": customer_data.postal_code,
            "country": customer_data.country,
            "tax_number": customer_data.tax_number,
            "credit_limit": customer_data.credit_limit,
            "payment_terms": customer_data.payment_terms,
            "notes": customer_data.notes,
            "status": CustomerStatus.ACTIVE,
            "blacklist_status": BlacklistStatus.CLEAR,
            "credit_rating": CreditRating.GOOD,
            "total_rentals": 0,
            "total_spent": 0.0,
            "is_active": True
        }
        
        # Create customer
        customer = await self.repository.create(customer_dict)
        
        return CustomerResponse.model_validate(customer)
    
    async def get_customer(self, customer_id: UUID) -> Optional[CustomerResponse]:
        """Get customer by ID."""
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            return None
        
        return CustomerResponse.model_validate(customer)
    
    async def get_customer_by_code(self, customer_code: str) -> Optional[CustomerResponse]:
        """Get customer by code."""
        customer = await self.repository.get_by_code(customer_code)
        if not customer:
            return None
        
        return CustomerResponse.model_validate(customer)
    
    async def update_customer(self, customer_id: UUID, update_data: CustomerUpdate) -> CustomerResponse:
        """Update customer information."""
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        
        # Update customer
        update_dict = {}
        if update_data.customer_type is not None:
            update_dict["customer_type"] = update_data.customer_type
        if update_data.business_name is not None:
            update_dict["business_name"] = update_data.business_name
        if update_data.first_name is not None:
            update_dict["first_name"] = update_data.first_name
        if update_data.last_name is not None:
            update_dict["last_name"] = update_data.last_name
        if update_data.email is not None:
            update_dict["email"] = update_data.email
        if update_data.phone is not None:
            update_dict["phone"] = update_data.phone
        if update_data.mobile is not None:
            update_dict["mobile"] = update_data.mobile
        if update_data.address_line1 is not None:
            update_dict["address_line1"] = update_data.address_line1
        if update_data.address_line2 is not None:
            update_dict["address_line2"] = update_data.address_line2
        if update_data.city is not None:
            update_dict["city"] = update_data.city
        if update_data.state is not None:
            update_dict["state"] = update_data.state
        if update_data.postal_code is not None:
            update_dict["postal_code"] = update_data.postal_code
        if update_data.country is not None:
            update_dict["country"] = update_data.country
        if update_data.tax_number is not None:
            update_dict["tax_number"] = update_data.tax_number
        if update_data.credit_limit is not None:
            update_dict["credit_limit"] = update_data.credit_limit
        if update_data.payment_terms is not None:
            update_dict["payment_terms"] = update_data.payment_terms
        if update_data.notes is not None:
            update_dict["notes"] = update_data.notes
        
        updated_customer = await self.repository.update(customer_id, update_dict)
        
        return CustomerResponse.model_validate(updated_customer)
    
    async def delete_customer(self, customer_id: UUID) -> bool:
        """Delete customer."""
        return await self.repository.delete(customer_id)
    
    async def list_customers(
        self,
        skip: int = 0,
        limit: int = 100,
        customer_type: Optional[CustomerType] = None,
        status: Optional[CustomerStatus] = None,
        blacklist_status: Optional[BlacklistStatus] = None,
        active_only: bool = True
    ) -> List[CustomerResponse]:
        """List customers with filtering."""
        customers = await self.repository.get_all(
            skip=skip,
            limit=limit,
            customer_type=customer_type,
            customer_status=status,
            blacklist_status=blacklist_status,
            active_only=active_only
        )
        
        return [CustomerResponse.model_validate(customer) for customer in customers]
    
    async def search_customers(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[CustomerResponse]:
        """Search customers."""
        customers = await self.repository.search(
            search_term=search_term,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [CustomerResponse.model_validate(customer) for customer in customers]
    
    async def count_customers(
        self,
        customer_type: Optional[CustomerType] = None,
        status: Optional[CustomerStatus] = None,
        blacklist_status: Optional[BlacklistStatus] = None,
        active_only: bool = True
    ) -> int:
        """Count customers with filtering."""
        return await self.repository.count_all(
            customer_type=customer_type,
            customer_status=status,
            blacklist_status=blacklist_status,
            active_only=active_only
        )
    
    async def update_customer_status(self, customer_id: UUID, status_update: CustomerStatusUpdate) -> CustomerResponse:
        """Update customer status."""
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        
        update_dict = {
            "status": status_update.status,
            "notes": status_update.notes
        }
        
        updated_customer = await self.repository.update(customer_id, update_dict)
        return CustomerResponse.model_validate(updated_customer)
    
    async def update_blacklist_status(self, customer_id: UUID, blacklist_update: CustomerBlacklistUpdate) -> CustomerResponse:
        """Update customer blacklist status."""
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        
        update_dict = {
            "blacklist_status": blacklist_update.blacklist_status,
            "blacklist_reason": blacklist_update.blacklist_reason,
            "notes": blacklist_update.notes
        }
        
        updated_customer = await self.repository.update(customer_id, update_dict)
        return CustomerResponse.model_validate(updated_customer)
    
    async def update_credit_info(self, customer_id: UUID, credit_update: CustomerCreditUpdate) -> CustomerResponse:
        """Update customer credit information."""
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        
        update_dict = {}
        if credit_update.credit_limit is not None:
            update_dict["credit_limit"] = credit_update.credit_limit
        if credit_update.credit_rating is not None:
            update_dict["credit_rating"] = credit_update.credit_rating
        if credit_update.payment_terms is not None:
            update_dict["payment_terms"] = credit_update.payment_terms
        if credit_update.notes is not None:
            update_dict["notes"] = credit_update.notes
        
        updated_customer = await self.repository.update(customer_id, update_dict)
        return CustomerResponse.model_validate(updated_customer)
    
    async def get_customer_statistics(self) -> Dict[str, Any]:
        """Get customer statistics."""
        # Get basic counts
        total_customers = await self.repository.count_all(active_only=False)
        active_customers = await self.repository.count_all(active_only=True)
        individual_customers = await self.repository.count_all(
            customer_type=CustomerType.INDIVIDUAL, active_only=True
        )
        business_customers = await self.repository.count_all(
            customer_type=CustomerType.BUSINESS, active_only=True
        )
        
        # Get recent customers
        recent_customers = await self.repository.get_all(skip=0, limit=10, active_only=True)
        
        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "inactive_customers": total_customers - active_customers,
            "individual_customers": individual_customers,
            "business_customers": business_customers,
            "blacklisted_customers": 0,  # Will be implemented when blacklist filtering is available
            "customers_by_credit_rating": {},
            "customers_by_state": {},
            "top_customers_by_rentals": [],
            "top_customers_by_spending": [],
            "recent_customers": [CustomerResponse.model_validate(customer) for customer in recent_customers]
        }