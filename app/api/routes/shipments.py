from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.shipment import ShipmentCreate, ShipmentResponse, ShipmentUpdate
from app.services.shipment_service import shipment_service

router = APIRouter(prefix="/api/shipments", tags=["shipments"])


@router.get("", response_model=list[ShipmentResponse])
def list_shipments(db: Session = Depends(get_db)):
    return shipment_service.list_shipments(db)


@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = shipment_service.get_shipment(db, shipment_id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    return shipment


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(shipment_in: ShipmentCreate, db: Session = Depends(get_db)):
    return shipment_service.create_shipment(db, shipment_in)


@router.put("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(shipment_id: int, shipment_in: ShipmentUpdate, db: Session = Depends(get_db)):
    shipment = shipment_service.update_shipment(db, shipment_id, shipment_in)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    return shipment


@router.delete("/{shipment_id}")
def delete_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = shipment_service.delete_shipment(db, shipment_id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )
    return {"message": "Shipment deleted successfully"}