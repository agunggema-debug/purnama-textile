"""Inisialisasi database: buat tabel (idempotent) dan jalankan seed."""
from sqlalchemy import inspect

import app.models  # noqa: F401  (daftarkan seluruh model pada metadata)
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.models.user import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin is None and settings.SEED_ON_INIT:
            from app.seed import run_seed

            run_seed(db)
            print("[init_db] Seed data selesai.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Database siap digunakan.")
