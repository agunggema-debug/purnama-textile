"""Layanan akuntansi: jurnal, buku besar, dan laporan keuangan."""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.finance import Account, JournalEntry, JournalLine
from app.services.utils import gen_code, parse_date


def resolve_account(db: Session, code: str) -> Account:
    account = db.query(Account).filter(Account.code == code).first()
    if account is None:
        raise ValueError(f"Akun dengan kode {code} tidak ditemukan di Chart of Accounts")
    return account


def post_journal(
    db: Session,
    *,
    entry_date,
    description: str,
    lines: List[Tuple[str, Decimal, Decimal]],
    reference: Optional[str] = None,
) -> JournalEntry:
    """Posting jurnal. `lines` = [(account_code, debit, credit), ...]."""
    total_dr = sum((Decimal(d) for _, d, _ in lines), Decimal("0"))
    total_cr = sum((Decimal(c) for _, _, c in lines), Decimal("0"))
    if total_dr != total_cr:
        raise ValueError(f"Jurnal tidak balance: debit={total_dr}, kredit={total_cr}")

    entry = JournalEntry(
        code=gen_code(db, JournalEntry, "JRNL"),
        entry_date=parse_date(entry_date),
        description=description,
        reference=reference,
        status="posted",
    )
    for acct_code, debit, credit in lines:
        account = resolve_account(db, acct_code)
        entry.lines.append(
            JournalLine(account_id=account.id, debit=Decimal(debit), credit=Decimal(credit))
        )
    db.add(entry)
    db.flush()
    return entry


def account_balance(db: Session, account: Account) -> Decimal:
    """Saldo buku besar sebuah akun (dr - cr)."""
    rows = (
        db.query(JournalLine)
        .join(JournalEntry)
        .filter(JournalLine.account_id == account.id, JournalEntry.status == "posted")
        .all()
    )
    return sum((Decimal(l.debit) - Decimal(l.credit) for l in rows), Decimal("0"))


# Kode akun HPP (Cost of Goods Sold). Dipakai untuk memisahkan HPP dari
# beban operasional pada laporan Laba/Rugi.
COGS_ACCOUNT_CODE = "5-5000"


def _is_cogs_account(acct: Account) -> bool:
    return acct.code == COGS_ACCOUNT_CODE or "harga pokok" in acct.name.lower()


def profit_loss(db: Session, year: Optional[int] = None) -> dict:
    """Laporan Laba/Rugi (P&L).

    - Pendapatan terletak pada sisi kredit jurnal (saldo debit-kredit < 0).
    - HPP dipisahkan dari beban operasional agar sesuai PRD §3.6.
    - Beban operasional terletak pada sisi debit jurnal.
    """
    revenue = Decimal("0")
    cogs = Decimal("0")
    expense = Decimal("0")
    for acct in db.query(Account).all():
        if year is not None and acct.created_at.year != year:
            continue
        bal = account_balance(db, acct)  # saldo = debit - kredit
        if acct.account_type == "revenue":
            if bal < 0:  # pendapatan = sisi kredit
                revenue += -bal
        elif acct.account_type == "expense":
            amt = bal if bal > 0 else Decimal("0")  # beban = sisi debit
            if _is_cogs_account(acct):
                cogs += amt
            else:
                expense += amt
    gross_profit = revenue - cogs
    net_profit = gross_profit - expense
    return {
        "revenue": revenue,
        "cost_of_goods_sold": cogs,
        "gross_profit": gross_profit,
        "expense": expense,
        "net_profit": net_profit,
    }


def balance_sheet(db: Session) -> dict:
    """Neraca (Balance Sheet).

    Memasukkan laba/rugi berjalan ke ekuitas (laba ditahan) sehingga persamaan
    akuntansi `Aset = Kewajiban + Ekuitas` tetap terpenuhi.
    """
    assets = Decimal("0")
    liabilities = Decimal("0")
    equity = Decimal("0")
    for acct in db.query(Account).all():
        bal = account_balance(db, acct)
        if acct.account_type == "asset":
            assets += bal
        elif acct.account_type == "liability":
            # saldo kewajiban normalnya negatif (kredit)
            liabilities += (-bal) if bal > 0 else abs(bal)
        elif acct.account_type == "equity":
            equity += (-bal) if bal > 0 else abs(bal)

    # Laba (rugi) periode berjalan dimasukkan sebagai laba ditahan agar neraca balance.
    retained_earnings = profit_loss(db).get("net_profit") or Decimal("0")
    total_equity = equity + retained_earnings

    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": total_equity,
        "retained_earnings": retained_earnings,
        "total_liab_equity": liabilities + total_equity,
    }


CASH_KEYWORDS = ("kas", "bank", "cash", "giro")


def cash_flow(db: Session) -> dict:
    cash_in = Decimal("0")
    cash_out = Decimal("0")
    for acct in db.query(Account).all():
        if acct.account_type != "asset" or not any(
            kw in acct.name.lower() for kw in CASH_KEYWORDS
        ):
            continue
        bal = account_balance(db, acct)
        if bal >= 0:
            cash_in += bal
        else:
            cash_out += abs(bal)
    return {
        "cash_in": cash_in,
        "cash_out": cash_out,
        "net_cash_flow": cash_in - cash_out,
    }
