"""Common API response schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """Standard API response wrapper."""

    success: bool = True
    message: str = "OK"
    data: DataT | None = None

