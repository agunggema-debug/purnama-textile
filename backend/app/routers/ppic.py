from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.ppic import BOM, BOMLine, MPS
from app.routers.base import create_crud_router
from app.services.mrp import compute_mrp
from app.services.utils import gen_code, parse_date

router = APIRouter(prefix="/api/ppic", tags=["PPIC"])

router.include_router(create_crud_router(BOM, "/boms", ["PPIC - BOM"]))
router.include_router(create_crud_router(MPS, "/mps", ["PPIC - MPS"]))


class BOMLineIn(BaseModel):
    material_id: int
    qty_per_output: Decimal
    waste_factor: Decimal = 0


class BOMCreate(BaseModel):
    product_id: int
    output_qty: Decimal = 1
    code: Optional[str] = None
    notes: Optional[str] = None
    lines: List[BOMLineIn]


class MPSCreate(BaseModel):
    product_id: int
    schedule_date: str
    qty: Decimal
    order_type: str = "make_to_stock"
    sales_order_id: Optional[int] = None


@router.post("/boms/full", response_model=dict)
def create_bom_with_lines(payload: BOMCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    bom = BOM(
        code=payload.code or gen_code(db, BOM, "BOM"),
        product_id=payload.product_id,
        output_qty=payload.output_qty,
        notes=payload.notes,
        is_active=True,
    )
    for line in payload.lines:
        bom.lines.append(
            BOMLine(
                material_id=line.material_id,
                qty_per_output=line.qty_per_output,
                waste_factor=line.waste_factor,
            )
        )
    db.add(bom)
    db.commit()
    db.refresh(bom)
    return {"id": bom.id, "code": bom.code, "line_count": len(bom.lines)}


@router.post("/mps/full", response_model=dict)
def create_mps(payload: MPSCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    mps = MPS(
        code=gen_code(db, MPS, "MPS"),
        product_id=payload.product_id,
        schedule_date=parse_date(payload.schedule_date),
        qty=payload.qty,
        order_type=payload.order_type,
        sales_order_id=payload.sales_order_id,
        status="draft",
    )
    db.add(mps)
    db.commit()
    db.refresh(mps)
    return {"id": mps.id, "code": mps.code}


@router.get("/mps/{mps_id}/mrp", response_model=dict)
def run_mrp(mps_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    try:
        return compute_mrp(db, mps_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
