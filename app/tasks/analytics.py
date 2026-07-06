from app.celery_app import celery
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.repositories.visit_analytics_repository import create_visit


@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def record_visit_analytics(self, short_code: str, ip: str, user_agent: str, referrer: str = None,
                           country: str = None, city: str = None, device_type: str = None):
    """
    Celery task to asynchronously record a visit to VisitAnalytics.
    """
    db: Session = SessionLocal()
    try:
        create_visit(
            db=db,
            short_code=short_code,
            ip=ip,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            city=city,
            device_type=device_type
        )
    except Exception as e:
        db.rollback()
        # Retry task automatically in case of temporary DB issues
        self.retry(exc=e)
    finally:
        db.close()