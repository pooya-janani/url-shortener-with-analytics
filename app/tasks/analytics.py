from app.celery_app import celery
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repositories.visit_analytics_repository import create_visit
from app.services.user_agent import parse_user_agent


@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def record_visit_analytics(
    self,
    short_code: str,
    ip: str,
    user_agent: str,
    referrer: str = None,
    country: str = None,
    city: str = None
):
    db: Session = SessionLocal()

    try:
        parsed = parse_user_agent(user_agent)

        create_visit(
            db=db,
            short_code=short_code,
            ip=ip,
            user_agent=user_agent,
            browser=parsed["browser"],
            os=parsed["os"],
            device_type=parsed["device_type"],
            referrer=referrer,
            country=country,
            city=city
        )

    except Exception as e:
        db.rollback()
        raise self.retry(exc=e)

    finally:
        db.close()