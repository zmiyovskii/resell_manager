from app.db.base import Base
from app.db.session import engine
from app.models import Expense, InventoryItem, InventoryMovement, Phone, Shipment, user

from app.models.user import User
from app.models.expense import Expense
from app.models.inventory_item import InventoryItem
from app.models.inventory_movement import InventoryMovement
from app.models.phone import Phone
from app.models.shipment import Shipment


def init_db():
    Base.metadata.create_all(bind=engine)