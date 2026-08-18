# Sistem ERP & SCM — Purnama Textile (On-Premise)

Sistem Enterprise Resource Planning (ERP) & Supply Chain Management (SCM) internal
untuk Purnama Textile, dirancang berjalan **on-premise** di jaringan intranet pabrik.

## Modul
1. **PPIC** — MPS, BOM, MRP (perencanaan kebutuhan material)
2. **Purchasing** — Vendor, PR, PO, Monitoring & Retur
3. **Warehouse** — Goods Receipt, Inventory Tracking, Stock Opname, Material Issue
4. **Produksi** — Surat Perintah Kerja (SPK), Workcenter Routing, QC & Waste
5. **Distribusi & Logistik** — Delivery Order, Packing List, Fleet
6. **Finance & Accounting** — General Ledger, AP/AR, Payroll, Laporan Keuangan

## Aturan Bisnis & Integritas Data
- **Stok anti-negatif:** transaksi keluar (Material Issue, Delivery Order, dan selisih Opname
  yang mengurangi stok) **ditolak** bila melebihi saldo on-hand yang tersedia → HTTP `400 Bad Request`.
- **Barang jadi dari QC:** hasil inspeksi yang **lolos (passed)** otomatis dicatat ke gudang
  barang jadi (`finished_goods_in`), sehingga stok siap jual tercatat sebelum pengiriman (DO).
- **Akuntansi otomatis:** penerimaan barang menjurnal (Debet Persediaan / Kredit Hutang),
  pengeluaran material menjurnal WIP, dan pengiriman menjurnal HPP & Pendapatan. Laporan
  **Laba/Rugi** memisahkan HPP dari beban operasional, dan **Neraca** memasukkan laba ditahan
  periode berjalan sehingga selalu *balance*.

## Stack
- **Backend:** Python FastAPI, SQLAlchemy, PostgreSQL, Redis, JWT Auth
- **Frontend:** React + Vite (dashboard web)
- **Deployment:** Docker & Docker Compose (on-premise)

## Menjalankan dengan Docker (produksi/on-premise)
```bash
cp backend/.env.example backend/.env
docker compose up -d --build
```
- Frontend : http://localhost
- Backend  : http://localhost:8000
- API Docs : http://localhost:8000/docs

## Menjalankan Backend secara lokal (development)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
# Base model (tanpa PostgreSQL) — lihat backend/.env.example untuk konfigurasi
python -m app.db.init_db
uvicorn app.main:app --reload
($env:DATABASE_URL='sqlite:///./purnama_erp.db'                           
>> .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload )
```

## Menjalankan Frontend secara lokal (development)
```bash
cd frontend
npm install
npm run dev
```

## Menjalankan Smoke Test (alur end-to-end)
Smoke test memverifikasi alur inti: Login → PPIC/MRP → PO → Goods Receipt → Material Issue /
Opname → Produksi (SPK + QC yang mengisi stok barang jadi) → DO / Packing → Laporan keuangan &
Payroll — termasuk **penolakan stok negatif**.

```bash
cd backend
# Gunakan database uji SQLite (tidak menyentuh PostgreSQL produksi):
$env:DATABASE_URL='sqlite:///./smoke_erp.db'   # Windows PowerShell
$env:SEED_ON_INIT='1'
python -m app.db.init_db
$env:SEED_ON_INIT='0'
python -m tests.smoke_test    # diharapkan: 28 lolos, 0 gagal
```

## Akun Default (dibuat saat seed)
| Username | Password | Role |
|----------|----------|------|
| admin    | admin123 | admin |

## Backup Database (NAS)
Jalankan script di `scripts/` melalui *cron job*; hasil *dump* disimpan ke
perangkat NAS terpisah. Lihat `scripts/backup.md`.

## Struktur Direktori
```
backend/    FastAPI backend (models, routers, services, seed)
frontend/   React dashboard
scripts/    Backup & utilitas ops
docker-compose.yml
```
