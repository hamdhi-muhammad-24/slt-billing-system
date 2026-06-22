# The users table and user_role enum live in app/db/models (created in the
# initial migration alongside billing tables).  Auth code imports from here so
# there is one canonical re-export point for the auth entity.
from app.db.models import User, UserRole  # noqa: F401

__all__ = ["User", "UserRole"]
