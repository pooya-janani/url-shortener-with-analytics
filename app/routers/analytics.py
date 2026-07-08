# app/routers/analytics.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"]
)

# 1. Line chart: visits per day
@router.get("/{short_code}/daily")
def get_daily_visits(short_code: str, db: Session = Depends(get_db)):
    results = (
        db.query(
            func.date(models.VisitAnalytics.timestamp).label("visit_date"),
            func.count().label("visits_count")
        )
        .join(models.ShortLink)
        .filter(models.ShortLink.short_code == short_code)
        .group_by(func.date(models.VisitAnalytics.timestamp))
        .order_by(func.date(models.VisitAnalytics.timestamp).desc())
        .all()
    )
    return {
        "short_code": short_code,
        "daily_visits": [{"date": str(r.visit_date), "count": r.visits_count} for r in results]
    }


# 2. Geographic breakdown: visits by country
@router.get("/{short_code}/by-country")
def get_visits_by_country(short_code: str, db: Session = Depends(get_db)):
    results = (
        db.query(
            models.VisitAnalytics.country.label("country"),
            func.count().label("visits_count")
        )
        .join(models.ShortLink)
        .filter(models.ShortLink.short_code == short_code)
        .group_by(models.VisitAnalytics.country)
        .order_by(func.count().desc())
        .all()
    )
    return {
        "short_code": short_code,
        "visits_by_country": [{"country": r.country, "count": r.visits_count} for r in results]
    }


# 3. Top referrers
@router.get("/{short_code}/by-referrer")
def get_visits_by_referrer(short_code: str, db: Session = Depends(get_db)):
    results = (
        db.query(
            models.VisitAnalytics.referrer.label("referrer"),
            func.count().label("visits_count")
        )
        .join(models.ShortLink)
        .filter(models.ShortLink.short_code == short_code)
        .group_by(models.VisitAnalytics.referrer)
        .order_by(func.count().desc())
        .all()
    )
    return {
        "short_code": short_code,
        "visits_by_referrer": [{"referrer": r.referrer, "count": r.visits_count} for r in results]
    }


# 4. Top browsers
@router.get("/{short_code}/by-browser")
def get_visits_by_browser(short_code: str, db: Session = Depends(get_db)):
    results = (
        db.query(
            models.VisitAnalytics.browser.label("browser"),
            func.count().label("visits_count")
        )
        .join(models.ShortLink)
        .filter(models.ShortLink.short_code == short_code)
        .group_by(models.VisitAnalytics.browser)
        .order_by(func.count().desc())
        .all()
    )
    return {
        "short_code": short_code,
        "visits_by_browser": [{"browser": r.browser, "count": r.visits_count} for r in results]
    }


# 5. Multi-link comparison
@router.get("/multi")
def get_visits_multi(short_codes: str, db: Session = Depends(get_db)):
    """
    Example: /api/v1/analytics/multi?short_codes=abc123,xyz789
    Returns total visits per short link.
    """
    codes_list = [code.strip() for code in short_codes.split(",")]
    results = (
        db.query(
            models.ShortLink.short_code,
            func.count(models.VisitAnalytics.id).label("visits_count")
        )
        .join(models.VisitAnalytics)
        .filter(models.ShortLink.short_code.in_(codes_list))
        .group_by(models.ShortLink.short_code)
        .all()
    )
    return {
        "results": [{"short_code": r.short_code, "count": r.visits_count} for r in results]
    }