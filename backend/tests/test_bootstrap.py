from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.core.db import init_db, recover_admin
from app.models import User, UserRole


def test_existing_active_administrator_is_never_modified_after_email_change() -> None:
    session = MagicMock(spec=Session)
    admin = User(
        email="existing-admin@example.com",
        hashed_password="existing-hash",
        role=UserRole.admin,
    )

    with (
        patch("app.core.db.lock_admin_invariant") as lock,
        patch("app.core.db.get_active_admin", return_value=admin),
        patch("app.core.db.settings.BOOTSTRAP_ADMIN_EMAIL", "old-admin@example.com"),
        patch("app.core.db.crud.get_user_by_email") as get_user_by_email,
        patch("app.core.db.crud.create_user") as create_user,
    ):
        init_db(session)

    lock.assert_called_once_with(session)
    get_user_by_email.assert_not_called()
    create_user.assert_not_called()


def test_startup_requires_recovery_when_only_inactive_admin_exists() -> None:
    session = MagicMock(spec=Session)
    inactive_admin = User(
        email="inactive-admin@example.com",
        hashed_password="existing-hash",
        role=UserRole.admin,
        is_active=False,
    )

    with (
        patch("app.core.db.lock_admin_invariant"),
        patch("app.core.db.get_active_admin", return_value=None),
        patch("app.core.db.get_any_admin", return_value=inactive_admin),
        pytest.raises(RuntimeError, match="recover_admin.py"),
    ):
        init_db(session)


def test_bootstrap_credentials_are_required_when_no_administrator_exists() -> None:
    session = MagicMock(spec=Session)

    with (
        patch("app.core.db.lock_admin_invariant"),
        patch("app.core.db.get_active_admin", return_value=None),
        patch("app.core.db.get_any_admin", return_value=None),
        patch("app.core.db.settings.BOOTSTRAP_ADMIN_EMAIL", None),
        patch("app.core.db.settings.BOOTSTRAP_ADMIN_TEMPORARY_PASSWORD", None),
        pytest.raises(RuntimeError, match="No administrator exists"),
    ):
        init_db(session)


def test_bootstrap_creates_an_admin_with_a_temporary_password() -> None:
    session = MagicMock(spec=Session)

    with (
        patch("app.core.db.lock_admin_invariant"),
        patch("app.core.db.get_active_admin", return_value=None),
        patch("app.core.db.get_any_admin", return_value=None),
        patch("app.core.db.settings.BOOTSTRAP_ADMIN_EMAIL", "admin@example.com"),
        patch(
            "app.core.db.settings.BOOTSTRAP_ADMIN_TEMPORARY_PASSWORD",
            "temporary-password",
        ),
        patch("app.core.db.crud.get_user_by_email", return_value=None),
        patch("app.core.db.crud.create_user") as create_user,
    ):
        init_db(session)

    user_create = create_user.call_args.kwargs["user_create"]
    assert user_create.email == "admin@example.com"
    assert user_create.role == UserRole.admin
    assert create_user.call_args.kwargs["password_change_required"] is True


def test_bootstrap_does_not_promote_an_existing_non_admin() -> None:
    session = MagicMock(spec=Session)
    member = User(
        email="admin@example.com",
        hashed_password="existing-hash",
        role=UserRole.member,
    )

    with (
        patch("app.core.db.lock_admin_invariant"),
        patch("app.core.db.get_active_admin", return_value=None),
        patch("app.core.db.get_any_admin", return_value=None),
        patch("app.core.db.settings.BOOTSTRAP_ADMIN_EMAIL", "admin@example.com"),
        patch(
            "app.core.db.settings.BOOTSTRAP_ADMIN_TEMPORARY_PASSWORD",
            "temporary-password",
        ),
        patch("app.core.db.crud.get_user_by_email", return_value=member),
        pytest.raises(RuntimeError, match="belongs to a non-admin user"),
    ):
        init_db(session)


def test_recovery_refuses_when_an_active_admin_exists() -> None:
    session = MagicMock(spec=Session)
    admin = User(
        email="admin@example.com",
        hashed_password="existing-hash",
        role=UserRole.admin,
    )

    with (
        patch("app.core.db.lock_admin_invariant"),
        patch("app.core.db.get_active_admin", return_value=admin),
        pytest.raises(RuntimeError, match="active administrator already exists"),
    ):
        recover_admin(
            session=session,
            email="recovery@example.com",
            temporary_password="temporary-password",
        )


def test_recovery_reactivates_and_promotes_an_existing_user() -> None:
    session = MagicMock(spec=Session)
    existing_user = User(
        email="recovery@example.com",
        hashed_password="old-hash",
        role=UserRole.member,
        is_active=False,
    )

    with (
        patch("app.core.db.lock_admin_invariant"),
        patch("app.core.db.get_active_admin", return_value=None),
        patch("app.core.db.crud.get_user_by_email", return_value=existing_user),
        patch("app.core.db.get_password_hash", return_value="new-hash"),
    ):
        recovered = recover_admin(
            session=session,
            email="recovery@example.com",
            temporary_password="temporary-password",
        )

    assert recovered is existing_user
    assert recovered.role == UserRole.admin
    assert recovered.is_active is True
    assert recovered.hashed_password == "new-hash"
    assert recovered.must_change_password is True
    session.commit.assert_called_once()


def test_recovery_creates_an_admin_when_the_account_does_not_exist() -> None:
    session = MagicMock(spec=Session)
    created_admin = User(
        email="recovery@example.com",
        hashed_password="new-hash",
        role=UserRole.admin,
        must_change_password=True,
    )

    with (
        patch("app.core.db.lock_admin_invariant"),
        patch("app.core.db.get_active_admin", return_value=None),
        patch("app.core.db.crud.get_user_by_email", return_value=None),
        patch(
            "app.core.db.crud.create_user", return_value=created_admin
        ) as create_user,
    ):
        recovered = recover_admin(
            session=session,
            email="recovery@example.com",
            temporary_password="temporary-password",
        )

    assert recovered is created_admin
    assert create_user.call_args.kwargs["password_change_required"] is True
