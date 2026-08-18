from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import DocStatus, QCDecision, TimestampMixin, WorkcenterType


class WorkOrder(Base, TimestampMixin):
    """Surat Perintah Kerja (SPK): instruksi produksi dari jadwal PPIC."""
    __tablename__ = "work_orders"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    mps_id: Mapped[Optional[int]] = mapped_column(ForeignKey("mps.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    planned_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    produced_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    mps = relationship("MPS")
    product = relationship("Product")
    operations = relationship("WorkOrderOperation", back_populates="work_order",
                               cascade="all, delete-orphan")
    qc_results = relationship("QCResult", back_populates="work_order", cascade="all, delete-orphan")


class WorkOrderOperation(Base, TimestampMixin):
    """Routing: progres tiap stasiun kerja untuk sebuah work order."""
    __tablename__ = "work_order_operations"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id"), nullable=False)
    workcenter_id: Mapped[int] = mapped_column(ForeignKey("workcenters.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(default=1, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.PENDING, nullable=False)
    qty_completed: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    qty_rejected: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    work_order = relationship("WorkOrder", back_populates="operations")
    workcenter = relationship("Workcenter")


class QCResult(Base, TimestampMixin):
    """Hasil inspeksi kualitas pasca-produksi (QC)."""
    __tablename__ = "qc_results"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    work_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("work_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    inspected_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    passed_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    rejected_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    decision: Mapped[QCDecision] = mapped_column(String(20), default=QCDecision.PASS, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    work_order = relationship("WorkOrder", back_populates="qc_results")
    product = relationship("Product")


class WasteLog(Base, TimestampMixin):
    """Pencatatan sisa material terbuang (waste) untuk manajemen limbah."""
    __tablename__ = "waste_logs"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    work_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("work_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    waste_date: Mapped[date] = mapped_column(Date, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)

    work_order = relationship("WorkOrder")
    product = relationship("Product")
