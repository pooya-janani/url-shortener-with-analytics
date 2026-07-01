from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import api_key_repository
from app.services.security import get_api_key_prefix, verify_api_key

def get_current_user_from_api_key(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
    ):
    prefix = get_api_key_prefix(x_api_key)
    api_key_record = api_key_repository.get_active_api_key_by_prefix(
        db=db,
        prefix=prefix,
        )
    if api_key_record is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or missing API key",
            )
    is_valid = verify_api_key(x_api_key, api_key_record.key_hash)

    if not is_valid:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid or missing API key",
        )
    return api_key_record.user
    
