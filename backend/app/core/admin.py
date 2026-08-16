from sqlalchemy import text
from sqlmodel import Session, col, func, select

from app.models import User, UserRole

# Stable, application-specific PostgreSQL advisory lock ID. Every transaction that
# can establish or reduce administrator availability must use this same lock.
ADMIN_INVARIANT_LOCK_ID = 0x4653545242414301


def lock_admin_invariant(session: Session) -> None:
    session.connection().execute(
        text("SELECT pg_advisory_xact_lock(:lock_id)"),
        {"lock_id": ADMIN_INVARIANT_LOCK_ID},
    )


def get_active_admin(session: Session) -> User | None:
    return session.exec(
        select(User).where(
            User.role == UserRole.admin,
            col(User.is_active).is_(True),
        )
    ).first()


def get_any_admin(session: Session) -> User | None:
    return session.exec(select(User).where(User.role == UserRole.admin)).first()


def count_active_admins(session: Session) -> int:
    return session.exec(
        select(func.count())
        .select_from(User)
        .where(
            User.role == UserRole.admin,
            col(User.is_active).is_(True),
        )
    ).one()
