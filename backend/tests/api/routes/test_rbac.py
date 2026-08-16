from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlmodel import Session, col, func, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, UserRole
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def create_role_headers(
    *, client: TestClient, db: Session, role: UserRole
) -> dict[str, str]:
    email = random_email()
    password = random_lower_string()
    crud.create_user(
        session=db,
        user_create=UserCreate(email=email, password=password, role=role),
    )
    return user_authentication_headers(client=client, email=email, password=password)


def test_manager_has_read_only_user_and_metrics_access(
    client: TestClient, db: Session
) -> None:
    headers = create_role_headers(client=client, db=db, role=UserRole.manager)

    assert (
        client.get(f"{settings.API_V1_STR}/users/", headers=headers).status_code == 200
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/metrics/insights", headers=headers
        ).status_code
        == 200
    )
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=headers,
        json={"email": random_email(), "password": random_lower_string()},
    )
    assert response.status_code == 403


def test_member_can_update_self_but_cannot_list_users_or_view_metrics(
    client: TestClient, db: Session
) -> None:
    headers = create_role_headers(client=client, db=db, role=UserRole.member)

    assert (
        client.get(f"{settings.API_V1_STR}/users/", headers=headers).status_code == 403
    )
    assert (
        client.get(
            f"{settings.API_V1_STR}/metrics/insights", headers=headers
        ).status_code
        == 403
    )
    response = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
        json={"full_name": "Updated Member"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Member"


def test_signup_cannot_request_an_elevated_role(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json={
            "email": random_email(),
            "password": random_lower_string(),
            "role": UserRole.admin,
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == UserRole.member


def test_temporary_password_blocks_application_until_replaced(
    client: TestClient, db: Session
) -> None:
    email = random_email()
    temporary_password = random_lower_string()
    new_password = random_lower_string()
    crud.create_user(
        session=db,
        user_create=UserCreate(
            email=email,
            password=temporary_password,
            role=UserRole.member,
        ),
        password_change_required=True,
    )
    headers = user_authentication_headers(
        client=client, email=email, password=temporary_password
    )

    current_user = client.get(f"{settings.API_V1_STR}/users/me", headers=headers).json()
    assert current_user["must_change_password"] is True
    assert (
        client.get(f"{settings.API_V1_STR}/items/", headers=headers).status_code == 403
    )

    response = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json={
            "current_password": temporary_password,
            "new_password": new_password,
        },
    )
    assert response.status_code == 200
    assert (
        client.get(f"{settings.API_V1_STR}/items/", headers=headers).status_code == 200
    )


def test_administrator_cannot_demote_or_deactivate_self(
    client: TestClient, admin_token_headers: dict[str, str]
) -> None:
    admin = client.get(
        f"{settings.API_V1_STR}/users/me", headers=admin_token_headers
    ).json()

    demote_response = client.patch(
        f"{settings.API_V1_STR}/users/{admin['id']}",
        headers=admin_token_headers,
        json={"role": UserRole.member},
    )
    deactivate_response = client.patch(
        f"{settings.API_V1_STR}/users/{admin['id']}",
        headers=admin_token_headers,
        json={"is_active": False},
    )

    assert demote_response.status_code == 403
    assert deactivate_response.status_code == 403


def test_concurrent_demotions_preserve_an_active_administrator(
    client: TestClient, db: Session
) -> None:
    password_a = random_lower_string()
    password_b = random_lower_string()
    admin_a = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(), password=password_a, role=UserRole.admin
        ),
    )
    admin_b = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(), password=password_b, role=UserRole.admin
        ),
    )
    headers_a = user_authentication_headers(
        client=client, email=admin_a.email, password=password_a
    )
    headers_b = user_authentication_headers(
        client=client, email=admin_b.email, password=password_b
    )
    bootstrap_admin = db.exec(
        select(User).where(User.email == settings.BOOTSTRAP_ADMIN_EMAIL)
    ).one()

    try:
        bootstrap_admin.is_active = False
        db.add(bootstrap_admin)
        db.commit()

        def demote(user_id: str, headers: dict[str, str]) -> int:
            return client.patch(
                f"{settings.API_V1_STR}/users/{user_id}",
                headers=headers,
                json={"role": UserRole.member},
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(
                executor.map(
                    lambda request: demote(*request),
                    [(str(admin_b.id), headers_a), (str(admin_a.id), headers_b)],
                )
            )

        assert 200 in responses
        assert all(status in {200, 403, 409} for status in responses)
        db.expire_all()
        active_admins = db.exec(
            select(func.count())
            .select_from(User)
            .where(
                User.role == UserRole.admin,
                col(User.is_active).is_(True),
            )
        ).one()
        assert active_admins == 1
    finally:
        db.rollback()
        db.expire_all()
        bootstrap_admin = db.get(User, bootstrap_admin.id)
        if bootstrap_admin:
            bootstrap_admin.role = UserRole.admin
            bootstrap_admin.is_active = True
            db.add(bootstrap_admin)
        for user_id in (admin_a.id, admin_b.id):
            user = db.get(User, user_id)
            if user:
                db.delete(user)
        db.commit()
