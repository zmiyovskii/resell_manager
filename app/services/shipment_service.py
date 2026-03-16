from sqlalchemy.orm import Session

from app.core.enums import ExpenseCategory, ExpenseType, LogisticsStatus
from app.repositories.expenses import expense_repository
from app.repositories.phones import phone_repository
from app.repositories.shipments import shipment_repository
from app.schemas.expense import ExpenseCreate
from app.schemas.shipment import AssignShipmentRequest, ShipmentCreate, ShipmentUpdate


class ShipmentService:
    def create_shipment(self, db: Session, shipment_in: ShipmentCreate):
        return shipment_repository.create(db, shipment_in)

    def list_shipments(self, db: Session):
        return shipment_repository.list_all(db)

    def get_shipment(self, db: Session, shipment_id: int):
        return shipment_repository.get_by_id(db, shipment_id)

    def update_shipment(self, db: Session, shipment_id: int, shipment_in: ShipmentUpdate):
        shipment = shipment_repository.get_by_id(db, shipment_id)
        if shipment is None:
            return None

        return shipment_repository.update(db, shipment, shipment_in)

    def delete_shipment(self, db: Session, shipment_id: int):
        shipment = shipment_repository.get_by_id(db, shipment_id)
        if shipment is None:
            return False

        phones = phone_repository.list_all(db)
        for phone in phones:
            if phone.shipment_id == shipment.id:
                phone.shipment_id = None
                db.add(phone)

        db.commit()
        expense_repository.delete_by_shipment_id(db, shipment.id)
        shipment_repository.delete(db, shipment)
        return True

    def assign_phone_to_shipment(self, db: Session, phone_id: int, assign_in: AssignShipmentRequest):
        # ТУТ phone_id = звичайний internal id з URL /web/phones/{phone_id}
        phone = phone_repository.get_by_id(db, phone_id)
        if phone is None:
            return None, "phone_not_found"

        # А shipment шукаємо по коду, наприклад SH-001
        shipment = shipment_repository.get_by_code(db, assign_in.shipment_id.strip())
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