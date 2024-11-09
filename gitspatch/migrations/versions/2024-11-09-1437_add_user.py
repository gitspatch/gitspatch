"""Add User

Revision ID: 795a498d82f5
Revises:
Create Date: 2024-11-09 14:37:10.716083

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "795a498d82f5"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "gitspatch_user",
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("id", sa.CHAR(length=14), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gitspatch_user")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("gitspatch_user")
    # ### end Alembic commands ###
