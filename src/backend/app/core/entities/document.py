"""
Document domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class DocumentType(Enum):
    RTI = "rti"
    FIR_COMPLAINT = "fir_complaint"
    CONSUMER_COMPLAINT = "consumer_complaint"
    RENT_NOTICE = "rent_notice"
    SCHOLARSHIP_GRIEVANCE = "scholarship_grievance"
    ELECTRICITY_COMPLAINT = "electricity_complaint"
    GENERAL = "general"


class DocumentStatus(Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    DOWNLOADED = "downloaded"
    SUBMITTED = "submitted"


@dataclass
class Document:
    """Domain entity representing a generated document."""
    
    id: Optional[int] = None
    public_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Ownership
    user_id: Optional[int] = None
    
    # Content
    doc_type: DocumentType = DocumentType.GENERAL
    status: DocumentStatus = DocumentStatus.DRAFT
    
    # Template data
    template_data: Dict[str, Any] = field(default_factory=dict)
    generated_content: Optional[str] = None
    
    # File storage
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    
    # Metadata
    title: Optional[str] = None
    jurisdiction: Optional[str] = None  # State/region
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    generated_at: Optional[datetime] = None
    downloaded_at: Optional[datetime] = None
    
    def mark_generated(self, content: str, file_path: str) -> None:
        """Mark document as generated."""
        self.generated_content = content
        self.file_path = file_path
        self.status = DocumentStatus.GENERATED
        self.generated_at = datetime.utcnow()
    
    def mark_downloaded(self) -> None:
        """Mark document as downloaded."""
        self.status = DocumentStatus.DOWNLOADED
        self.downloaded_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'public_id': self.public_id,
            'doc_type': self.doc_type.value,
            'status': self.status.value,
            'title': self.title,
            'jurisdiction': self.jurisdiction,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'download_url': f'/api/documents/{self.public_id}/download' if self.file_path else None
        }