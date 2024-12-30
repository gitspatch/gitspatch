import hashlib
import hmac
import secrets
import string
import zlib


def get_token_hash(token: str, *, secret: str) -> str:
    hash = hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256)
    return hash.hexdigest()


def _crc32_to_base62(number: int) -> str:
    characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base = len(characters)
    encoded = ""
    while number:
        number, remainder = divmod(number, base)
        encoded = characters[remainder] + encoded
    return encoded.zfill(6)  # Ensure the checksum is 6 characters long


def generate_token(*, prefix: str, secret: str) -> tuple[str, str]:
    """
    Generate a token suitable for sensitive values
    like authorization codes or refresh tokens.

    Returns both the actual value and its HMAC-SHA256 hash.
    Only the latter shall be stored in database.
    """
    # Generate a high entropy random token
    token = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
    )

    # Calculate a 32-bit CRC checksum
    checksum = zlib.crc32(token.encode("utf-8")) & 0xFFFFFFFF
    checksum_base62 = _crc32_to_base62(checksum)

    # Concatenate the prefix, token, and checksum
    full_token = f"{prefix}{token}{checksum_base62}"

    return full_token, get_token_hash(full_token, secret=secret)
