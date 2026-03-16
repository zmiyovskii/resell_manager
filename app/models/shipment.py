from datetime import date

from sqlalchemy import Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ShipmentStatus
from app.db.base import Base, TimestampMixin


class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    carrier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_date: Mapped[date] = mapped_column(Date, nullable=False)
    sent_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    arrival_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=ShipmentStatus.COLLECTING.value, nullable=False)
    default_carrier_fee: Mapped[float] = mapped_column(Float, default=10, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    phones = relationship("Phone", back_populates="shipment")
    expenses = relationship("Expense", back_populates="shipment")