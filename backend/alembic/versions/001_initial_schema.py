from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = '001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with final schema."""

    # Create table_entry table with LONGTEXT for body column
    op.create_table(
        "table_entry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("body", mysql.LONGTEXT, nullable=False),
        sa.Column("columns", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create join_history table
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

    # Create uploaded_table table
    op.create_table(
        "uploaded_table",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "upload_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("body", mysql.LONGTEXT, nullable=False),
        sa.Column("columns", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("uploaded_table")
    op.drop_table("join_history")
    op.drop_table("table_entry")
