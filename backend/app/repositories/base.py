"""Generic SQLAlchemy 2.0 repository base.

Provides a small, typed CRUD surface that concrete repositories can extend.
Routers should never call this directly — use a service.
"""
from __future__ import annotations

from typing import Generic, Iterable, Optional, Type, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, db: Session, model: Type[ModelT] | None = None):
        self.db = db
        if model is not None:
            self.model = model

    # ---- Reads ----
    def get(self, id_: int) -> Optional[ModelT]:
        return self.db.get(self.model, id_)

    def list_items(self, *, offset: int = 0, limit: int = 50) -> list[ModelT]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        return int(self.db.execute(select(func.count()).select_from(self.model)).scalar_one())

    # ---- Writes ----
    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        self.db.flush()
        return instance

    def add_all(self, instances: Iterable[ModelT]) -> list[ModelT]:
        items = list(instances)
        self.db.add_all(items)
        self.db.flush()
        return items

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)
        self.db.flush()

    def delete_by_id(self, id_: int) -> int:
        result = self.db.execute(delete(self.model).where(self.model.id == id_))  # type: ignore[attr-defined]
        self.db.flush()
        return int(result.rowcount or 0)
