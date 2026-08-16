import argparse
import logging

from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.db import engine
from app.models import UserCreate, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create local RBAC demo users")
    parser.add_argument("--temporary-password", required=True)
    parser.add_argument("--manager-email", default="manager@example.com")
    parser.add_argument("--member-email", default="member@example.com")
    return parser.parse_args()


def ensure_user(*, session: Session, email: str, password: str, role: UserRole) -> None:
    existing_user = crud.get_user_by_email(session=session, email=email)
    if existing_user:
        logger.info("Demo user %s already exists; leaving it unchanged", email)
        return

    crud.create_user(
        session=session,
        user_create=UserCreate(email=email, password=password, role=role),
        password_change_required=True,
    )
    logger.info("Created %s demo user: %s", role, email)


def main() -> None:
    if settings.FASTAPI_ENV != "development":
        raise RuntimeError("Demo users can only be seeded in development")

    args = parse_args()
    with Session(engine) as session:
        ensure_user(
            session=session,
            email=args.manager_email,
            password=args.temporary_password,
            role=UserRole.manager,
        )
        ensure_user(
            session=session,
            email=args.member_email,
            password=args.temporary_password,
            role=UserRole.member,
        )


if __name__ == "__main__":
    main()
