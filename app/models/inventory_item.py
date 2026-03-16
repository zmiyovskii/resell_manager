from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class InventoryItem(TimestampMixin, Base):
    __tablename__ = "inventory_items"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    avg_price: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    movements = relationship("InventoryMovement", back_populates="inventory_item")