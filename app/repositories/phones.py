from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.phone import Phone
from app.schemas.phone import PhoneCreate, PhoneUpdate


class PhoneRepository:
    def get_next_display_id(self, db: Session) -> int:
        stmt = select(Phone).where(Phone.deleted_at.is_(None)).order_by(Phone.display_id.desc())
        last_phone = db.execute(stmt).scalars().first()
        return 1 if last_phone is None else last_phone.display_id + 1

    def create(self, db: Session, phone_in: PhoneCreate) -> Phone:
        display_id = self.get_next_display_id(db)

        phone = Phone(
            display_id=display_id,
            model=phone_in.model,
            storage=phone_in.storage,
            buy_price=phone_in.buy_price,
            buy_date=phone_in.buy_date,
            listing_url=phone_in.listing_url,
            defect=phone_in.defect,
            notes=phone_in.notes,
        )

        db.add(phone)
        db.commit()
        db.refresh(phone)
        return phone

    def list_all(self, db: Session) -> Sequence[Phone]:
        stmt = (
            select(Phone)
            .where(Phone.deleted_at.is_(None))
            .order_by(Phone.display_id.desc())
        )
        return db.execute(stmt).scalars().all()

    def delete(self, db: Session, phone: Phone):
        db.delete(phone)
        db.commit()
        return phone

    def get_by_id(self, db: Session, phone_id: int) -> Phone | None:
        stmt = select(Phone).where(
            Phone.id == phone_id,
            Phone.deleted_at.is_(None),
        )
        return db.execute(stmt).scalars().first()

    def update(self, db: Session, phone: Phone, phone_in: PhoneUpdate) -> Phone:
        update_data = phone_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(phone, field, value)

        db.add(phone)
        db.commit()
        db.refresh(phone)
        return phone

    def soft_delete(self, db: Session, phone: Phone) -> Phone:
        phone.deleted_at = datetime.utcnow()
        db.add(phone)
        db.commit()
        db.refresh(phone)
        return phone

    def get_by_display_id(self, db: Session, display_id: int) -> Phone | None:
        stmt = select(Phone).where(
            Phone.display_id == display_id,
            Phone.deleted_at.is_(None),
        )
        return db.execute(stmt).scalars().first()

phone_repository = PhoneRepository()