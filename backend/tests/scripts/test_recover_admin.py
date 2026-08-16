from collections.abc import Iterator

import pytest

from scripts import recover_admin as command


def test_prompt_temporary_password_confirms_without_exposing_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answers: Iterator[str] = iter(["temporary-password", "temporary-password"])
    monkeypatch.setattr(command.getpass, "getpass", lambda _prompt: next(answers))

    assert command.prompt_temporary_password() == "temporary-password"


def test_prompt_temporary_password_rejects_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answers: Iterator[str] = iter(["temporary-password", "different-password"])
    monkeypatch.setattr(command.getpass, "getpass", lambda _prompt: next(answers))

    with pytest.raises(RuntimeError, match="do not match"):
        command.prompt_temporary_password()


@pytest.mark.parametrize("password", ["short", "x" * 129])
def test_prompt_temporary_password_enforces_length(
    monkeypatch: pytest.MonkeyPatch, password: str
) -> None:
    answers: Iterator[str] = iter([password, password])
    monkeypatch.setattr(command.getpass, "getpass", lambda _prompt: next(answers))

    with pytest.raises(RuntimeError, match="Temporary password must contain"):
        command.prompt_temporary_password()
