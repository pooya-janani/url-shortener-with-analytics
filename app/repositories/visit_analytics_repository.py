from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models

def create_visit(db: Session, short_code: str, ip: str, user_agent: str, referrer: str = None,
                 country: str = None, city: str = None, device_type: str = None):
    """
    Create a new VisitAnalytics record in the database using the short_code to resolve short_link_id
    """
    # Resolve short_link_id from short_code
    short_link = db.query(models.ShortLink).filter(models.ShortLink.short_code == short_code).first()
    if not short_link:
        return None

    new_record = models.VisitAnalytics(
        short_link_id=short_link.id,
        ip=ip,
        user_agent=user_agent,
        referrer=referrer,
        country=country,
        city=city,
        device_type=device_type
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


def get_visits_for_link(db: Session, short_code: str):
    """Return all VisitAnalytics records for a given short_code"""
    return (db.query(models.VisitAnalytics)
            .join(models.ShortLink)
            .filter(models.ShortLink.short_code == short_code)
            ).all()


def get_visits_by_day(db: Session, short_code: str, day: datetime):
    """Return VisitAnalytics records for a given short_code filtered by day"""
    return (db.query(models.VisitAnalytics)
            .join(models.ShortLink)
            .filter(
                models.ShortLink.short_code == short_code,
                func.date(models.VisitAnalytics.timestamp) == day.date()
            )).all()


def get_visits_by_country(db: Session, short_code: str, country: str):
    """Return VisitAnalytics records for a given short_code filtered by country"""
    return (db.query(models.VisitAnalytics)
            .join(models.ShortLink)
            .filter(
                models.ShortLink.short_code == short_code,
                models.VisitAnalytics.country == country
            )).all()


def get_visits_by_device_type(db: Session, short_code: str, device_type: str):
    """Return VisitAnalytics records for a given short_code filtered by device type"""
    return (db.query(models.VisitAnalytics)
            .join(models.ShortLink)
            .filter(
                models.ShortLink.short_code == short_code,
                models.VisitAnalytics.device_type == device_type
            )).all()