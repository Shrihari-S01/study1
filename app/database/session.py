"""
Database session dependency.

Provides an AsyncSession dependency for FastAPI.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db


# ==========================================================
# Database Session Dependency
# ==========================================================

DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]