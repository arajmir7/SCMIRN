from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class DocumentGeneratedEvent:
    """Domain event - immutable fact that something happened"""
    document_id: str
    user_id: int
    doc_type: str
    generated_at: datetime
    file_path: str

@dataclass(frozen=True)
class IssueEscalatedEvent:
    issue_id: str
    from_status: str
    to_status: str
    escalated_at: datetime
    reason: str
