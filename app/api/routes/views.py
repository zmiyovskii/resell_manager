from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.expense import ExpenseCreate, PhoneExpenseCreate
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryPurchaseCreate,
    InventoryUseCreate,
    InventoryWriteoffCreate,
)
from app.schemas.phone import PhoneCreate, PhoneSell, PhoneUpdate
from app.schemas.shipment import AssignShipmentRequest, ShipmentCreate, ShipmentUpdate
from app.services.dashboard_service import dashboard_service
from app.services.expense_service import expense_service
from app.services.inventory_service import inventory_service
from app.services.phone_service import phone_service
from app.services.shipment_service import shipment_service

router = APIRouter(tags=["views"])
templates = Jinja2Templates(directory="app/templates")


def get_current_user(request: Request):
    return request.cookies.get("user")


def require_login(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
    return None


@router.get("/web/dashboard", response_class=HTMLResponse)
def web_dashboard(
    request: Request,
    period: str = Query(default="all"),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    allowed_periods = {"all", "today", "7d", "30d", "month"}
    if period not in allowed_periods:
        period = "all"

    summary = dashboard_service.get_summary(db, period=period)
    all_phones = phone_service.list_phones(db)

    recent_phones = all_phones[:5]

    profitable_phones = [p for p in all_phones if p.profit is not None and p.profit > 0]
    profitable_phones = sorted(profitable_phones, key=lambda p: p.profit, reverse=True)[:5]

    loss_phones = [p for p in all_phones if p.profit is not None and p.profit < 0]
    loss_phones = sorted(loss_phones, key=lambda p: p.profit)[:5]

    recent_sales = [p for p in all_phones if p.sell_price is not None]
    recent_sales = sorted(
        recent_sales,
        key=lambda p: (p.sell_date is not None, p.sell_date),
        reverse=True,
    )[:5]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "summary": summary,
            "period": period,
            "recent_phones": recent_phones,
            "profitable_phones": profitable_phones,
            "loss_phones": loss_phones,
            "recent_sales": recent_sales,
        },
    )


