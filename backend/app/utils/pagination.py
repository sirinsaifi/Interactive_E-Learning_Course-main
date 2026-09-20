"""Pagination helpers used by repositories and services."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PageParams:
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return max(self.page - 1, 0) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
