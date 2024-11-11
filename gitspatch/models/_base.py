from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

TABLE_PREFIX = "gitspatch_"


def get_prefixed_tablename(tablename: str) -> str:
    return f"{TABLE_PREFIX}{tablename}"


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )

    def __init_subclass__(cls) -> None:
        cls.__tablename__ = get_prefixed_tablename(cls.__tablename__)
        super().__init_subclass__()
