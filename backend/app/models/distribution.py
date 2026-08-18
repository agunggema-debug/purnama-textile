from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import DocStatus, TimestampMixin


class SalesOrder(Base, TimestampMixin):
    """Pesanan pelanggan (B2B/B2C) yang menjadi sumber MPS Make-to-Order."""
    __tablename__ = "sales_orders"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    customer = relationship("Customer")
    lines = relationship("SalesOrderLine", back_populates="sales_order", cascade="all, delete-orphan")


class SalesOrderLine(Base):
    __tablename__ = "sales_order_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)

    sales_order = relationship("SalesOrder", back_populates="lines")
    product = relationship("Product")


class DeliveryOrder(Base, TimestampMixin):
    """Delivery Order (DO): surat jalan & alokasi stok untuk pengiriman."""
    __tablename__ = "delivery_orders"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    sales_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales_orders.id"))
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)
    destination_address: Mapped[Optional[str]] = mapped_column(Text)

    sales_order = relationship("SalesOrder")
    customer = relationship("Customer")
    lines = relationship("DOLine", back_populates="delivery_order", cascade="all, delete-orphan")


class DOLine(Base):
    __tablename__ = "do_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    delivery_order_id: Mapped[int] = mapped_column(ForeignKey("delivery_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouse_locations.id"))

    delivery_order = relationship("DeliveryOrder", back_populates="lines")
    product = relationship("Product")
    location = relationship("WarehouseLocation")


class PackingList(Base, TimestampMixin):
    """Packing List: rincian kemasan kiriman barang jadi."""
    __tablename__ = "packing_lists"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    delivery_order_id: Mapped[int] = mapped_column(ForeignKey("delivery_orders.id"), nullable=False)
    shipping_marks: Mapped[Optional[str]] = mapped_column(Text)
    total_packages: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)

    delivery_order = relationship("DeliveryOrder")
    lines = relationship("PackingListLine", back_populates="packing_list",
                         cascade="all, delete-orphan")


class PackingListLine(Base):
    __tablename__ = "packing_list_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    packing_list_id: Mapped[int] = mapped_column(ForeignKey("packing_lists.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    packing_list = relationship("PackingList", back_populates="lines")
    product = relationship("Product")


class Shipment(Base, TimestampMixin):
    """Fleet Management: pelacakan armada/Ekspedisi pengiriman."""
    __tablename__ = "shipments"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    delivery_order_id: Mapped[int] = mapped_column(ForeignKey("delivery_orders.id"), nullable=False)
    carrier: Mapped[str] = mapped_column(String(120), nullable=False)
    vehicle_no: Mapped[Optional[str]] = mapped_column(String(40))
    tracking_no: Mapped[Optional[str]] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="scheduled", nullable=False)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    delivery_order = relationship("DeliveryOrder")
