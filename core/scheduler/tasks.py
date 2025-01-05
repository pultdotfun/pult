from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from core.pult.processor import PULTProcessor
from core.websocket.handler import WebSocketManager
from models.user import User
from models.engagement import Engagement
from core.logger import log_info, log_error
from core.monitoring.metrics import BACKGROUND_TASKS, PROCESSING_TIME
import time

class TaskScheduler:
    def __init__(self, db: Session, websocket_manager: WebSocketManager):
        self.scheduler = AsyncIOScheduler()
        self.db = db
        self.websocket_manager = websocket_manager
        self.pult_processor = PULTProcessor(db)
        
    def start(self):
        """Start the scheduler"""
        # Schedule PULT updates every hour
        self.scheduler.add_job(
            self.update_pult_scores,
            CronTrigger(hour='*'),  # Every hour
            id='pult_updates'
        )
        
        # Schedule data cleanup daily
        self.scheduler.add_job(
            self.cleanup_old_data,
            CronTrigger(hour=0),  # Midnight
            id='data_cleanup'
        )
        
        # Schedule analytics aggregation
        self.scheduler.add_job(
            self.aggregate_analytics,
            CronTrigger(minute='*/15'),  # Every 15 minutes
            id='analytics_aggregation'
        )
        
        self.scheduler.start()
        log_info("Task scheduler started")
        
    async def update_pult_scores(self):
        """Update PULT scores for all users"""
        try:
            start_time = time.time()
            users = self.db.query(User).all()
            
            for user in users:
                try:
                    score = self.pult_processor.process_user_data(user.id)
                    await self.websocket_manager.send_update(
                        user.id,
                        {
                            "type": "score_update",
                            "score": score,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    BACKGROUND_TASKS.labels(
                        task_type="pult_update",
                        status="success"
                    ).inc()
                except Exception as e:
                    log_error(e, f"Error updating PULT score for user {user.id}")
                    BACKGROUND_TASKS.labels(
                        task_type="pult_update",
                        status="error"
                    ).inc()
            
            PROCESSING_TIME.labels(task_type="pult_update").observe(
                time.time() - start_time
            )
            
        except Exception as e:
            log_error(e, "Error in PULT score update job")
    
    async def cleanup_old_data(self):
        """Clean up old engagement data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            self.db.query(Engagement).filter(
                Engagement.created_at < cutoff_date
            ).delete()
            self.db.commit()
            
            BACKGROUND_TASKS.labels(
                task_type="cleanup",
                status="success"
            ).inc()
            
        except Exception as e:
            log_error(e, "Error in data cleanup job")
            BACKGROUND_TASKS.labels(
                task_type="cleanup",
                status="error"
            ).inc()
    
    async def aggregate_analytics(self):
        """Aggregate analytics data"""
        try:
            start_time = time.time()
            # Aggregate engagement data
            analytics = self.db.query(
                Engagement.engagement_type,
                func.count(Engagement.id)
            ).group_by(
                Engagement.engagement_type
            ).all()
            
            # Cache results
            await cache.set(
                "analytics_summary",
                {
                    "data": dict(analytics),
                    "updated_at": datetime.utcnow().isoformat()
                },
                expire_minutes=15
            )
            
            PROCESSING_TIME.labels(task_type="analytics").observe(
                time.time() - start_time
            )
            
        except Exception as e:
            log_error(e, "Error in analytics aggregation job") 