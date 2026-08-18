import inspect
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, create_model
from sqlalchemy import Date, DateTime, Boolean, Integer, Numeric, String, Text


def _map_python_type(col_type):
    if isinstance(col_type, (Integer,)) or (isinstance(col_type, Numeric) and col_type.precision is None):
        return int
    if isinstance(col_type, Boolean):
        return bool
    if isinstance(col_type, DateTime):
        return datetime
    if isinstance(col_type, Date):
        return date
    if isinstance(col_type, Numeric):
        return Decimal
    return str  # String / Text / Enum-as-string / lainnya


class ORMReadBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ORMWriterBase(BaseModel):
    """Semua kolom opsional agar pembuatan dokumen dapat bertahap."""


def build_read_model(orm_cls, name=None):
    """Bangun pydantic model respons dari kolom-kolom SQLAlchemy model."""
    fields = {}
    for col in orm_cls.__table__.columns:
        fields[col.name] = (Optional[_map_python_type(col.type)], None)
    return create_model(name or f"{orm_cls.__name__}Read", __base__=ORMReadBase, **fields)


def build_write_model(orm_cls, name=None, exclude=()):
    """Bangun pydantic model untuk create/update tanpa PK & timestamp."""
    fields = {}
    for col in orm_cls.__table__.columns:
        if col.name in ("id", "created_at", "updated_at") or col.name in exclude:
            continue
        fields[col.name] = (Optional[_map_python_type(col.type)], None)
    return create_model(name or f"{orm_cls.__name__}Write", __base__=ORMWriterBase, **fields)


__all__ = ["build_read_model", "build_write_model", "ORMReadBase", "ORMWriterBase"]
