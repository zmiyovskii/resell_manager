from datetime import datetime
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.models.expense import Expense

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate


class ExpenseRepository:
    def create(self, db: Session, expense_in: ExpenseCreate) -> Expense:
        expense = Expense(
            type=expense_in.type,
            category=expense_in.category,
            amount=expense_in.amount,
            date=expense_in.date,
            phone_id=expense_in.phone_id,
            shipment_id=expense_in.shipment_id,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    def list_all(self, db: Session) -> Sequence[Expense]:
        stmt = (
            select(Expense)
            .where(Expense.deleted_at.is_(None))
            .order_by(Expense.id.desc())
        )
        return db.execute(stmt).scalars().all()

    def list_by_phone_id(self, db: Session, phone_id: int) -> Sequence[Expense]:
        stmt = (
            select(Expense)
            .where(
                Expense.phone_id == phone_id,
                Expense.deleted_at.is_(None),
            )
            .order_by(Expense.id.desc())
        )
        return db.execute(stmt).scalars().all()

    def get_by_id(self, db: Session, expense_id: int) -> Expense | None:
        stmt = select(Expense).where(
            Expense.id == expense_id,
            Expense.deleted_at.is_(None),
        )
        return db.execute(stmt).scalars().first()

    def hard_delete(self, db: Session, expense: Expense):
        db.delete(expense)
        db.commit()
        return expense

    def delete_by_phone_id(self, db: Session, phone_id: int):
        stmt = delete(Expense).where(Expense.phone_id == phone_id)
        db.execute(stmt)
        db.commit()

    def delete_by_shipment_id(self, db: Session, shipment_id: int):
        stmt = delete(Expense).where(Expense.shipment_id == shipment_id)
        db.execute(stmt)
        db.commit()

    def soft_delete(self, db: Session, expense: Expense) -> Expense:
        expense.deleted_at = datetime.utcnow()
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    def get_phone_expenses_total(self, db: Session, phone_id: int) -> float:
        stmt = (
            select(func.coalesce(func.sum(Expense.amount), 0.0))
            .where(
                Expense.phone_id == phone_id,
                Expense.deleted_at.is_(None),
            )
        )
        result = db.execute(stmt).scalar_one()
        return float(result or 0.0)


expense_repository = ExpenseRepository()