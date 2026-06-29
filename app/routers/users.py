from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.repositories import user_repository
from app.services.security import hash_password


router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)


@router.post("/", response_model=schemas.UserResponse)
def create_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = user_repository.get_user_by_email(db, user_data.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    hashed_password = hash_password(user_data.password)

    new_user = user_repository.create_user(
        db=db,
        email=user_data.email,
        hashed_password=hashed_password,
    )

    return new_user