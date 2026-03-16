from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExpenseBase(BaseModel):
    type: str = Field(..., max_length=50)
    category: str = Field(..., max_length=50)
    amount: float = Field(..., gt=0)
    date: date
    phone_id: Optional[int] = None
    shipment_id: Optional[int] = None


class ExpenseCreate(ExpenseBase):
    pass


class PhoneExpenseCreate(BaseModel):
    category: str = Field(..., max_length=50)
    amount: float = Field(..., gt=0)
    date: date


class ExpenseResponse(BaseModel):
    id: int
    type: str
    category: str
    amount: float
    date: date
    phone_id: Optional[int]
    shipment_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)