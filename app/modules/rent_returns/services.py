"""
Rent Return Services

Business logic for rent return operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transaction_base.services import BaseTransactionService
from app.modules.transaction_base.models import TransactionType, TransactionStatus
from app.modules.rent_returns.repository import RentReturnsRepository, RentReturnLineRepository, RentReturnInspectionRepository
from app.modules.rent_returns.schemas import (
    RentReturnCreate,
    RentReturnUpdate,
    RentReturnResponse,
    RentReturnListResponse,
    RentReturnReportResponse,
    RentReturnInspectionRequest,
    RentReturnInspectionResponse,
    DepositRefundRequest,
    DamageAssessmentRequest,
)


class RentReturnsService(BaseTransactionService):
    """Service for rent return operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.rent_returns_repository = RentReturnsRepository(session)
        self.rent_return_line_repository = RentReturnLineRepository(session)
        self.rent_return_inspection_repository = RentReturnInspectionRepository(session)
    
    async def create_rent_return(self, return_data: RentReturnCreate) -> RentReturnResponse:
        """Create a new rent return."""
        # Generate return number if not provided
        if not return_data.return_number:
            return_number = await self.rent_returns_repository.generate_return_number()
        else:
            return_number = return_data.return_number
        
        # Generate transaction number
        transaction_number = self.generate_transaction_number(TransactionType.RETURN)
        
        # Calculate totals
        totals = self.calculate_transaction_totals(return_data.transaction_lines)
        
        # Prepare return data
        return_dict = return_data.model_dump(exclude={'transaction_lines'})
        return_dict.update({
            'transaction_number': transaction_number,
            'return_number': return_number,
            'transaction_type': TransactionType.RETURN,
            **totals
        })
        
        # Create return
        rent_return = await self.rent_returns_repository.create_rent_return(return_dict)
        
        # Create return lines
        for line_data in return_data.transaction_lines:
            line_dict = line_data.model_dump()
            line_dict.update({
                'transaction_id': rent_return.id,
                'line_total': line_data.repair_cost + line_data.cleaning_fee
            })
            await self.rent_return_line_repository.create_rent_return_line(line_dict)
        
        # Refresh and return
        rent_return = await self.rent_returns_repository.get_rent_return_by_id(rent_return.id)
        return RentReturnResponse.model_validate(rent_return)
    
    async def get_rent_return(self, return_id: UUID) -> Optional[RentReturnResponse]:
        """Get rent return by ID."""
        rent_return = await self.rent_returns_repository.get_rent_return_by_id(return_id)
        if not rent_return:
            return None
        return RentReturnResponse.model_validate(rent_return)
    
    async def get_rent_returns(
        self,
        page: int = 1,
        page_size: int = 100,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> RentReturnListResponse:
        """Get rent returns with pagination and filters."""
        offset = (page - 1) * page_size
        
        rent_returns = await self.rent_returns_repository.get_by_type(
            transaction_type=TransactionType.RETURN,
            limit=page_size,
            offset=offset,
            customer_id=customer_id,
            location_id=location_id,
            date_from=date_from,
            date_to=date_to
        )
        
        total = await self.rent_returns_repository.count_by_type(
            transaction_type=TransactionType.RETURN,
            customer_id=customer_id,
            location_id=location_id,
            date_from=date_from,
            date_to=date_to
        )
        
        return_responses = [RentReturnResponse.model_validate(ret) for ret in rent_returns]
        total_pages = (total + page_size - 1) // page_size
        
        return RentReturnListResponse(
            rent_returns=return_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def process_inspection(
        self,
        return_id: UUID,
        inspection_request: RentReturnInspectionRequest
    ) -> RentReturnInspectionResponse:
        """Process return inspection."""
        inspection_data = inspection_request.model_dump()
        inspection_data.update({
            'return_id': return_id,
            'id': str(UUID.uuid4()),
            'total_damage_value': sum(
                item.get('repair_cost', 0) for item in inspection_request.damage_items
            )
        })
        
        inspection = await self.rent_return_inspection_repository.create_inspection(inspection_data)
        
        # Update return with inspection details
        rent_return = await self.rent_returns_repository.get_rent_return_by_id(return_id)
        if rent_return:
            rent_return.inspection_completed = True
            rent_return.inspection_date = date.today()
            rent_return.inspected_by = inspection_request.inspector_id
            await self.session.commit()
        
        return RentReturnInspectionResponse.model_validate(inspection)
    
    async def process_deposit_refund(
        self,
        return_id: UUID,
        refund_request: DepositRefundRequest
    ) -> RentReturnResponse:
        """Process deposit refund."""
        rent_return = await self.rent_returns_repository.get_rent_return_by_id(return_id)
        if not rent_return:
            return None
        
        rent_return.deposit_refund_processed = True
        rent_return.deposit_refund_date = refund_request.refund_date
        
        await self.session.commit()
        
        return RentReturnResponse.model_validate(rent_return)
    
    async def get_pending_inspections(self, limit: int = 100) -> List[RentReturnResponse]:
        """Get returns with pending inspections."""
        returns = await self.rent_returns_repository.get_pending_inspections(limit=limit)
        return [RentReturnResponse.model_validate(ret) for ret in returns]
    
    async def get_damaged_returns(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100
    ) -> List[RentReturnResponse]:
        """Get returns with damage."""
        returns = await self.rent_returns_repository.get_damaged_returns(
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        return [RentReturnResponse.model_validate(ret) for ret in returns]