from app.celery_app import celery
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repositories.visit_analytics_repository import create_visit
from app.services.user_agent import parse_user_agent
from app.services.geoip import get_location
from app.services.ip import anonymize_ip

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
        location = get_location(ip)
        safe_ip = anonymize_ip(ip)
        parsed = parse_user_agent(user_agent)

        create_visit(
            db=db,
            short_code=short_code,
            ip=safe_ip,
            user_agent=user_agent,
            browser=parsed["browser"],
            os=parsed["os"],
            device_type=parsed["device_type"],
            referrer=referrer,
            country=location["country"],
            city=location["city"],
        )

    except Exception as e:
        db.rollback()
        raise self.retry(exc=e)

    finally:
        db.close()