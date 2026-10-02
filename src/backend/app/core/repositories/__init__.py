"""
Repository interfaces (abstract).
Concrete implementations are in infrastructure layer.
"""

from .base_repository import BaseRepository
from .issue_repository import IssueRepository

__all__ = ['BaseRepository', 'IssueRepository']