import argparse
import getpass
import logging

from pydantic import EmailStr, TypeAdapter
from sqlmodel import Session

from app.core.db import engine, recover_admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recover access when no active administrator exists"
    )
    parser.add_argument("--email", required=True)
    return parser.parse_args()


def prompt_temporary_password() -> str:
    password = getpass.getpass("Temporary password: ")
    confirmation = getpass.getpass("Confirm temporary password: ")
    if password != confirmation:
        raise RuntimeError("Temporary passwords do not match")
    if len(password) < 8:
        raise RuntimeError("Temporary password must contain at least 8 characters")
    if len(password) > 128:
        raise RuntimeError("Temporary password must contain at most 128 characters")
    return password


def main() -> None:
    args = parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email))
    temporary_password = prompt_temporary_password()

    with Session(engine) as session:
        admin = recover_admin(
            session=session,
            email=email,
            temporary_password=temporary_password,
        )
    logger.info(
        "Recovered administrator %s; a password replacement is required at login",
        admin.email,
    )


if __name__ == "__main__":
    main()
