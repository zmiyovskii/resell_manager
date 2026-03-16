from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InventoryMovementType
from app.db.base import Base, TimestampMixin


class InventoryMovement(TimestampMixin, Base):
    __tablename__ = "inventory_movements"

    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(
        String(50),
        default=InventoryMovementType.PURCHASE.value,
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    phone_id: Mapped[int | None] = mapped_column(ForeignKey("phones.id"), nullable=True, index=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    inventory_item = relationship("InventoryItem", back_populates="movements")
    phone = relationship("Phone", back_populates="inventory_movements")