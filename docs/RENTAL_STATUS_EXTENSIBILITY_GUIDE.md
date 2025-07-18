# Rental Status Feature - Extensibility & Future Enhancements Guide

## Overview

The rental status feature has been architected with extensibility as a core principle. This document details the extensible design patterns, potential enhancements, and how to implement additional features building on the existing foundation.

## 🏗️ Extensible Architecture Foundation

### 1. **Modular Service Architecture**

#### Status Calculator Service
**File**: `app/modules/transactions/services/rental_status_calculator.py`

**Extensibility Features**:
- **Pluggable Business Rules**: Status calculation logic is isolated and can be enhanced
- **Multiple Status Types**: Easy to add new status categories (e.g., maintenance, inspection)
- **Custom Date Logic**: Configurable date calculations for different business scenarios
- **Multi-tenant Support**: Ready for tenant-specific status rules

**Extension Points**:
```python
# Example: Custom status calculation rules
class CustomRentalStatusCalculator(RentalStatusCalculator):
    async def calculate_line_item_status(self, line, as_of_date=None):
        # Add custom business logic
        if self._is_maintenance_required(line):
            return LineItemStatus.MAINTENANCE_REQUIRED
        
        # Call parent logic for standard cases
        return await super().calculate_line_item_status(line, as_of_date)
    
    def _is_maintenance_required(self, line):
        # Custom maintenance logic
        return line.usage_hours > 1000
```

#### Status Update Service
**File**: `app/modules/transactions/services/rental_status_updater.py`

**Extensibility Features**:
- **Event-driven Updates**: Pluggable event handlers for different triggers
- **Custom Audit Trails**: Extensible metadata and logging capabilities
- **Batch Processing**: Configurable batch operations for large datasets
- **Integration Hooks**: Ready for external system notifications

**Extension Points**:
```python
# Example: Custom update workflows
class EnhancedRentalStatusUpdater(RentalStatusUpdater):
    async def update_transaction_status(self, transaction_id, **kwargs):
        # Pre-update hooks
        await self._send_notification(transaction_id)
        await self._update_external_systems(transaction_id)
        
        # Standard update
        result = await super().update_transaction_status(transaction_id, **kwargs)
        
        # Post-update hooks
        await self._trigger_workflows(transaction_id, result)
        
        return result
```

### 2. **Flexible Data Model**

#### RentalStatusLog Model
**Extensibility Features**:
- **JSON Metadata Field**: Store arbitrary context data
- **Flexible Change Reasons**: Enum easily extensible for new reasons
- **Multi-entity Support**: Works with transactions, line items, and future entities
- **Audit Trail Ready**: Complete context preservation for compliance

**Extension Examples**:
```python
# New status change reasons
class RentalStatusChangeReason(PyEnum):
    # Existing reasons...
    MAINTENANCE_SCHEDULED = "MAINTENANCE_SCHEDULED"
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST" 
    INSURANCE_CLAIM = "INSURANCE_CLAIM"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    WEATHER_DELAY = "WEATHER_DELAY"

# Enhanced metadata examples
metadata_examples = {
    "maintenance": {
        "maintenance_type": "preventive",
        "scheduled_date": "2025-02-01",
        "technician_id": "tech_123",
        "estimated_duration": "4 hours"
    },
    "customer_request": {
        "request_type": "extension",
        "customer_reason": "project delayed",
        "approved_by": "manager_456",
        "new_return_date": "2025-02-15"
    },
    "quality_issue": {
        "issue_type": "damage",
        "severity": "minor",
        "photos": ["photo1.jpg", "photo2.jpg"],
        "inspection_notes": "Small scratch on surface"
    }
}
```

### 3. **Configurable Scheduler System**

#### Task Scheduler Service
**File**: `app/core/scheduler.py`

**Extensibility Features**:
- **Pluggable Job Types**: Easy to add new scheduled operations
- **Configurable Timing**: Database-driven scheduling configuration
- **Error Recovery**: Built-in retry and recovery mechanisms
- **Monitoring Ready**: Complete job execution tracking

