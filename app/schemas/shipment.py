from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ShipmentBase(BaseModel):
    code: str = Field(..., max_length=50)
    carrier_name: Optional[str] = Field(default=None, max_length=100)
    created_date: date
    sent_date: Optional[date] = None
    arrival_date: Optional[date] = None
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="collecting", max_length=50)
    default_carrier_fee: float = Field(default=10, ge=0)
    note: Optional[str] = Field(default=None, max_length=500)


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    code: Optional[str] = Field(default=None, max_length=50)
    carrier_name: Optional[str] = Field(default=None, max_length=100)
    created_date: Optional[date] = None
    sent_date: Optional[date] = None
    arrival_date: Optional[date] = None
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)
    default_carrier_fee: Optional[float] = Field(default=None, ge=0)
    note: Optional[str] = Field(default=None, max_length=500)


class ShipmentResponse(BaseModel):
    id: int
    code: str
    carrier_name: Optional[str]
    created_date: date
    sent_date: Optional[date]
    arrival_date: Optional[date]
    tracking_number: Optional[str]
    status: str
    default_carrier_fee: float
    note: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AssignShipmentRequest(BaseModel):
    shipment_id: str
    carrier_fee: Optional[float] = Field(default=None, ge=0)
    expense_date: date