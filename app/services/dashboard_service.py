from sqlalchemy.orm import Session

from app.repositories.dashboard import dashboard_repository


class DashboardService:
    def get_summary(self, db: Session, period: str = "all"):
        phones = {
            "active": dashboard_repository.count_active(db),
            "in_shipment": dashboard_repository.count_in_shipment(db),
            "repair": dashboard_repository.count_repair(db),
            "ready": dashboard_repository.count_ready(db),
            "sold_total": dashboard_repository.count_sold_total(db),
            "returned": dashboard_repository.count_returned(db),
            "total": dashboard_repository.count_total_phones(db),
            "bought_in_period": dashboard_repository.count_bought_in_period(db, period),
            "sold_in_period": dashboard_repository.count_sold_in_period(db, period),
        }

        finance = {
            "invested_active_phones": dashboard_repository.invested_active_phones(db),
            "invested_bought_in_period": dashboard_repository.invested_bought_in_period(db, period),
            "invested_in_inventory_period": dashboard_repository.invested_in_inventory_period(db, period),
            "turnover_period": dashboard_repository.turnover_period(db, period),
            "sold_phones_profit_period": dashboard_repository.sold_phones_profit_period(db, period),
            "phone_expenses_period": dashboard_repository.phone_expenses_period(db, period),
            "inventory_purchases_period": dashboard_repository.inventory_purchases_period(db, period),
            "business_expenses_period": dashboard_repository.business_expenses_period(db, period),
            "total_expenses_period": dashboard_repository.total_expenses_period(db, period),
            "net_profit_period": dashboard_repository.net_profit_period(db, period),
        }

        shipments = {
            "open_shipments": dashboard_repository.count_open_shipments(db),
            "arrived_shipments": dashboard_repository.count_arrived_shipments(db),
            "phones_in_transit": dashboard_repository.count_phones_in_transit(db),
            "best_shipment_profit": dashboard_repository.best_shipment_profit(db),
            "worst_shipment_profit": dashboard_repository.worst_shipment_profit(db),
        }

        return {
            "period": period,
            "phones": phones,
            "finance": finance,
            "shipments": shipments,
        }


dashboard_service = DashboardService()