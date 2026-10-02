"""
Concrete repository implementations using SQLAlchemy.
"""

from typing import List, Optional, Tuple
from math import radians, cos, sin, asin, sqrt

from app.extensions import db
from app.core.repositories.issue_repository import IssueRepository
from app.core.entities.issue import Issue, Location, PriorityTier, IssueStatus


class SQLAlchemyIssueRepository(IssueRepository):
    """
    SQLAlchemy implementation of IssueRepository.
    Translates between ORM models and domain entities.
    """
    
    def get_by_id(self, id: int) -> Optional[Issue]:
        from .models import IssueORM
        orm = IssueORM.query.get(id)
        return orm.to_entity() if orm else None
    
    def get_by_public_id(self, public_id: str) -> Optional[Issue]:
        from .models import IssueORM
        orm = IssueORM.query.filter_by(public_id=public_id).first()
        return orm.to_entity() if orm else None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Issue]:
        from .models import IssueORM
        orms = IssueORM.query.order_by(IssueORM.priority_score.desc()).limit(limit).offset(offset).all()
        return [orm.to_entity() for orm in orms]
    
    def get_by_status(self, status: str, limit: int = 100) -> List[Issue]:
        from .models import IssueORM
        orms = IssueORM.query.filter_by(status=status).order_by(IssueORM.created_at.desc()).limit(limit).all()
        return [orm.to_entity() for orm in orms]
    
    def get_by_priority_tier(self, tier: str, limit: int = 100) -> List[Issue]:
        from .models import IssueORM
        orms = IssueORM.query.filter_by(priority_tier=tier).order_by(IssueORM.priority_score.desc()).limit(limit).all()
        return [orm.to_entity() for orm in orms]
    
    def get_nearby(self, location: Location, radius_km: float, 
                   limit: int = 100) -> List[Issue]:
        """
        Get issues within radius using Haversine formula.
        For production, use PostGIS for better performance.
        """
        from .models import IssueORM
        
        # Haversine formula in SQL
        lat, lon = location.latitude, location.longitude
        
        # Rough bounding box first (performance)
        km_per_deg_lat = 111
        km_per_deg_lon = 111 * cos(radians(lat))
        
        lat_range = radius_km / km_per_deg_lat
        lon_range = radius_km / km_per_deg_lon
        
        orms = IssueORM.query.filter(
            IssueORM.lat.between(lat - lat_range, lat + lat_range),
            IssueORM.lon.between(lon - lon_range, lon + lon_range)
        ).all()
        
        # Precise distance calculation
        result = []
        for orm in orms:
            dist = self._haversine(lat, lon, orm.lat, orm.lon)
            if dist <= radius_km:
                result.append((dist, orm))
        
        # Sort by distance
        result.sort(key=lambda x: x[0])
        return [orm.to_entity() for _, orm in result[:limit]]
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def get_funding_leaderboard(self, limit: int = 10) -> List[Issue]:
        from .models import IssueORM
        orms = IssueORM.query.order_by(IssueORM.fund_collected.desc()).limit(limit).all()
        return [orm.to_entity() for orm in orms]
    
    def create(self, entity: Issue) -> Issue:
        from .models import IssueORM
        import json
        
        orm = IssueORM(
            public_id=entity.public_id,
            title=entity.title,
            description=entity.description,
            category=entity.category,
            lat=entity.location.latitude if entity.location else None,
            lon=entity.location.longitude if entity.location else None,
            priority_score=entity.priority_score,
            priority_tier=entity.priority_tier.value,
            ai_confidence=entity.ai_confidence,
            status=entity.status.value,
            fund_target=entity.fund_target,
            fund_collected=entity.fund_collected,
            media_files=json.dumps([m.url for m in entity.media_files]),
            integrity_hash=entity.integrity_hash,
            reporter_id=entity.reporter_id
        )
        
        db.session.add(orm)
        db.session.commit()
        
        entity.id = orm.id
        return entity
    
    def update(self, entity: Issue) -> Issue:
        from .models import IssueORM
        import json
        
        orm = IssueORM.query.get(entity.id)
        if not orm:
            raise ValueError(f"Issue with id {entity.id} not found")
        
        orm.title = entity.title
        orm.description = entity.description
        orm.status = entity.status.value
        orm.fund_collected = entity.fund_collected
        orm.media_files = json.dumps([m.url for m in entity.media_files])
        
        db.session.commit()
        return entity
    
    def delete(self, id: int) -> bool:
        from .models import IssueORM
        orm = IssueORM.query.get(id)
        if orm:
            db.session.delete(orm)
            db.session.commit()
            return True
        return False
    
    def exists(self, id: int) -> bool:
        from .models import IssueORM
        return IssueORM.query.get(id) is not None
    
    def add_funding(self, issue_id: int, amount: float) -> Tuple[bool, float]:
        from .models import IssueORM
        
        orm = IssueORM.query.get(issue_id)
        if not orm:
            return False, 0
        
        orm.fund_collected += amount
        
        # Auto-update status if funded
        if orm.fund_collected >= orm.fund_target:
            orm.status = 'funded'
        
        db.session.commit()
        return True, orm.fund_collected
    
    def get_statistics(self) -> dict:
        from .models import IssueORM
        from sqlalchemy import func
        
        stats = {
            'total': IssueORM.query.count(),
            'critical': IssueORM.query.filter_by(priority_tier='critical').count(),
            'high': IssueORM.query.filter_by(priority_tier='high').count(),
            'resolved': IssueORM.query.filter_by(status='resolved').count(),
            'total_raised': db.session.query(func.sum(IssueORM.fund_collected)).scalar() or 0
        }
        
        return stats