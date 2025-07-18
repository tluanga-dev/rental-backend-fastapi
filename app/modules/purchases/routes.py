"""
Purchase Routes

API endpoints for purchase operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.transaction_base.models import TransactionStatus
from app.modules.purchases.services import PurchasesService
from app.modules.purchases.schemas import (
    PurchaseCreate,
    PurchaseUpdate,
    PurchaseResponse,
    PurchaseListResponse,
    PurchaseReportResponse,
    PurchaseOrderResponse,
    ReceivingUpdateRequest,
    ApprovalRequest,
    InspectionRequest,
    PurchaseReportRequest,
)

router = APIRouter(prefix="/purchases", tags=["purchases"])


def get_purchases_service(session: AsyncSession = Depends(get_session)) -> PurchasesService:
    """Get purchases service instance."""
    return PurchasesService(session)


@router.post("/", response_model=PurchaseResponse)
async def create_purchase(
    purchase_data: PurchaseCreate,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Create a new purchase."""
    try:
        return await service.create_purchase(purchase_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PurchaseListResponse)
async def get_purchases(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    supplier_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    status: Optional[TransactionStatus] = Query(None),
    approval_status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get purchases with pagination and filters."""
    return await service.get_purchases(
        page=page,
        page_size=page_size,
        supplier_id=supplier_id,
        location_id=location_id,
        status=status,
        approval_status=approval_status,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(
    purchase_id: UUID,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get purchase by ID."""
    purchase = await service.get_purchase(purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.put("/{purchase_id}", response_model=PurchaseResponse)
async def update_purchase(
    purchase_id: UUID,
    update_data: PurchaseUpdate,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Update purchase."""
    purchase = await service.update_purchase(purchase_id, update_data)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.delete("/{purchase_id}")
async def delete_purchase(
    purchase_id: UUID,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Delete purchase."""
    try:
        success = await service.delete_purchase(purchase_id)
        if not success:
            raise HTTPException(status_code=404, detail="Purchase not found")
        return {"message": "Purchase deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/po/{po_number}", response_model=PurchaseResponse)
async def get_purchase_by_po(
    po_number: str,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get purchase by PO number."""
    purchase = await service.get_purchase_by_po_number(po_number)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.get("/{purchase_id}/order", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    purchase_id: UUID,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get purchase order information."""
    order = await service.get_purchase_order(purchase_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return order


@router.post("/{purchase_id}/approve", response_model=PurchaseResponse)
async def approve_purchase(
    purchase_id: UUID,
    approval_request: ApprovalRequest,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Approve purchase."""
    purchase = await service.approve_purchase(purchase_id, approval_request)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.post("/{purchase_id}/receiving", response_model=PurchaseResponse)
async def update_receiving(
    purchase_id: UUID,
    receiving_update: ReceivingUpdateRequest,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Update receiving information."""
    purchase = await service.update_receiving(purchase_id, receiving_update)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.post("/{purchase_id}/inspection", response_model=PurchaseResponse)
async def update_inspection(
    purchase_id: UUID,
    inspection_request: InspectionRequest,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Update inspection information."""
    purchase = await service.update_inspection(purchase_id, inspection_request)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.get("/supplier/{supplier_id}", response_model=PurchaseListResponse)
async def get_supplier_purchases(
    supplier_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get purchases for a specific supplier."""
    return await service.get_supplier_purchases(
        supplier_id=supplier_id,
        page=page,
        page_size=page_size
    )


@router.get("/pending/approvals", response_model=List[PurchaseResponse])
async def get_pending_approvals(
    limit: int = Query(100, ge=1, le=1000),
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get purchases pending approval."""
    return await service.get_pending_approvals(limit=limit)


@router.get("/pending/receipts", response_model=List[PurchaseResponse])
async def get_pending_receipts(
    location_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get purchases with pending receipts."""
    return await service.get_pending_receipts(
        location_id=location_id,
        limit=limit
    )


@router.get("/overdue/list", response_model=List[PurchaseResponse])
async def get_overdue_purchases(
    limit: int = Query(100, ge=1, le=1000),
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get overdue purchases."""
    return await service.get_overdue_purchases(limit=limit)


@router.post("/reports/purchases", response_model=PurchaseReportResponse)
async def generate_purchase_report(
    report_request: PurchaseReportRequest,
    service: PurchasesService = Depends(get_purchases_service)
):
    """Generate purchase report."""
    return await service.get_purchase_report(
        date_from=report_request.date_from,
        date_to=report_request.date_to,
        supplier_id=report_request.supplier_id,
        location_id=report_request.location_id,
        approval_status=report_request.approval_status
    )


@router.get("/reports/summary")
async def get_purchase_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    supplier_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    service: PurchasesService = Depends(get_purchases_service)
):
    """Get purchase summary statistics."""
    return await service.get_purchase_report(
        date_from=date_from,
        date_to=date_to,
        supplier_id=supplier_id,
        location_id=location_id,
        approval_status=approval_status
    )