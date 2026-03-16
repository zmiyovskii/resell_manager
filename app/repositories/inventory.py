from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from sqlalchemy import delete

from app.models.inventory_item import InventoryItem
from app.models.inventory_movement import InventoryMovement
from app.schemas.inventory import InventoryItemCreate, InventoryItemUpdate


class InventoryRepository:
    def create_item(self, db: Session, item_in: InventoryItemCreate) -> InventoryItem:
        item = InventoryItem(
            name=item_in.name,
            quantity=item_in.quantity,
            avg_price=item_in.avg_price,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def get_item_by_name(self, db: Session, name: str) -> InventoryItem | None:
        stmt = select(InventoryItem).where(
            InventoryItem.name == name,
            InventoryItem.deleted_at.is_(None),
        )
        return db.execute(stmt).scalars().first()

    def delete_item(self, db: Session, item: InventoryItem):
        db.delete(item)
        db.commit()
        return True

    def delete_movements_by_item_id(self, db: Session, item_id: int):
        stmt = delete(InventoryMovement).where(InventoryMovement.inventory_item_id == item_id)
        db.execute(stmt)
        db.commit()

    def delete_movements_by_phone_id(self, db: Session, phone_id: int):
        stmt = delete(InventoryMovement).where(InventoryMovement.phone_id == phone_id)
        db.execute(stmt)
        db.commit()

    def list_items(self, db: Session) -> Sequence[InventoryItem]:
        stmt = (
            select(InventoryItem)
            .where(InventoryItem.deleted_at.is_(None))
            .order_by(InventoryItem.name.asc())
        )
        return db.execute(stmt).scalars().all()

    def get_item(self, db: Session, item_id: int) -> InventoryItem | None:
        stmt = select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.deleted_at.is_(None),
        )
        return db.execute(stmt).scalars().first()

    def update_item(self, db: Session, item: InventoryItem, item_in: InventoryItemUpdate) -> InventoryItem:
        update_data = item_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(item, field, value)

        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def delete_item(self, db: Session, item: InventoryItem):
        db.delete(item)
        db.commit()

    def create_movement(
        self,
        db: Session,
        inventory_item_id: int,
        movement_type: str,
        quantity: int,
        unit_price: float | None = None,
        phone_id: int | None = None,
        note: str | None = None,
    ) -> InventoryMovement:
        movement = InventoryMovement(
            inventory_item_id=inventory_item_id,
            type=movement_type,
            quantity=quantity,
            unit_price=unit_price,
            phone_id=phone_id,
            note=note,
        )
        db.add(movement)
        db.commit()
        db.refresh(movement)
        return movement

    def soft_delete_item(self, db: Session, item: InventoryItem) -> InventoryItem:
        item.deleted_at = datetime.utcnow()
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def list_movements(self, db: Session, item_id: int | None = None) -> Sequence[InventoryMovement]:
        stmt = (
            select(InventoryMovement)
            .where(InventoryMovement.deleted_at.is_(None))
            .order_by(InventoryMovement.id.desc())
        )

        if item_id is not None:
            stmt = stmt.where(InventoryMovement.inventory_item_id == item_id)

        return db.execute(stmt).scalars().all()


inventory_repository = InventoryRepository()