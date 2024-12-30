from sqlalchemy import select

from gitspatch.models import User

from ._base import Repository


class UserRepository(Repository[User]):
    model = User

    async def get_by_github_account_id(self, github_account_id: str) -> User | None:
        statement = select(User).where(User.github_account_id == github_account_id)
        return await self.get_one_or_none(statement)

    async def get_by_customer_id(self, customer_id: str) -> User | None:
        statement = select(User).where(User.customer_id == customer_id)
        return await self.get_one_or_none(statement)
