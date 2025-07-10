from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.analytics.models import (
    AnalyticsReport, BusinessMetric, SystemAlert,
    ReportType, ReportStatus, ReportFormat, MetricType,
    AlertSeverity, AlertStatus
)
from app.modules.analytics.repository import (
    AnalyticsReportRepository, BusinessMetricRepository, SystemAlertRepository
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
from app.modules.transactions.repository import TransactionHeaderRepository
from app.modules.customers.repository import CustomerRepository
from app.modules.inventory.repository import ItemRepository, InventoryUnitRepository
from app.modules.rentals.repository import RentalReturnRepository


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.report_repository = AnalyticsReportRepository(session)
        self.metric_repository = BusinessMetricRepository(session)
        self.alert_repository = SystemAlertRepository(session)
        # Import other repositories for analytics
        self.transaction_repository = TransactionHeaderRepository(session)
        self.customer_repository = CustomerRepository(session)
        self.item_repository = ItemRepository(session)
        self.inventory_unit_repository = InventoryUnitRepository(session)
        self.rental_return_repository = RentalReturnRepository(session)
    
    # Analytics Report operations
    async def create_report(self, report_data: AnalyticsReportCreate, generated_by: UUID) -> AnalyticsReportResponse:
        """Create a new analytics report."""
        try:
            report = await self.report_repository.create(report_data, generated_by)
            return AnalyticsReportResponse.model_validate(report)
        except Exception as e:
            raise ValidationError(f"Failed to create analytics report: {str(e)}")
    
    async def get_report(self, report_id: UUID) -> AnalyticsReportResponse:
        """Get analytics report by ID."""
        report = await self.report_repository.get_by_id(report_id)
        if not report:
            raise NotFoundError(f"Analytics report with ID {report_id} not found")
        
        return AnalyticsReportResponse.model_validate(report)
    
    async def get_reports(
        self, 
        skip: int = 0, 
        limit: int = 100,
        report_type: Optional[ReportType] = None,
        report_status: Optional[ReportStatus] = None,
        generated_by: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        active_only: bool = True
    ) -> List[AnalyticsReportListResponse]:
        """Get all analytics reports with optional filtering."""
        reports = await self.report_repository.get_all(
            skip=skip,
            limit=limit,
            report_type=report_type,
            report_status=report_status,
            generated_by=generated_by,
            start_date=start_date,
            end_date=end_date,
            active_only=active_only
        )
        
        return [AnalyticsReportListResponse.model_validate(report) for report in reports]
    
    async def search_reports(
        self, 
        search_params: AnalyticsSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[AnalyticsReportListResponse]:
        """Search analytics reports."""
        reports = await self.report_repository.search(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [AnalyticsReportListResponse.model_validate(report) for report in reports]
    
    async def update_report(self, report_id: UUID, report_data: AnalyticsReportUpdate) -> AnalyticsReportResponse:
        """Update an analytics report."""
        report = await self.report_repository.update(report_id, report_data)
        if not report:
            raise NotFoundError(f"Analytics report with ID {report_id} not found")
        
        return AnalyticsReportResponse.model_validate(report)
    
    async def delete_report(self, report_id: UUID) -> bool:
        """Delete an analytics report."""
        success = await self.report_repository.delete(report_id)
        if not success:
            raise NotFoundError(f"Analytics report with ID {report_id} not found")
        
        return success
    
    async def generate_report(self, report_id: UUID, generation_request: ReportGenerationRequest) -> AnalyticsReportResponse:
        """Generate a report."""
        report = await self.report_repository.get_by_id(report_id)
        if not report:
            raise NotFoundError(f"Analytics report with ID {report_id} not found")
        
        try:
            # Start generation
            report.start_generation()
            await self.session.commit()
            
            # Generate report based on type
            file_path, file_size = await self._generate_report_file(report, generation_request)
            
            # Complete generation
            report.complete_generation(file_path, file_size)
            await self.session.commit()
            
            return AnalyticsReportResponse.model_validate(report)
            
        except Exception as e:
            # Fail generation
            report.fail_generation(str(e))
            await self.session.commit()
            raise ValidationError(f"Failed to generate report: {str(e)}")
    
    async def _generate_report_file(self, report: AnalyticsReport, generation_request: ReportGenerationRequest) -> tuple[str, int]:
        """Generate report file based on type."""
        # This would contain the actual report generation logic
        # For now, we'll simulate file generation
        import json
        import os
        
        # Create reports directory if it doesn't exist
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate report data based on type
        report_data = await self._generate_report_data(report, generation_request)
        
        # Generate file based on format
        file_name = f"{report.report_name}_{report.id}.{report.report_format.lower()}"
        file_path = os.path.join(reports_dir, file_name)
        
        if report.report_format == ReportFormat.JSON.value:
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        elif report.report_format == ReportFormat.CSV.value:
            import csv
            with open(file_path, 'w', newline='') as f:
                if report_data.get('rows'):
                    writer = csv.DictWriter(f, fieldnames=report_data['rows'][0].keys())
                    writer.writeheader()
                    writer.writerows(report_data['rows'])
        else:
            # For PDF and Excel, we'd use appropriate libraries
            with open(file_path, 'w') as f:
                f.write(json.dumps(report_data, indent=2, default=str))
        
        file_size = os.path.getsize(file_path)
        return file_path, file_size
    
    async def _generate_report_data(self, report: AnalyticsReport, generation_request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate report data based on type."""
        data = {
            'report_name': report.report_name,
            'report_type': report.report_type,
            'generated_at': datetime.utcnow().isoformat(),
            'date_range': {
                'start': generation_request.start_date.isoformat() if generation_request.start_date else None,
                'end': generation_request.end_date.isoformat() if generation_request.end_date else None
            },
            'filters': generation_request.filters or {},
            'data': []
        }
        
        if report.report_type == ReportType.SALES.value:
            data['data'] = await self._generate_sales_data(generation_request)
        elif report.report_type == ReportType.RENTALS.value:
            data['data'] = await self._generate_rentals_data(generation_request)
        elif report.report_type == ReportType.INVENTORY.value:
            data['data'] = await self._generate_inventory_data(generation_request)
        elif report.report_type == ReportType.CUSTOMER.value:
            data['data'] = await self._generate_customer_data(generation_request)
        elif report.report_type == ReportType.FINANCIAL.value:
            data['data'] = await self._generate_financial_data(generation_request)
        elif report.report_type == ReportType.PERFORMANCE.value:
            data['data'] = await self._generate_performance_data(generation_request)
        
        return data
    
    async def _generate_sales_data(self, generation_request: ReportGenerationRequest) -> List[Dict[str, Any]]:
        """Generate sales report data."""
        # Get sales transactions
        transactions = await self.transaction_repository.get_all(
            date_from=generation_request.start_date,
            date_to=generation_request.end_date,
            active_only=True
        )
        
        sales_data = []
        for transaction in transactions:
            if transaction.is_sale():
                sales_data.append({
                    'transaction_id': str(transaction.id),
                    'transaction_date': transaction.transaction_date.isoformat(),
                    'customer_id': transaction.customer_id,
                    'total_amount': float(transaction.total_amount),
                    'status': transaction.status
                })
        
        return sales_data
    
    async def _generate_rentals_data(self, generation_request: ReportGenerationRequest) -> List[Dict[str, Any]]:
        """Generate rentals report data."""
        # Get rental returns
        returns = await self.rental_return_repository.get_all(
            date_from=generation_request.start_date,
            date_to=generation_request.end_date,
            active_only=True
        )
        
        rental_data = []
        for return_item in returns:
            rental_data.append({
                'return_id': str(return_item.id),
                'return_date': return_item.return_date.isoformat(),
                'return_type': return_item.return_type,
                'status': return_item.return_status,
                'total_late_fee': float(return_item.total_late_fee),
                'total_damage_fee': float(return_item.total_damage_fee),
                'total_refund': float(return_item.total_refund_amount)
            })
        
        return rental_data
    
    async def _generate_inventory_data(self, generation_request: ReportGenerationRequest) -> List[Dict[str, Any]]:
        """Generate inventory report data."""
        # Get inventory units
        inventory_units = await self.inventory_unit_repository.get_all(active_only=True)
        
        inventory_data = []
        for unit in inventory_units:
            inventory_data.append({
                'unit_id': str(unit.id),
                'unit_code': unit.unit_code,
                'item_id': unit.item_id,
                'status': unit.status,
                'condition': unit.condition,
                'location_id': unit.location_id,
                'purchase_price': float(unit.purchase_price)
            })
        
        return inventory_data
    
    async def _generate_customer_data(self, generation_request: ReportGenerationRequest) -> List[Dict[str, Any]]:
        """Generate customer report data."""
        # Get customers
        customers = await self.customer_repository.get_all(active_only=True)
        
        customer_data = []
        for customer in customers:
            customer_data.append({
                'customer_id': str(customer.id),
                'customer_name': customer.customer_name,
                'customer_type': customer.customer_type,
                'tier': customer.tier,
                'status': customer.status,
                'credit_limit': float(customer.credit_limit),
                'outstanding_balance': float(customer.outstanding_balance)
            })
        
        return customer_data
    
    async def _generate_financial_data(self, generation_request: ReportGenerationRequest) -> List[Dict[str, Any]]:
        """Generate financial report data."""
        # Get transactions for financial analysis
        transactions = await self.transaction_repository.get_all(
            date_from=generation_request.start_date,
            date_to=generation_request.end_date,
            active_only=True
        )
        
        financial_data = []
        for transaction in transactions:
            financial_data.append({
                'transaction_id': str(transaction.id),
                'transaction_date': transaction.transaction_date.isoformat(),
                'transaction_type': transaction.transaction_type,
                'total_amount': float(transaction.total_amount),
                'tax_amount': float(transaction.tax_amount),
                'discount_amount': float(transaction.discount_amount),
                'net_amount': float(transaction.net_amount)
            })
        
        return financial_data
    
    async def _generate_performance_data(self, generation_request: ReportGenerationRequest) -> List[Dict[str, Any]]:
        """Generate performance report data."""
        # Get metrics for performance analysis
        metrics = await self.metric_repository.get_all(active_only=True)
        
        performance_data = []
        for metric in metrics:
            performance_data.append({
                'metric_id': str(metric.id),
                'metric_name': metric.metric_name,
                'metric_type': metric.metric_type,
                'category': metric.category,
                'current_value': float(metric.current_value),
                'target_value': float(metric.target_value) if metric.target_value else None,
                'tracked_date': metric.tracked_date.isoformat()
            })
        
        return performance_data
    
    # Business Metric operations
    async def create_metric(self, metric_data: BusinessMetricCreate) -> BusinessMetricResponse:
        """Create a new business metric."""
        try:
            metric = await self.metric_repository.create(metric_data)
            return BusinessMetricResponse.model_validate(metric)
        except Exception as e:
            raise ValidationError(f"Failed to create business metric: {str(e)}")
    
    async def get_metric(self, metric_id: UUID) -> BusinessMetricResponse:
        """Get business metric by ID."""
        metric = await self.metric_repository.get_by_id(metric_id)
        if not metric:
            raise NotFoundError(f"Business metric with ID {metric_id} not found")
        
        return BusinessMetricResponse.model_validate(metric)
    
    async def get_metrics(
        self, 
        skip: int = 0, 
        limit: int = 100,
        metric_type: Optional[MetricType] = None,
        category: Optional[str] = None,
        has_target: Optional[bool] = None,
        active_only: bool = True
    ) -> List[BusinessMetricListResponse]:
        """Get all business metrics with optional filtering."""
        metrics = await self.metric_repository.get_all(
            skip=skip,
            limit=limit,
            metric_type=metric_type,
            category=category,
            has_target=has_target,
            active_only=active_only
        )
        
        return [BusinessMetricListResponse.model_validate(metric) for metric in metrics]
    
    async def search_metrics(
        self, 
        search_params: MetricSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[BusinessMetricListResponse]:
        """Search business metrics."""
        metrics = await self.metric_repository.search(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [BusinessMetricListResponse.model_validate(metric) for metric in metrics]
    
    async def update_metric(self, metric_id: UUID, metric_data: BusinessMetricUpdate) -> BusinessMetricResponse:
        """Update a business metric."""
        metric = await self.metric_repository.update(metric_id, metric_data)
        if not metric:
            raise NotFoundError(f"Business metric with ID {metric_id} not found")
        
        return BusinessMetricResponse.model_validate(metric)
    
    async def delete_metric(self, metric_id: UUID) -> bool:
        """Delete a business metric."""
        success = await self.metric_repository.delete(metric_id)
        if not success:
            raise NotFoundError(f"Business metric with ID {metric_id} not found")
        
        return success
    
    async def update_metric_value(self, metric_id: UUID, value_update: MetricValueUpdate) -> BusinessMetricResponse:
        """Update metric value."""
        metric = await self.metric_repository.get_by_id(metric_id)
        if not metric:
            raise NotFoundError(f"Business metric with ID {metric_id} not found")
        
        metric.update_value(value_update.new_value)
        await self.session.commit()
        await self.session.refresh(metric)
        
        return BusinessMetricResponse.model_validate(metric)
    
    async def get_metric_history(self, metric_name: str, limit: int = 30) -> List[BusinessMetricResponse]:
        """Get metric history by name."""
        metrics = await self.metric_repository.get_metric_history(metric_name, limit)
        return [BusinessMetricResponse.model_validate(metric) for metric in metrics]
    
    # System Alert operations
    async def create_alert(self, alert_data: SystemAlertCreate) -> SystemAlertResponse:
        """Create a new system alert."""
        try:
            alert = await self.alert_repository.create(alert_data)
            return SystemAlertResponse.model_validate(alert)
        except Exception as e:
            raise ValidationError(f"Failed to create system alert: {str(e)}")
    
    async def get_alert(self, alert_id: UUID) -> SystemAlertResponse:
        """Get system alert by ID."""
        alert = await self.alert_repository.get_by_id(alert_id)
        if not alert:
            raise NotFoundError(f"System alert with ID {alert_id} not found")
        
        return SystemAlertResponse.model_validate(alert)
    
    async def get_alerts(
        self, 
        skip: int = 0, 
        limit: int = 100,
        alert_type: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        source: Optional[str] = None,
        active_only: bool = True
    ) -> List[SystemAlertListResponse]:
        """Get all system alerts with optional filtering."""
        alerts = await self.alert_repository.get_all(
            skip=skip,
            limit=limit,
            alert_type=alert_type,
            severity=severity,
            status=status,
            source=source,
            active_only=active_only
        )
        
        return [SystemAlertListResponse.model_validate(alert) for alert in alerts]
    
    async def search_alerts(
        self, 
        search_params: AlertSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[SystemAlertListResponse]:
        """Search system alerts."""
        alerts = await self.alert_repository.search(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [SystemAlertListResponse.model_validate(alert) for alert in alerts]
    
    async def update_alert(self, alert_id: UUID, alert_data: SystemAlertUpdate) -> SystemAlertResponse:
        """Update a system alert."""
        alert = await self.alert_repository.update(alert_id, alert_data)
        if not alert:
            raise NotFoundError(f"System alert with ID {alert_id} not found")
        
        return SystemAlertResponse.model_validate(alert)
    
    async def delete_alert(self, alert_id: UUID) -> bool:
        """Delete a system alert."""
        success = await self.alert_repository.delete(alert_id)
        if not success:
            raise NotFoundError(f"System alert with ID {alert_id} not found")
        
        return success
    
    async def acknowledge_alert(self, alert_id: UUID, acknowledged_by: UUID, request: AlertAcknowledgeRequest) -> SystemAlertResponse:
        """Acknowledge an alert."""
        alert = await self.alert_repository.get_by_id(alert_id)
        if not alert:
            raise NotFoundError(f"System alert with ID {alert_id} not found")
        
        alert.acknowledge(str(acknowledged_by), request.notes)
        await self.session.commit()
        await self.session.refresh(alert)
        
        return SystemAlertResponse.model_validate(alert)
    
    async def resolve_alert(self, alert_id: UUID, resolved_by: UUID, request: AlertResolveRequest) -> SystemAlertResponse:
        """Resolve an alert."""
        alert = await self.alert_repository.get_by_id(alert_id)
        if not alert:
            raise NotFoundError(f"System alert with ID {alert_id} not found")
        
        alert.resolve(str(resolved_by), request.resolution_notes)
        await self.session.commit()
        await self.session.refresh(alert)
        
        return SystemAlertResponse.model_validate(alert)
    
    async def suppress_alert(self, alert_id: UUID) -> SystemAlertResponse:
        """Suppress an alert."""
        alert = await self.alert_repository.get_by_id(alert_id)
        if not alert:
            raise NotFoundError(f"System alert with ID {alert_id} not found")
        
        alert.suppress()
        await self.session.commit()
        await self.session.refresh(alert)
        
        return SystemAlertResponse.model_validate(alert)
    
    # Dashboard and reporting operations
    async def get_analytics_dashboard(self) -> AnalyticsDashboard:
        """Get analytics dashboard data."""
        # Get report summary
        report_summary = await self.report_repository.get_report_summary()
        
        # Get alert counts
        active_alerts = await self.alert_repository.count_by_status(AlertStatus.ACTIVE)
        critical_alerts = await self.alert_repository.count_by_severity(AlertSeverity.CRITICAL)
        
        # Get metrics counts
        all_metrics = await self.metric_repository.get_all(active_only=True)
        metrics_with_targets = await self.metric_repository.get_metrics_with_targets()
        metrics_meeting_targets = await self.metric_repository.get_metrics_meeting_targets()
        
        # Get recent reports
        recent_reports = await self.get_reports(limit=10)
        
        # Get critical alerts
        critical_alerts_list = await self.get_alerts(
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            limit=10
        )
        
        # Get key metrics
        key_metrics = await self.get_metrics(limit=10)
        
        return AnalyticsDashboard(
            total_reports=report_summary['total_reports'],
            pending_reports=report_summary['pending_reports'],
            completed_reports=report_summary['completed_reports'],
            failed_reports=report_summary['failed_reports'],
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
            total_metrics=len(all_metrics),
            metrics_with_targets=len(metrics_with_targets),
            metrics_meeting_targets=len(metrics_meeting_targets),
            recent_reports=recent_reports,
            critical_alerts_list=critical_alerts_list,
            key_metrics=key_metrics
        )
    
    async def get_system_health(self) -> SystemHealthSummary:
        """Get system health summary."""
        # Get alert counts
        active_alerts = await self.alert_repository.count_by_status(AlertStatus.ACTIVE)
        critical_alerts = await self.alert_repository.count_by_severity(AlertSeverity.CRITICAL)
        warning_alerts = await self.alert_repository.count_by_severity(AlertSeverity.MEDIUM)
        
        # Determine overall health
        if critical_alerts > 0:
            overall_health = "CRITICAL"
        elif warning_alerts > 5:
            overall_health = "WARNING"
        elif active_alerts > 0:
            overall_health = "DEGRADED"
        else:
            overall_health = "HEALTHY"
        
        # Get system stats (these would be implemented with actual system monitoring)
        system_uptime = "99.9%"
        database_size = "245 MB"
        storage_usage = "15.2 GB"
        cpu_usage = 25.4
        memory_usage = 68.7
        disk_usage = 42.1
        
        return SystemHealthSummary(
            overall_health=overall_health,
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
            warning_alerts=warning_alerts,
            system_uptime=system_uptime,
            last_backup=datetime.utcnow() - timedelta(hours=6),
            database_size=database_size,
            storage_usage=storage_usage,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage
        )
    
    # Metric calculation and automation
    async def calculate_key_metrics(self) -> List[BusinessMetricResponse]:
        """Calculate and update key business metrics."""
        metrics = []
        
        # Calculate total revenue
        total_revenue = await self._calculate_total_revenue()
        revenue_metric = await self._update_or_create_metric(
            "total_revenue",
            MetricType.CURRENCY,
            "financial",
            total_revenue,
            unit="USD"
        )
        metrics.append(BusinessMetricResponse.model_validate(revenue_metric))
        
        # Calculate total customers
        total_customers = await self._calculate_total_customers()
        customers_metric = await self._update_or_create_metric(
            "total_customers",
            MetricType.COUNTER,
            "business",
            total_customers,
            unit="customers"
        )
        metrics.append(BusinessMetricResponse.model_validate(customers_metric))
        
        # Calculate inventory utilization
        inventory_utilization = await self._calculate_inventory_utilization()
        utilization_metric = await self._update_or_create_metric(
            "inventory_utilization",
            MetricType.PERCENTAGE,
            "operations",
            inventory_utilization,
            unit="%"
        )
        metrics.append(BusinessMetricResponse.model_validate(utilization_metric))
        
        # Calculate return rate
        return_rate = await self._calculate_return_rate()
        return_metric = await self._update_or_create_metric(
            "return_rate",
            MetricType.PERCENTAGE,
            "operations",
            return_rate,
            unit="%"
        )
        metrics.append(BusinessMetricResponse.model_validate(return_metric))
        
        return metrics
    
    async def _calculate_total_revenue(self) -> Decimal:
        """Calculate total revenue from transactions."""
        transactions = await self.transaction_repository.get_all(active_only=True)
        total = sum(transaction.total_amount for transaction in transactions)
        return total
    
    async def _calculate_total_customers(self) -> Decimal:
        """Calculate total number of customers."""
        customers = await self.customer_repository.get_all(active_only=True)
        return Decimal(str(len(customers)))
    
    async def _calculate_inventory_utilization(self) -> Decimal:
        """Calculate inventory utilization percentage."""
        inventory_units = await self.inventory_unit_repository.get_all(active_only=True)
        if not inventory_units:
            return Decimal("0")
        
        rented_units = len([unit for unit in inventory_units if unit.is_rented()])
        total_units = len(inventory_units)
        
        utilization = (rented_units / total_units) * 100
        return Decimal(str(utilization)).quantize(Decimal('0.01'))
    
    async def _calculate_return_rate(self) -> Decimal:
        """Calculate return rate percentage."""
        returns = await self.rental_return_repository.get_all(active_only=True)
        transactions = await self.transaction_repository.get_all(active_only=True)
        
        if not transactions:
            return Decimal("0")
        
        rental_transactions = [t for t in transactions if t.is_rental()]
        if not rental_transactions:
            return Decimal("0")
        
        return_rate = (len(returns) / len(rental_transactions)) * 100
        return Decimal(str(return_rate)).quantize(Decimal('0.01'))
    
    async def _update_or_create_metric(
        self, 
        metric_name: str, 
        metric_type: MetricType, 
        category: str, 
        value: Decimal,
        unit: Optional[str] = None
    ) -> BusinessMetric:
        """Update existing metric or create new one."""
        existing_metric = await self.metric_repository.get_by_name(metric_name)
        
        if existing_metric:
            existing_metric.update_value(value)
            await self.session.commit()
            await self.session.refresh(existing_metric)
            return existing_metric
        else:
            metric_data = BusinessMetricCreate(
                metric_name=metric_name,
                metric_type=metric_type,
                category=category,
                current_value=value,
                unit=unit
            )
            return await self.metric_repository.create(metric_data)