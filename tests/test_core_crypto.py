import zlib

from gitspatch.core.crypto import generate_token
from gitspatch.core.settings import Settings

PREFIX = "test_"


def _base62_to_crc32(encoded: str) -> int:
    characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base = len(characters)
    number = 0
    for char in encoded:
        number = number * base + characters.index(char)
    return number


def test_generate_token(i: int, settings: Settings) -> None:
    token, _ = generate_token(prefix=PREFIX, secret=settings.secret)

    assert token.startswith(PREFIX)
    unprefixed_token = token[len(PREFIX) :]
    checksum = unprefixed_token[-6:]
    token_value = unprefixed_token[:-6]

    decoded_checksum = _base62_to_crc32(checksum)
    expected_checksum = zlib.crc32(token_value.encode("utf-8")) & 0xFFFFFFFF
    assert decoded_checksum == expected_checksum
