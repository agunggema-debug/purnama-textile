from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import DocStatus, TimestampMixin


class Account(Base, TimestampMixin):
    """Chart of Accounts (CoA) untuk jurnal & pelaporan keuangan."""
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # asset / liability / equity / revenue / expense
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class JournalEntry(Base, TimestampMixin):
    """Jurnal umum: dibuat otomatis dari transaksi modul lain."""
    __tablename__ = "journal_entries"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(80))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="posted", nullable=False)

    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")


class APInvoice(Base, TimestampMixin):
    """Accounts Payable: utang kepada vendor atas pembelian."""
    __tablename__ = "ap_invoices"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    vendor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vendors.id"))
    po_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"))
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)

    vendor = relationship("Vendor")
    po = relationship("PurchaseOrder")


class ARInvoice(Base, TimestampMixin):
    """Accounts Receivable: tagihan/piutang kepada klien B2B."""
    __tablename__ = "ar_invoices"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    sales_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales_orders.id"))
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)

    customer = relationship("Customer")
    sales_order = relationship("SalesOrder")


class PaymentIn(Base, TimestampMixin):
    """Penerimaan pembayaran dari pelanggan (AR)."""
    __tablename__ = "payments_in"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ar_invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ar_invoices.id"))
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), default="transfer", nullable=False)

    ar_invoice = relationship("ARInvoice")


class PaymentOut(Base, TimestampMixin):
    """Pembayaran kepada vendor (AP)."""
    __tablename__ = "payments_out"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ap_invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ap_invoices.id"))
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), default="transfer", nullable=False)

    ap_invoice = relationship("APInvoice")


class PayrollRun(Base, TimestampMixin):
    """Menjalankan penggajian untuk sebuah periode."""
    __tablename__ = "payroll_runs"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    period_month: Mapped[int] = mapped_column(nullable=False)
    period_year: Mapped[int] = mapped_column(nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    status: Mapped[DocStatus] = mapped_column(String(20), default=DocStatus.DRAFT, nullable=False)

    lines = relationship("PayrollLine", back_populates="run", cascade="all, delete-orphan")


class PayrollLine(Base):
    __tablename__ = "payroll_lines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payroll_run_id: Mapped[int] = mapped_column(ForeignKey("payroll_runs.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    base_salary: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    overtime: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    allowance: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    deduction: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    net_pay: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)

    run = relationship("PayrollRun", back_populates="lines")
    employee = relationship("Employee")