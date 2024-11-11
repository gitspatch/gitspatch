import hashlib
import hmac
import secrets


def get_token_hash(token: str, *, secret: str) -> str:
    hash = hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256)
    return hash.hexdigest()


def generate_token(*, secret: str) -> tuple[str, str]:
    """
    Generate a token suitable for sensitive values
    like authorization codes or refresh tokens.

    Returns both the actual value and its HMAC-SHA256 hash.
    Only the latter shall be stored in database.
    """
    token = secrets.token_urlsafe()
    return token, get_token_hash(token, secret=secret)
