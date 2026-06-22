from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth import repository as auth_repo
from app.auth.schemas import UserOut
from app.auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserOut:
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise _401

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise _401

    user = auth_repo.get_user_by_id(db, int(user_id_str))
    if user is None or not user.is_active:
        raise _401

    return UserOut(
        id=user.id,
        email=user.email,
        role=payload["role"],
        customer_id=payload.get("customer_id"),
    )


def require_admin(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
