from dataclasses import dataclass
from fastapi import Query
from pydantic import BaseModel


@dataclass
class PaginationParams:
    page: int = Query(1, ge=1)
    limit: int = Query(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    limit: int


def paginate[T](
    items: list[T],
    total: int,
    pagination: PaginationParams,
) -> PaginatedResponse[T]:
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )