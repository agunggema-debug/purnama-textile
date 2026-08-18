<p align="center">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-2c78c7?style=for-the-badge" alt="Production Ready"/>
  <img src="https://img.shields.io/badge/Arsitektur-On--Premise-1e4f8a?style=for-the-badge" alt="On-Premise"/>
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
</p>

<h1 align="center">Sistem ERP &amp; SCM — Purnama Textile</h1>

<p align="center">
  <b>Enterprise Resource Planning (ERP) &amp; Supply Chain Management (SCM)</b> internal untuk Purnama
  Textile — dirancang berjalan <b>on-premise</b> di jaringan intranet pabrik.
  
</p>

---

## 📦 Modul

Sistem mencakup **6 modul inti** yang tersusun sekuensial mengikuti alur operasional pabrik (dari perencanaan hingga pelaporan keuangan):

| #   | Modul                     | Cakupan Utama                                                                   |
| --- | ------------------------- | ------------------------------------------------------------------------------- |
| 1   | **PPIC**                  | MPS (Master Production Schedule), BOM, MRP                                      |
| 2   | **Purchasing**            | Vendor/Supplier, Purchase Request (PR), Purchase Order (PO), Monitoring & Retur |
| 3   | **Warehouse**             | Goods Receipt, Inventory Tracking, Stock Opname, Material Issue                 |
| 4   | **Produksi**              | Surat Perintah Kerja (SPK), Workcenter Routing, QC & Waste                      |
| 5   | **Distribusi & Logistik** | Delivery Order (DO), Packing List, Fleet/Ekspedisi                              |
| 6   | **Finance & Accounting**  | General Ledger, AP/AR, Payroll, Laporan Keuangan                                |

---

## 🧾 Aturan Bisnis & Integritas Data

> **🛡️ Stok anti-negatif** — Transaksi keluar (Material Issue, Delivery Order, dan selisih Opname yang mengurangi stok) **ditolak** bila melebihi saldo _on-hand_ yang tersedia → HTTP `400 Bad Request`.

> **✅ Barang jadi dari QC** — Hasil inspeksi yang **lolos (passed)** otomatis tercatat ke gudang barang jadi (`finished_goods_in`), sehingga stok siap jual terekam sebelum pengiriman (DO).

> **🧮 Akuntansi otomatis** — Penerimaan barang menjurnal (Debet Persediaan / Kredit Hutang), pengeluaran material menjurnal WIP, dan pengiriman menjurnal HPP & Pendapatan. Laporan **Laba/Rugi** memisahkan HPP dari beban operasional, dan **Neraca** memasukkan laba ditahan periode berjalan sehingga selalu _balance_.

---

## 🛠️ Stack Teknologi

| Layer           | Teknologi                            |
| --------------- | ------------------------------------ |
| **Backend**     | Python · FastAPI · SQLAlchemy        |
| **Database**    | PostgreSQL                           |
| **Caching**     | Redis                                |
| **Autentikasi** | JWT                                  |
| **Frontend**    | React + Vite (dashboard web)         |
| **Deployment**  | Docker & Docker Compose (on-premise) |

---

## 🚀 Menjalankan dengan Docker (produksi / on-premise)

```bash
# 1. Siapkan lingkungan backend (ganti isi sesuai kebutuhan server)
cp backend/.env.example backend/.env

# 2. Build & jalankan seluruh layanan
docker compose up -d --build
```

| Layanan            | Alamat                     |
| ------------------ | -------------------------- |
| Frontend           | http://localhost           |
| Backend API        | http://localhost:8000      |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 🧑‍💻 Menjalankan Backend secara Lokal (development)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Inisialisasi skema & data master (tanpa PostgreSQL gunakan SQLite):
python -m app.db.init_db

# Jalankan server development:
uvicorn app.main:app --reload
```

> 💡 Konfigurasi koneksi DB diatur melalui `DATABASE_URL` — lihat `backend/.env.example` untuk opsi SQLite vs PostgreSQL.

---

## 🎨 Menjalankan Frontend secara Lokal (development)

```bash
cd frontend
npm install
npm run dev
```

---

## ✅ Smoke Test (Alur End-to-End)

Smoke test memverifikasi alur inti: **Login → PPIC/MRP → PO → Goods Receipt → Material Issue/Opname → Produksi (SPK + QC yang mengisi stok barang jadi) → DO/Packing → Laporan keuangan & Payroll**, termasuk **penolakan stok negatif**.

```bash
cd backend
# Gunakan database uji SQLite (tidak menyentuh PostgreSQL produksi):
$env:DATABASE_URL='sqlite:///./smoke_erp.db'   # Windows PowerShell
$env:SEED_ON_INIT='1'
python -m app.db.init_db
$env:SEED_ON_INIT='0'
python -m tests.smoke_test    # diharapkan: 28 lolos, 0 gagal
```

---

## 👤 Akun Default

Dibuat otomatis saat proses _seed_:

| Username |  Password  | Role  |
| :------: | :--------: | :---: |
| `admin`  | `admin123` | admin |

> ⚠️ **Penting:** Segera ganti kata sandi default ini setelah instalasi pertama.

---

## 💾 Backup Database (NAS)

Jalankan script di folder `scripts/` melalui _cron job_; hasil _dump_ disimpan ke perangkat **NAS** terpisah sebagai lapisan perlindungan data. Lihat panduan lengkap di `scripts/backup.md`.

---

## 📁 Struktur Direktori

```
purnama-textile/
├─ backend/            # FastAPI backend (models, routers, services, seed)
├─ frontend/           # React dashboard
├─ scripts/            # Backup & utilitas operasional
├─ docker-compose.yml  # Orkestrasi layanan on-premise
├─ PRD_ERP_Purnama_Textile.md
└─ README.md
```

---

<img width="1907" height="908" alt="image" src="https://github.com/user-attachments/assets/8d905bfd-03d2-4585-9343-73642b8fbe34" />


<p align="center">
  <sub>© Purnama Textile — Sistem ERP &amp; SCM On-Premise</sub>
</p>
```

---

<img width="1919" height="904" alt="image" src="https://github.com/user-attachments/assets/afbac0c5-d326-4000-a340-f76a80a95562" />



---
<img width="1882" height="899" alt="image" src="https://github.com/user-attachments/assets/81e2eff5-5960-4a11-93a6-db9c5f634927" />


```


