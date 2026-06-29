from sqlalchemy.orm import Session

from app import models


def create_api_key(db: Session, user_id: int, key_hash: str, prefix: str):
    new_api_key = models.ApiKey(
        user_id=user_id,
        key_hash=key_hash,
        prefix=prefix,
    )
    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)
    return new_api_key


def get_active_api_key_by_prefix(db: Session, prefix: str):
    return (
        db.query(models.ApiKey)
        .filter(
            models.ApiKey.prefix == prefix,
            models.ApiKey.is_active == True,
        )
        .first()
    )