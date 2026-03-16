from enum import Enum


class LogisticsStatus(str, Enum):
    WAITING_SHIPMENT = "waiting_shipment"
    IN_SHIPMENT = "in_shipment"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"


class WorkStatus(str, Enum):
    BOUGHT = "bought"
    REPAIR = "repair"
    READY = "ready"


class FinalStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    RETURNED = "returned"
    REFUNDED = "refunded"


class ShipmentStatus(str, Enum):
    COLLECTING = "collecting"
    SENT = "sent"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    CLOSED = "closed"
    PROBLEM = "problem"


class ExpenseType(str, Enum):
    PHONE = "phone"
    SHIPMENT = "shipment"
    BUSINESS = "business"
    INVENTORY_PURCHASE = "inventory_purchase"


class ExpenseCategory(str, Enum):
    CARRIER_FEE = "carrier_fee"
    DISPLAY = "display"
    BATTERY = "battery"
    BACKGLASS = "backglass"
    SHIPPING = "shipping"
    GLUE = "glue"
    TOOLS = "tools"
    OTHER = "other"


class InventoryMovementType(str, Enum):
    PURCHASE = "purchase"
    USE = "use"
    WRITEOFF = "writeoff"
    ADJUSTMENT = "adjustment"