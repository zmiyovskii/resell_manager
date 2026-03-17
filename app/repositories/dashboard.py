from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import ExpenseType, FinalStatus, LogisticsStatus, ShipmentStatus, WorkStatus
from app.models.expense import Expense
from app.models.phone import Phone
from app.models.shipment import Shipment


class DashboardRepository:
    def _get_period_start(self, period: str) -> date | None:
        today = date.today()

        if period == "today":
            return today
        if period == "7d":
            return today - timedelta(days=6)
        if period == "30d":
            return today - timedelta(days=29)
        if period == "month":
            return today.replace(day=1)

        return None

    def count_active(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Phone.final_status == FinalStatus.ACTIVE.value,
        )
        return int(db.execute(stmt).scalar() or 0)

    def count_in_shipment(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Phone.logistics_status == LogisticsStatus.IN_SHIPMENT.value,
        )
        return int(db.execute(stmt).scalar() or 0)

    def count_repair(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Phone.work_status == WorkStatus.REPAIR.value,
        )
        return int(db.execute(stmt).scalar() or 0)

    def count_ready(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Phone.work_status == WorkStatus.READY.value,
        )
        return int(db.execute(stmt).scalar() or 0)

    def count_sold_total(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Phone.final_status == FinalStatus.SOLD.value,
        )
        return int(db.execute(stmt).scalar() or 0)

    def count_returned(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Phone.final_status == FinalStatus.RETURNED.value,
        )
        return int(db.execute(stmt).scalar() or 0)

    def count_total_phones(self, db: Session) -> int:
        stmt = select(func.count())
        return int(db.execute(stmt).scalar() or 0)

    def count_bought_in_period(self, db: Session, period: str) -> int:
        start_date = self._get_period_start(period)

        stmt = select(func.count())
        if start_date is not None:
            stmt = stmt.where(Phone.buy_date >= start_date)

        return int(db.execute(stmt.select_from(Phone)).scalar() or 0)

    def count_sold_in_period(self, db: Session, period: str) -> int:
        start_date = self._get_period_start(period)

        stmt = select(func.count()).where(
            Phone.final_status == FinalStatus.SOLD.value,
            Phone.sell_date.is_not(None),
        )
        if start_date is not None:
            stmt = stmt.where(Phone.sell_date >= start_date)

        return int(db.execute(stmt).scalar() or 0)

    def invested_active_phones(self, db: Session) -> float:
        active_buy_sum = db.execute(
            select(func.coalesce(func.sum(Phone.buy_price), 0.0)).where(
                Phone.final_status == FinalStatus.ACTIVE.value,
            )
        ).scalar() or 0.0

        active_phone_expenses_sum = db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0.0))
            .join(Phone, Expense.phone_id == Phone.id)
            .where(
                Phone.final_status == FinalStatus.ACTIVE.value,
                Expense.type == ExpenseType.PHONE.value,
            )
        ).scalar() or 0.0

        return float(active_buy_sum) + float(active_phone_expenses_sum)

    def invested_bought_in_period(self, db: Session, period: str) -> float:
        start_date = self._get_period_start(period)

        stmt = select(func.coalesce(func.sum(Phone.buy_price), 0.0))
        if start_date is not None:
            stmt = stmt.where(Phone.buy_date >= start_date)

        return float(db.execute(stmt.select_from(Phone)).scalar() or 0.0)

    def invested_in_inventory_period(self, db: Session, period: str) -> float:
        start_date = self._get_period_start(period)

        stmt = select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.type == ExpenseType.INVENTORY_PURCHASE.value,
        )
        if start_date is not None:
            stmt = stmt.where(Expense.date >= start_date)

        return float(db.execute(stmt).scalar() or 0.0)

    def turnover_period(self, db: Session, period: str) -> float:
        start_date = self._get_period_start(period)

        stmt = select(func.coalesce(func.sum(Phone.sell_price), 0.0)).where(
            Phone.final_status == FinalStatus.SOLD.value,
            Phone.sell_date.is_not(None),
        )
        if start_date is not None:
            stmt = stmt.where(Phone.sell_date >= start_date)

        return float(db.execute(stmt).scalar() or 0.0)

    def sold_phones_profit_period(self, db: Session, period: str) -> float:
        start_date = self._get_period_start(period)

        sold_phones_stmt = select(Phone.id).where(
            Phone.final_status == FinalStatus.SOLD.value,
            Phone.sell_date.is_not(None),
        )
        if start_date is not None:
            sold_phones_stmt = sold_phones_stmt.where(Phone.sell_date >= start_date)

        sold_phone_ids = list(db.execute(sold_phones_stmt).scalars().all())
        if not sold_phone_ids:
            return 0.0

        sold_buy_sum = db.execute(
            select(func.coalesce(func.sum(Phone.buy_price), 0.0)).where(
                Phone.id.in_(sold_phone_ids)
            )
        ).scalar() or 0.0

        sold_phone_expenses_sum = db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                Expense.type == ExpenseType.PHONE.value,
                Expense.phone_id.in_(sold_phone_ids),
            )
        ).scalar() or 0.0

        sold_revenue_sum = db.execute(
            select(func.coalesce(func.sum(Phone.sell_price), 0.0)).where(
                Phone.id.in_(sold_phone_ids)
            )
        ).scalar() or 0.0

        return float(sold_revenue_sum) - float(sold_buy_sum) - float(sold_phone_expenses_sum)

    def phone_expenses_period(self, db: Session, period: str) -> float:
        start_date = self._get_period_start(period)

        stmt = select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.type == ExpenseType.PHONE.value,
        )
        if start_date is not None:
            stmt = stmt.where(Expense.date >= start_date)

        return float(db.execute(stmt).scalar() or 0.0)

    def inventory_purchases_period(self, db: Session, period: str) -> float:
        start_date = self._get_period_start(period)

        stmt = select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.type == ExpenseType.INVENTORY_PURCHASE.value,
        )
        if start_date is not None:
            stmt = stmt.where(Expense.date >= start_date)

        return float(db.execute(stmt).scalar() or 0.0)

    def business_expenses_period(self, db: Session, period: str) -> float:
        start_date = self._get_period_start(period)

        stmt = select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.type == ExpenseType.BUSINESS.value,
        )
        if start_date is not None:
            stmt = stmt.where(Expense.date >= start_date)

        return float(db.execute(stmt).scalar() or 0.0)

    def total_expenses_period(self, db: Session, period: str) -> float:
        start_date = self._get_period_start(period)

        stmt = select(func.coalesce(func.sum(Expense.amount), 0.0))
        if start_date is not None:
            stmt = stmt.where(Expense.date >= start_date)

        return float(db.execute(stmt.select_from(Expense)).scalar() or 0.0)

    def net_profit_period(self, db: Session, period: str) -> float:
        return self.sold_phones_profit_period(db, period) - self.business_expenses_period(db, period)

    def count_open_shipments(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Shipment.status.in_(
                [
                    ShipmentStatus.COLLECTING.value,
                    ShipmentStatus.SENT.value,
                    ShipmentStatus.IN_TRANSIT.value,
                ]
            ),
        )
        return int(db.execute(stmt).scalar() or 0)

    def count_arrived_shipments(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Shipment.status == ShipmentStatus.ARRIVED.value,
        )
        return int(db.execute(stmt).scalar() or 0)

    def count_phones_in_transit(self, db: Session) -> int:
        stmt = select(func.count()).where(
            Phone.logistics_status.in_(
                [
                    LogisticsStatus.IN_SHIPMENT.value,
                    LogisticsStatus.IN_TRANSIT.value,
                ]
            ),
        )
        return int(db.execute(stmt).scalar() or 0)

    def shipment_profit(self, db: Session, shipment_id: int) -> float:
        revenue = db.execute(
            select(func.coalesce(func.sum(Phone.sell_price), 0.0)).where(
                Phone.shipment_id == shipment_id,
                Phone.final_status == FinalStatus.SOLD.value,
            )
        ).scalar() or 0.0

        buy_sum = db.execute(
            select(func.coalesce(func.sum(Phone.buy_price), 0.0)).where(
                Phone.shipment_id == shipment_id,
            )
        ).scalar() or 0.0

        shipment_expenses = db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                Expense.shipment_id == shipment_id,
            )
        ).scalar() or 0.0

        return float(revenue) - float(buy_sum) - float(shipment_expenses)

    def best_shipment_profit(self, db: Session) -> float:
        shipments = db.execute(
            select(Shipment)
        ).scalars().all()

        if not shipments:
            return 0.0

        profits = [self.shipment_profit(db, shipment.id) for shipment in shipments]
        return float(max(profits)) if profits else 0.0

    def worst_shipment_profit(self, db: Session) -> float:
        shipments = db.execute(
            select(Shipment)
        ).scalars().all()

        if not shipments:
            return 0.0

        profits = [self.shipment_profit(db, shipment.id) for shipment in shipments]
        return float(min(profits)) if profits else 0.0


dashboard_repository = DashboardRepository()