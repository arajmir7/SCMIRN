"""
Data Transfer Objects for Issue-related data.
Used for API serialization/deserialization.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class IssueResponseDTO:
    """DTO for issue API responses."""
    id: str
    title: str
    description: str
    category: str
    priority_tier: str
    priority_score: float
    status: str
    fund_target: float
    fund_collected: float
    progress_percentage: float
    location: Optional[dict]
    media_urls: List[str]
    created_at: str
    ai_confidence: float
    
    @classmethod
    def from_entity(cls, entity) -> 'IssueResponseDTO':
        """Create DTO from domain entity."""
        data = entity.to_dict()
        return cls(**data)


@dataclass
class CreateIssueRequestDTO:
    """DTO for creating new issue."""
    title: str
    description: str
    category: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    fund_target: float = 5000.0