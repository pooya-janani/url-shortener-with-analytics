import hashlib
import hmac
import secrets

from passlib.context import CryptContext

from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    token = secrets.token_urlsafe(32)
    return f"usk_{token}"


def hash_api_key(api_key: str) -> str:
    return hmac.new(
        settings.API_KEY_HASH_SECRET.encode("utf-8"),
        api_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    calculated_hash = hash_api_key(plain_api_key)
    return hmac.compare_digest(calculated_hash, hashed_api_key)


def get_api_key_prefix(api_key: str) -> str:
    return api_key[:12]