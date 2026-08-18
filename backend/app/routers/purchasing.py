from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.purchasing import (
    PRLine,
    PurchaseRequest,
    PurchaseReturn,
    PurchaseReturnLine,
    POLine,
    PurchaseOrder,
)
from app.routers.base import create_crud_router
from app.services.utils import gen_code, parse_date

router = APIRouter(prefix="/api/purchasing", tags=["Purchasing"])

router.include_router(create_crud_router(PurchaseRequest, "/pr", ["PR"]))
router.include_router(create_crud_router(PurchaseOrder, "/po", ["PO"]))
router.include_router(create_crud_router(PurchaseReturn, "/returns", ["Return"]))


class LineIn(BaseModel):
    product_id: int
    qty: Decimal
    required_date: Optional[str] = None
    unit_price: Decimal = 0
    eta: Optional[str] = None


class PRCreate(BaseModel):
    requested_by: str
    requested_date: Optional[str] = None
    notes: Optional[str] = None
    lines: List[LineIn]


class POCreate(BaseModel):
    vendor_id: int
    order_date: Optional[str] = None
    expected_arrival: Optional[str] = None
    notes: Optional[str] = None
    lines: List[LineIn]


class ReturnCreate(BaseModel):
    po_id: int
    reason: Optional[str] = None
    lines: List[LineIn]


@router.post("/pr/full", response_model=dict)
def create_pr(payload: PRCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pr = PurchaseRequest(
        code=gen_code(db, PurchaseRequest, "PR"),
        requested_by=payload.requested_by,
        requested_date=parse_date(payload.requested_date or date.today()),
        notes=payload.notes,
        status="draft",
    )
    for line in payload.lines:
        pr.lines.append(
            PRLine(
                product_id=line.product_id,
                qty=line.qty,
                required_date=parse_date(line.required_date or date.today()),
            )
        )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return {"id": pr.id, "code": pr.code}


@router.post("/pr/{pr_id}/approve", response_model=dict)
def approve_pr(pr_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pr = db.get(PurchaseRequest, pr_id)
    if not pr:
        raise HTTPException(404, "PR tidak ditemukan")
    pr.status = "approved"
    db.commit()
    return {"id": pr.id, "status": pr.status}


@router.post("/po/full", response_model=dict)
def create_po(payload: POCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    po = PurchaseOrder(
        code=gen_code(db, PurchaseOrder, "PO"),
        vendor_id=payload.vendor_id,
        order_date=parse_date(payload.order_date or date.today()),
        expected_arrival=parse_date(payload.expected_arrival),
        notes=payload.notes,
        status="draft",
    )
    for line in payload.lines:
        po.lines.append(
            POLine(
                product_id=line.product_id,
                qty=line.qty,
                unit_price=line.unit_price,
                eta=parse_date(line.eta),
            )
        )
    db.add(po)
    db.commit()
    db.refresh(po)
    return {"id": po.id, "code": po.code}


@router.post("/po/{po_id}/approve", response_model=dict)
def approve_po(po_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(404, "PO tidak ditemukan")
    po.status = "approved"
    db.commit()
    return {"id": po.id, "status": po.status}


@router.post("/returns/full", response_model=dict)
def create_return(payload: ReturnCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    ret = PurchaseReturn(
        code=gen_code(db, PurchaseReturn, "PRT"),
        po_id=payload.po_id,
        return_date=date.today(),
        reason=payload.reason,
        status="draft",
    )
    for line in payload.lines:
        ret.lines.append(PurchaseReturnLine(product_id=line.product_id, qty=line.qty))
    db.add(ret)
    db.commit()
    db.refresh(ret)
    return {"id": ret.id, "code": ret.code}
