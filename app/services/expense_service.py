from sqlalchemy.orm import Session

from app.core.enums import ExpenseType
from app.repositories.expenses import expense_repository
from app.repositories.phones import phone_repository
from app.repositories.shipments import shipment_repository
from app.schemas.expense import ExpenseCreate, PhoneExpenseCreate


class ExpenseService:
    def create_expense(self, db: Session, expense_in: ExpenseCreate):
        if expense_in.phone_id is not None:
            phone = phone_repository.get_by_id(db, expense_in.phone_id)
            if phone is None:
                return None, "phone_not_found"

        if expense_in.shipment_id is not None:
            shipment = shipment_repository.get_by_id(db, expense_in.shipment_id)
            if shipment is None:
                return None, "shipment_not_found"

        expense = expense_repository.create(db, expense_in)
        return expense, None

    def add_phone_expense(self, db: Session, phone_id: int, expense_in: PhoneExpenseCreate):
        phone = phone_repository.get_by_id(db, phone_id)
        if phone is None:
            return None

        full_expense = ExpenseCreate(
            type=ExpenseType.PHONE.value,
            category=expense_in.category,
            amount=expense_in.amount,
            date=expense_in.date,
            phone_id=phone_id,
            shipment_id=None,
        )
        return expense_repository.create(db, full_expense)

    def list_expenses(self, db: Session):
        return expense_repository.list_all(db)

    def list_phone_expenses(self, db: Session, phone_id: int):
        return expense_repository.list_by_phone_id(db, phone_id)

    def delete_expense(self, db: Session, expense_id: int):
        expense = expense_repository.get_by_id(db, expense_id)
        if expense is None:
            return None

        return expense_repository.hard_delete(db, expense)

    def get_phone_expenses_total(self, db: Session, phone_id: int) -> float:
        return expense_repository.get_phone_expenses_total(db, phone_id)


expense_service = ExpenseService()