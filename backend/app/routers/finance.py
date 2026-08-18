from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.finance import (
    Account,
    APInvoice,
    ARInvoice,
    JournalEntry,
    PaymentIn,
    PaymentOut,
    PayrollRun,
)
from app.routers.base import create_crud_router
from app.services.accounting import balance_sheet, cash_flow, post_journal, profit_loss
from app.services.payroll import run_payroll
from app.services.utils import parse_date

router = APIRouter(prefix="/api/finance", tags=["Finance & Accounting"])


@router.get("/ap/overview", response_model=List[dict])
def list_ap(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(APInvoice).all()
    return [
        {
            "id": inv.id, "code": inv.code,
            "vendor": inv.vendor.name if inv.vendor else None,
            "invoice_date": inv.invoice_date, "due_date": inv.due_date,
            "amount": inv.amount, "paid_amount": inv.paid_amount,
            "balance": inv.amount - inv.paid_amount,
        }
        for inv in rows
    ]


@router.get("/ar/overview", response_model=List[dict])
def list_ar(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(ARInvoice).all()
    return [
        {
            "id": inv.id, "code": inv.code,
            "customer": inv.customer.name if inv.customer else None,
            "invoice_date": inv.invoice_date, "due_date": inv.due_date,
            "amount": inv.amount, "paid_amount": inv.paid_amount,
            "balance": inv.amount - inv.paid_amount,
        }
        for inv in rows
    ]


router.include_router(create_crud_router(Account, "/accounts", ["Accounts"]))
router.include_router(create_crud_router(APInvoice, "/ap", ["AP"]))
router.include_router(create_crud_router(ARInvoice, "/ar", ["AR"]))
router.include_router(create_crud_router(PaymentIn, "/payments-in", ["Payment In"]))
router.include_router(create_crud_router(PaymentOut, "/payments-out", ["Payment Out"]))
router.include_router(create_crud_router(PayrollRun, "/payroll-runs", ["Payroll"]))


class PaymentInCreate(BaseModel):
    ar_invoice_id: int
    payment_date: Optional[str] = None
    amount: Decimal
    method: str = "transfer"


class PaymentOutCreate(BaseModel):
    ap_invoice_id: int
    payment_date: Optional[str] = None
    amount: Decimal
    method: str = "transfer"


@router.get("/journals", response_model=List[dict])
def list_journals(skip: int = 0, limit: int = 200, db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(JournalEntry).order_by(JournalEntry.id.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": e.id,
            "code": e.code,
            "entry_date": e.entry_date,
            "reference": e.reference,
            "description": e.description,
            "lines": [
                {"account": l.account.code, "account_name": l.account.name,
                 "debit": l.debit, "credit": l.credit}
                for l in e.lines
            ],
        }
        for e in rows
    ]


@router.post("/payments-in/full", response_model=dict)
def create_payment_in(payload: PaymentInCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    inv = db.get(ARInvoice, payload.ar_invoice_id)
    if not inv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="AR invoice tidak ditemukan")
    amount = Decimal(payload.amount)
    if amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Jumlah pembayaran harus lebih dari 0")
    balance = Decimal(inv.amount or 0) - Decimal(inv.paid_amount or 0)
    if amount > balance:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Jumlah pembayaran melebihi saldo piutang (sisa saldo {balance})",
        )
    payment = PaymentIn(
        ar_invoice_id=payload.ar_invoice_id,
        payment_date=parse_date(payload.payment_date or date.today()),
        amount=payload.amount,
        method=payload.method,
    )
    db.add(payment)
    inv.paid_amount = Decimal(inv.paid_amount or 0) + amount
    post_journal(
        db, entry_date=payment.payment_date,
        description=f"Penerimaan pembayaran {inv.code}",
        lines=[("1-1000", amount, 0), ("1-1300", 0, amount)],
        reference=inv.code,
    )
    db.commit()
    return {"id": payment.id, "ar_invoice": inv.code, "balance": inv.amount - inv.paid_amount}


@router.post("/payments-out/full", response_model=dict)
def create_payment_out(payload: PaymentOutCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    inv = db.get(APInvoice, payload.ap_invoice_id)
    if not inv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="AP invoice tidak ditemukan")
    amount = Decimal(payload.amount)
    if amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Jumlah pembayaran harus lebih dari 0")
    balance = Decimal(inv.amount or 0) - Decimal(inv.paid_amount or 0)
    if amount > balance:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Jumlah pembayaran melebihi saldo hutang (sisa saldo {balance})",
        )
    payment = PaymentOut(
        ap_invoice_id=payload.ap_invoice_id,
        payment_date=parse_date(payload.payment_date or date.today()),
        amount=payload.amount,
        method=payload.method,
    )
    db.add(payment)
    inv.paid_amount = Decimal(inv.paid_amount or 0) + amount
    post_journal(
        db, entry_date=payment.payment_date,
        description=f"Pembayaran hutang {inv.code}",
        lines=[("2-2000", amount, 0), ("1-1000", 0, amount)],
        reference=inv.code,
    )
    db.commit()
    return {"id": payment.id, "ap_invoice": inv.code, "balance": inv.amount - inv.paid_amount}


@router.post("/payroll-runs/generate", response_model=dict)
def generate_payroll(month: int, year: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    run = run_payroll(db, month, year)
    return {
        "id": run.id, "code": run.code,
        "period": f"{year}-{month:02d}",
        "total_amount": run.total_amount,
        "employee_count": len(run.lines),
    }


@router.get("/reports/profit-loss")
def report_profit_loss(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return profit_loss(db)


@router.get("/reports/balance-sheet")
def report_balance_sheet(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return balance_sheet(db)


@router.get("/reports/cash-flow")
def report_cash_flow(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return cash_flow(db)
