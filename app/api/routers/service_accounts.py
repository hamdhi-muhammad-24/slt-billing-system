from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.errors import NotFound
from app.api.schemas import DailyUsageRecordOut
from app.auth import repository as auth_repo
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserOut
from app.db.models import ServiceAccount

router = APIRouter(prefix="/service-accounts", tags=["service-accounts"])


def _require_service_account_owner(
    service_account_id: int,
    current_user: UserOut,
    db: Session,
) -> ServiceAccount:
    service = db.get(ServiceAccount, service_account_id)
    if service is None:
        raise NotFound(f"Service account {service_account_id} not found")
    if current_user.role == "ADMIN":
        return service
    owner_customer_id = auth_repo.get_customer_id_for_account(db, service.account_id)
    if owner_customer_id is None or current_user.customer_id != owner_customer_id:
        raise NotFound(f"Service account {service_account_id} not found")
    return service


@router.get(
    "/{service_account_id}/daily-usage",
    response_model=list[DailyUsageRecordOut],
    summary="Daily usage for a service account",
    description="Returns day-by-day broadband usage for the requested billing month.",
)
def list_daily_usage_for_service(
    service_account_id: int,
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> list[DailyUsageRecordOut]:
    _require_service_account_owner(service_account_id, current_user, db)
    return crud.list_daily_usage_for_service(db, service_account_id, period=period)
