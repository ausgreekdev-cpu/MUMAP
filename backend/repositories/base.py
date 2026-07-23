from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(getattr(self.model, field) == value).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> List[ModelType]:
        query = self.db.query(self.model)

        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        if order_by and hasattr(self.model, order_by):
            order_col = getattr(self.model, order_by)
            if descending:
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col.asc())

        return query.offset(skip).limit(limit).all()

    def count(self, filters: Optional[dict] = None) -> int:
        query = self.db.query(func.count(self.model.id))

        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        return query.scalar() or 0

    def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        db_obj = self.get(id)
        if db_obj:
            for key, value in obj_in.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def exists(self, id: int) -> bool:
        return self.db.query(self.model.id).filter(self.model.id == id).first() is not None

    def get_or_create(self, defaults: dict, **kwargs) -> tuple[ModelType, bool]:
        instance = self.db.query(self.model).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            params = {**kwargs, **defaults}
            instance = self.model(**params)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            return instance, True
