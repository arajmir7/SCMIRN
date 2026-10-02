"""
Issue domain entity - pure business logic, no framework dependencies.
This is the heart of the domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
import uuid


class IssueStatus(Enum):
    REPORTED = "reported"
    VERIFIED = "verified"
    FUNDED = "funded"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class PriorityTier(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Location:
    """Value object for geographic coordinates."""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    
    def to_tuple(self) -> tuple:
        return (self.latitude, self.longitude)
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate Haversine distance to another location in km."""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


@dataclass
class MediaFile:
    """Value object for uploaded media."""
    url: str
    file_type: str  # image, video
    uploaded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Issue:
    """
    Domain entity representing a civic issue.
    Contains business rules and invariants.
    """
    
    # Identity
    id: Optional[int] = None
    public_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Content
    title: str = ""
    description: str = ""
    category: str = ""  # road, water, electricity, etc.
    
    # Location
    location: Optional[Location] = None
    
    # Priority (calculated by AI)
    priority_score: float = 0.0
    priority_tier: PriorityTier = PriorityTier.MEDIUM
    ai_confidence: float = 0.0
    
    # Status
    status: IssueStatus = IssueStatus.REPORTED
    
    # Funding
    fund_target: float = 5000.0
    fund_collected: float = 0.0
    
    # Media
    media_files: List[MediaFile] = field(default_factory=list)
    
    # Metadata
    integrity_hash: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Reporter
    reporter_id: Optional[int] = None
    reporter_phone: Optional[str] = None
    
    def __post_init__(self):
        """Validate invariants after creation."""
        if self.priority_score < 0 or self.priority_score > 10000:
            raise ValueError("Priority score must be between 0 and 10000")
        
        if self.fund_target <= 0:
            raise ValueError("Fund target must be positive")
    
    def calculate_progress_percentage(self) -> float:
        """Calculate funding progress."""
        if self.fund_target == 0:
            return 0.0
        return min(100.0, (self.fund_collected / self.fund_target) * 100)
    
    def add_funding(self, amount: float) -> None:
        """Add funding and update status if target reached."""
        if amount <= 0:
            raise ValueError("Funding amount must be positive")
        
        self.fund_collected += amount
        
        if self.fund_collected >= self.fund_target:
            self.status = IssueStatus.FUNDED
    
    def verify(self) -> None:
        """Mark issue as verified."""
        self.status = IssueStatus.VERIFIED
        self.updated_at = datetime.utcnow()
    
    def resolve(self) -> None:
        """Mark issue as resolved."""
        self.status = IssueStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'public_id': self.public_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'location': {
                'lat': self.location.latitude if self.location else None,
                'lng': self.location.longitude if self.location else None
            } if self.location else None,
            'priority_score': self.priority_score,
            'priority_tier': self.priority_tier.value,
            'status': self.status.value,
            'fund_target': self.fund_target,
            'fund_collected': self.fund_collected,
            'progress_percentage': round(self.calculate_progress_percentage(), 1),
            'media_files': [
                {'url': m.url, 'type': m.file_type} 
                for m in self.media_files
            ],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ai_confidence': self.ai_confidence
        }
    
    @classmethod
    def calculate_priority_tier(cls, score: float) -> PriorityTier:
        """Calculate tier from score."""
        if score >= 8500:
            return PriorityTier.CRITICAL
        elif score >= 6500:
            return PriorityTier.HIGH
        elif score >= 4000:
            return PriorityTier.MEDIUM
        else:
            return PriorityTier.LOW