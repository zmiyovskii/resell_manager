from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.inventory import (
    InventoryAdjustCreate,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryMovementResponse,
    InventoryPurchaseCreate,
    InventoryUseCreate,
    InventoryWriteoffCreate,
)
from app.services.inventory_service import inventory_service

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryItemResponse])
def list_inventory(db: Session = Depends(get_db)):
    return inventory_service.list_items(db)


@router.get("/{item_id}", response_model=InventoryItemResponse)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = inventory_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_item(item_in: InventoryItemCreate, db: Session = Depends(get_db)):
    return inventory_service.create_item(db, item_in)


@router.put("/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(item_id: int, item_in: InventoryItemUpdate, db: Session = Depends(get_db)):
    item = inventory_service.update_item(db, item_id, item_in)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.delete("/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = inventory_service.delete_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return {"message": "Inventory item deleted successfully"}


@router.post("/{item_id}/purchase", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def purchase_inventory_item(item_id: int, purchase_in: InventoryPurchaseCreate, db: Session = Depends(get_db)):
    movement, error = inventory_service.purchase_item(db, item_id, purchase_in)

    if error == "item_not_found":
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return movement


@router.post("/{item_id}/use", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def use_inventory_item(item_id: int, use_in: InventoryUseCreate, db: Session = Depends(get_db)):
    movement, error = inventory_service.use_item_for_phone(db, item_id, use_in)

    if error == "item_not_found":
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if error == "phone_not_found":
        raise HTTPException(status_code=404, detail="Phone not found")
    if error == "not_enough_stock":
        raise HTTPException(status_code=400, detail="Not enough stock")

    return movement


@router.post("/{item_id}/writeoff", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def writeoff_inventory_item(item_id: int, writeoff_in: InventoryWriteoffCreate, db: Session = Depends(get_db)):
    movement, error = inventory_service.writeoff_item(db, item_id, writeoff_in)

    if error == "item_not_found":
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if error == "not_enough_stock":
        raise HTTPException(status_code=400, detail="Not enough stock")

    return movement


@router.post("/{item_id}/adjust", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def adjust_inventory_item(item_id: int, adjust_in: InventoryAdjustCreate, db: Session = Depends(get_db)):
    movement = inventory_service.adjust_item(db, item_id, adjust_in)
    if movement is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return movement


@router.get("/movements/all", response_model=list[InventoryMovementResponse])
def list_inventory_movements(
    item_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return inventory_service.list_movements(db, item_id=item_id)