from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.expense import ExpenseResponse, PhoneExpenseCreate
from app.schemas.phone import PhoneCreate, PhoneResponse, PhoneSell, PhoneUpdate
from app.schemas.shipment import AssignShipmentRequest
from app.services.expense_service import expense_service
from app.services.phone_service import phone_service
from app.services.shipment_service import shipment_service

router = APIRouter(prefix="/api/phones", tags=["phones"])


@router.get("", response_model=list[PhoneResponse])
def list_phones(db: Session = Depends(get_db)):
    return phone_service.list_phones(db)


@router.get("/{phone_id}", response_model=PhoneResponse)
def get_phone(phone_id: int, db: Session = Depends(get_db)):
    phone = phone_service.get_phone(db, phone_id)
    if phone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone not found",
        )
    return phone


@router.post("", response_model=PhoneResponse, status_code=status.HTTP_201_CREATED)
def create_phone(phone_in: PhoneCreate, db: Session = Depends(get_db)):
    return phone_service.create_phone(db, phone_in)


@router.put("/{phone_id}", response_model=PhoneResponse)
def update_phone(phone_id: int, phone_in: PhoneUpdate, db: Session = Depends(get_db)):
    phone = phone_service.update_phone(db, phone_id, phone_in)
    if phone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone not found",
        )
    return phone


@router.post("/{phone_id}/sell", response_model=PhoneResponse)
def sell_phone(phone_id: int, sell_in: PhoneSell, db: Session = Depends(get_db)):
    phone = phone_service.sell_phone(db, phone_id, sell_in)
    if phone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone not found",
        )
    return phone


@router.post("/{phone_id}/assign-shipment", response_model=PhoneResponse)
def assign_shipment(phone_id: int, assign_in: AssignShipmentRequest, db: Session = Depends(get_db)):
    phone, error = shipment_service.assign_phone_to_shipment(db, phone_id, assign_in)

    if error == "phone_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone not found",
        )

    if error == "shipment_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    return phone_service.get_phone(db, phone.id)


@router.delete("/{phone_id}")
def delete_phone(phone_id: int, db: Session = Depends(get_db)):
    phone = phone_service.delete_phone(db, phone_id)
    if phone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone not found",
        )
    return {"message": "Phone deleted successfully"}


@router.post("/{phone_id}/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_phone_expense(
    phone_id: int,
    expense_in: PhoneExpenseCreate,
    db: Session = Depends(get_db),
):
    expense = expense_service.add_phone_expense(db, phone_id, expense_in)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone not found",
        )
    return expense