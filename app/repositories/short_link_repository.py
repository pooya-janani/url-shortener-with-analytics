from datetime import datetime

from sqlalchemy.orm import Session

from app import models


def short_code_exists(db: Session, short_code: str) -> bool:
    existing_code = (
        db.query(models.ShortLink)
        .filter(models.ShortLink.short_code == short_code)
        .first()
    )
    return existing_code is not None


def get_short_link_by_code(db: Session, short_code: str):
    return (
        db.query(models.ShortLink)
        .filter(models.ShortLink.short_code == short_code)
        .first()
    )


def create_short_link(
    db: Session,
    user_id: int,
    original_url: str,
    short_code: str,
    password_hash: str | None = None,
    expires_at: datetime | None = None,
    redirect_type: int = 302,
):
    new_short_link = models.ShortLink(
        user_id=user_id,
        original_url=original_url,
        short_code=short_code,
        password_hash=password_hash,
        expires_at=expires_at,
        redirect_type=redirect_type,
    )
    db.add(new_short_link)
    db.commit()
    db.refresh(new_short_link)
    return new_short_link