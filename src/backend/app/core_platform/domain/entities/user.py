"""User domain entity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.core_platform.domain.value_objects import Email, PhoneNumber


@dataclass(frozen=True)
class User:
    id: str
    phone: PhoneNumber
    name: str
    email: Optional[Email] = None
    is_verified: bool = False

    @classmethod
    def create(
        cls,
        phone: PhoneNumber,
        name: str,
        is_verified: bool = False,
        email: Optional[Email] = None,
        user_id: Optional[str] = None,
    ) -> "User":
        if not isinstance(phone, PhoneNumber):
            raise ValueError("Invalid phone format")
        if not name or not name.strip():
            raise ValueError("Name is required")
        return cls(
            id=user_id or str(uuid4()),
            phone=phone,
            name=name.strip(),
            email=email,
            is_verified=is_verified,
        )

    def can_generate_document(self) -> bool:
        return bool(self.is_verified)
