from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.master import Product
from app.models.purchasing import PurchaseOrder
from app.models.warehouse import (
    GoodsReceipt,
    GoodsReceiptLine,
    InventoryItem,
    MaterialIssue,
    MaterialIssueLine,
    OpnameLine,
    StockOpname,
    StockTransaction,
)
from app.routers.base import create_crud_router
from app.services.accounting import post_journal, resolve_account
from app.services.stock import get_on_hand, post_stock_transaction
from app.services.utils import gen_code, parse_date

router = APIRouter(prefix="/api/warehouse", tags=["Warehouse"])

router.include_router(create_crud_router(GoodsReceipt, "/goods-receipts", ["Goods Receipt"]))
router.include_router(create_crud_router(MaterialIssue, "/material-issues", ["Material Issue"]))
router.include_router(create_crud_router(StockOpname, "/opnames", ["Stock Opname"]))


class GRLineIn(BaseModel):
    product_id: int
    location_id: Optional[int] = None
    qty: Decimal
    unit_cost: Decimal = 0


class GRCreate(BaseModel):
    po_id: Optional[int] = None
    vendor_id: Optional[int] = None
    receipt_date: Optional[str] = None
    notes: Optional[str] = None
    lines: List[GRLineIn]


class MLineIn(BaseModel):
    product_id: int
    location_id: Optional[int] = None
    qty: Decimal


class MICreate(BaseModel):
    work_order_id: Optional[int] = None
    issue_date: Optional[str] = None
    notes: Optional[str] = None
    lines: List[MLineIn]


class OpnameLineIn(BaseModel):
    product_id: int
    location_id: Optional[int] = None
    system_qty: Decimal = 0
    actual_qty: Decimal = 0


class OpnameCreate(BaseModel):
    opname_date: Optional[str] = None
    notes: Optional[str] = None
    lines: List[OpnameLineIn]


