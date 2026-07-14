"""
Synthetic seed data for the SLT e-bill system.

Usage:  python -m app.db.seed
"""

from __future__ import annotations

import sys
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.security import hash_password
from app.core.logging import configure_logging, get_logger
from app.db.base import SessionLocal
from app.db.models import UserRole

log = get_logger(__name__)

def seed_admin(session: Session) -> None:
    admin_email = "admin@slt.lk"
    admin = session.query(User).filter(User.email == admin_email).first()
    
    if not admin:
        log.info(f"Creating default admin user: {admin_email}")
        admin = User(
            email=admin_email,
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
    else:
        log.info(f"Admin user {admin_email} already exists.")

    admin1_email = "admin1@slt.lk"
    admin1 = session.query(User).filter(User.email == admin1_email).first()
    if not admin1:
        log.info(f"Creating default admin1 user: {admin1_email}")
        admin1 = User(
            email=admin1_email,
            password_hash=hash_password("admin1123"),
            role=UserRole.ADMIN1,
            is_active=True,
        )
        session.add(admin1)
    else:
        log.info(f"Admin1 user {admin1_email} already exists.")
        
    session.commit()

def main() -> int:
    configure_logging()
    log.info("Starting database seed...")

    try:
        with SessionLocal() as session:
            seed_admin(session)
            log.info("Database seeding complete.")
    except Exception as e:
        log.error(f"Seeding failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
