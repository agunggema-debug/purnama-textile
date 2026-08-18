from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import DocStatus, StockMovementType, TimestampMixin


class StockTransaction(Base, TimestampMixin):
    """Buku besar stok: seluruh pergerakan masuk/keluar barang."""
    __tablename__ = "stock_transactions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouse_locations.id"))
    movement_type: Mapped[StockMovementType] = mapped_column(String(40), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # "in" | "out"
    reference: Mapped[Optional[str]] = mapped_column(String(80))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)

    product = relationship("Product")
    location = relationship("WarehouseLocation")


class InventoryItem(Base):
    """Saldo stok real-time per produk per lokasi (dijaga tetap sinkron)."""
    __tablename__ = "inventory_items"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouse_locations.id"))
    on_hand: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    reserved: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)

    product = relationship("Product")
    location = relationship("WarehouseLocation")


class GoodsReceipt(Base, TimestampMixin):
    """Penerimaan barang dari vendor (Goods Receipt) & penempatan (putaway)."""
    __tablename__ = "goods_receipts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    po_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"))
    vendor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vendors.id"))
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    po = relationship("PurchaseOrder")
    vendor = relationship("Vendor")
    lines = relationship("GoodsReceiptLine", cascade="all, delete-orphan")


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    gr_id: Mapped[int] = mapped_column(ForeignKey("goods_receipts.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouse_locations.id"))
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)

    product = relationship("Product")
    location = relationship("WarehouseLocation")


class MaterialIssue(Base, TimestampMixin):
    """Pengeluaran material dari gudang ke lantai produksi."""
    __tablename__ = "material_issues"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    work_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("work_orders.id"))
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    work_order = relationship("WorkOrder")
    lines = relationship("MaterialIssueLine", cascade="all, delete-orphan")


class MaterialIssueLine(Base):
    __tablename__ = "material_issue_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    material_issue_id: Mapped[int] = mapped_column(ForeignKey("material_issues.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouse_locations.id"))
    qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    product = relationship("Product")
    location = relationship("WarehouseLocation")


class StockOpname(Base, TimestampMixin):
    """Rekonsiliasi stok fisik vs sistem secara berkala."""
    __tablename__ = "stock_opnames"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    opname_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    lines = relationship("OpnameLine", cascade="all, delete-orphan")


class OpnameLine(Base):
    __tablename__ = "opname_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    opname_id: Mapped[int] = mapped_column(ForeignKey("stock_opnames.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouse_locations.id"))
    system_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    actual_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)

    product = relationship("Product")
    location = relationship("WarehouseLocation")