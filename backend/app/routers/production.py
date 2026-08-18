from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.master import WarehouseLocation
from app.models.production import QCResult, WasteLog, WorkOrder, WorkOrderOperation
from app.routers.base import create_crud_router
from app.services.stock import post_stock_transaction
from app.services.utils import gen_code, parse_date

router = APIRouter(prefix="/api/production", tags=["Produksi"])

router.include_router(create_crud_router(WorkOrder, "/work-orders", ["SPK - Work Order"]))
router.include_router(create_crud_router(WorkOrderOperation, "/operations", ["Workcenter Operation"]))
router.include_router(create_crud_router(QCResult, "/qc", ["QC"]))
router.include_router(create_crud_router(WasteLog, "/waste", ["Waste Log"]))


class WorkOrderCreate(BaseModel):
    mps_id: Optional[int] = None
    product_id: int
    planned_qty: Decimal
    start_date: str
    due_date: str
    workcenter_ids: List[int] = []


class OperationUpdate(BaseModel):
    status: Optional[str] = None
    qty_completed: Optional[Decimal] = None
    qty_rejected: Optional[Decimal] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class QCCreate(BaseModel):
    work_order_id: Optional[int] = None
    product_id: int
    inspected_qty: Decimal
    passed_qty: Decimal
    rejected_qty: Decimal
    decision: str = "pass"
    notes: Optional[str] = None


class WasteCreate(BaseModel):
    work_order_id: Optional[int] = None
    product_id: int
    waste_date: str
    qty: Decimal
    reason: Optional[str] = None


@router.post("/work-orders/full", response_model=dict)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    wo = WorkOrder(
        code=gen_code(db, WorkOrder, "SPK"),
        mps_id=payload.mps_id,
        product_id=payload.product_id,
        planned_qty=payload.planned_qty,
        produced_qty=Decimal("0"),
        status="draft",
        start_date=parse_date(payload.start_date),
        due_date=parse_date(payload.due_date),
    )
    for seq, wc_id in enumerate(payload.workcenter_ids, start=1):
        wo.operations.append(
            WorkOrderOperation(workcenter_id=wc_id, sequence=seq, status="pending")
        )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return {"id": wo.id, "code": wo.code, "operations": len(wo.operations)}


@router.post("/work-orders/{wo_id}/operations/{op_id}/update", response_model=dict)
def update_operation(
    wo_id: int, op_id: int, payload: OperationUpdate,
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise HTTPException(404, "Work order tidak ditemukan")
    op = next((o for o in wo.operations if o.id == op_id), None)
    if not op:
        raise HTTPException(404, "Operasi tidak ditemukan")
    if payload.status is not None:
        op.status = payload.status
    if payload.qty_completed is not None:
        op.qty_completed = payload.qty_completed
    if payload.qty_rejected is not None:
        op.qty_rejected = payload.qty_rejected
    if payload.started_at:
        op.started_at = datetime.fromisoformat(payload.started_at)
    if payload.finished_at:
        op.finished_at = datetime.fromisoformat(payload.finished_at)
    db.commit()
    return {"id": op.id, "wo_id": wo_id, "status": op.status, "qty_completed": op.qty_completed}


@router.post("/qc/full", response_model=dict)
def create_qc(payload: QCCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    qc = QCResult(
        work_order_id=payload.work_order_id,
        product_id=payload.product_id,
        inspected_qty=payload.inspected_qty,
        passed_qty=payload.passed_qty,
        rejected_qty=payload.rejected_qty,
        decision=payload.decision,
        notes=payload.notes,
    )
    if payload.work_order_id:
        wo = db.get(WorkOrder, payload.work_order_id)
        if wo:
            wo.produced_qty = Decimal(wo.produced_qty or 0) + Decimal(payload.passed_qty)
    db.add(qc)
    db.flush()

    # Barang yang lolos QC masuk ke gudang barang jadi (finished_goods_in),
    # sehingga stok barang jadi tercatat sebelum didistribusikan (PRD §3.4 → §3.3).
    if Decimal(payload.passed_qty or 0) > 0:
        fg_location = (
            db.query(WarehouseLocation)
            .filter(WarehouseLocation.warehouse_type == "finished_good", WarehouseLocation.is_active.is_(True))
            .order_by(WarehouseLocation.id)
            .first()
        )
        post_stock_transaction(
            db,
            product_id=payload.product_id,
            location_id=fg_location.id if fg_location else None,
            movement_type="finished_goods_in",
            qty=payload.passed_qty,
            direction="in",
            reference=f"QC-{qc.id}",
            transaction_date=date.today(),
        )

    db.commit()
    db.refresh(qc)
    return {"id": qc.id, "decision": qc.decision, "passed_qty": qc.passed_qty}


@router.post("/waste/full", response_model=dict)
def create_waste(payload: WasteCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    waste = WasteLog(
        work_order_id=payload.work_order_id,
        product_id=payload.product_id,
        waste_date=payload.waste_date,
        qty=payload.qty,
        reason=payload.reason,
    )
    db.add(waste)
    db.commit()
    db.refresh(waste)
    return {"id": waste.id, "qty": waste.qty}


@router.get("/work-orders/{wo_id}/detail", response_model=dict)
def work_order_detail(wo_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise HTTPException(404, "Work order tidak ditemukan")
    return {
        "id": wo.id,
        "code": wo.code,
        "product_code": wo.product.code,
        "product_name": wo.product.name,
        "planned_qty": wo.planned_qty,
        "produced_qty": wo.produced_qty,
        "status": wo.status,
        "start_date": wo.start_date,
        "due_date": wo.due_date,
        "operations": [
            {
                "id": o.id,
                "workcenter": o.workcenter.name if o.workcenter else None,
                "workcenter_type": o.workcenter.workcenter_type if o.workcenter else None,
                "sequence": o.sequence,
                "status": o.status,
                "qty_completed": o.qty_completed,
                "qty_rejected": o.qty_rejected,
            }
            for o in sorted(wo.operations, key=lambda o: o.sequence)
        ],
    }
