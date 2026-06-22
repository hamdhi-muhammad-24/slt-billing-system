from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth import repository as auth_repo
from app.auth.dependencies import get_current_user
from app.auth.schemas import Token, UserOut
from app.auth.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = auth_repo.get_user_by_email(db, form.username)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    customer_id = auth_repo.get_customer_id_for_user(db, user.id)
    return Token(
        access_token=create_access_token(
            user_id=user.id,
            role=user.role.value,
            customer_id=customer_id,
        )
    )


@router.get("/me", response_model=UserOut)
def me(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    return current_user
