from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routers import accounts, billing, customers, health, invoice_templates, invoices, service_accounts
from app.auth import router as auth_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title="SLT E-Bill API",
        version="1.0.0",
        description="REST API for the SLT e-billing system.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)
    application.include_router(auth_router.router)
    application.include_router(health.router)
    application.include_router(customers.router)
    application.include_router(accounts.router)
    application.include_router(service_accounts.router)
    application.include_router(invoices.router)
    application.include_router(invoice_templates.router)
    application.include_router(billing.router)
    return application


app = create_app()
