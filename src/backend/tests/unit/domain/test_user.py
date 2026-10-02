import pytest
from app.core_platform.domain.entities.user import User
from app.core_platform.domain.value_objects import PhoneNumber, Email

class TestUser:
    def test_cannot_create_user_with_invalid_phone(self):
        with pytest.raises(ValueError, match="Invalid phone format"):
            User.create(
                phone=PhoneNumber("12345"),  # Too short
                name="Test User"
            )
    
    def test_user_can_generate_document_when_verified(self):
        user = User.create(
            phone=PhoneNumber("9876543210"),
            name="Verified User",
            is_verified=True
        )
        assert user.can_generate_document() is True
