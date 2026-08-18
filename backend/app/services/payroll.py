"""Layanan penggajian: hitung upah karyawan per periode."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.finance import PayrollLine, PayrollRun
from app.models.master import Employee
from app.services.utils import gen_code


def run_payroll(db: Session, month: int, year: int) -> PayrollRun:
    employees = db.query(Employee).filter(Employee.is_active.is_(True)).all()
    run = PayrollRun(
        code=gen_code(db, PayrollRun, "PAY"),
        period_month=month,
        period_year=year,
        total_amount=Decimal("0"),
        status="draft",
    )
    db.add(run)
    db.flush()

    total = Decimal("0")
    for emp in employees:
        base = Decimal(emp.base_salary)
        allowance = Decimal(emp.daily_allowance)
        # contoh sederhana: lembur 5% dari gaji pokok, potongan 2% (asuransi/sosial)
        overtime = (base * Decimal("0.05")).quantize(Decimal("0.01"))
        deduction = (base * Decimal("0.02")).quantize(Decimal("0.01"))
        net = base + overtime + allowance - deduction
        total += net
        run.lines.append(
            PayrollLine(
                employee_id=emp.id,
                base_salary=base,
                overtime=overtime,
                allowance=allowance,
                deduction=deduction,
                net_pay=net,
            )
        )

    run.total_amount = total.quantize(Decimal("0.01"))
    db.commit()
    db.refresh(run)
    return run
