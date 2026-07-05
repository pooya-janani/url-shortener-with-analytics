from app.celery_app import celery
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import SessionLocal
from app.repositories.short_link_repository import get_short_link_by_code, create_short_link
from app.models import ShortLink
import os
import redis

r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), decode_responses=True)


@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def flush_clicks_to_db(self, short_code: str):
    """
    Flush click counts from Redis to PostgreSQL safely and atomically.
    - Uses GETSET to read and reset Redis counter atomically
    - Rolls back DB transaction if commit fails
    - Retries automatically on temporary failure
    """
    db: Session = SessionLocal()
    try:
        count_key = f"clicks:{short_code}"

        # Atomic read + reset
        clicks = r.getset(count_key, 0)
        if clicks and int(clicks) > 0:
            link = get_short_link_by_code(db, short_code)
            if link:
                link.click_count += int(clicks)
                link.last_clicked_at = datetime.utcnow()
                try:
                    db.commit()
                except SQLAlchemyError as e:
                    db.rollback()  # undo partial changes
                    # Push clicks back to Redis to avoid loss
                    r.incrby(count_key, int(clicks))
                    # Retry the task
                    self.retry(exc=e)
    finally:
        db.close()