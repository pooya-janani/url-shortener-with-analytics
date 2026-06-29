from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.repositories import api_key_repository, user_repository
from app.services.security import (
    generate_api_key,
    get_api_key_prefix,
    hash_api_key,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["api-keys"],
)


@router.post("/users/{user_id}/api-keys", response_model=schemas.ApiKeyResponse)
def create_api_key_for_user(user_id: int, db: Session = Depends(get_db)):
    user = user_repository.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    raw_api_key = generate_api_key()
    key_hash = hash_api_key(raw_api_key)
    prefix = get_api_key_prefix(raw_api_key)

    new_api_key = api_key_repository.create_api_key(
        db=db,
        user_id=user.id,
        key_hash=key_hash,
        prefix=prefix,
    )

    return {
        "id": new_api_key.id,
        "prefix": new_api_key.prefix,
        "api_key": raw_api_key,
        "created_at": new_api_key.created_at,
    }