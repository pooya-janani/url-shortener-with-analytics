import secrets

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def generate_short_code(length: int = 7) -> str:
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))