**Extension Examples**:
```python
# Example: Custom scheduled tasks
async def customer_notification_job():
    """Send automated notifications to customers."""
    # Implementation for customer alerts
    pass

async def maintenance_scheduling_job():
    """Schedule preventive maintenance for rental items."""
    # Implementation for maintenance scheduling
    pass

# Register custom jobs
await scheduler.add_job(
    func=customer_notification_job,
    trigger=CronTrigger(hour=9, minute=0),  # Daily at 9 AM
    id='customer_notifications',
    name='Daily Customer Notifications'
)
```

## 🚀 Future Enhancement Opportunities

### 1. **Advanced Status Types**

#### Equipment-Specific Statuses
```python
class EquipmentStatus(PyEnum):
    """Equipment-specific status types."""
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    MAINTENANCE = "MAINTENANCE"
    REPAIR = "REPAIR"
    INSPECTION = "INSPECTION"
    QUARANTINE = "QUARANTINE"
    RETIRED = "RETIRED"

class LocationStatus(PyEnum):
    """Location-specific status types."""
    ON_SITE = "ON_SITE"
    IN_TRANSIT = "IN_TRANSIT"
    AT_DEPOT = "AT_DEPOT"
    LOST = "LOST"
    RECOVERED = "RECOVERED"
```

#### Multi-Dimensional Status Tracking
```python
class RentalStatusMatrix:
    """Multi-dimensional status tracking."""
    
    def __init__(self):
        self.rental_status = None      # Business rental status
        self.equipment_status = None   # Physical equipment status
        self.location_status = None    # Geographic/logistics status
        self.payment_status = None     # Financial status
        self.compliance_status = None  # Regulatory/safety status
    
    def get_overall_status(self):
        """Calculate overall status from multiple dimensions."""
        # Complex logic to determine primary status
        pass
```

### 2. **Predictive Analytics Integration**

#### ML-Powered Status Prediction
```python
class RentalStatusPredictor:
    """Machine learning-powered status prediction."""
    
    async def predict_late_returns(self, days_ahead=7):
        """Predict which rentals are likely to be returned late."""
        # ML model implementation
        pass
    
    async def predict_maintenance_needs(self, equipment_id):
        """Predict when equipment will need maintenance."""
        # Predictive maintenance logic
        pass
    
    async def predict_demand_patterns(self, item_category):
        """Predict future rental demand patterns."""
        # Demand forecasting logic
        pass
```

#### Risk Assessment Engine
```python
class RentalRiskAssessment:
    """Risk assessment for rental transactions."""
    
    async def calculate_default_risk(self, customer_id, transaction_value):
        """Calculate probability of payment default."""
        pass
    
    async def assess_damage_risk(self, item_id, customer_history):
        """Assess likelihood of equipment damage."""
        pass
    
    async def evaluate_late_return_risk(self, rental_conditions):
        """Evaluate risk of late return."""
        pass
```

### 3. **Enhanced Notification System**

#### Multi-Channel Notifications
```python
class NotificationService:
    """Multi-channel notification system."""
    
    async def send_status_change_notification(self, transaction_id, old_status, new_status):
        """Send notifications via multiple channels."""
        
        # Email notifications
        await self._send_email_notification(transaction_id, old_status, new_status)
        
        # SMS notifications
        await self._send_sms_notification(transaction_id, old_status, new_status)
        
        # Push notifications
        await self._send_push_notification(transaction_id, old_status, new_status)
        
        # Webhook notifications
        await self._send_webhook_notification(transaction_id, old_status, new_status)
    
    async def schedule_reminder_notifications(self, transaction_id):
        """Schedule automated reminder notifications."""
        # Implementation for reminder scheduling
        pass
```

#### Smart Notification Rules
```python
class NotificationRuleEngine:
    """Rule-based notification system."""
    
    def __init__(self):
        self.rules = [
            {
                "condition": "status == 'LATE' and days_overdue > 3",
                "action": "send_urgent_notification",
                "channels": ["email", "sms"],
                "escalation": True
            },
            {
                "condition": "status == 'PARTIAL_RETURN' and customer_tier == 'premium'",
                "action": "send_personalized_follow_up",
                "channels": ["email", "phone_call"],
                "priority": "high"
            }
        ]
    
    async def evaluate_rules(self, transaction_id, status_change):
        """Evaluate notification rules and trigger appropriate actions."""
        pass
```

### 4. **Advanced Reporting & Analytics**

