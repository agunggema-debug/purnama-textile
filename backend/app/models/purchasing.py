from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import DocStatus, TimestampMixin


class PurchaseRequest(Base, TimestampMixin):
    """Purchase Request: permintaan pembelian dari PPIC/penyedia data."""
    __tablename__ = "purchase_requests"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(120), nullable=False)
    requested_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    lines = relationship("PRLine", back_populates="pr", cascade="all, delete-orphan")


class PRLine(Base):
    __tablename__ = "pr_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pr_id: Mapped[int] = mapped_column(ForeignKey("purchase_requests.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    required_date: Mapped[date] = mapped_column(Date, nullable=False)

    pr = relationship("PurchaseRequest", back_populates="lines")
    product = relationship("Product")


class PurchaseOrder(Base, TimestampMixin):
    """Purchase Order: pesanan pembelian resmi kepada vendor, tunduk persetujuan."""
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    vendor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vendors.id"))
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_arrival: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(120))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    vendor = relationship("Vendor")
    lines = relationship("POLine", back_populates="po", cascade="all, delete-orphan")


class POLine(Base):
    __tablename__ = "po_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    received_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    eta: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    po = relationship("PurchaseOrder", back_populates="lines")
    product = relationship("Product")


class PurchaseReturn(Base, TimestampMixin):
    """Retur pembelian atas ketidaksesuaian barang yang diterima."""
    __tablename__ = "purchase_returns"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    return_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)

    po = relationship("PurchaseOrder")
    lines = relationship("PurchaseReturnLine", back_populates="return_doc", cascade="all, delete-orphan")


class PurchaseReturnLine(Base):
    __tablename__ = "purchase_return_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    return_id: Mapped[int] = mapped_column(ForeignKey("purchase_returns.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    return_doc = relationship("PurchaseReturn", back_populates="lines")
    product = relationship("Product")
