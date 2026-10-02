"""
Issue repository interface.
"""

from abc import abstractmethod
from typing import List, Optional, Tuple

from .base_repository import BaseRepository
from ..entities.issue import Issue, Location


class IssueRepository(BaseRepository[Issue]):
    """Repository interface for Issue entities."""
    
    @abstractmethod
    def get_by_status(self, status: str, limit: int = 100) -> List[Issue]:
        """Get issues by status."""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_priority_tier(self, tier: str, limit: int = 100) -> List[Issue]:
        """Get issues by priority tier."""
        raise NotImplementedError
    
    @abstractmethod
    def get_nearby(self, location: Location, radius_km: float, 
                   limit: int = 100) -> List[Issue]:
        """Get issues near a location."""
        raise NotImplementedError
    
    @abstractmethod
    def get_funding_leaderboard(self, limit: int = 10) -> List[Issue]:
        """Get most funded issues."""
        raise NotImplementedError
    
    @abstractmethod
    def add_funding(self, issue_id: int, amount: float) -> Tuple[bool, float]:
        """
        Add funding to an issue.
        Returns: (success, new_total)
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_statistics(self) -> dict:
        """Get aggregate statistics."""
        raise NotImplementedError