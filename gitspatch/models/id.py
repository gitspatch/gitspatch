import functools
import secrets
import string
from typing import ClassVar

from sqlalchemy import CHAR
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

RANDOM_LENGTH = 10
PREFIX_LENGTH = 3


class IDGenerator:
    # Exclude similar-looking characters like l, 1, I, 0, O
    ALPHABET = string.ascii_letters.replace("l", "").replace("I", "").replace(
        "O", ""
    ) + string.digits.replace("0", "")
    RANDOM_LENGTH = 10

    @classmethod
    def generate_id(cls, prefix: str) -> str:
        random_part = "".join(
            secrets.choice(cls.ALPHABET) for _ in range(cls.RANDOM_LENGTH)
        )
        return f"{prefix}_{random_part}"


class IDModel:
    __idprefix__: ClassVar[str]

    @declared_attr
    def id(cls) -> Mapped[str]:
        return mapped_column(
            CHAR(RANDOM_LENGTH + PREFIX_LENGTH + 1),
            primary_key=True,
            nullable=False,
            default=functools.partial(IDGenerator.generate_id, cls.__idprefix__),
        )
