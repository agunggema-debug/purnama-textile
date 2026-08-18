from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.distribution import (
    DeliveryOrder,
    DOLine,
    PackingList,
    PackingListLine,
    SalesOrder,
    SalesOrderLine,
    Shipment,
)
from app.models.master import Product
from app.routers.base import create_crud_router
from app.services.accounting import post_journal
from app.services.stock import get_on_hand, post_stock_transaction
from app.services.utils import gen_code, parse_date

router = APIRouter(prefix="/api/distribution", tags=["Distribusi & Logistik"])

router.include_router(create_crud_router(SalesOrder, "/sales-orders", ["Sales Order"]))
router.include_router(create_crud_router(DeliveryOrder, "/delivery-orders", ["DO"]))
router.include_router(create_crud_router(PackingList, "/packing-lists", ["Packing List"]))
router.include_router(create_crud_router(Shipment, "/shipments", ["Shipment"]))


class SalesLineIn(BaseModel):
    product_id: int
    qty: Decimal
    unit_price: Decimal = 0
    delivery_date: str


class SalesOrderCreate(BaseModel):
    customer_id: Optional[int] = None
    order_date: Optional[str] = None
    notes: Optional[str] = None
    lines: List[SalesLineIn]


class DOLineIn(BaseModel):
    product_id: int
    qty: Decimal
    location_id: Optional[int] = None


class DOCreate(BaseModel):
    sales_order_id: Optional[int] = None
    customer_id: Optional[int] = None
    delivery_date: Optional[str] = None
    destination_address: Optional[str] = None
    lines: List[DOLineIn]


class PackingLineIn(BaseModel):
    product_id: int
    qty: Decimal


class PackingCreate(BaseModel):
    delivery_order_id: int
    shipping_marks: Optional[str] = None
    total_packages: int = 0
    lines: List[PackingLineIn]


@router.post("/sales-orders/full", response_model=dict)
def create_sales_order(payload: SalesOrderCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    so = SalesOrder(
        code=gen_code(db, SalesOrder, "SO"),
        customer_id=payload.customer_id,
        order_date=parse_date(payload.order_date or date.today()),
        notes=payload.notes,
        status="draft",
    )
    for line in payload.lines:
        so.lines.append(
            SalesOrderLine(
                product_id=line.product_id,
                qty=line.qty,
                unit_price=line.unit_price,
                delivery_date=parse_date(line.delivery_date),
            )
        )
    db.add(so)
    db.commit()
    db.refresh(so)
    return {"id": so.id, "code": so.code, "line_count": len(so.lines)}


@router.get("/sales-orders/{so_id}/detail", response_model=dict)
def sales_order_detail(so_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    so = db.get(SalesOrder, so_id)
    if not so:
        raise HTTPException(404, "Sales Order tidak ditemukan")
    return {
        "id": so.id,
        "code": so.code,
        "customer": so.customer.name if so.customer else None,
        "order_date": so.order_date,
        "status": so.status,
        "total": sum((Decimal(l.qty) * Decimal(l.unit_price) for l in so.lines), Decimal("0")),
        "lines": [
            {
                "product": l.product.name,
                "product_code": l.product.code,
                "qty": l.qty,
                "unit_price": l.unit_price,
                "delivery_date": l.delivery_date,
            }
            for l in so.lines
        ],
    }


@router.post("/delivery-orders/full", response_model=dict)
def create_delivery_order(payload: DOCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    do = DeliveryOrder(
        code=gen_code(db, DeliveryOrder, "DO"),
        sales_order_id=payload.sales_order_id,
        customer_id=payload.customer_id,
        delivery_date=parse_date(payload.delivery_date or date.today()),
        destination_address=payload.destination_address,
        status="draft",
    )
    unit_prices: dict = {}
    if payload.sales_order_id:
        so = db.get(SalesOrder, payload.sales_order_id)
        if so:
            unit_prices = {l.product_id: Decimal(l.unit_price) for l in so.lines}

    # Validasi kecukupan stok barang jadi sebelum pengiriman (PRD §3.5)
    for line in payload.lines:
        available = get_on_hand(db, line.product_id, line.location_id)
        if Decimal(line.qty) > available:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Stok barang jadi produk {line.product_id} tidak mencukupi "
                       f"(tersedia {available}, diminta {line.qty}) di lokasi {line.location_id}",
            )

    revenue = Decimal("0")
    cogs = Decimal("0")
    for line in payload.lines:
        do.lines.append(
            DOLine(product_id=line.product_id, qty=line.qty, location_id=line.location_id)
        )
        product = db.get(Product, line.product_id)
        price = unit_prices.get(line.product_id, Decimal("0"))
        revenue += Decimal(line.qty) * price
        cogs += Decimal(line.qty) * Decimal(product.standard_cost if product else 0)

    db.add(do)
    db.flush()

    for line in do.lines:
        post_stock_transaction(
            db,
            product_id=line.product_id,
            location_id=line.location_id,
            movement_type="sale_out",
            qty=line.qty,
            direction="out",
            reference=do.code,
            transaction_date=do.delivery_date,
        )

    revenue = revenue.quantize(Decimal("0.01"))
    cogs = cogs.quantize(Decimal("0.01"))
    # COGS: Debit HPP, Kredit Persediaan Barang Jadi
    post_journal(
        db, entry_date=do.delivery_date,
        description=f"HPP pengiriman {do.code}",
        lines=[("5-5000", cogs, 0), ("1-1200", 0, cogs)], reference=do.code,
    )
    # Penjualan/AR: Debit Piutang, Kredit Pendapatan
    post_journal(
        db, entry_date=do.delivery_date,
        description=f"Penjualan {do.code}",
        lines=[("1-1300", revenue, 0), ("4-4000", 0, revenue)], reference=do.code,
    )

    do.status = "completed"
    db.commit()
    return {"id": do.id, "code": do.code, "revenue": revenue, "cogs": cogs}


@router.post("/packing-lists/full", response_model=dict)
def create_packing_list(payload: PackingCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pl = PackingList(
        code=gen_code(db, PackingList, "PL"),
        delivery_order_id=payload.delivery_order_id,
        shipping_marks=payload.shipping_marks,
        total_packages=payload.total_packages,
        status="draft",
    )
    for line in payload.lines:
        pl.lines.append(PackingListLine(product_id=line.product_id, qty=line.qty))
    db.add(pl)
    db.commit()
    db.refresh(pl)
    return {"id": pl.id, "code": pl.code}