#### Dynamic Dashboard System
```python
class RentalStatusDashboard:
    """Dynamic dashboard for rental status analytics."""
    
    async def get_real_time_metrics(self):
        """Get real-time rental status metrics."""
        return {
            "active_rentals": await self._count_active_rentals(),
            "overdue_rentals": await self._count_overdue_rentals(),
            "revenue_at_risk": await self._calculate_revenue_at_risk(),
            "avg_return_time": await self._calculate_avg_return_time(),
            "customer_satisfaction": await self._get_satisfaction_scores()
        }
    
    async def generate_trend_analysis(self, period_days=30):
        """Generate trend analysis for rental patterns."""
        pass
    
    async def create_custom_report(self, report_config):
        """Generate custom reports based on configuration."""
        pass
```

#### Business Intelligence Integration
```python
class RentalStatusBI:
    """Business intelligence integration."""
    
    async def export_to_data_warehouse(self, start_date, end_date):
        """Export status data to data warehouse."""
        pass
    
    async def generate_executive_summary(self, period):
        """Generate executive summary report."""
        pass
    
    async def create_kpi_dashboard(self, kpis):
        """Create KPI dashboard for management."""
        pass
```

### 5. **Integration & API Extensions**

#### Webhook System
```python
class RentalStatusWebhooks:
    """Webhook system for external integrations."""
    
    async def register_webhook(self, url, events, authentication):
        """Register webhook for status events."""
        pass
    
    async def trigger_webhook(self, event_type, transaction_id, payload):
        """Trigger webhook for status change events."""
        pass
    
    def get_supported_events(self):
        return [
            "status.changed",
            "rental.overdue",
            "rental.returned",
            "rental.extended",
            "payment.due"
        ]
```

#### Third-Party Integrations
```python
class ExternalSystemIntegration:
    """Integration with external systems."""
    
    async def sync_with_accounting_system(self, transaction_id):
        """Sync rental status with accounting system."""
        pass
    
    async def update_crm_system(self, customer_id, rental_status):
        """Update customer status in CRM system."""
        pass
    
    async def integrate_with_telematics(self, equipment_id):
        """Integrate with equipment telematics system."""
        pass
```

### 6. **Mobile & Field Operations**

#### Mobile API Extensions
```python
class MobileRentalStatusAPI:
    """Mobile-optimized API endpoints."""
    
    @router.get("/mobile/rentals/nearby")
    async def get_nearby_rentals(self, location: GeoLocation):
        """Get rentals near current location."""
        pass
    
    @router.post("/mobile/rentals/{id}/status/field-update")
    async def field_status_update(self, rental_id: UUID, field_data: FieldStatusUpdate):
        """Update rental status from field operations."""
        pass
    
    @router.get("/mobile/rentals/offline-sync")
    async def get_offline_sync_data(self):
        """Get data for offline mobile operations."""
        pass
```

#### Offline Capability
```python
class OfflineRentalStatus:
    """Offline-capable status management."""
    
    async def queue_status_update(self, update_data):
        """Queue status update for offline processing."""
        pass
    
    async def sync_offline_changes(self, offline_updates):
        """Sync offline changes when connection restored."""
        pass
    
    async def resolve_conflicts(self, conflicts):
        """Resolve conflicts between offline and online data."""
        pass
```

## 🔧 Implementation Patterns for Extensions

### 1. **Service Extension Pattern**

```python
# Base service
class BaseRentalStatusService:
    def __init__(self, session):
        self.session = session
    
    async def calculate_status(self, transaction_id):
        # Base implementation
        pass

# Extended service
class EnhancedRentalStatusService(BaseRentalStatusService):
    def __init__(self, session, ml_service, notification_service):
        super().__init__(session)
        self.ml_service = ml_service
        self.notification_service = notification_service
    
    async def calculate_status(self, transaction_id):
        # Enhanced implementation with ML and notifications
        base_status = await super().calculate_status(transaction_id)
        predicted_issues = await self.ml_service.predict_issues(transaction_id)
        
        if predicted_issues:
            await self.notification_service.send_proactive_alert(transaction_id)
        
        return base_status
```

### 2. **Plugin Architecture Pattern**

