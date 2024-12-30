import zlib

from gitspatch.core.crypto import generate_token
from gitspatch.core.settings import Settings

PREFIX = "test_"


def base62decode(encoded: str) -> bytes:
    characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base = len(characters)
    decoded = 0
    for character in encoded:
        decoded = decoded * base + characters.index(character)
    return decoded.to_bytes((decoded.bit_length() + 7) // 8, byteorder="big")


def test_generate_token(settings: Settings) -> None:
    token, _ = generate_token(prefix=PREFIX, secret=settings.secret)

    assert token.startswith(PREFIX)
    unprefixed_token = token[len(PREFIX) :]
    checksum = unprefixed_token[-6:]
    token_value = unprefixed_token[:-6]

    decoded_checksum = int.from_bytes(base62decode(checksum))
    assert decoded_checksum == zlib.crc32(token_value.encode("utf-8")) & 0xFFFFFFFF
