"""Persistence models package.

This package exposes the project `Base` class and individual model modules.
Each model is defined in its own file to match the repository's style.
"""

from .base import Base
from .table_entry import TableEntry

__all__ = ["Base", "TableEntry"]
