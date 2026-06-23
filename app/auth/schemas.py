from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    customer_id: int | None = None


class PdfTokenOut(BaseModel):
    token: str
    expires_in: int
