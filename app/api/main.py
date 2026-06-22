from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routers import accounts, billing, customers, health, invoices


def create_app() -> FastAPI:
    application = FastAPI(
        title="SLT E-Bill API",
        version="1.0.0",
        description="REST API for the SLT e-billing system.",
    )
    register_exception_handlers(application)
    application.include_router(health.router)
    application.include_router(customers.router)
    application.include_router(accounts.router)
    application.include_router(invoices.router)
    application.include_router(billing.router)
    return application


app = create_app()
