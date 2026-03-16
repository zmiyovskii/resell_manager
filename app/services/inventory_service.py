from datetime import date

from sqlalchemy.orm import Session

from app.core.enums import ExpenseType, InventoryMovementType
from app.repositories.expenses import expense_repository
from app.repositories.inventory import inventory_repository
from app.repositories.phones import phone_repository
from app.schemas.expense import ExpenseCreate
from app.schemas.inventory import (
    InventoryAdjustCreate,
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryPurchaseCreate,
    InventoryUseCreate,
    InventoryWriteoffCreate,
)


class InventoryService:
    def _attach_total_value(self, item):
        total_value = float(item.quantity) * float(item.avg_price)
        setattr(item, "total_value", total_value)
        return item

    def create_item(self, db: Session, item_in: InventoryItemCreate):
        existing = inventory_repository.get_item_by_name(db, item_in.name)

        if existing is not None:
            old_qty = int(existing.quantity)
            old_avg = float(existing.avg_price)

            add_qty = int(item_in.quantity)
            add_price = float(item_in.avg_price)

            total_old_value = old_qty * old_avg
            total_new_value = add_qty * add_price
            final_qty = old_qty + add_qty

            if final_qty > 0:
                existing.avg_price = (total_old_value + total_new_value) / final_qty

            existing.quantity = final_qty

            db.add(existing)
            db.commit()
            db.refresh(existing)

            movement = inventory_repository.create_movement(
                db=db,
                inventory_item_id=existing.id,
                movement_type=InventoryMovementType.PURCHASE.value,
                quantity=add_qty,
                unit_price=add_price,
                note="Initial stock add / merge",
            )

            expense_repository.create(
                db,
                ExpenseCreate(
                    type=ExpenseType.INVENTORY_PURCHASE.value,
                    category="other",
                    amount=float(add_qty) * float(add_price),
                    date=date.today(),
                    phone_id=None,
                    shipment_id=None,
                ),
            )

            return self._attach_total_value(existing), None

        item = inventory_repository.create_item(db, item_in)

        inventory_repository.create_movement(
            db=db,
            inventory_item_id=item.id,
            movement_type=InventoryMovementType.PURCHASE.value,
            quantity=int(item_in.quantity),
            unit_price=float(item_in.avg_price),
            note="Initial stock create",
        )

        expense_repository.create(
            db,
            ExpenseCreate(
                type=ExpenseType.INVENTORY_PURCHASE.value,
                category="other",
                amount=float(item_in.quantity) * float(item_in.avg_price),
                date=date.today(),
                phone_id=None,
                shipment_id=None,
            ),
        )

        return self._attach_total_value(item), None

    def list_items(self, db: Session):
        items = inventory_repository.list_items(db)
        return [self._attach_total_value(item) for item in items]

    def get_item(self, db: Session, item_id: int):
        item = inventory_repository.get_item(db, item_id)
        if item is None:
            return None
        return self._attach_total_value(item)

    def update_item(self, db: Session, item_id: int, item_in: InventoryItemUpdate):
        item = inventory_repository.get_item(db, item_id)
        if item is None:
            return None

        item = inventory_repository.update_item(db, item, item_in)
        return self._attach_total_value(item)

    def delete_item(self, db: Session, item_id: int):
        item = inventory_repository.get_item(db, item_id)
        if item is None:
            return False

        inventory_repository.delete_movements_by_item_id(db, item.id)
        inventory_repository.delete_item(db, item)
        return True

    def purchase_item(self, db: Session, item_id: int, purchase_in: InventoryPurchaseCreate):
        item = inventory_repository.get_item(db, item_id)
        if item is None:
            return None, "item_not_found"

        old_qty = int(item.quantity)
        old_avg = float(item.avg_price)

        new_qty = int(purchase_in.quantity)
        new_price = float(purchase_in.unit_price)

        total_old_value = old_qty * old_avg
        total_new_value = new_qty * new_price
        final_qty = old_qty + new_qty

        if final_qty > 0:
            item.avg_price = (total_old_value + total_new_value) / final_qty

        item.quantity = final_qty

        db.add(item)
        db.commit()
        db.refresh(item)

        movement = inventory_repository.create_movement(
            db=db,
            inventory_item_id=item.id,
            movement_type=InventoryMovementType.PURCHASE.value,
            quantity=new_qty,
            unit_price=new_price,
            note=purchase_in.note,
        )

        expense_repository.create(
            db,
            ExpenseCreate(
                type=ExpenseType.INVENTORY_PURCHASE.value,
                category="other",
                amount=float(new_qty) * float(new_price),
                date=date.today(),
                phone_id=None,
                shipment_id=None,
            ),
        )

        return movement, None

    def use_item_for_phone(self, db: Session, item_id: int, use_in: InventoryUseCreate):
        item = inventory_repository.get_item(db, item_id)
        if item is None:
            return None, "item_not_found"

        phone = phone_repository.get_by_display_id(db, use_in.phone_id)
        if phone is None:
            return None, "phone_not_found"

        if item.quantity < use_in.quantity:
            return None, "not_enough_stock"

        item.quantity -= use_in.quantity

        db.add(item)
        db.commit()
        db.refresh(item)

        movement = inventory_repository.create_movement(
            db=db,
            inventory_item_id=item.id,
            movement_type=InventoryMovementType.USE.value,
            quantity=use_in.quantity,
            unit_price=item.avg_price,
            phone_id=phone.id,
            note=use_in.note,
        )

        expense_amount = float(use_in.quantity) * float(item.avg_price)

        expense_repository.create(
            db,
            ExpenseCreate(
                type=ExpenseType.PHONE.value,
                category="other",
                amount=expense_amount,
                date=date.today(),
                phone_id=phone.id,
                shipment_id=None,
            ),
        )

        return movement, None

    def writeoff_item(self, db: Session, item_id: int, writeoff_in: InventoryWriteoffCreate):
        item = inventory_repository.get_item(db, item_id)
        if item is None:
            return None, "item_not_found"

        if item.quantity < writeoff_in.quantity:
            return None, "not_enough_stock"

        item.quantity -= writeoff_in.quantity

        db.add(item)
        db.commit()
        db.refresh(item)

        movement = inventory_repository.create_movement(
            db=db,
            inventory_item_id=item.id,
            movement_type=InventoryMovementType.WRITEOFF.value,
            quantity=writeoff_in.quantity,
            unit_price=item.avg_price,
            note=writeoff_in.note,
        )

        return movement, None

    def adjust_item(self, db: Session, item_id: int, adjust_in: InventoryAdjustCreate):
        item = inventory_repository.get_item(db, item_id)
        if item is None:
            return None

        item.quantity = adjust_in.quantity

        db.add(item)
        db.commit()
        db.refresh(item)

        movement = inventory_repository.create_movement(
            db=db,
            inventory_item_id=item.id,
            movement_type=InventoryMovementType.ADJUSTMENT.value,
            quantity=adjust_in.quantity,
            unit_price=item.avg_price,
            note=adjust_in.note,
        )

        return movement

    def list_movements(self, db: Session, item_id: int | None = None):
        return inventory_repository.list_movements(db, item_id=item_id)


inventory_service = InventoryService()