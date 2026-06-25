import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.auth.dependencies import (
    get_current_user,
    require_account_owner,
    require_admin,
    require_invoice_owner,
    require_pdf_access,
)
from app.auth.schemas import UserOut


def _test_admin() -> UserOut:
    return UserOut(
        id=0,
        email="test-admin@slt.local",
        role="ADMIN",
        customer_id=None,
    )


def _allow_pdf_access() -> None:
    return None


@pytest.fixture(scope="session")
def client() -> TestClient:
    app.dependency_overrides[get_current_user] = _test_admin
    app.dependency_overrides[require_admin] = _test_admin
    app.dependency_overrides[require_account_owner] = _test_admin
    app.dependency_overrides[require_invoice_owner] = _test_admin
    app.dependency_overrides[require_pdf_access] = _allow_pdf_access
    with TestClient(app, headers={"Authorization": "Bearer test-admin-token"}) as c:
        yield c
    app.dependency_overrides.clear()
