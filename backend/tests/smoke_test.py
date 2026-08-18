"""Smoke test end-to-end alur inti ERP Purnama Textile (via FastAPI TestClient).

Menjalankan:  python -m tests.smoke_test
Menggunakan database SQLite/PostgreSQL sesuai DATABASE_URL yang aktif.
"""
import os

os.environ.setdefault("SEED_ON_INIT", "0")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

PASS = 0
FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [OK] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {extra}")


def main():
    print("== Login ==")
    r = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    check("login admin", r.status_code == 200, r.text)
    token = r.json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/auth/me", headers=H)
    check("auth/me", r.status_code == 200 and r.json()["role"] == "admin")

    print("== PPIC / MRP ==")
    mps = client.get("/api/ppic/mps", headers=H).json()
    check("MPS seeded", len(mps) >= 1)
    mps_id = mps[0]["id"]
    r = client.get(f"/api/ppic/mps/{mps_id}/mrp", headers=H)
    check("MRP run", r.status_code == 200, r.text)
    mrp = r.json()
    check("MRP requirements", len(mrp.get("requirements", [])) >= 1)

    print("== Master lookup ==")
    products = client.get("/api/master/products", headers=H).json()
    vendors = client.get("/api/master/vendors", headers=H).json()
    customers = client.get("/api/master/customers", headers=H).json()
    locations = client.get("/api/master/locations", headers=H).json()
    check("products/vendors/customers/locations exist",
          products and vendors and customers and locations)
    vendor = vendors[0]
    customer = customers[0]
    raw_prod = next(p for p in products if p["product_type"] == "raw_material")
    fg_prod = next(p for p in products if p["product_type"] == "finished_good")
    loc_raw = next(l for l in locations if l["warehouse_type"] == "raw_material")
    loc_fg = next(l for l in locations if l["warehouse_type"] == "finished_good")

    print("== Purchasing: PO ==")
    r = client.post("/api/purchasing/po/full", headers=H, json={
        "vendor_id": vendor["id"],
        "lines": [{"product_id": raw_prod["id"], "qty": 100, "unit_price": 55000}],
    })
    check("create PO", r.status_code == 200, r.text)
    po_id = r.json()["id"]
    r = client.post(f"/api/purchasing/po/{po_id}/approve", headers=H)
    check("approve PO", r.status_code == 200 and r.json()["status"] == "approved", r.text)

    print("== Warehouse: Goods Receipt + Material Issue + Opname ==")
    r = client.post("/api/warehouse/goods-receipts/full", headers=H, json={
        "po_id": po_id, "vendor_id": vendor["id"],
        "lines": [{"product_id": raw_prod["id"], "location_id": loc_raw["id"],
                   "qty": 100, "unit_cost": 55000}],
    })
    check("create Goods Receipt", r.status_code == 200 and r.json().get("journal_id"), r.text)

    inv_raw = next((i for i in client.get("/api/warehouse/inventory", headers=H).json()
                    if i["product_id"] == raw_prod["id"] and i["location_code"] == loc_raw["code"]), None)
    check("stock increased after GR", inv_raw and float(inv_raw["on_hand"]) > 0, str(inv_raw))

    r = client.post("/api/warehouse/material-issues/full", headers=H, json={
        "lines": [{"product_id": raw_prod["id"], "location_id": loc_raw["id"], "qty": 30}],
    })
    check("Material Issue", r.status_code == 200 and r.json().get("journal_id"), r.text)

    r = client.post("/api/warehouse/opnames/full", headers=H, json={
        "lines": [{"product_id": raw_prod["id"], "location_id": loc_raw["id"],
                   "system_qty": 70, "actual_qty": 68}],
    })
    check("Stock Opname", r.status_code == 200, r.text)

    # Validasi stok anti-negatif: pengeluaran melebihi saldo harus ditolak (400)
    r = client.post("/api/warehouse/material-issues/full", headers=H, json={
        "lines": [{"product_id": raw_prod["id"], "location_id": loc_raw["id"], "qty": 99999}],
    })
    check("over-issue rejected (anti-negative stock)", r.status_code == 400, r.text)

    movements = client.get("/api/warehouse/movements", headers=H).json()
    check("movements recorded", len(movements) >= 3)

    # Produksi dilakukan lebih dulu agar barang jadi tersedia sebelum DO.
    print("== Production: SPK + QC == (mengisi stok barang jadi)")
    workcenters = client.get("/api/master/workcenters", headers=H).json()
    r = client.post("/api/production/work-orders/full", headers=H, json={
        "product_id": fg_prod["id"], "planned_qty": 12,
        "start_date": "2025-08-20", "due_date": "2025-08-30",
        "workcenter_ids": [wc["id"] for wc in workcenters],
    })
    check("create SPK/Work Order", r.status_code == 200, r.text)
    wo_id = r.json()["id"]
    r = client.post("/api/production/qc/full", headers=H, json={
        "work_order_id": wo_id, "product_id": fg_prod["id"],
        "inspected_qty": 12, "passed_qty": 10, "rejected_qty": 2, "decision": "pass",
    })
    check("QC result", r.status_code == 200 and float(r.json().get("passed_qty") or 0) == 10.0, r.text)

    # Barang hasil QC yang lolos harus tercatat sebagai stok barang jadi
    fg_qc = next((i for i in client.get("/api/warehouse/inventory", headers=H).json()
                  if i["product_id"] == fg_prod["id"] and i["location_code"] == loc_fg["code"]), None)
    check("finished goods stocked after QC", fg_qc and float(fg_qc["on_hand"]) >= 10, str(fg_qc))

    r = client.get(f"/api/production/work-orders/{wo_id}/detail", headers=H)
    check("WO detail+operations", r.status_code == 200 and len(r.json()["operations"]) >= 1, r.text)

    print("== Distribution: SO + DO + Packing ==")
    r = client.post("/api/distribution/sales-orders/full", headers=H, json={
        "customer_id": customer["id"],
        "lines": [{"product_id": fg_prod["id"], "qty": 10, "unit_price": 60000,
                   "delivery_date": "2025-09-01"}],
    })
    check("create SO", r.status_code == 200, r.text)
    so_id = r.json()["id"]

    r = client.post("/api/distribution/delivery-orders/full", headers=H, json={
        "sales_order_id": so_id, "customer_id": customer["id"],
        "lines": [{"product_id": fg_prod["id"], "location_id": loc_fg["id"], "qty": 10}],
    })
    check("create DO (sale out)", r.status_code == 200, r.text)
    do_payload = r.json()
    check("DO revenue>0", float(do_payload["revenue"]) > 0, str(do_payload))

    # Setelah stok barang jadi habis, pengiriman tambahan harus ditolak (400)
    r = client.post("/api/distribution/delivery-orders/full", headers=H, json={
        "customer_id": customer["id"],
        "lines": [{"product_id": fg_prod["id"], "location_id": loc_fg["id"], "qty": 5}],
    })
    check("delivery over-stock rejected (anti-negative stock)", r.status_code == 400, r.text)

    r = client.post("/api/distribution/packing-lists/full", headers=H, json={
        "delivery_order_id": do_payload["id"], "total_packages": 2,
        "lines": [{"product_id": fg_prod["id"], "qty": 10}],
    })
    check("create Packing List", r.status_code == 200, r.text)

    print("== Finance: reports + payroll ==")
    pl = client.get("/api/finance/reports/profit-loss", headers=H).json()
    check("Profit & Loss revenue>0", float(pl.get("revenue", 0)) > 0, str(pl))
    bs = client.get("/api/finance/reports/balance-sheet", headers=H).json()
    check("Balance Sheet assets counted", float(bs.get("assets", 0)) != 0, str(bs))
    cf = client.get("/api/finance/reports/cash-flow", headers=H).json()
    check("Cash Flow present", "net_cash_flow" in cf)

    r = client.post("/api/finance/payroll-runs/generate?month=8&year=2025", headers=H)
    check("generate payroll", r.status_code == 200 and r.json().get("employee_count", 0) >= 1, r.text)

    journals = client.get("/api/finance/journals", headers=H).json()
    check("journals auto-posted", len(journals) >= 4, f"found {len(journals)}")

    print(f"\n===== HASIL: {PASS} lolos, {FAIL} gagal =====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())