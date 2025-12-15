"""change_body_column_to_longtext

Revision ID: 404d6e528958
Revises: 7309b800992a
Create Date: 2025-12-07 22:51:26.329771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '404d6e528958'
down_revision: Union[str, Sequence[str], None] = '7309b800992a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change body column from TEXT to LONGTEXT to support larger datasets
    op.execute("ALTER TABLE table_entry MODIFY body LONGTEXT NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    # Change body column back from LONGTEXT to TEXT
    op.execute("ALTER TABLE table_entry MODIFY body TEXT NOT NULL")
