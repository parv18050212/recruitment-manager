from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Initialize Celery
celery_app = Celery(
    "recruitment_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.agent_orchestrator',
        'app.tasks.periodic_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    # Autonomous agent loop - runs every 5 minutes
    'autonomous-agent-loop': {
        'task': 'app.tasks.agent_orchestrator.autonomous_agent_loop',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    
    # Process new candidates - runs every 10 minutes
    'process-new-candidates': {
        'task': 'app.tasks.periodic_tasks.process_new_candidates',
        'schedule': crontab(minute='*/10'),
    },
    
    # Generate daily reports - runs at 9 AM daily
    'generate-daily-report': {
        'task': 'app.tasks.periodic_tasks.generate_daily_report',
        'schedule': crontab(hour=9, minute=0),
    },
    
    # Cleanup old logs - runs weekly
    'cleanup-old-logs': {
        'task': 'app.tasks.periodic_tasks.cleanup_old_logs',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2 AM
    },
}