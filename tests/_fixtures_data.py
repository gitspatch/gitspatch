from typing import TypedDict, TypeVar

from gitspatch.core.database import AsyncSession
from gitspatch.models import Base, User

M = TypeVar("M", bound=Base)


async def create_data_fixture(session: AsyncSession, object: M) -> M:
    session.add(object)
    await session.flush()
    return object


class FixturesData(TypedDict):
    users: dict[str, User]


fixtures_data_definitions: FixturesData = {
    "users": {
        "user1": User(
            email="user1@example.com",
            github_account_id="user1_github_account_id",
            _github_token={"access_token": "user1_access_token"},
        )
    }
}
