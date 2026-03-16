from sqlalchemy.orm import Session

from app.repositories.inventory import inventory_repository
from app.core.enums import FinalStatus
from app.repositories.expenses import expense_repository
from app.repositories.phones import phone_repository
from app.schemas.phone import PhoneCreate, PhoneSell, PhoneUpdate


class PhoneService:
    def _attach_calculated_fields(self, db: Session, phone):
        phone_expenses_total = expense_repository.get_phone_expenses_total(db, phone.id)
        total_cost = float(phone.buy_price) + float(phone_expenses_total)
        profit = None

        if phone.sell_price is not None:
            profit = float(phone.sell_price) - total_cost

        setattr(phone, "phone_expenses_total", phone_expenses_total)
        setattr(phone, "total_cost", total_cost)
        setattr(phone, "profit", profit)
        return phone

    def create_phone(self, db: Session, phone_in: PhoneCreate):
        phone = phone_repository.create(db, phone_in)
        return self._attach_calculated_fields(db, phone)

    def list_phones(self, db: Session):
        phones = phone_repository.list_all(db)
        return [self._attach_calculated_fields(db, phone) for phone in phones]

    def get_phone(self, db: Session, phone_id: int):
        phone = phone_repository.get_by_id(db, phone_id)
        if phone is None:
            return None
        return self._attach_calculated_fields(db, phone)

    def update_phone(self, db: Session, phone_id: int, phone_in: PhoneUpdate):
        phone = phone_repository.get_by_id(db, phone_id)
        if phone is None:
            return None

        phone = phone_repository.update(db, phone, phone_in)
        return self._attach_calculated_fields(db, phone)

    def sell_phone(self, db: Session, phone_id: int, sell_in: PhoneSell):
        phone = phone_repository.get_by_id(db, phone_id)
        if phone is None:
            return None

        phone.sell_price = sell_in.sell_price
        phone.sell_date = sell_in.sell_date
        phone.final_status = FinalStatus.SOLD.value

        db.add(phone)
        db.commit()
        db.refresh(phone)

        return self._attach_calculated_fields(db, phone)

    def return_phone(self, db: Session, phone_id: int):
        phone = phone_repository.get_by_id(db, phone_id)
        if phone is None:
            return None

        phone.final_status = FinalStatus.RETURNED.value

        db.add(phone)
        db.commit()
        db.refresh(phone)

        return self._attach_calculated_fields(db, phone)

    def delete_phone(self, db: Session, phone_id: int):
        phone = phone_repository.get_by_id(db, phone_id)
        if phone is None:
            return None

        expense_repository.delete_by_phone_id(db, phone.id)
        inventory_repository.delete_movements_by_phone_id(db, phone.id)

        return phone_repository.delete(db, phone)


phone_service = PhoneService()