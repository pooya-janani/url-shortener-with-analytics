from sqlalchemy.orm import Session

from app import models


def get_user_by_email(db: Session, email: str):
    return (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )


def get_user_by_id(db: Session, user_id: int):
    return (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )


def create_user(db: Session, email: str, hashed_password: str):
    new_user = models.User(
        email=email,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user