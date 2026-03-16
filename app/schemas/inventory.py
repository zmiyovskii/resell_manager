from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InventoryItemCreate(BaseModel):
    name: str = Field(..., max_length=150)
    quantity: int = Field(..., ge=0)
    avg_price: float = Field(..., ge=0)


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=150)
    quantity: Optional[int] = Field(default=None, ge=0)
    avg_price: Optional[float] = Field(default=None, ge=0)


class InventoryItemResponse(BaseModel):
    id: int
    name: str
    quantity: int
    avg_price: float
    total_value: float
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class InventoryPurchaseCreate(BaseModel):
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    note: Optional[str] = Field(default=None, max_length=500)


class InventoryUseCreate(BaseModel):
    quantity: int = Field(..., gt=0)
    phone_id: int
    note: Optional[str] = Field(default=None, max_length=500)


class InventoryWriteoffCreate(BaseModel):
    quantity: int = Field(..., gt=0)
    note: Optional[str] = Field(default=None, max_length=500)


class InventoryAdjustCreate(BaseModel):
    quantity: int = Field(..., ge=0)
    note: Optional[str] = Field(default=None, max_length=500)


class InventoryMovementResponse(BaseModel):
    id: int
    inventory_item_id: int
    type: str
    quantity: int
    unit_price: Optional[float]
    phone_id: Optional[int]
    note: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)