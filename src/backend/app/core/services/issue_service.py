"""Issue service wrapper."""

from app.infrastructure.database.repositories import SQLAlchemyIssueRepository


class IssueService:
    def __init__(self, repo=None):
        self.repo = repo or SQLAlchemyIssueRepository()

    def get_all(self):
        return self.repo.get_all()
