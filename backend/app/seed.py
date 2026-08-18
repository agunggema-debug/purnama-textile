"""Seed data awal: master, chart of accounts, akun admin, dan contoh PPIC."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.finance import Account
from app.models.master import (
    Customer,
    Employee,
    Product,
    ProductCategory,
    UoM,
    Vendor,
    WarehouseLocation,
    Workcenter,
)
from app.models.ppic import BOM, BOMLine, MPS
from app.models.user import User

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def _make_accounts(db: Session):
    accounts = [
        ("1-1000", "Kas & Bank", "asset"),
        ("1-1100", "Persediaan Bahan Baku", "asset"),
        ("1-1150", "Barang Dalam Proses (WIP)", "asset"),
        ("1-1200", "Persediaan Barang Jadi", "asset"),
        ("1-1300", "Piutang Usaha (AR)", "asset"),
        ("2-2000", "Hutang Usaha (AP)", "liability"),
        ("3-3000", "Modal Pemilik", "equity"),
        ("4-4000", "Pendapatan Penjualan", "revenue"),
        ("5-5000", "Harga Pokok Penjualan (HPP)", "expense"),
        ("5-5100", "Beban Operasional", "expense"),
        ("5-5200", "Beban Gaji", "expense"),
        ("5-5400", "Selisih Stok (Opname)", "expense"),
    ]
    for code, name, type_ in accounts:
        if not db.query(Account).filter(Account.code == code).first():
            db.add(Account(code=code, name=name, account_type=type_))


def _make_master(db: Session):
    uom = {}
    for code in ("kg", "meter", "pcs", "roll", "liter", "pack"):
        uom[code] = db.query(UoM).filter(UoM.code == code).first() or UoM(code=code, name=code)
        db.add(uom[code])
    db.flush()

    cate = {}
    for code, name in (("RM", "Bahan Baku"), ("SF", "Setengah Jadi"), ("FG", "Barang Jadi")):
        cate[code] = db.query(ProductCategory).filter(ProductCategory.code == code).first() \
            or ProductCategory(code=code, name=name)
        db.add(cate[code])
    db.flush()

    products = {
        "benang": dict(code="RM-BNG-001", name="Benang Cotton Ne 24", category_id=cate["RM"].id,
                       uom_id=uom["kg"].id, product_type="raw_material", standard_cost=Decimal("50000")),
        "kain_greige": dict(code="SF-KG-001", name="Kain Greige Rajut", category_id=cate["SF"].id,
                            uom_id=uom["meter"].id, product_type="semi_finished", standard_cost=Decimal("30000")),
        "pewarna": dict(code="RM-PWN-001", name="Bahan Pewarna Reaktif", category_id=cate["RM"].id,
                        uom_id=uom["kg"].id, product_type="raw_material", standard_cost=Decimal("80000")),
        "kain_jadi": dict(code="FG-KJ-001", name="Kain Cetak Jadi Premium", category_id=cate["FG"].id,
                          uom_id=uom["meter"].id, product_type="finished_good",
                          standard_cost=Decimal("45000"), standard_price=Decimal("60000")),
        "bedcover": dict(code="FG-BC-001", name="Bed Cover Set Queen", category_id=cate["FG"].id,
                         uom_id=uom["pcs"].id, product_type="finished_good",
                         standard_cost=Decimal("120000"), standard_price=Decimal("180000")),
        "benang_jahit": dict(code="RM-BJ-001", name="Benang Jahit Nilon", category_id=cate["RM"].id,
                             uom_id=uom["roll"].id, product_type="raw_material", standard_cost=Decimal("15000")),
    }
    stored = {}
    for key, p in products.items():
        existing = db.query(Product).filter(Product.code == p["code"]).first()
        if existing:
            stored[key] = existing
        else:
            stored[key] = Product(**p)
            db.add(stored[key])
    db.flush()

    locations = {
        "gudang_baku": dict(code="WH-RM-01", name="Gudang Bahan Baku - Rak A", warehouse_type="raw_material"),
        "gudang_jadi": dict(code="WH-FG-01", name="Gudang Barang Jadi - Zona 1", warehouse_type="finished_good"),
    }
    for key, loc in locations.items():
        if not db.query(WarehouseLocation).filter(WarehouseLocation.code == loc["code"]).first():
            db.add(WarehouseLocation(**loc))

    if not db.query(Customer).first():
        db.add(Customer(code="CUS-001", name="PT Ekspor Maju Indonesia", contact_person="Bpk. Andi",
                        phone="021-5550100", email="andi@ekspormaju.co.id", address="Jakarta"))
    if not db.query(Vendor).first():
        db.add(Vendor(code="VEN-001", name="PT Benang Jaya", category="Bahan Baku - Benang",
                      contact_person="Ibu Sari", phone="021-5550200", email="cs@benangjaya.co.id",
                      address="Bandung"))
        db.add(Vendor(code="VEN-002", name="CV Pewarna Nusantara", category="Bahan Baku - Pewarna",
                      contact_person="Bpk. Budi", phone="021-5550300", email="sales@pewarnanusantara.co.id",
                      address="Jakarta"))

    db.flush()

    workcenters = [
        ("WC-KNIT", "Mesin Knitting", "knitting"),
        ("WC-DYE", "Line Dyeing & Printing", "dyeing_printing"),
        ("WC-FIN", "Special Treatment / Finishing", "special_treatment"),
        ("WC-CUTSEW", "Dept. Cut & Sew", "cut_sew"),
    ]
    for code, name, wtype in workcenters:
        if not db.query(Workcenter).filter(Workcenter.code == code).first():
            db.add(Workcenter(code=code, name=name, workcenter_type=wtype))

    if not db.query(Employee).first():
        employees = [
            ("EMP-001", "Rudi Setiawan", "Operator Knitting", "produksi", 4000000, 25000),
            ("EMP-002", "Siti Aminah", "Operator Dyeing", "produksi", 4200000, 25000),
            ("EMP-003", "Joko Susilo", "QC Inspector", "produksi", 4500000, 30000),
            ("EMP-004", "Dewi Lestari", "Supervisor Gudang", "warehouse", 5000000, 35000),
        ]
        for emp_no, name, pos, dept, salary, allowance in employees:
            db.add(Employee(employee_no=emp_no, name=name, position=pos, department=dept,
                            base_salary=Decimal(salary), daily_allowance=Decimal(allowance)))

    db.flush()
    return stored


def _make_ppic_example(db: Session, products):
    bom = db.query(BOM).filter(BOM.code == "BOM-BC-001").first()
    if bom is None:
        bom = BOM(code="BOM-BC-001", product_id=products["bedcover"].id,
                  output_qty=Decimal("1"), is_active=True,
                  notes="BOM Bed Cover Set Queen (output 1 set)")
        bom.lines.append(BOMLine(material_id=products["kain_jadi"].id,
                                 qty_per_output=Decimal("6.5"), waste_factor=Decimal("0.05")))
        bom.lines.append(BOMLine(material_id=products["benang_jahit"].id,
                                 qty_per_output=Decimal("2"), waste_factor=Decimal("0.03")))
        db.add(bom)
        db.flush()

    if not db.query(MPS).first():
        db.add(MPS(code="MPS-001", product_id=products["bedcover"].id,
                   schedule_date=date.today() + timedelta(days=7), qty=Decimal("10"),
                   order_type="make_to_order", status="approved"))
    db.flush()


def run_seed(db: Session) -> None:
    _make_accounts(db)
    products = _make_master(db)
    _make_ppic_example(db, products)

    if not db.query(User).filter(User.username == ADMIN_USERNAME).first():
        db.add(User(username=ADMIN_USERNAME, full_name="Administrator Purnama Textile",
                    email="admin@purnamatextile.co.id",
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    role="admin", is_active=True))
    db.commit()
    print(f"[seed] Akun default dibuat: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")