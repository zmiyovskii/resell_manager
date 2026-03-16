from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import FinalStatus, LogisticsStatus, WorkStatus
from app.db.base import Base, TimestampMixin


class Phone(TimestampMixin, Base):
    __tablename__ = "phones"

    display_id: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    storage: Mapped[str] = mapped_column(String(50), nullable=False)
    buy_price: Mapped[float] = mapped_column(Float, nullable=False)
    buy_date: Mapped[date] = mapped_column(Date, nullable=False)
    listing_url: Mapped[str] = mapped_column(String(500), nullable=False)
    defect: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    shipment_id: Mapped[int | None] = mapped_column(ForeignKey("shipments.id"), nullable=True)

    logistics_status: Mapped[str] = mapped_column(
        String(50),
        default=LogisticsStatus.WAITING_SHIPMENT.value,
        nullable=False,
        index=True,
    )
    work_status: Mapped[str] = mapped_column(
        String(50),
        default=WorkStatus.BOUGHT.value,
        nullable=False,
        index=True,
    )
    final_status: Mapped[str] = mapped_column(
        String(50),
        default=FinalStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )

    sell_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    shipment = relationship("Shipment", back_populates="phones")
    expenses = relationship("Expense", back_populates="phone")
    inventory_movements = relationship("InventoryMovement", back_populates="phone")