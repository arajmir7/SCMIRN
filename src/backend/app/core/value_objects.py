"""Domain value objects."""
from __future__ import annotations

from dataclasses import dataclass
import re


_PHONE_RE = re.compile(r"^\d{10}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class PhoneNumber:
    value: str

    def __post_init__(self) -> None:
        if not _PHONE_RE.match(self.value):
            raise ValueError("Invalid phone format")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise ValueError("Invalid email format")

    def __str__(self) -> str:
        return self.value


__all__ = ["PhoneNumber", "Email"]
