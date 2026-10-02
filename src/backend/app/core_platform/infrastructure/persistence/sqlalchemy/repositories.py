"""
Legacy compatibility layer.
Expose IssueRepository for modules still importing from core_platform.
"""

from app.infrastructure.database.repositories import SQLAlchemyIssueRepository as IssueRepository

__all__ = ["IssueRepository"]
