from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ExpenseCategory, ExpenseType
from app.db.base import Base, TimestampMixin


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    type: Mapped[str] = mapped_column(String(50), default=ExpenseType.PHONE.value, nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(50),
        default=ExpenseCategory.OTHER.value,
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    phone_id: Mapped[int | None] = mapped_column(ForeignKey("phones.id"), nullable=True, index=True)
    shipment_id: Mapped[int | None] = mapped_column(ForeignKey("shipments.id"), nullable=True, index=True)

    phone = relationship("Phone", back_populates="expenses")
    shipment = relationship("Shipment", back_populates="expenses")