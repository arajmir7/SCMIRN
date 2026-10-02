"""
Abstract base repository interface.
Implements Repository Pattern for data access abstraction.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Generic repository interface.
    
    All concrete repositories must implement these methods.
    This allows swapping database implementations without touching domain logic.
    """
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by primary key."""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_public_id(self, public_id: str) -> Optional[T]:
        """Get entity by public identifier."""
        raise NotImplementedError
    
    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination."""
        raise NotImplementedError
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity."""
        raise NotImplementedError
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity."""
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        raise NotImplementedError
    
    @abstractmethod
    def exists(self, id: int) -> bool:
        """Check if entity exists."""
        raise NotImplementedError