from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ExpenseCategory, ExpenseType, LogisticsStatus
from app.models.phone import Phone
from app.repositories.expenses import expense_repository
from app.repositories.phones import phone_repository
from app.repositories.shipments import shipment_repository
from app.schemas.expense import ExpenseCreate
from app.schemas.shipment import AssignShipmentRequest, ShipmentCreate, ShipmentUpdate


class ShipmentService:
    def _attach_shipment_stats(self, db: Session, shipment):
        phones = db.execute(
            select(Phone)
            .where(
                Phone.shipment_id == shipment.id,
                Phone.deleted_at.is_(None),
            )
            .order_by(Phone.display_id.asc())
        ).scalars().all()

        phones_count = len(phones)
        sold_phones = [phone for phone in phones if phone.final_status == "sold"]
        sold_count = len(sold_phones)
        remaining_count = phones_count - sold_count

        buy_total = float(sum(float(phone.buy_price or 0) for phone in phones))
        revenue_total = float(sum(float(phone.sell_price or 0) for phone in sold_phones))

        expenses_total = 0.0
        for phone in phones:
            phone_expenses = expense_repository.get_phone_expenses_total(db, phone.id)
            expenses_total += float(phone_expenses)

        profit = revenue_total - buy_total - expenses_total

        setattr(shipment, "phones", phones)
        setattr(shipment, "phones_count", phones_count)
        setattr(shipment, "sold_count", sold_count)
        setattr(shipment, "remaining_count", remaining_count)
        setattr(shipment, "buy_total", buy_total)
        setattr(shipment, "expenses_total", expenses_total)
        setattr(shipment, "revenue_total", revenue_total)
        setattr(shipment, "profit", profit)

        return shipment

    def create_shipment(self, db: Session, shipment_in: ShipmentCreate):
        shipment = shipment_repository.create(db, shipment_in)
        return self._attach_shipment_stats(db, shipment)

    def list_shipments(self, db: Session):
        shipments = shipment_repository.list_all(db)
        return [self._attach_shipment_stats(db, shipment) for shipment in shipments]

    def get_shipment(self, db: Session, shipment_id: int):
        shipment = shipment_repository.get_by_id(db, shipment_id)
        if shipment is None:
            return None
        return self._attach_shipment_stats(db, shipment)

    def update_shipment(self, db: Session, shipment_id: int, shipment_in: ShipmentUpdate):
        shipment = shipment_repository.get_by_id(db, shipment_id)
        if shipment is None:
            return None

        shipment = shipment_repository.update(db, shipment, shipment_in)
        return self._attach_shipment_stats(db, shipment)

    def delete_shipment(self, db: Session, shipment_id: int):
        shipment = shipment_repository.get_by_id(db, shipment_id)
        if shipment is None:
            return None

        return shipment_repository.soft_delete(db, shipment)

    def assign_phone_to_shipment(self, db: Session, phone_id: int, assign_in: AssignShipmentRequest):
        phone = phone_repository.get_by_id(db, phone_id)
        if phone is None:
            return None, "phone_not_found"

        shipment = shipment_repository.get_by_id(db, assign_in.shipment_id)
        if shipment is None:
            return None, "shipment_not_found"

        carrier_fee = (
            assign_in.carrier_fee
            if assign_in.carrier_fee is not None
            else float(shipment.default_carrier_fee)
        )

        phone.shipment_id = shipment.id
        phone.logistics_status = LogisticsStatus.IN_SHIPMENT.value

        db.add(phone)
        db.commit()
        db.refresh(phone)

        expense_in = ExpenseCreate(
            type=ExpenseType.PHONE.value,
            category=ExpenseCategory.CARRIER_FEE.value,
            amount=carrier_fee,
            date=assign_in.expense_date,
            phone_id=phone.id,
            shipment_id=shipment.id,
        )
        expense_repository.create(db, expense_in)

        return phone, None


shipment_service = ShipmentService()