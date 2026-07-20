from celery import Celery
from celery.schedules import crontab
import json

from ..config import settings

# Create Celery app
celery_app = Celery(
    "multi_agent_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-tasks": {
            "task": "backend.services.tasks.cleanup_expired_tasks",
            "schedule": crontab(hour="*/6"),  # Every 6 hours
        },
        "update-agent-metrics": {
            "task": "backend.services.tasks.update_agent_metrics",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        "send-webhook-retries": {
            "task": "backend.services.tasks.retry_failed_webhooks",
            "schedule": crontab(minute="*/10"),  # Every 10 minutes
        },
    },
)


@celery_app.task(bind=True, max_retries=3)
def process_task_async(self, task_id: int):
    """Process a task asynchronously."""
    from ..database import SessionLocal
    from ..models.task import Task, TaskStatus
    from ..services.orchestrator import OrchestratorService
    
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": "Task not found"}
        
        # Update status
        task.status = TaskStatus.IN_PROGRESS.value
        db.commit()
        
        # Process with orchestrator
        orchestrator = OrchestratorService(db)
        result = orchestrator.process_task(task)
        
        return {"task_id": task_id, "result": result}
    except Exception as e:
        # Update task status on failure
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED.value
            task.error_message = str(e)
            db.commit()
        
        # Retry on transient errors
        self.retry(exc=e, countdown=60)
    finally:
        db.close()


@celery_app.task
def cleanup_expired_tasks():
    """Clean up expired and stale tasks."""
    from ..database import SessionLocal
    from ..models.task import Task, TaskStatus
    
    db = SessionLocal()
    try:
        # Find stale in-progress tasks (stuck for > 1 hour)
        from datetime import datetime, timedelta
        threshold = datetime.utcnow() - timedelta(hours=1)
        
        stale_tasks = db.query(Task).filter(
            Task.status == TaskStatus.IN_PROGRESS.value,
            Task.started_at < threshold
        ).all()
        
        for task in stale_tasks:
            task.status = TaskStatus.TIMEOUT.value
            task.error_message = "Task timed out"
        
        db.commit()
        return {"cleaned": len(stale_tasks)}
    finally:
        db.close()


@celery_app.task
def update_agent_metrics():
    """Update agent performance metrics."""
    from ..database import SessionLocal
    from ..models.agent import Agent, AgentMetric
    from sqlalchemy import func
    
    db = SessionLocal()
    try:
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        
        for agent in agents:
            # Calculate average task time
            if agent.completed_tasks_count > 0:
                avg_time = agent.total_processing_time / agent.completed_tasks_count
                agent.average_task_time = avg_time
            
            # Calculate health score based on success rate
            total_tasks = agent.completed_tasks_count + agent.failed_tasks_count
            if total_tasks > 0:
                success_rate = agent.completed_tasks_count / total_tasks
                agent.health_score = min(1.0, success_rate * 1.1)  # Slight bonus
            
            # Record metric
            metric = AgentMetric(
                agent_id=agent.id,
                metric_type="health_score",
                value=agent.health_score,
            )
            db.add(metric)
        
        db.commit()
        return {"updated": len(agents)}
    finally:
        db.close()


@celery_app.task
def retry_failed_webhooks():
    """Retry failed webhook deliveries."""
    from ..database import SessionLocal
    from ..models.user import Webhook
    
    db = SessionLocal()
    try:
        webhooks = db.query(Webhook).filter(
            Webhook.is_active == True,
            Webhook.failure_count > 0,
            Webhook.failure_count < 5
        ).all()
        
        # Reset failure count for retry
        for webhook in webhooks:
            webhook.failure_count = max(0, webhook.failure_count - 1)
        
        db.commit()
        return {"reset": len(webhooks)}
    finally:
        db.close()


@celery_app.task
def send_notification(user_id: int, title: str, message: str, data: dict = None):
    """Send notification to user (email, push, etc.)."""
    # Placeholder for notification service
    # Implement email, SMS, or push notifications here
    return {"user_id": user_id, "title": title, "sent": True}
