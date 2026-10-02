"""
GetIssues query - retrieves issues with filtering.
Implements CQRS Query pattern (read-only, optimized).
"""

from dataclasses import dataclass
from typing import List, Optional, Dict

from app.core.repositories.issue_repository import IssueRepository
from app.core.entities.issue import Issue


@dataclass
class GetIssuesQuery:
    """Query parameters for fetching issues."""
    tier: Optional[str] = None
    status: Optional[str] = None
    nearby_lat: Optional[float] = None
    nearby_lon: Optional[float] = None
    radius_km: float = 5.0
    limit: int = 100
    offset: int = 0


class GetIssuesHandler:
    """
    Handler for GetIssuesQuery.
    Optimized for read performance with caching.
    """
    
    def __init__(self, issue_repo: IssueRepository):
        self._repo = issue_repo
    
    def execute(self, query: GetIssuesQuery) -> Dict:
        """Execute query and return results."""
        
        # Determine query type
        if query.nearby_lat and query.nearby_lon:
            # Geo query
            from app.core.entities.issue import Location
            location = Location(query.nearby_lat, query.nearby_lon)
            issues = self._repo.get_nearby(location, query.radius_km, query.limit)
        elif query.tier:
            issues = self._repo.get_by_priority_tier(query.tier, query.limit)
        elif query.status:
            issues = self._repo.get_by_status(query.status, query.limit)
        else:
            issues = self._repo.get_all(query.limit, query.offset)
        
        return {
            'success': True,
            'count': len(issues),
            'issues': [issue.to_dict() for issue in issues]
        }


class GetIssueStatisticsHandler:
    """Handler for dashboard statistics."""
    
    def __init__(self, issue_repo: IssueRepository):
        self._repo = issue_repo
    
    def execute(self) -> Dict:
        """Get aggregated statistics."""
        stats = self._repo.get_statistics()
        
        return {
            'success': True,
            'statistics': stats
        }