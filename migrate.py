from app.db.base import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE invoice_templates ADD COLUMN approval_status VARCHAR DEFAULT 'PENDING' NOT NULL;"))
    conn.commit()
