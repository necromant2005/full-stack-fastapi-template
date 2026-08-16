from sqlmodel import Session, create_engine

from app import crud
from app.core.admin import get_active_admin, get_any_admin, lock_admin_invariant
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User, UserCreate, UserRole

engine = create_engine(str(settings.DATABASE_URL))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    lock_admin_invariant(session)

    if get_active_admin(session):
        return

    if get_any_admin(session):
        raise RuntimeError(
            "No active administrator exists. Run "
            "'python scripts/recover_admin.py --email <email>' to recover access."
        )

    email = settings.BOOTSTRAP_ADMIN_EMAIL
    password = settings.BOOTSTRAP_ADMIN_TEMPORARY_PASSWORD
    if not email or not password:
        raise RuntimeError(
            "No administrator exists. Set BOOTSTRAP_ADMIN_EMAIL and "
            "BOOTSTRAP_ADMIN_TEMPORARY_PASSWORD to create the first administrator."
        )

    existing_user = crud.get_user_by_email(session=session, email=email)
    if existing_user:
        raise RuntimeError(
            "The bootstrap administrator email belongs to a non-admin user. "
            "Choose another BOOTSTRAP_ADMIN_EMAIL."
        )

    user_in = UserCreate(email=email, password=password, role=UserRole.admin)
    crud.create_user(
        session=session,
        user_create=user_in,
        password_change_required=True,
    )


def recover_admin(*, session: Session, email: str, temporary_password: str) -> User:
    lock_admin_invariant(session)
    if get_active_admin(session):
        raise RuntimeError(
            "An active administrator already exists; use normal user management."
        )

    existing_user = crud.get_user_by_email(session=session, email=email)
    if existing_user:
        existing_user.role = UserRole.admin
        existing_user.is_active = True
        existing_user.hashed_password = get_password_hash(temporary_password)
        existing_user.must_change_password = True
        session.add(existing_user)
        session.commit()
        session.refresh(existing_user)
        return existing_user

    user_in = UserCreate(
        email=email,
        password=temporary_password,
        role=UserRole.admin,
    )
    return crud.create_user(
        session=session,
        user_create=user_in,
        password_change_required=True,
    )
