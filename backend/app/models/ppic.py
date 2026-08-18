from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import DocStatus, TimestampMixin


class BOM(Base, TimestampMixin):
    """Bill of Materials: 'resep' produksi sebuah produk jadi."""
    __tablename__ = "boms"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    # kuantitas output yang dihasilkan oleh satu set BOM ini (mis. 100 meter)
    output_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(250))

    product = relationship("Product")
    lines = relationship("BOMLine", back_populates="bom", cascade="all, delete-orphan")


class BOMLine(Base):
    __tablename__ = "bom_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bom_id: Mapped[int] = mapped_column(ForeignKey("boms.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    # kebutuhan material per output_qty dari BOM header (mis. 1.2 kg benang)
    qty_per_output: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    waste_factor: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=0, nullable=False)

    bom = relationship("BOM", back_populates="lines")
    material = relationship("Product")


class MPS(Base, TimestampMixin):
    """Master Production Schedule: jadwal produksi induk (MTO / MTS)."""
    __tablename__ = "mps"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # make_to_order / make_to_stock
    order_type: Mapped[str] = mapped_column(String(30), default="make_to_stock", nullable=False)
    sales_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales_orders.id"))
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)

    product = relationship("Product")
    sales_order = relationship("SalesOrder")