@router.get("/inventory", response_model=List[dict])
def list_inventory(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(InventoryItem).all()
    result = []
    for item in items:
        product = item.product
        result.append(
            {
                "product_id": item.product_id,
                "product_code": product.code,
                "product_name": product.name,
                "location_code": item.location.code if item.location else None,
                "on_hand": item.on_hand,
                "reserved": item.reserved,
            }
        )
    return result


@router.get("/movements", response_model=List[dict])
def list_movements(skip: int = 0, limit: int = 200, db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(StockTransaction).order_by(StockTransaction.id.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": t.id,
            "product_code": t.product.code,
            "product_name": t.product.name,
            "movement_type": t.movement_type,
            "direction": t.direction,
            "qty": t.qty,
            "unit_cost": t.unit_cost,
            "reference": t.reference,
            "transaction_date": t.transaction_date,
            "location_code": t.location.code if t.location else None,
        }
        for t in rows
    ]


@router.post("/goods-receipts/full", response_model=dict)
def create_goods_receipt(payload: GRCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    gr = GoodsReceipt(
        code=gen_code(db, GoodsReceipt, "GR"),
        po_id=payload.po_id,
        vendor_id=payload.vendor_id,
        receipt_date=parse_date(payload.receipt_date or date.today()),
        notes=payload.notes,
        status="draft",
    )
    total_amount = Decimal("0")
    for line in payload.lines:
        gr.lines.append(
            GoodsReceiptLine(
                product_id=line.product_id,
                location_id=line.location_id,
                qty=line.qty,
                unit_cost=line.unit_cost,
            )
        )
        total_amount += Decimal(line.qty) * Decimal(line.unit_cost)

    db.add(gr)
    db.flush()

    # Posting stok masuk & update received_qty pada PO
    for line in gr.lines:
        post_stock_transaction(
            db,
            product_id=line.product_id,
            location_id=line.location_id,
            movement_type="goods_receipt",
            qty=line.qty,
            direction="in",
            reference=gr.code,
            unit_cost=line.unit_cost,
            transaction_date=gr.receipt_date,
        )
    if payload.po_id:
        po = db.get(PurchaseOrder, payload.po_id)
        if po:
            # Akumulasi total qty yang diterima per produk dari dokumen GR ini
            # (menangani beberapa baris dengan produk yang sama),
            # lalu tambahkan ke received_qty baris PO yang bersesuaian.
            received_by_product: dict = {}
            for line in gr.lines:
                if any(l.product_id == line.product_id for l in po.lines):
                    received_by_product[line.product_id] = (
                        received_by_product.get(line.product_id, Decimal("0")) + Decimal(line.qty)
                    )
            for po_line in po.lines:
                if po_line.product_id in received_by_product:
                    po_line.received_qty = Decimal(po_line.received_qty or 0) + received_by_product[po_line.product_id]
            remain = sum(
                (Decimal(l.qty) - Decimal(l.received_qty or 0) for l in po.lines),
                Decimal("0"),
            )
            po.status = "completed" if remain <= 0 else "partial"

    # Jurnal otomatis: Debit Persediaan, Kredit Hutang Usaha
    total_amount = total_amount.quantize(Decimal("0.01"))
    entry = post_journal(
        db,
        entry_date=gr.receipt_date,
        description=f"Penerimaan barang {gr.code} dari vendor",
        lines=[("1-1100", total_amount, 0), ("2-2000", 0, total_amount)],
        reference=gr.code,
    )
    gr.status = "completed"
    db.commit()
    return {
        "id": gr.id,
        "code": gr.code,
        "journal_id": entry.id,
        "total_amount": total_amount,
    }


@router.post("/material-issues/full", response_model=dict)
def create_material_issue(payload: MICreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    mi = MaterialIssue(
        code=gen_code(db, MaterialIssue, "MI"),
        work_order_id=payload.work_order_id,
        issue_date=parse_date(payload.issue_date or date.today()),
        notes=payload.notes,
        status="draft",
    )
    # Validasi kecukupan stok sebelum pengeluaran material (PRD §3.3)
    for line in payload.lines:
        available = get_on_hand(db, line.product_id, line.location_id)
        if Decimal(line.qty) > available:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Stok material untuk produk {line.product_id} tidak mencukupi "
                       f"(tersedia {available}, diminta {line.qty})",
            )
    total_amount = Decimal("0")
    for line in payload.lines:
        mi.lines.append(
            MaterialIssueLine(
                product_id=line.product_id,
                location_id=line.location_id,
                qty=line.qty,
            )
        )
        product = db.get(Product, line.product_id)
        if product:
            total_amount += Decimal(line.qty) * Decimal(product.standard_cost)

    db.add(mi)
    db.flush()

    for line in mi.lines:
        post_stock_transaction(
            db,
            product_id=line.product_id,
            location_id=line.location_id,
            movement_type="material_issue",
            qty=line.qty,
            direction="out",
            reference=mi.code,
            transaction_date=mi.issue_date,
        )

    # Jurnal: Debit WIP, Kredit Persediaan Bahan Baku
    total_amount = total_amount.quantize(Decimal("0.01"))
    entry = post_journal(
        db,
        entry_date=mi.issue_date,
        description=f"Pengeluaran material {mi.code} ke lantai produksi",
        lines=[("1-1150", total_amount, 0), ("1-1100", 0, total_amount)],
        reference=mi.code,
    )
    mi.status = "completed"
    db.commit()
    return {"id": mi.id, "code": mi.code, "journal_id": entry.id, "total_amount": total_amount}


@router.post("/opnames/full", response_model=dict)
def create_opname(payload: OpnameCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    opname = StockOpname(
        code=gen_code(db, StockOpname, "OPN"),
        opname_date=parse_date(payload.opname_date or date.today()),
        notes=payload.notes,
        status="draft",
    )
    db.add(opname)
    db.flush()

    for line in payload.lines:
        opname.lines.append(
            OpnameLine(
                product_id=line.product_id,
                location_id=line.location_id,
                system_qty=line.system_qty,
                actual_qty=line.actual_qty,
            )
        )
        diff = Decimal(line.actual_qty) - Decimal(line.system_qty)
        if diff == 0:
            continue
        direction = "in" if diff > 0 else "out"
        # Selisih pengurangan (out) tidak boleh melebihi stok yang tersedia
        if direction == "out":
            available = get_on_hand(db, line.product_id, line.location_id)
            if abs(diff) > available:
                db.rollback()
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f"Selisih opname melebihi stok tersedia untuk produk "
                           f"{line.product_id} (tersedia {available}, selisih {abs(diff)})",
                )
        product = db.get(Product, line.product_id)
        unit_cost = Decimal(product.standard_cost) if product else Decimal("0")
        post_stock_transaction(
            db,
            product_id=line.product_id,
            location_id=line.location_id,
            movement_type="adjustment",
            qty=abs(diff),
            direction=direction,
            reference=opname.code,
            unit_cost=unit_cost,
            transaction_date=opname.opname_date,
        )
        amount = (abs(diff) * unit_cost).quantize(Decimal("0.01"))
        account = "1-1100" if (product and product.product_type == "raw_material") else "1-1200"
        if direction == "in":
            post_journal(db, entry_date=opname.opname_date,
                         description=f"Opname {opname.code}: selisih lebih",
                         lines=[(account, amount, 0), ("5-5400", 0, amount)], reference=opname.code)
        else:
            post_journal(db, entry_date=opname.opname_date,
                         description=f"Opname {opname.code}: selisih kurang",
                         lines=[("5-5400", amount, 0), (account, 0, amount)], reference=opname.code)

    opname.status = "completed"
    db.commit()
    return {"id": opname.id, "code": opname.code, "line_count": len(opname.lines)}