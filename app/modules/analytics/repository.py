from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import and_, or_, func, select, update, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.modules.analytics.models import (
    AnalyticsReport, BusinessMetric, SystemAlert,
    ReportType, ReportStatus, ReportFormat, MetricType,
    AlertSeverity, AlertStatus
)
from app.modules.analytics.schemas import (
    AnalyticsReportCreate, AnalyticsReportUpdate,
    BusinessMetricCreate, BusinessMetricUpdate,
    SystemAlertCreate, SystemAlertUpdate,
    AnalyticsSearch, MetricSearch, AlertSearch
)


class AnalyticsReportRepository:
    """Repository for AnalyticsReport operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, report_data: AnalyticsReportCreate, generated_by: UUID) -> AnalyticsReport:
        """Create a new analytics report."""
        report = AnalyticsReport(
            report_name=report_data.report_name,
            report_type=report_data.report_type,
            report_format=report_data.report_format,
            generated_by=str(generated_by),
            start_date=report_data.start_date,
            end_date=report_data.end_date,
            filters=report_data.filters,
            parameters=report_data.parameters
        )
        
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report
    
    async def get_by_id(self, report_id: UUID) -> Optional[AnalyticsReport]:
        """Get analytics report by ID."""
        query = select(AnalyticsReport).where(AnalyticsReport.id == report_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        report_type: Optional[ReportType] = None,
        report_status: Optional[ReportStatus] = None,
        generated_by: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        active_only: bool = True
    ) -> List[AnalyticsReport]:
        """Get all analytics reports with optional filtering."""
        query = select(AnalyticsReport)
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(AnalyticsReport.is_active == True)
        if report_type:
            conditions.append(AnalyticsReport.report_type == report_type.value)
        if report_status:
            conditions.append(AnalyticsReport.report_status == report_status.value)
        if generated_by:
            conditions.append(AnalyticsReport.generated_by == str(generated_by))
        if start_date:
            conditions.append(AnalyticsReport.start_date >= start_date)
        if end_date:
            conditions.append(AnalyticsReport.end_date <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(AnalyticsReport.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search(
        self, 
        search_params: AnalyticsSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[AnalyticsReport]:
        """Search analytics reports."""
        query = select(AnalyticsReport)
        
        conditions = []
        if active_only:
            conditions.append(AnalyticsReport.is_active == True)
        
        if search_params.report_type:
            conditions.append(AnalyticsReport.report_type == search_params.report_type.value)
        if search_params.report_status:
            conditions.append(AnalyticsReport.report_status == search_params.report_status.value)
        if search_params.generated_by:
            conditions.append(AnalyticsReport.generated_by == str(search_params.generated_by))
        if search_params.start_date:
            conditions.append(AnalyticsReport.start_date >= search_params.start_date)
        if search_params.end_date:
            conditions.append(AnalyticsReport.end_date <= search_params.end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(AnalyticsReport.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, report_id: UUID, report_data: AnalyticsReportUpdate) -> Optional[AnalyticsReport]:
        """Update an analytics report."""
        query = select(AnalyticsReport).where(AnalyticsReport.id == report_id)
        result = await self.session.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            return None
        
        # Update fields
        update_data = report_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(report, field, value)
        
        await self.session.commit()
        await self.session.refresh(report)
        return report
    
    async def delete(self, report_id: UUID) -> bool:
        """Soft delete an analytics report."""
        query = select(AnalyticsReport).where(AnalyticsReport.id == report_id)
        result = await self.session.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            return False
        
        report.is_active = False
        await self.session.commit()
        return True
    
    async def get_by_type(self, report_type: ReportType, limit: int = 10) -> List[AnalyticsReport]:
        """Get reports by type."""
        query = select(AnalyticsReport).where(
            and_(
                AnalyticsReport.report_type == report_type.value,
                AnalyticsReport.is_active == True
            )
        ).order_by(desc(AnalyticsReport.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_status(self, status: ReportStatus, limit: int = 10) -> List[AnalyticsReport]:
        """Get reports by status."""
        query = select(AnalyticsReport).where(
            and_(
                AnalyticsReport.report_status == status.value,
                AnalyticsReport.is_active == True
            )
        ).order_by(desc(AnalyticsReport.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_reports(self) -> List[AnalyticsReport]:
        """Get pending reports."""
        return await self.get_by_status(ReportStatus.PENDING)
    
    async def get_failed_reports(self) -> List[AnalyticsReport]:
        """Get failed reports."""
        return await self.get_by_status(ReportStatus.FAILED)
    
    async def count_by_status(self, status: ReportStatus) -> int:
        """Count reports by status."""
        query = select(func.count(AnalyticsReport.id)).where(
            and_(
                AnalyticsReport.report_status == status.value,
                AnalyticsReport.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar()
    
    async def get_report_summary(self) -> Dict[str, Any]:
        """Get report summary statistics."""
        query = select(AnalyticsReport).where(AnalyticsReport.is_active == True)
        result = await self.session.execute(query)
        reports = result.scalars().all()
        
        total_reports = len(reports)
        pending_reports = len([r for r in reports if r.report_status == ReportStatus.PENDING.value])
        completed_reports = len([r for r in reports if r.report_status == ReportStatus.COMPLETED.value])
        failed_reports = len([r for r in reports if r.report_status == ReportStatus.FAILED.value])
        
        # Count by type
        type_counts = {}
        for report_type in ReportType:
            type_counts[report_type.value] = len([r for r in reports if r.report_type == report_type.value])
        
        return {
            'total_reports': total_reports,
            'pending_reports': pending_reports,
            'completed_reports': completed_reports,
            'failed_reports': failed_reports,
            'reports_by_type': type_counts
        }


class BusinessMetricRepository:
    """Repository for BusinessMetric operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, metric_data: BusinessMetricCreate) -> BusinessMetric:
        """Create a new business metric."""
        metric = BusinessMetric(
            metric_name=metric_data.metric_name,
            metric_type=metric_data.metric_type,
            category=metric_data.category,
            current_value=metric_data.current_value,
            previous_value=metric_data.previous_value,
            target_value=metric_data.target_value,
            unit=metric_data.unit,
            calculation_method=metric_data.calculation_method
        )
        
        self.session.add(metric)
        await self.session.commit()
        await self.session.refresh(metric)
        return metric
    
    async def get_by_id(self, metric_id: UUID) -> Optional[BusinessMetric]:
        """Get business metric by ID."""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, metric_name: str) -> Optional[BusinessMetric]:
        """Get business metric by name."""
        query = select(BusinessMetric).where(
            and_(
                BusinessMetric.metric_name == metric_name,
                BusinessMetric.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        metric_type: Optional[MetricType] = None,
        category: Optional[str] = None,
        has_target: Optional[bool] = None,
        active_only: bool = True
    ) -> List[BusinessMetric]:
        """Get all business metrics with optional filtering."""
        query = select(BusinessMetric)
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(BusinessMetric.is_active == True)
        if metric_type:
            conditions.append(BusinessMetric.metric_type == metric_type.value)
        if category:
            conditions.append(BusinessMetric.category == category)
        if has_target is not None:
            if has_target:
                conditions.append(BusinessMetric.target_value.is_not(None))
            else:
                conditions.append(BusinessMetric.target_value.is_(None))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(BusinessMetric.tracked_date)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search(
        self, 
        search_params: MetricSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[BusinessMetric]:
        """Search business metrics."""
        query = select(BusinessMetric)
        
        conditions = []
        if active_only:
            conditions.append(BusinessMetric.is_active == True)
        
        if search_params.metric_type:
            conditions.append(BusinessMetric.metric_type == search_params.metric_type.value)
        if search_params.category:
            conditions.append(BusinessMetric.category == search_params.category)
        if search_params.has_target is not None:
            if search_params.has_target:
                conditions.append(BusinessMetric.target_value.is_not(None))
            else:
                conditions.append(BusinessMetric.target_value.is_(None))
        if search_params.target_met is not None:
            if search_params.target_met:
                conditions.append(BusinessMetric.current_value >= BusinessMetric.target_value)
            else:
                conditions.append(BusinessMetric.current_value < BusinessMetric.target_value)
        if search_params.tracked_from:
            conditions.append(BusinessMetric.tracked_date >= search_params.tracked_from)
        if search_params.tracked_to:
            conditions.append(BusinessMetric.tracked_date <= search_params.tracked_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(BusinessMetric.tracked_date)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, metric_id: UUID, metric_data: BusinessMetricUpdate) -> Optional[BusinessMetric]:
        """Update a business metric."""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await self.session.execute(query)
        metric = result.scalar_one_or_none()
        
        if not metric:
            return None
        
        # Update fields
        update_data = metric_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(metric, field, value)
        
        await self.session.commit()
        await self.session.refresh(metric)
        return metric
    
    async def delete(self, metric_id: UUID) -> bool:
        """Soft delete a business metric."""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await self.session.execute(query)
        metric = result.scalar_one_or_none()
        
        if not metric:
            return False
        
        metric.is_active = False
        await self.session.commit()
        return True
    
    async def get_by_category(self, category: str) -> List[BusinessMetric]:
        """Get metrics by category."""
        query = select(BusinessMetric).where(
            and_(
                BusinessMetric.category == category,
                BusinessMetric.is_active == True
            )
        ).order_by(desc(BusinessMetric.tracked_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_metrics_with_targets(self) -> List[BusinessMetric]:
        """Get metrics that have targets set."""
        query = select(BusinessMetric).where(
            and_(
                BusinessMetric.target_value.is_not(None),
                BusinessMetric.is_active == True
            )
        ).order_by(desc(BusinessMetric.tracked_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_metrics_meeting_targets(self) -> List[BusinessMetric]:
        """Get metrics that are meeting their targets."""
        query = select(BusinessMetric).where(
            and_(
                BusinessMetric.target_value.is_not(None),
                BusinessMetric.current_value >= BusinessMetric.target_value,
                BusinessMetric.is_active == True
            )
        ).order_by(desc(BusinessMetric.tracked_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_metric_history(self, metric_name: str, limit: int = 30) -> List[BusinessMetric]:
        """Get metric history by name."""
        query = select(BusinessMetric).where(
            and_(
                BusinessMetric.metric_name == metric_name,
                BusinessMetric.is_active == True
            )
        ).order_by(desc(BusinessMetric.tracked_date)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class SystemAlertRepository:
    """Repository for SystemAlert operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, alert_data: SystemAlertCreate) -> SystemAlert:
        """Create a new system alert."""
        alert = SystemAlert(
            alert_name=alert_data.alert_name,
            alert_type=alert_data.alert_type,
            severity=alert_data.severity,
            message=alert_data.message,
            description=alert_data.description,
            source=alert_data.source,
            trigger_condition=alert_data.trigger_condition
        )
        
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert
    
    async def get_by_id(self, alert_id: UUID) -> Optional[SystemAlert]:
        """Get system alert by ID."""
        query = select(SystemAlert).where(SystemAlert.id == alert_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        alert_type: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        source: Optional[str] = None,
        active_only: bool = True
    ) -> List[SystemAlert]:
        """Get all system alerts with optional filtering."""
        query = select(SystemAlert)
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(SystemAlert.is_active == True)
        if alert_type:
            conditions.append(SystemAlert.alert_type == alert_type)
        if severity:
            conditions.append(SystemAlert.severity == severity.value)
        if status:
            conditions.append(SystemAlert.status == status.value)
        if source:
            conditions.append(SystemAlert.source == source)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(SystemAlert.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search(
        self, 
        search_params: AlertSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[SystemAlert]:
        """Search system alerts."""
        query = select(SystemAlert)
        
        conditions = []
        if active_only:
            conditions.append(SystemAlert.is_active == True)
        
        if search_params.alert_type:
            conditions.append(SystemAlert.alert_type == search_params.alert_type)
        if search_params.severity:
            conditions.append(SystemAlert.severity == search_params.severity.value)
        if search_params.status:
            conditions.append(SystemAlert.status == search_params.status.value)
        if search_params.source:
            conditions.append(SystemAlert.source == search_params.source)
        if search_params.created_from:
            conditions.append(SystemAlert.created_at >= search_params.created_from)
        if search_params.created_to:
            conditions.append(SystemAlert.created_at <= search_params.created_to)
        if search_params.resolved_from:
            conditions.append(SystemAlert.resolved_at >= search_params.resolved_from)
        if search_params.resolved_to:
            conditions.append(SystemAlert.resolved_at <= search_params.resolved_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(SystemAlert.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, alert_id: UUID, alert_data: SystemAlertUpdate) -> Optional[SystemAlert]:
        """Update a system alert."""
        query = select(SystemAlert).where(SystemAlert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
        
        # Update fields
        update_data = alert_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alert, field, value)
        
        await self.session.commit()
        await self.session.refresh(alert)
        return alert
    
    async def delete(self, alert_id: UUID) -> bool:
        """Soft delete a system alert."""
        query = select(SystemAlert).where(SystemAlert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return False
        
        alert.is_active = False
        await self.session.commit()
        return True
    
    async def get_active_alerts(self) -> List[SystemAlert]:
        """Get active alerts."""
        query = select(SystemAlert).where(
            and_(
                SystemAlert.status == AlertStatus.ACTIVE.value,
                SystemAlert.is_active == True
            )
        ).order_by(desc(SystemAlert.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_critical_alerts(self) -> List[SystemAlert]:
        """Get critical alerts."""
        query = select(SystemAlert).where(
            and_(
                SystemAlert.severity == AlertSeverity.CRITICAL.value,
                SystemAlert.status == AlertStatus.ACTIVE.value,
                SystemAlert.is_active == True
            )
        ).order_by(desc(SystemAlert.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_severity(self, severity: AlertSeverity) -> List[SystemAlert]:
        """Get alerts by severity."""
        query = select(SystemAlert).where(
            and_(
                SystemAlert.severity == severity.value,
                SystemAlert.is_active == True
            )
        ).order_by(desc(SystemAlert.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_status(self, status: AlertStatus) -> List[SystemAlert]:
        """Get alerts by status."""
        query = select(SystemAlert).where(
            and_(
                SystemAlert.status == status.value,
                SystemAlert.is_active == True
            )
        ).order_by(desc(SystemAlert.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_by_severity(self, severity: AlertSeverity) -> int:
        """Count alerts by severity."""
        query = select(func.count(SystemAlert.id)).where(
            and_(
                SystemAlert.severity == severity.value,
                SystemAlert.status == AlertStatus.ACTIVE.value,
                SystemAlert.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar()
    
    async def count_by_status(self, status: AlertStatus) -> int:
        """Count alerts by status."""
        query = select(func.count(SystemAlert.id)).where(
            and_(
                SystemAlert.status == status.value,
                SystemAlert.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar()
    
    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        query = select(SystemAlert).where(SystemAlert.is_active == True)
        result = await self.session.execute(query)
        alerts = result.scalars().all()
        
        total_alerts = len(alerts)
        active_alerts = len([a for a in alerts if a.status == AlertStatus.ACTIVE.value])
        resolved_alerts = len([a for a in alerts if a.status == AlertStatus.RESOLVED.value])
        
        # Count by severity
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([a for a in alerts if a.severity == severity.value])
        
        # Count by status
        status_counts = {}
        for status in AlertStatus:
            status_counts[status.value] = len([a for a in alerts if a.status == status.value])
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'resolved_alerts': resolved_alerts,
            'alerts_by_severity': severity_counts,
            'alerts_by_status': status_counts
        }