```python
class RentalStatusPlugin:
    """Base class for rental status plugins."""
    
    def get_name(self) -> str:
        raise NotImplementedError
    
    async def on_status_change(self, transaction_id, old_status, new_status):
        """Hook called when status changes."""
        pass
    
    async def calculate_custom_status(self, transaction_data):
        """Calculate custom status if applicable."""
        return None

class MaintenancePlugin(RentalStatusPlugin):
    def get_name(self) -> str:
        return "maintenance_tracker"
    
    async def on_status_change(self, transaction_id, old_status, new_status):
        if new_status == "RETURNED":
            await self._schedule_maintenance_check(transaction_id)

# Plugin registry
class RentalStatusPluginRegistry:
    def __init__(self):
        self.plugins = []
    
    def register_plugin(self, plugin: RentalStatusPlugin):
        self.plugins.append(plugin)
    
    async def notify_status_change(self, transaction_id, old_status, new_status):
        for plugin in self.plugins:
            await plugin.on_status_change(transaction_id, old_status, new_status)
```

### 3. **Configuration-Driven Extensions**

```python
class RentalStatusConfiguration:
    """Configuration-driven status behavior."""
    
    def __init__(self):
        self.status_rules = {}
        self.notification_rules = {}
        self.integration_settings = {}
    
    def load_from_database(self):
        """Load configuration from database."""
        pass
    
    def get_status_calculation_rules(self, rule_type):
        """Get status calculation rules for specific type."""
        return self.status_rules.get(rule_type, {})
    
    def get_notification_settings(self, event_type):
        """Get notification settings for specific event."""
        return self.notification_rules.get(event_type, {})

# Example configuration
status_config = {
    "late_threshold_hours": 24,
    "grace_period_days": 1,
    "escalation_rules": [
        {"days_overdue": 1, "action": "send_reminder"},
        {"days_overdue": 3, "action": "send_urgent_notice"},
        {"days_overdue": 7, "action": "escalate_to_manager"}
    ],
    "custom_statuses": {
        "seasonal_equipment": {
            "winter_storage": "WINTER_STORAGE",
            "summer_maintenance": "SUMMER_MAINTENANCE"
        }
    }
}
```

## 📊 Performance & Scalability Extensions

### 1. **Caching Layer**

```python
class RentalStatusCache:
    """Redis-based caching for rental status."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_cached_status(self, transaction_id):
        """Get cached status calculation."""
        cache_key = f"rental_status:{transaction_id}"
        return await self.redis.get(cache_key)
    
    async def cache_status(self, transaction_id, status_data, ttl=300):
        """Cache status calculation result."""
        cache_key = f"rental_status:{transaction_id}"
        await self.redis.setex(cache_key, ttl, json.dumps(status_data))
    
    async def invalidate_cache(self, transaction_id):
        """Invalidate cached status."""
        cache_key = f"rental_status:{transaction_id}"
        await self.redis.delete(cache_key)
```

### 2. **Batch Processing Optimization**

```python
class OptimizedBatchProcessor:
    """Optimized batch processing for large datasets."""
    
    async def process_status_updates_in_chunks(self, transaction_ids, chunk_size=100):
        """Process status updates in optimized chunks."""
        
        for i in range(0, len(transaction_ids), chunk_size):
            chunk = transaction_ids[i:i + chunk_size]
            
            # Parallel processing within chunk
            tasks = [
                self._process_single_status(tid) 
                for tid in chunk
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle errors
            await self._handle_batch_results(chunk, results)
    
    async def _process_single_status(self, transaction_id):
        """Process single transaction status."""
        # Optimized single transaction processing
        pass
```

### 3. **Database Optimization**

```python
class RentalStatusQueryOptimizer:
    """Query optimization for rental status operations."""
    
    def get_optimized_status_query(self, filters):
        """Get optimized query for status retrieval."""
        
        # Use appropriate indexes and query patterns
        query = select(TransactionHeader).options(
            selectinload(TransactionHeader.transaction_lines),
            selectinload(TransactionHeader.rental_lifecycle)
        )
        
        # Add optimized filters
        if filters.get('overdue_only'):
            query = query.where(
                and_(
                    TransactionHeader.rental_end_date < date.today(),
                    TransactionHeader.current_rental_status.in_(['LATE', 'LATE_PARTIAL_RETURN'])
                )
            )
        
        return query
    
    def create_performance_indexes(self):
        """Create additional indexes for performance."""
        indexes = [
            "CREATE INDEX CONCURRENTLY idx_transaction_rental_end_status ON transaction_headers(rental_end_date, current_rental_status) WHERE transaction_type = 'RENTAL'",
            "CREATE INDEX CONCURRENTLY idx_status_log_changed_at_desc ON rental_status_logs(changed_at DESC)",
            "CREATE INDEX CONCURRENTLY idx_lifecycle_status_return_date ON rental_lifecycles(current_status, expected_return_date)"
        ]
        return indexes
```

