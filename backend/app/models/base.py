from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class IDMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)


# ---------------------------------------------------------------------------
# Enumerasi status yang dipakai lintas modul
# ---------------------------------------------------------------------------
class UserRole(str, Enum):
    ADMIN = "admin"
    PPIC = "ppic"
    PURCHASING = "purchasing"
    WAREHOUSE = "warehouse"
    PRODUCTION = "production"
    QC = "qc"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    VIEWER = "viewer"


class DocStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StockMovementType(str, Enum):
    GOODS_RECEIPT = "goods_receipt"
    MATERIAL_ISSUE = "material_issue"
    FINISHED_GOODS_IN = "finished_goods_in"
    SALE_OUT = "sale_out"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"


class WorkcenterType(str, Enum):
    KNITTING = "knitting"
    DYEING_PRINTING = "dyeing_printing"
    SPECIAL_TREATMENT = "special_treatment"
    CUT_SEW = "cut_sew"


class QCDecision(str, Enum):
    PASS = "pass"
    REJECT = "reject"
    REWORK = "rework"


class UOMUnit(str, Enum):
    KG = "kg"
    METER = "meter"
    PCS = "pcs"
    ROLL = "roll"
    LITER = "liter"
    PACK = "pack"
