"""
Task Scheduler Service for FastAPI Application

Integrates APScheduler with FastAPI to provide background task scheduling
for rental status updates and other maintenance tasks.
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional, Dict, Any, Callable, List
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.system.service import SystemService

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Application task scheduler using APScheduler.
    
    Provides background task scheduling capabilities for:
    - Daily rental status checks
    - System maintenance tasks
    - Data cleanup operations
    - Custom scheduled tasks
    """
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
        self._system_service: Optional[SystemService] = None
    
    async def initialize(self):
        """Initialize the scheduler with configuration from system settings."""
        if self.scheduler is not None:
            return
        
        # Configure APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': AsyncIOExecutor()
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'  # Will be updated from settings
        )
        
        # Add event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        
        logger.info("Task scheduler initialized")
    
    async def start(self):
        """Start the scheduler and register default jobs."""
        if not self.scheduler:
            await self.initialize()
        
        if self._running:
            return
        
        # Load configuration from system settings
        await self._load_configuration()
        
        # Register default jobs
        await self._register_default_jobs()
        
        # Start the scheduler
        self.scheduler.start()
        self._running = True
        
        logger.info("Task scheduler started")
    
    async def stop(self):
        """Stop the scheduler gracefully."""
        if self.scheduler and self._running:
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Task scheduler stopped")
    
    async def _load_configuration(self):
        """Load scheduler configuration from system settings."""
        try:
            async for session in get_session():
                self._system_service = SystemService(session)
                
                # Get timezone setting
                timezone = await self._system_service.get_setting_value('task_scheduler_timezone', 'UTC')
                
                # Update scheduler timezone
                if self.scheduler:
                    self.scheduler.configure(timezone=timezone)
                
                logger.info(f"Scheduler configured with timezone: {timezone}")
                break
                
        except Exception as e:
            logger.error(f"Failed to load scheduler configuration: {e}")
            # Continue with defaults
    
    async def _register_default_jobs(self):
        """Register default scheduled jobs."""
        if not self.scheduler:
            return
        
        try:
            async for session in get_session():
                system_service = SystemService(session)
                
                # Check if rental status checking is enabled
                status_check_enabled = await system_service.get_setting_value('rental_status_check_enabled', True)
                
                if status_check_enabled:
                    # Get the time to run the status check
                    check_time_str = await system_service.get_setting_value('rental_status_check_time', '00:00')
                    
                    try:
                        # Parse time string (HH:MM format)
                        hour, minute = map(int, check_time_str.split(':'))
                        
                        # Add daily rental status check job
                        self.scheduler.add_job(
                            func=self._rental_status_check_job,
                            trigger=CronTrigger(hour=hour, minute=minute),
                            id='daily_rental_status_check',
                            name='Daily Rental Status Check',
                            replace_existing=True
                        )
                        
                        logger.info(f"Scheduled daily rental status check at {check_time_str}")
                        
                    except ValueError:
                        logger.error(f"Invalid time format in setting: {check_time_str}")
                
                # Add weekly cleanup job (Sundays at 2 AM)
                self.scheduler.add_job(
                    func=self._weekly_cleanup_job,
                    trigger=CronTrigger(day_of_week=6, hour=2, minute=0),  # Sunday at 2 AM
                    id='weekly_cleanup',
                    name='Weekly System Cleanup',
                    replace_existing=True
                )
                
                logger.info("Default scheduled jobs registered")
                break
                
        except Exception as e:
            logger.error(f"Failed to register default jobs: {e}")
    
    async def _rental_status_check_job(self):
        """Daily job to check and update rental statuses."""
        logger.info("Starting daily rental status check job")
        
        try:
            async for session in get_session():
                from app.modules.transactions.services.rental_status_updater import RentalStatusUpdater
                
                updater = RentalStatusUpdater(session)
                
                # Run batch update for all active rentals
                results = await updater.batch_update_overdue_statuses(
                    changed_by=None  # System change
                )
                
                logger.info(f"Daily rental status check completed: {results['successful_updates']} updates, {results['failed_updates']} failures")
                
                # Log to system audit
                if self._system_service:
                    await self._system_service.create_audit_log(
                        action='SCHEDULED_TASK',
                        entity_type='RentalStatusCheck',
                        audit_metadata={
                            'job_name': 'daily_rental_status_check',
                            'results': results
                        },
                        success=results['failed_updates'] == 0
                    )
                
                break
                
        except Exception as e:
            logger.error(f"Daily rental status check job failed: {e}")
            
            # Log error to system audit
            if self._system_service:
                try:
                    async for session in get_session():
                        system_service = SystemService(session)
                        await system_service.create_audit_log(
                            action='SCHEDULED_TASK',
                            entity_type='RentalStatusCheck',
                            audit_metadata={
                                'job_name': 'daily_rental_status_check',
                                'error': str(e)
                            },
                            success=False,
                            error_message=str(e)
                        )
                        break
                except:
                    pass  # Don't fail if audit logging fails
            
            raise
    
    async def _weekly_cleanup_job(self):
        """Weekly job for system maintenance and cleanup."""
        logger.info("Starting weekly cleanup job")
        
        try:
            async for session in get_session():
                system_service = SystemService(session)
                
                # Perform system maintenance
                maintenance_results = await system_service.perform_system_maintenance(
                    user_id=None  # System maintenance
                )
                
                # Clean up old rental status logs
                retention_days = await system_service.get_setting_value('rental_status_log_retention_days', 365)
                
                # TODO: Implement rental status log cleanup
                # This would be implemented when we add the cleanup method to the status updater
                
                logger.info(f"Weekly cleanup completed: {maintenance_results}")
                
                # Log to system audit
                await system_service.create_audit_log(
                    action='SCHEDULED_TASK',
                    entity_type='SystemMaintenance',
                    audit_metadata={
                        'job_name': 'weekly_cleanup',
                        'results': maintenance_results
                    },
                    success=True
                )
                
                break
                
        except Exception as e:
            logger.error(f"Weekly cleanup job failed: {e}")
            raise
    
    def _job_executed(self, event):
        """Handle job execution events."""
        logger.info(f"Job {event.job_id} executed successfully")
    
    def _job_error(self, event):
        """Handle job error events."""
        logger.error(f"Job {event.job_id} failed: {event.exception}")
    
    async def add_job(
        self,
        func: Callable,
        trigger,
        job_id: str,
        name: Optional[str] = None,
        **kwargs
    ):
        """Add a custom job to the scheduler."""
        if not self.scheduler:
            await self.initialize()
        
        if self.scheduler:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name or job_id,
                replace_existing=True,
                **kwargs
            )
            logger.info(f"Added job: {job_id}")
    
    async def remove_job(self, job_id: str):
        """Remove a job from the scheduler."""
        if self.scheduler and self._running:
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed job: {job_id}")
            except Exception as e:
                logger.error(f"Failed to remove job {job_id}: {e}")
    
    async def get_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs."""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return jobs
    
    async def trigger_job(self, job_id: str):
        """Manually trigger a job to run immediately."""
        if self.scheduler and self._running:
            try:
                job = self.scheduler.get_job(job_id)
                if job:
                    self.scheduler.modify_job(job_id, next_run_time=datetime.now())
                    logger.info(f"Triggered job: {job_id}")
                else:
                    raise ValueError(f"Job {job_id} not found")
            except Exception as e:
                logger.error(f"Failed to trigger job {job_id}: {e}")
                raise


# Global scheduler instance
task_scheduler = TaskScheduler()


@asynccontextmanager
async def scheduler_lifespan():
    """Context manager for scheduler lifecycle management."""
    try:
        await task_scheduler.start()
        yield task_scheduler
    finally:
        await task_scheduler.stop()


# Dependency for getting the scheduler in FastAPI routes
async def get_scheduler() -> TaskScheduler:
    """FastAPI dependency for getting the task scheduler."""
    return task_scheduler