## 🔮 Migration & Upgrade Patterns

### 1. **Feature Flags**

```python
class RentalStatusFeatureFlags:
    """Feature flags for gradual rollout of new features."""
    
    def __init__(self, config_service):
        self.config = config_service
    
    async def is_feature_enabled(self, feature_name, context=None):
        """Check if feature is enabled for context."""
        flag = await self.config.get_feature_flag(feature_name)
        
        if context and flag.get('percentage_rollout'):
            # Percentage-based rollout
            return self._calculate_rollout_eligibility(context, flag['percentage_rollout'])
        
        return flag.get('enabled', False)
    
    async def enable_predictive_analytics(self, transaction_id):
        """Check if predictive analytics should be used."""
        return await self.is_feature_enabled('predictive_analytics', {'transaction_id': transaction_id})
```

### 2. **Version Compatibility**

```python
class RentalStatusVersionManager:
    """Manage multiple versions of status calculation logic."""
    
    def __init__(self):
        self.calculators = {
            'v1': RentalStatusCalculatorV1,
            'v2': RentalStatusCalculatorV2,
            'v3': RentalStatusCalculatorV3
        }
    
    async def calculate_status(self, transaction_id, version='latest'):
        """Calculate status using specified version."""
        if version == 'latest':
            version = max(self.calculators.keys())
        
        calculator_class = self.calculators[version]
        calculator = calculator_class(self.session)
        
        return await calculator.calculate_transaction_status(transaction_id)
    
    async def migrate_status_calculations(self, from_version, to_version):
        """Migrate status calculations between versions."""
        # Implementation for version migration
        pass
```

## 📈 Monitoring & Observability Extensions

### 1. **Metrics Collection**

```python
class RentalStatusMetrics:
    """Comprehensive metrics collection."""
    
    def __init__(self, metrics_client):
        self.metrics = metrics_client
    
    async def record_status_calculation_time(self, calculation_time, transaction_count):
        """Record status calculation performance metrics."""
        self.metrics.histogram('rental_status_calculation_duration', calculation_time)
        self.metrics.gauge('rental_status_transactions_processed', transaction_count)
    
    async def record_status_change(self, old_status, new_status, reason):
        """Record status change metrics."""
        self.metrics.counter('rental_status_changes_total', 
                           tags={'old_status': old_status, 'new_status': new_status, 'reason': reason})
    
    async def record_batch_processing_stats(self, batch_size, success_count, failure_count):
        """Record batch processing statistics."""
        self.metrics.gauge('rental_status_batch_size', batch_size)
        self.metrics.gauge('rental_status_batch_success', success_count)
        self.metrics.gauge('rental_status_batch_failures', failure_count)
```

### 2. **Health Checks**

```python
class RentalStatusHealthCheck:
    """Comprehensive health checks for rental status system."""
    
    async def check_calculator_performance(self):
        """Check status calculator performance."""
        start_time = time.time()
        
        # Test calculation on sample data
        test_result = await self._run_test_calculation()
        
        calculation_time = time.time() - start_time
        
        return {
            'status': 'healthy' if calculation_time < 1.0 else 'degraded',
            'calculation_time': calculation_time,
            'test_passed': test_result is not None
        }
    
    async def check_scheduler_health(self):
        """Check task scheduler health."""
        return {
            'status': 'healthy',
            'jobs_registered': len(await self.scheduler.get_jobs()),
            'last_run_times': await self._get_last_run_times()
        }
    
    async def check_database_performance(self):
        """Check database performance for status operations."""
        # Test key queries and measure performance
        pass
```

This extensible architecture provides a solid foundation for future enhancements while maintaining backward compatibility and system stability. The modular design allows for incremental feature additions without disrupting existing functionality.