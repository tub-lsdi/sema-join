"""create tables for history

Revision ID: 2d8a1db4c906
Revises:
Create Date: 2025-11-02 14:38:00.507429

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2d8a1db4c906"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "table_entry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("columns", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "join_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("list_r_entry_id", sa.Integer(), nullable=False),
        sa.Column("list_s_entry_id", sa.Integer(), nullable=False),
        sa.Column("bridge_table_entry_id", sa.Integer(), nullable=False),
        sa.Column("result_entry_id", sa.Integer(), nullable=False),
        sa.Column("r_join_col", sa.String(length=64), nullable=False),
        sa.Column("s_join_col", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["bridge_table_entry_id"],
            ["table_entry.id"],
        ),
        sa.ForeignKeyConstraint(
            ["list_r_entry_id"],
            ["table_entry.id"],
        ),
        sa.ForeignKeyConstraint(
            ["list_s_entry_id"],
            ["table_entry.id"],
        ),
        sa.ForeignKeyConstraint(
            ["result_entry_id"],
            ["table_entry.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("join_history")
    op.drop_table("table_entry")
    # ### end Alembic commands ###
