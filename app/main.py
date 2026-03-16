from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from starlette.staticfiles import StaticFiles

from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.expenses import router as expenses_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.phones import router as phones_router
from app.api.routes.shipments import router as shipments_router
from app.api.routes.views import router as views_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import engine

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup():
    init_db()


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router)
app.include_router(phones_router)
app.include_router(expenses_router)
app.include_router(shipments_router)
app.include_router(dashboard_router)
app.include_router(inventory_router)
app.include_router(views_router)


@app.get("/")
def root():
    return RedirectResponse(url="/web/dashboard")


@app.get("/health/db")
def health_db():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}
