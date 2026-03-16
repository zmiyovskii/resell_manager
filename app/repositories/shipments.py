from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate


class ShipmentRepository:
    def create(self, db: Session, shipment_in: ShipmentCreate) -> Shipment:
        shipment = Shipment(
            code=shipment_in.code,
            carrier_name=shipment_in.carrier_name,
            created_date=shipment_in.created_date,
            sent_date=shipment_in.sent_date,
            arrival_date=shipment_in.arrival_date,
            tracking_number=shipment_in.tracking_number,
            status=shipment_in.status,
            default_carrier_fee=shipment_in.default_carrier_fee,
            note=shipment_in.note,
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        return shipment

    def list_all(self, db: Session) -> Sequence[Shipment]:
        stmt = (
            select(Shipment)
            .where(Shipment.deleted_at.is_(None))
            .order_by(Shipment.id.desc())
        )
        return db.execute(stmt).scalars().all()

    def get_by_id(self, db: Session, shipment_id: int) -> Shipment | None:
        stmt = select(Shipment).where(
            Shipment.id == shipment_id,
            Shipment.deleted_at.is_(None),
        )
        return db.execute(stmt).scalars().first()

    def delete(self, db: Session, shipment: Shipment):
        db.delete(shipment)
        db.commit()
        return shipment

    def update(self, db: Session, shipment: Shipment, shipment_in: ShipmentUpdate) -> Shipment:
        update_data = shipment_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(shipment, field, value)

        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        return shipment

    def soft_delete(self, db: Session, shipment: Shipment) -> Shipment:
        shipment.deleted_at = datetime.utcnow()
        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        return shipment

    def get_by_code(self, db: Session, code: str) -> Shipment | None:
        stmt = select(Shipment).where(
            Shipment.code == code,
            Shipment.deleted_at.is_(None),
        )
        return db.execute(stmt).scalars().first()

shipment_repository = ShipmentRepository()