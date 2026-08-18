from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session


def parse_date(value) -> Optional[date]:
    """Normalisasi nilai tanggal (str ISO / date) menjadi objek date."""
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def gen_code(db: Session, model, prefix: str, sep: str = "-") -> str:
    """Buat kode dokumen berurutan: PREFIX-YYYYMMDD-XXXX."""
    today = date.today().strftime("%Y%m%d")
    count = db.query(model).count() + 1
    return f"{prefix}{sep}{today}{sep}{count:04d}"


def next_number(model, db: Session, prefix: str) -> str:
    return gen_code(db, model, prefix)
