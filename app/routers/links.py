from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_from_api_key, get_current_user_from_api_key_optional
from app.schemas import ShortLinkCreate, ShortLinkResponse
from app.services.short_code import generate_short_code
from app.repositories.short_link_repository import short_code_exists, create_short_link
from app.services.security import hash_password
from fastapi.responses import RedirectResponse
from app.services.cache import get_original_url_from_cache, refresh_hot_link, increment_click, r
from app.tasks.clicks import flush_clicks_to_db
from app.services.rate_limit import check_rate_limit
from app.tasks.analytics import record_visit_analytics
import logging

logger = logging.getLogger("redirect_logger")
logger.setLevel(logging.INFO)
logger.propagate = False

import sys
from logging import StreamHandler, Formatter

if not logger.hasHandlers():
    handler = StreamHandler(sys.stdout)  # send logs to stdout (docker console)
    handler.setLevel(logging.INFO)
    formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    
router = APIRouter(
    prefix="/api/v1/links",
    tags=["links"],
)


@router.post("/", response_model= ShortLinkResponse)
def create_short_link_router(
    short_link: ShortLinkCreate, 
    user= Depends(get_current_user_from_api_key),
    db: Session = Depends(get_db),
    ):
    if short_link.custom_alias is None:
        short_code = generate_short_code()
        while short_code_exists(
            db= db, 
            short_code= short_code
            ):
            short_code = generate_short_code()
    else:
        short_code = short_link.custom_alias
        if short_code_exists(
            db=db,
            short_code=short_code
        ):
            raise HTTPException(
                status_code= status.HTTP_409_CONFLICT,
                detail= "exists"
            )
    if short_link.password:
        hashed_password = hash_password(short_link.password)
    else:
        hashed_password = None
    
    db_obj =  create_short_link(
        db=db,
        user_id= user.id,
        original_url= str(short_link.original_url),
        short_code= short_code,
        password_hash= hashed_password,
        expires_at= short_link.expires_at,
        redirect_type= short_link.redirect_type
    )

    return {
        "id": db_obj.id,
        "original_url": db_obj.original_url,
        "short_code": db_obj.short_code,
        "short_url": f"http://localhost:8000/{db_obj.short_code}",
        "expires_at": db_obj.expires_at,
        "redirect_type": db_obj.redirect_type,
        "is_active": db_obj.is_active,
        "created_at": db_obj.created_at,
    }
    

@router.get("/{short_code}")
def redirect_func(
    short_code: str, 
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user_from_api_key_optional)
):
    ip = request.headers.get("X-Forwarded-For") or request.client.host
    logger.info(f"Redirect request: path={request.url.path}, ip={ip}, user={user}")

    # ---- Ignore asset requests or prefetches ----
    if request.url.path.endswith((".ico", ".png", ".svg", ".json", ".txt")):
        return Response(status_code=204)  # no content for assets

    # ---- Determine rate limiting key ----
    if user:
        key = f"user:{user.id}"
        is_authenticated = True
    else:
        key = f"ip:{request.client.host}"
        is_authenticated = False

    # Apply rate limiting
    check_rate_limit(key=key, is_authenticated=is_authenticated)

    # ---- Fetch original URL ----
    original_url = get_original_url_from_cache(short_code, db)
    if not original_url:
        raise HTTPException(status_code=404, detail="Link not found or expired")

    # ---- Record visit analytics asynchronously ----

    record_visit_analytics.delay(
        short_code=short_code,
        ip=ip,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer")
    )

    # ---- Hot link detection ----
    refresh_hot_link(short_code)

    # ---- Click tracking ----
    increment_click(short_code)
    flush_clicks_to_db.delay(short_code)

    # ---- Return redirect response ----
    return RedirectResponse(url=original_url)