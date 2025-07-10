from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.shared.dependencies import get_session
from app.modules.analytics.service import AnalyticsService
from app.modules.analytics.models import (
    ReportType, ReportStatus, ReportFormat, MetricType,
    AlertSeverity, AlertStatus
)
from app.modules.analytics.schemas import (
    AnalyticsReportCreate, AnalyticsReportUpdate, AnalyticsReportResponse,
    AnalyticsReportListResponse, BusinessMetricCreate, BusinessMetricUpdate,
    BusinessMetricResponse, BusinessMetricListResponse, SystemAlertCreate,
    SystemAlertUpdate, SystemAlertResponse, SystemAlertListResponse,
    AnalyticsSearch, MetricSearch, AlertSearch, AnalyticsDashboard,
    SystemHealthSummary, AlertAcknowledgeRequest, AlertResolveRequest,
    MetricValueUpdate, ReportGenerationRequest
)


router = APIRouter(prefix="/analytics", tags=["Analytics & System Management"])


# Dependency to get analytics service
async def get_analytics_service(session: AsyncSession = Depends(get_session)) -> AnalyticsService:
    return AnalyticsService(session)


# Analytics Report endpoints
@router.post("/reports", response_model=AnalyticsReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: AnalyticsReportCreate,
    generated_by: UUID = Query(..., description="User ID generating the report"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Create a new analytics report."""
    try:
        return await service.create_report(report_data, generated_by)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/reports/{report_id}", response_model=AnalyticsReportResponse)
async def get_report(
    report_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics report by ID."""
    try:
        return await service.get_report(report_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/reports", response_model=List[AnalyticsReportListResponse])
async def get_reports(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    report_status: Optional[ReportStatus] = Query(None, description="Filter by report status"),
    generated_by: Optional[UUID] = Query(None, description="Filter by generator"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    active_only: bool = Query(True, description="Only active reports"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get all analytics reports with optional filtering."""
    try:
        return await service.get_reports(
            skip=skip,
            limit=limit,
            report_type=report_type,
            report_status=report_status,
            generated_by=generated_by,
            start_date=start_date,
            end_date=end_date,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/reports/search", response_model=List[AnalyticsReportListResponse])
async def search_reports(
    search_params: AnalyticsSearch,
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    active_only: bool = Query(True, description="Only active reports"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Search analytics reports."""
    try:
        return await service.search_reports(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/reports/{report_id}", response_model=AnalyticsReportResponse)
async def update_report(
    report_id: UUID,
    report_data: AnalyticsReportUpdate,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Update an analytics report."""
    try:
        return await service.update_report(report_id, report_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Delete an analytics report."""
    try:
        success = await service.delete_report(report_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/reports/{report_id}/generate", response_model=AnalyticsReportResponse)
async def generate_report(
    report_id: UUID,
    generation_request: ReportGenerationRequest,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Generate a report."""
    try:
        return await service.generate_report(report_id, generation_request)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Business Metric endpoints
@router.post("/metrics", response_model=BusinessMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_metric(
    metric_data: BusinessMetricCreate,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Create a new business metric."""
    try:
        return await service.create_metric(metric_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/metrics/{metric_id}", response_model=BusinessMetricResponse)
async def get_metric(
    metric_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get business metric by ID."""
    try:
        return await service.get_metric(metric_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/metrics", response_model=List[BusinessMetricListResponse])
async def get_metrics(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    has_target: Optional[bool] = Query(None, description="Filter by target presence"),
    active_only: bool = Query(True, description="Only active metrics"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get all business metrics with optional filtering."""
    try:
        return await service.get_metrics(
            skip=skip,
            limit=limit,
            metric_type=metric_type,
            category=category,
            has_target=has_target,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/metrics/search", response_model=List[BusinessMetricListResponse])
async def search_metrics(
    search_params: MetricSearch,
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    active_only: bool = Query(True, description="Only active metrics"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Search business metrics."""
    try:
        return await service.search_metrics(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/metrics/{metric_id}", response_model=BusinessMetricResponse)
async def update_metric(
    metric_id: UUID,
    metric_data: BusinessMetricUpdate,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Update a business metric."""
    try:
        return await service.update_metric(metric_id, metric_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(
    metric_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Delete a business metric."""
    try:
        success = await service.delete_metric(metric_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/metrics/{metric_id}/value", response_model=BusinessMetricResponse)
async def update_metric_value(
    metric_id: UUID,
    value_update: MetricValueUpdate,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Update metric value."""
    try:
        return await service.update_metric_value(metric_id, value_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/metrics/{metric_name}/history", response_model=List[BusinessMetricResponse])
async def get_metric_history(
    metric_name: str,
    limit: int = Query(30, ge=1, le=100, description="Maximum records to return"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get metric history by name."""
    try:
        return await service.get_metric_history(metric_name, limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/metrics/calculate", response_model=List[BusinessMetricResponse])
async def calculate_key_metrics(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Calculate and update key business metrics."""
    try:
        return await service.calculate_key_metrics()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# System Alert endpoints
@router.post("/alerts", response_model=SystemAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: SystemAlertCreate,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Create a new system alert."""
    try:
        return await service.create_alert(alert_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/alerts/{alert_id}", response_model=SystemAlertResponse)
async def get_alert(
    alert_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get system alert by ID."""
    try:
        return await service.get_alert(alert_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/alerts", response_model=List[SystemAlertListResponse])
async def get_alerts(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    active_only: bool = Query(True, description="Only active alerts"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get all system alerts with optional filtering."""
    try:
        return await service.get_alerts(
            skip=skip,
            limit=limit,
            alert_type=alert_type,
            severity=severity,
            status=status,
            source=source,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/alerts/search", response_model=List[SystemAlertListResponse])
async def search_alerts(
    search_params: AlertSearch,
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    active_only: bool = Query(True, description="Only active alerts"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Search system alerts."""
    try:
        return await service.search_alerts(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/alerts/{alert_id}", response_model=SystemAlertResponse)
async def update_alert(
    alert_id: UUID,
    alert_data: SystemAlertUpdate,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Update a system alert."""
    try:
        return await service.update_alert(alert_id, alert_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Delete a system alert."""
    try:
        success = await service.delete_alert(alert_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge", response_model=SystemAlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    acknowledge_request: AlertAcknowledgeRequest,
    acknowledged_by: UUID = Query(..., description="User ID acknowledging the alert"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Acknowledge an alert."""
    try:
        return await service.acknowledge_alert(alert_id, acknowledged_by, acknowledge_request)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/alerts/{alert_id}/resolve", response_model=SystemAlertResponse)
async def resolve_alert(
    alert_id: UUID,
    resolve_request: AlertResolveRequest,
    resolved_by: UUID = Query(..., description="User ID resolving the alert"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Resolve an alert."""
    try:
        return await service.resolve_alert(alert_id, resolved_by, resolve_request)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/alerts/{alert_id}/suppress", response_model=SystemAlertResponse)
async def suppress_alert(
    alert_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Suppress an alert."""
    try:
        return await service.suppress_alert(alert_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Dashboard and monitoring endpoints
@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics dashboard data."""
    try:
        return await service.get_analytics_dashboard()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/system/health", response_model=SystemHealthSummary)
async def get_system_health(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get system health summary."""
    try:
        return await service.get_system_health()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Report type specific endpoints
@router.get("/reports/types/{report_type}", response_model=List[AnalyticsReportListResponse])
async def get_reports_by_type(
    report_type: ReportType,
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get reports by type."""
    try:
        return await service.get_reports(
            report_type=report_type,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/status/{report_status}", response_model=List[AnalyticsReportListResponse])
async def get_reports_by_status(
    report_status: ReportStatus,
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get reports by status."""
    try:
        return await service.get_reports(
            report_status=report_status,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Metric category specific endpoints
@router.get("/metrics/categories/{category}", response_model=List[BusinessMetricListResponse])
async def get_metrics_by_category(
    category: str,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get metrics by category."""
    try:
        return await service.get_metrics(
            category=category
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/metrics/with-targets", response_model=List[BusinessMetricListResponse])
async def get_metrics_with_targets(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get metrics that have targets set."""
    try:
        return await service.get_metrics(
            has_target=True
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Alert severity specific endpoints
@router.get("/alerts/severity/{severity}", response_model=List[SystemAlertListResponse])
async def get_alerts_by_severity(
    severity: AlertSeverity,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get alerts by severity."""
    try:
        return await service.get_alerts(
            severity=severity
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/alerts/active", response_model=List[SystemAlertListResponse])
async def get_active_alerts(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get active alerts."""
    try:
        return await service.get_alerts(
            status=AlertStatus.ACTIVE
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/alerts/critical", response_model=List[SystemAlertListResponse])
async def get_critical_alerts(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get critical alerts."""
    try:
        return await service.get_alerts(
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Health check endpoint
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for analytics service."""
    return {"status": "healthy", "service": "analytics-system-management"}