from fastapi import FastAPI

from app.api.routers import accounts, customers, health, invoices


def create_app() -> FastAPI:
    application = FastAPI(
        title="SLT E-Bill API",
        version="1.0.0",
        description="REST API for the SLT e-billing system.",
    )
    application.include_router(health.router)
    application.include_router(customers.router)
    application.include_router(accounts.router)
    application.include_router(invoices.router)
    return application


app = create_app()
