"""SQLAlchemy ORM 模型 (声明式基类)"""
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    @property
    def as_dict(self):
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}
