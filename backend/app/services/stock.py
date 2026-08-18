"""Layanan stok: mencatat pergerakan stok & menjaga saldo inventory sinkron."""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.warehouse import InventoryItem, StockTransaction
from app.services.utils import parse_date


class InsufficientStockError(Exception):
    """Ditampilkan saat transaksi keluar melebihi saldo on-hand yang tersedia."""


def post_stock_transaction(
    db: Session,
    *,
    product_id: int,
    location_id: Optional[int],
    movement_type: str,
    qty: Decimal,
    direction: str,
    reference: Optional[str],
    unit_cost: Decimal = Decimal("0"),
    transaction_date: Optional[date] = None,
) -> StockTransaction:
    """Catat pergerakan stok dan perbarui saldo on-hand di inventory.

    Melarang transaksi keluar (``direction == \"out\"``) yang membuat saldo
    negatif, untuk menjaga akurasi stok real-time (PRD §3.3).
    """
    qty = Decimal(qty)
    tx = StockTransaction(
        product_id=product_id,
        location_id=location_id,
        movement_type=movement_type,
        qty=abs(qty),
        direction=direction,
        reference=reference,
        unit_cost=unit_cost,
        transaction_date=parse_date(transaction_date) or date.today(),
    )
    db.add(tx)

    inv = db.query(InventoryItem).filter(
        InventoryItem.product_id == product_id,
        InventoryItem.location_id == location_id,
    ).first()
    if inv is None:
        inv = InventoryItem(product_id=product_id, location_id=location_id, on_hand=0, reserved=0)
        db.add(inv)

    if direction == "out" and Decimal(inv.on_hand) < abs(qty):
        raise InsufficientStockError(
            f"Stok tidak mencukupi (tersedia {inv.on_hand}, diminta {abs(qty)}) "
            f"untuk transaksi keluar '{movement_type}'"
        )

    if direction == "in":
        inv.on_hand += abs(qty)
    else:
        inv.on_hand -= abs(qty)

    db.flush()
    return tx


def get_on_hand(db: Session, product_id: int, location_id: Optional[int] = None) -> Decimal:
    q = db.query(InventoryItem).filter(InventoryItem.product_id == product_id)
    if location_id is not None:
        q = q.filter(InventoryItem.location_id == location_id)
    items = q.all()
    return sum((Decimal(i.on_hand) for i in items), Decimal("0"))