@router.get("/web/phones", response_class=HTMLResponse)
def web_phones(
    request: Request,
    status_filter: str = Query(default="all"),
    q: str = Query(default=""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    phones = phone_service.list_phones(db)

    if q:
        q_lower = q.lower().strip()
        phones = [
            p for p in phones
            if q_lower in p.model.lower() or q_lower in p.storage.lower()
        ]

    if status_filter == "active":
        phones = [p for p in phones if p.final_status == "active"]
    elif status_filter == "sold":
        phones = [p for p in phones if p.final_status == "sold"]
    elif status_filter == "in_shipment":
        phones = [p for p in phones if p.logistics_status == "in_shipment"]
    elif status_filter == "repair":
        phones = [p for p in phones if p.work_status == "repair"]
    elif status_filter == "ready":
        phones = [p for p in phones if p.work_status == "ready"]
    elif status_filter == "profit":
        phones = [p for p in phones if p.profit is not None and p.profit > 0]
    elif status_filter == "loss":
        phones = [p for p in phones if p.profit is not None and p.profit < 0]

    return templates.TemplateResponse(
        "phones/list.html",
        {
            "request": request,
            "phones": phones,
            "status_filter": status_filter,
            "q": q,
        },
    )


@router.get("/web/phones/create", response_class=HTMLResponse)
def web_phone_create_page(request: Request):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    return templates.TemplateResponse(
        "phones/create.html",
        {
            "request": request,
            "success_message": None,
            "error_message": None,
            "warnings": [],
        },
    )


@router.post("/web/phones/create", response_class=HTMLResponse)
def web_phone_create(
    request: Request,
    model: str = Form(...),
    storage: str = Form(...),
    buy_price: float = Form(...),
    buy_date: date = Form(...),
    listing_url: str = Form(...),
    defect: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    phone_in = PhoneCreate(
        model=model,
        storage=storage,
        buy_price=buy_price,
        buy_date=buy_date,
        listing_url=listing_url,
        defect=defect or None,
        notes=notes or None,
    )
    phone = phone_service.create_phone(db, phone_in)
    return RedirectResponse(url=f"/web/phones/{phone.id}", status_code=303)


@router.get("/web/phones/{phone_id}", response_class=HTMLResponse)
def web_phone_detail(phone_id: int, request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    phone = phone_service.get_phone(db, phone_id)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    expenses = expense_service.list_phone_expenses(db, phone_id)

    warnings = []
    if phone.final_status == "sold":
        warnings.append("Телефон уже позначений як проданий. Новий продаж просто перезапише поточні дані.")
    if phone.shipment_id is not None:
        warnings.append("Телефон уже прив’язаний до shipment. Повторне прив’язування оновить shipment і додасть нову carrier fee витрату.")
    if phone.sell_price is not None:
        warnings.append("У телефона вже є ціна продажу. Повторний продаж просто перезапише поточні дані.")

    return templates.TemplateResponse(
        "phones/detail.html",
        {
            "request": request,
            "phone": phone,
            "expenses": expenses,
            "warnings": warnings,
            "success_message": None,
            "error_message": None,
        },
    )


@router.get("/web/phones/{phone_id}/edit", response_class=HTMLResponse)
def web_phone_edit_page(phone_id: int, request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    phone = phone_service.get_phone(db, phone_id)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    return templates.TemplateResponse(
        "phones/edit.html",
        {
            "request": request,
            "phone": phone,
            "warnings": [],
        },
    )


@router.post("/web/phones/{phone_id}/edit", response_class=HTMLResponse)
def web_phone_edit(
    phone_id: int,
    request: Request,
    model: str = Form(...),
    storage: str = Form(...),
    buy_price: float = Form(...),
    buy_date: date = Form(...),
    listing_url: str = Form(...),
    defect: str = Form(""),
    notes: str = Form(""),
    logistics_status: str = Form(...),
    work_status: str = Form(...),
    final_status: str = Form(...),
    shipment_id: str = Form(""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    phone_in = PhoneUpdate(
        model=model,
        storage=storage,
        buy_price=buy_price,
        buy_date=buy_date,
        listing_url=listing_url,
        defect=defect or None,
        notes=notes or None,
        logistics_status=logistics_status,
        work_status=work_status,
        final_status=final_status,
        shipment_id=int(shipment_id) if shipment_id else None,
    )

    phone = phone_service.update_phone(db, phone_id, phone_in)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    return RedirectResponse(url=f"/web/phones/{phone_id}", status_code=303)


@router.post("/web/phones/{phone_id}/sell", response_class=HTMLResponse)
def web_phone_sell(
    phone_id: int,
    request: Request,
    sell_price: float = Form(...),
    sell_date: date = Form(...),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    sell_in = PhoneSell(sell_price=sell_price, sell_date=sell_date)
    phone = phone_service.sell_phone(db, phone_id, sell_in)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    return RedirectResponse(url=f"/web/phones/{phone_id}", status_code=303)


@router.post("/web/phones/{phone_id}/return", response_class=HTMLResponse)
def web_phone_return(
    phone_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    phone = phone_service.return_phone(db, phone_id)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    return RedirectResponse(url=f"/web/phones/{phone_id}", status_code=303)

@router.post("/web/phones/{phone_id}/quick-logistics-status", response_class=HTMLResponse)
def web_phone_quick_logistics_status(
    phone_id: int,
    request: Request,
    logistics_status: str = Form(...),
    db: Session = Depends(get_db),
):
    phone = phone_service.set_logistics_status(db, phone_id, logistics_status)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    return RedirectResponse(url=f"/web/phones/{phone_id}", status_code=303)


@router.post("/web/phones/{phone_id}/quick-work-status", response_class=HTMLResponse)
def web_phone_quick_work_status(
    phone_id: int,
    request: Request,
    work_status: str = Form(...),
    db: Session = Depends(get_db),
):
    phone = phone_service.set_work_status(db, phone_id, work_status)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    return RedirectResponse(url=f"/web/phones/{phone_id}", status_code=303)


@router.post("/web/phones/{phone_id}/quick-final-status", response_class=HTMLResponse)
def web_phone_quick_final_status(
    phone_id: int,
    request: Request,
    final_status: str = Form(...),
    db: Session = Depends(get_db),
):
    phone = phone_service.set_final_status(db, phone_id, final_status)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    return RedirectResponse(url=f"/web/phones/{phone_id}", status_code=303)

@router.post("/web/phones/{phone_id}/expense", response_class=HTMLResponse)
def web_phone_add_expense(
    phone_id: int,
    request: Request,
    category: str = Form(...),
    amount: float = Form(...),
    date_value: str = Form(..., alias="date"),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    expense_in = PhoneExpenseCreate(
        category=category,
        amount=amount,
        date=date.fromisoformat(date_value),
    )
    expense = expense_service.add_phone_expense(db, phone_id, expense_in)
    if expense is None:
        raise HTTPException(status_code=404, detail="Phone not found")

    return RedirectResponse(url=f"/web/phones/{phone_id}", status_code=303)


@router.post("/web/phones/{phone_id}/assign-shipment", response_class=HTMLResponse)
def web_phone_assign_shipment(
    phone_id: int,
    request: Request,
    shipment_id: str = Form(...),
    carrier_fee: str = Form(""),
    expense_date: date = Form(...),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    assign_in = AssignShipmentRequest(
        shipment_id=shipment_id,
        carrier_fee=float(carrier_fee) if carrier_fee else None,
        expense_date=expense_date,
    )

    _, error = shipment_service.assign_phone_to_shipment(db, phone_id, assign_in)

    if error == "phone_not_found":
        raise HTTPException(status_code=404, detail="Phone not found")
    if error == "shipment_not_found":
        raise HTTPException(status_code=404, detail="Shipment not found")

    return RedirectResponse(url=f"/web/phones/{phone_id}", status_code=303)


@router.get("/web/shipments", response_class=HTMLResponse)
def web_shipments(request: Request, db: Session = Depends(get_db)):
    shipments = shipment_service.list_shipments(db)
    return templates.TemplateResponse(
        "shipments/list.html",
        {
            "request": request,
            "shipments": shipments,
            "warnings": [],
        },
    )


@router.get("/web/shipments/{shipment_id}", response_class=HTMLResponse)
def web_shipment_detail(shipment_id: int, request: Request, db: Session = Depends(get_db)):
    shipment = shipment_service.get_shipment(db, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return templates.TemplateResponse(
        "shipments/detail.html",
        {
            "request": request,
            "shipment": shipment,
            "phones": getattr(shipment, "phones", []),
            "warnings": [],
            "success_message": None,
            "error_message": None,
        },
    )


@router.get("/web/shipments/create", response_class=HTMLResponse)
def web_shipment_create_page(request: Request):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    return templates.TemplateResponse(
        "shipments/create.html",
        {
            "request": request,
            "warnings": [],
        },
    )


@router.post("/web/shipments/create", response_class=HTMLResponse)
def web_shipment_create(
    request: Request,
    code: str = Form(...),
    created_date: date = Form(...),
    sent_date: str = Form(""),
    carrier_name: str = Form(""),
    arrival_date: str = Form(""),
    tracking_number: str = Form(""),
    status: str = Form(...),
    default_carrier_fee: float = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    shipment_in = ShipmentCreate(
        code=code,
        created_date=created_date,
        sent_date=date.fromisoformat(sent_date) if sent_date else None,
        arrival_date=date.fromisoformat(arrival_date) if arrival_date else None,
        tracking_number=tracking_number or None,
        status=status,
        default_carrier_fee=default_carrier_fee,
        note=note or None,
        carrier_name=carrier_name or None,
    )
    shipment_service.create_shipment(db, shipment_in)
    return RedirectResponse(url="/web/shipments", status_code=303)


@router.get("/web/shipments/{shipment_id}/edit", response_class=HTMLResponse)
def web_shipment_edit_page(shipment_id: int, request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    shipment = shipment_service.get_shipment(db, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return templates.TemplateResponse(
        "shipments/edit.html",
        {
            "request": request,
            "shipment": shipment,
            "warnings": [],
        },
    )


@router.post("/web/shipments/{shipment_id}/delete", response_class=HTMLResponse)
def web_shipment_delete(
    shipment_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    deleted = shipment_service.delete_shipment(db, shipment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return RedirectResponse(url="/web/shipments", status_code=303)


@router.post("/web/shipments/{shipment_id}/edit", response_class=HTMLResponse)
def web_shipment_edit(
    shipment_id: int,
    request: Request,
    code: str = Form(...),
    created_date: date = Form(...),
    sent_date: str = Form(""),
    arrival_date: str = Form(""),
    tracking_number: str = Form(""),
    carrier_name: str = Form(""),
    status: str = Form(...),
    default_carrier_fee: float = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    shipment_in = ShipmentUpdate(
        code=code,
        created_date=created_date,
        sent_date=date.fromisoformat(sent_date) if sent_date else None,
        arrival_date=date.fromisoformat(arrival_date) if arrival_date else None,
        tracking_number=tracking_number or None,
        status=status,
        default_carrier_fee=default_carrier_fee,
        note=note or None,
        carrier_name=carrier_name or None,
    )
    shipment = shipment_service.update_shipment(db, shipment_id, shipment_in)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return RedirectResponse(url="/web/shipments", status_code=303)


@router.get("/web/expenses", response_class=HTMLResponse)
def web_expenses(request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    expenses = expense_service.list_expenses(db)
    return templates.TemplateResponse(
        "expenses/list.html",
        {
            "request": request,
            "expenses": expenses,
            "warnings": [],
        },
    )


@router.get("/web/expenses/create", response_class=HTMLResponse)
def web_expense_create_page(request: Request):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    return templates.TemplateResponse(
        "expenses/create.html",
        {
            "request": request,
            "error_message": None,
            "success_message": None,
            "warnings": [],
        },
    )


@router.post("/web/expenses/create", response_class=HTMLResponse)
def web_expense_create(
    request: Request,
    type: str = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    date_value: str = Form(..., alias="date"),
    phone_id: str = Form(""),
    shipment_id: str = Form(""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    expense_in = ExpenseCreate(
        type=type,
        category=category,
        amount=amount,
        date=date.fromisoformat(date_value),
        phone_id=int(phone_id) if phone_id else None,
        shipment_id=int(shipment_id) if shipment_id else None,
    )

    expense, error = expense_service.create_expense(db, expense_in)

    if error == "phone_not_found":
        return templates.TemplateResponse(
            "expenses/create.html",
            {
                "request": request,
                "error_message": "Телефон з таким ID не знайдено.",
                "success_message": None,
                "warnings": [],
            },
        )

    if error == "shipment_not_found":
        return templates.TemplateResponse(
            "expenses/create.html",
            {
                "request": request,
                "error_message": "Shipment з таким ID не знайдено.",
                "success_message": None,
                "warnings": [],
            },
        )

    return RedirectResponse(url="/web/expenses", status_code=303)


@router.get("/web/inventory", response_class=HTMLResponse)
def web_inventory(request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    inventory_items = inventory_service.list_items(db)
    return templates.TemplateResponse(
        "inventory/list.html",
        {
            "request": request,
            "inventory_items": inventory_items,
            "warnings": [],
        },
    )


@router.get("/web/inventory/create", response_class=HTMLResponse)
def web_inventory_create_page(request: Request):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    return templates.TemplateResponse(
        "inventory/create.html",
        {
            "request": request,
            "error_message": None,
            "success_message": None,
            "warnings": [],
        },
    )


@router.post("/web/inventory/create", response_class=HTMLResponse)
def web_inventory_create(
    request: Request,
    name: str = Form(...),
    quantity: int = Form(...),
    avg_price: float = Form(...),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    item_in = InventoryItemCreate(name=name, quantity=quantity, avg_price=avg_price)
    item, error = inventory_service.create_item(db, item_in)

    if error == "name_exists":
        return templates.TemplateResponse(
            "inventory/create.html",
            {
                "request": request,
                "error_message": "Позиція з такою назвою вже існує.",
                "success_message": None,
                "warnings": [],
            },
        )

    return RedirectResponse(url="/web/inventory", status_code=303)


@router.get("/web/inventory/{item_id}/edit", response_class=HTMLResponse)
def web_inventory_edit_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    item = inventory_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return templates.TemplateResponse(
        "inventory/edit.html",
        {
            "request": request,
            "item": item,
            "error_message": None,
            "success_message": None,
            "warnings": [],
        },
    )


@router.post("/web/inventory/{item_id}/edit", response_class=HTMLResponse)
def web_inventory_edit(
    item_id: int,
    request: Request,
    name: str = Form(...),
    quantity: int = Form(...),
    avg_price: float = Form(...),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    item_in = InventoryItemUpdate(name=name, quantity=quantity, avg_price=avg_price)
    item = inventory_service.update_item(db, item_id, item_in)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return RedirectResponse(url="/web/inventory", status_code=303)


@router.post("/web/inventory/{item_id}/delete", response_class=HTMLResponse)
def web_inventory_delete(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    deleted = inventory_service.delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return RedirectResponse(url="/web/inventory", status_code=303)


@router.get("/web/inventory/{item_id}/purchase", response_class=HTMLResponse)
def web_inventory_purchase_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    item = inventory_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return templates.TemplateResponse(
        "inventory/purchase.html",
        {
            "request": request,
            "item": item,
            "error_message": None,
            "success_message": None,
            "warnings": [],
        },
    )


@router.post("/web/phones/{phone_id}/delete", response_class=HTMLResponse)
def web_phone_delete(
    phone_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    deleted = phone_service.delete_phone(db, phone_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Phone not found")

    return RedirectResponse(url="/web/phones", status_code=303)


@router.post("/web/expenses/{expense_id}/delete", response_class=HTMLResponse)
def web_expense_delete(
    expense_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    deleted = expense_service.delete_expense(db, expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")

    return RedirectResponse(url="/web/expenses", status_code=303)


@router.post("/web/inventory/{item_id}/purchase", response_class=HTMLResponse)
def web_inventory_purchase(
    item_id: int,
    request: Request,
    quantity: int = Form(...),
    unit_price: float = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    purchase_in = InventoryPurchaseCreate(
        quantity=quantity,
        unit_price=unit_price,
        note=note or None,
    )
    _, error = inventory_service.purchase_item(db, item_id, purchase_in)

    if error == "item_not_found":
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return RedirectResponse(url="/web/inventory", status_code=303)


@router.get("/web/inventory/{item_id}/use", response_class=HTMLResponse)
def web_inventory_use_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    item = inventory_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return templates.TemplateResponse(
        "inventory/use.html",
        {
            "request": request,
            "item": item,
            "error_message": None,
            "success_message": None,
            "warnings": [],
        },
    )


@router.post("/web/inventory/{item_id}/use", response_class=HTMLResponse)
def web_inventory_use(
    item_id: int,
    request: Request,
    quantity: int = Form(...),
    phone_id: int = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    use_in = InventoryUseCreate(
        quantity=quantity,
        phone_id=phone_id,
        note=note or None,
    )
    _, error = inventory_service.use_item_for_phone(db, item_id, use_in)

    if error == "item_not_found":
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if error == "phone_not_found":
        raise HTTPException(status_code=404, detail="Телефон не знайдено")
    if error == "not_enough_stock":
        item = inventory_service.get_item(db, item_id)
        return templates.TemplateResponse(
            "inventory/use.html",
            {
                "request": request,
                "item": item,
                "error_message": "Недостатньо товару на складі для цієї дії.",
                "success_message": None,
                "warnings": [],
            },
        )

    return RedirectResponse(url="/web/inventory", status_code=303)


@router.get("/web/inventory/{item_id}/writeoff", response_class=HTMLResponse)
def web_inventory_writeoff_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    item = inventory_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return templates.TemplateResponse(
        "inventory/writeoff.html",
        {
            "request": request,
            "item": item,
            "error_message": None,
            "success_message": None,
            "warnings": [],
        },
    )


@router.post("/web/inventory/{item_id}/writeoff", response_class=HTMLResponse)
def web_inventory_writeoff(
    item_id: int,
    request: Request,
    quantity: int = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    writeoff_in = InventoryWriteoffCreate(
        quantity=quantity,
        note=note or None,
    )
    _, error = inventory_service.writeoff_item(db, item_id, writeoff_in)

    if error == "item_not_found":
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if error == "not_enough_stock":
        item = inventory_service.get_item(db, item_id)
        return templates.TemplateResponse(
            "inventory/writeoff.html",
            {
                "request": request,
                "item": item,
                "error_message": "Недостатньо кількості на складі для списання.",
                "success_message": None,
                "warnings": [],
            },
        )

    return RedirectResponse(url="/web/inventory", status_code=303)