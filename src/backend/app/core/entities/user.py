"""
User domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid


@dataclass
class User:
    """Domain entity representing a system user."""
    
    id: Optional[int] = None
    public_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Contact info (primary identifier is phone in India)
    phone: str = ""
    email: Optional[str] = None
    
    # Profile
    name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None
    
    # Preferences
    preferred_language: str = "en"  # ISO code
    notification_enabled: bool = True
    
    # Verification
    phone_verified: bool = False
    email_verified: bool = False
    
    # Security
    password_hash: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    def can_generate_document(self) -> bool:
        """Check if user can generate documents."""
        return self.phone_verified and self.is_active
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excludes sensitive fields)."""
        return {
            'id': self.id,
            'public_id': self.public_id,
            'phone': self.phone,
            'email': self.email,
            'name': self.name,
            'state': self.state,
            'preferred_language': self.preferred_language,
            'phone_verified': self.phone_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }