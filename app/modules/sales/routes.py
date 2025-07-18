"""
Sales Routes

API endpoints for sales operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.transactions.base.models import TransactionStatus
from app.modules.sales.services import SalesService
from app.modules.sales.schemas import (
    SaleCreate,
    SaleUpdate,
    SaleResponse,
    SaleListResponse,
    SalesReportResponse,
    SaleInvoiceResponse,
    ShippingUpdateRequest,
    BackorderRequest,
    SalesReportRequest,
)

router = APIRouter(prefix="/sales", tags=["sales"])


def get_sales_service(session: AsyncSession = Depends(get_session)) -> SalesService:
    """Get sales service instance."""
    return SalesService(session)


@router.post("/", response_model=SaleResponse)
async def create_sale(
    sale_data: SaleCreate,
    service: SalesService = Depends(get_sales_service)
):
    """Create a new sale."""
    try:
        return await service.create_sale(sale_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=SaleListResponse)
async def get_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    customer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    sales_person_id: Optional[UUID] = Query(None),
    status: Optional[TransactionStatus] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: SalesService = Depends(get_sales_service)
):
    """Get sales with pagination and filters."""
    return await service.get_sales(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        location_id=location_id,
        sales_person_id=sales_person_id,
        status=status,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: UUID,
    service: SalesService = Depends(get_sales_service)
):
    """Get sale by ID."""
    sale = await service.get_sale(sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.put("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: UUID,
    update_data: SaleUpdate,
    service: SalesService = Depends(get_sales_service)
):
    """Update sale."""
    sale = await service.update_sale(sale_id, update_data)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.delete("/{sale_id}")
async def delete_sale(
    sale_id: UUID,
    service: SalesService = Depends(get_sales_service)
):
    """Delete sale."""
    try:
        success = await service.delete_sale(sale_id)
        if not success:
            raise HTTPException(status_code=404, detail="Sale not found")
        return {"message": "Sale deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{sale_id}/complete", response_model=SaleResponse)
async def complete_sale(
    sale_id: UUID,
    service: SalesService = Depends(get_sales_service)
):
    """Mark sale as completed."""
    sale = await service.complete_sale(sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.post("/{sale_id}/cancel", response_model=SaleResponse)
async def cancel_sale(
    sale_id: UUID,
    reason: Optional[str] = Query(None),
    service: SalesService = Depends(get_sales_service)
):
    """Cancel sale."""
    sale = await service.cancel_sale(sale_id, reason)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.get("/invoice/{invoice_number}", response_model=SaleResponse)
async def get_sale_by_invoice(
    invoice_number: str,
    service: SalesService = Depends(get_sales_service)
):
    """Get sale by invoice number."""
    sale = await service.get_sale_by_invoice_number(invoice_number)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.get("/{sale_id}/invoice", response_model=SaleInvoiceResponse)
async def get_invoice(
    sale_id: UUID,
    service: SalesService = Depends(get_sales_service)
):
    """Get invoice information for a sale."""
    invoice = await service.get_invoice(sale_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Sale not found")
    return invoice


@router.post("/{sale_id}/shipping", response_model=SaleResponse)
async def update_shipping(
    sale_id: UUID,
    shipping_update: ShippingUpdateRequest,
    service: SalesService = Depends(get_sales_service)
):
    """Update shipping information."""
    sale = await service.update_shipping(sale_id, shipping_update)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.post("/{sale_id}/backorder", response_model=SaleResponse)
async def create_backorder(
    sale_id: UUID,
    backorder_request: BackorderRequest,
    service: SalesService = Depends(get_sales_service)
):
    """Create backorder for a line item."""
    sale = await service.create_backorder(sale_id, backorder_request)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.get("/customer/{customer_id}", response_model=SaleListResponse)
async def get_customer_sales(
    customer_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    status: Optional[TransactionStatus] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: SalesService = Depends(get_sales_service)
):
    """Get sales for a specific customer."""
    return await service.get_customer_sales(
        customer_id=customer_id,
        page=page,
        page_size=page_size,
        status=status,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/pending/shipments", response_model=List[SaleResponse])
async def get_pending_shipments(
    location_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: SalesService = Depends(get_sales_service)
):
    """Get sales with pending shipments."""
    return await service.get_pending_shipments(
        location_id=location_id,
        limit=limit
    )


@router.get("/backorders/list", response_model=List[SaleResponse])
async def get_backorders(
    customer_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: SalesService = Depends(get_sales_service)
):
    """Get sales with backorders."""
    return await service.get_backorders(
        customer_id=customer_id,
        limit=limit
    )


@router.post("/reports/sales", response_model=SalesReportResponse)
async def generate_sales_report(
    report_request: SalesReportRequest,
    service: SalesService = Depends(get_sales_service)
):
    """Generate sales report."""
    return await service.get_sales_report(
        date_from=report_request.date_from,
        date_to=report_request.date_to,
        customer_id=report_request.customer_id,
        location_id=report_request.location_id,
        sales_person_id=report_request.sales_person_id
    )


@router.get("/reports/summary")
async def get_sales_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    customer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    sales_person_id: Optional[UUID] = Query(None),
    service: SalesService = Depends(get_sales_service)
):
    """Get sales summary statistics."""
    return await service.get_sales_report(
        date_from=date_from,
        date_to=date_to,
        customer_id=customer_id,
        location_id=location_id,
        sales_person_id=sales_person_id
    )