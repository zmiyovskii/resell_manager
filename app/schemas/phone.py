from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PhoneBase(BaseModel):
    model: str = Field(..., max_length=100)
    storage: str = Field(..., max_length=50)
    buy_price: float = Field(..., ge=0)
    buy_date: date
    listing_url: str = Field(..., max_length=500)
    defect: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=1000)


class PhoneCreate(PhoneBase):
    pass


class PhoneUpdate(BaseModel):
    model: Optional[str] = Field(default=None, max_length=100)
    storage: Optional[str] = Field(default=None, max_length=50)
    buy_price: Optional[float] = Field(default=None, ge=0)
    buy_date: Optional[date] = None
    listing_url: Optional[str] = Field(default=None, max_length=500)
    defect: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=1000)
    logistics_status: Optional[str] = Field(default=None, max_length=50)
    work_status: Optional[str] = Field(default=None, max_length=50)
    final_status: Optional[str] = Field(default=None, max_length=50)
    shipment_id: Optional[int] = None
    sell_price: Optional[float] = Field(default=None, ge=0)
    sell_date: Optional[date] = None


class PhoneSell(BaseModel):
    sell_price: float = Field(..., gt=0)
    sell_date: date


class PhoneResponse(BaseModel):
    id: int
    display_id: int
    model: str
    storage: str
    buy_price: float
    buy_date: date
    listing_url: str
    defect: Optional[str]
    notes: Optional[str]
    shipment_id: Optional[int]
    logistics_status: str
    work_status: str
    final_status: str
    sell_price: Optional[float]
    sell_date: Optional[date]

    phone_expenses_total: float
    total_cost: float
    profit: Optional[float]

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)