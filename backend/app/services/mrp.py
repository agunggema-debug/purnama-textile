"""Material Requirements Planning (MRP): hitung kebutuhan material dari jadwal produksi."""
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from sqlalchemy.orm import Session

from app.models.ppic import BOM, MPS
from app.models.warehouse import InventoryItem
from app.services.stock import get_on_hand


def _round_qty(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_mrp(db: Session, mps_id: int) -> dict:
    """Hitung kebutuhan material untuk sebuah MPS (satu baris jadwal)."""
    mps = db.get(MPS, mps_id)
    if mps is None:
        raise ValueError("MPS tidak ditemukan")

    bom = (
        db.query(BOM)
        .filter(BOM.product_id == mps.product_id, BOM.is_active.is_(True))
        .first()
    )
    if bom is None:
        raise ValueError("BOM aktif tidak ditemukan untuk produk ini")

    # jumlah batch BOM yang dibutuhkan untuk memproduksi qty MPS
    batches = mps.qty / bom.output_qty if bom.output_qty else Decimal("1")

    requirements: List[dict] = []
    for line in bom.lines:
        gross = Decimal(line.qty_per_output) * Decimal(batches)
        gross *= Decimal("1") + Decimal(line.waste_factor or 0)
        gross = _round_qty(gross)
        on_hand = get_on_hand(db, line.material_id)
        net = _round_qty(max(gross - on_hand, Decimal("0")))
        requirements.append(
            {
                "material_id": line.material_id,
                "material_code": line.material.code,
                "material_name": line.material.name,
                "gross_requirement": gross,
                "on_hand": on_hand,
                "net_requirement": net,
                "uom": line.material.uom.name if line.material.uom else "",
            }
        )

    return {
        "mps_id": mps.id,
        "mps_code": mps.code,
        "product_id": mps.product_id,
        "product_code": mps.product.code,
        "planned_qty": mps.qty,
        "bom_code": bom.code,
        "requirements": requirements,
    }
