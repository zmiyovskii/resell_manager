from pydantic import BaseModel


class PhonesSummary(BaseModel):
    active: int
    in_shipment: int
    repair: int
    ready: int
    sold_total: int
    returned: int
    total: int
    bought_in_period: int
    sold_in_period: int


class FinanceSummary(BaseModel):
    invested_active_phones: float
    invested_bought_in_period: float
    invested_in_inventory_period: float
    turnover_period: float
    sold_phones_profit_period: float
    phone_expenses_period: float
    inventory_purchases_period: float
    business_expenses_period: float
    total_expenses_period: float
    net_profit_period: float


class ShipmentSummary(BaseModel):
    open_shipments: int
    arrived_shipments: int
    phones_in_transit: int
    best_shipment_profit: float
    worst_shipment_profit: float


class DashboardSummary(BaseModel):
    period: str
    phones: PhonesSummary
    finance: FinanceSummary
    shipments: ShipmentSummary