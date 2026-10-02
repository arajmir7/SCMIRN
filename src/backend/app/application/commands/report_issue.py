"""
ReportIssue command - handles issue creation workflow.
Implements CQRS Command pattern.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from app.core.entities.issue import Issue, Location, MediaFile, PriorityTier, IssueStatus
from app.core.services.ai_engine import ai_engine
from app.core.repositories.issue_repository import IssueRepository


@dataclass
class ReportIssueCommand:
    """Command to report a new civic issue."""
    title: str
    description: str
    category: str
    lat: Optional[float]
    lon: Optional[float]
    media_urls: List[str]
    fund_target: float
    reporter_id: Optional[int] = None
    reporter_phone: Optional[str] = None


class ReportIssueHandler:
    """
    Handler for ReportIssueCommand.
    Orchestrates the issue creation workflow.
    """
    
    def __init__(self, issue_repo: IssueRepository):
        self._repo = issue_repo
    
    def execute(self, command: ReportIssueCommand) -> dict:
        """
        Execute the command.
        
        Returns:
            Dict with created issue details and AI analysis
        """
        # Step 1: AI Analysis
        full_text = f"{command.title} {command.description}"
        intent_result = ai_engine.process(full_text)
        
        # Step 2: Calculate priority using AI
        score, tier, confidence = ai_engine.calculate_priority(
            command.title,
            command.description,
            command.category
        )
        
        # Step 3: Create location if coordinates provided
        location = None
        if command.lat and command.lon:
            location = Location(
                latitude=command.lat,
                longitude=command.lon
            )
        
        # Step 4: Create media files
        media_files = [
            MediaFile(url=url, file_type='image') 
            for url in command.media_urls
        ]
        
        # Step 5: Create domain entity
        issue = Issue(
            title=command.title,
            description=command.description,
            category=command.category,
            location=location,
            priority_score=score,
            priority_tier=PriorityTier(tier),
            ai_confidence=confidence,
            status=IssueStatus.REPORTED,
            fund_target=command.fund_target,
            media_files=media_files,
            reporter_id=command.reporter_id
        )
        
        # Step 6: Persist
        created = self._repo.create(issue)
        
        # Step 7: Return result
        return {
            'success': True,
            'issue_id': created.public_id,
            'priority': {
                'tier': tier,
                'score': score,
                'confidence': confidence
            },
            'ai_analysis': {
                'intent': intent_result.intent,
                'recommended_action': intent_result.action
            },
            'message': f'Issue reported successfully! AI classified as {tier.upper()} priority.'
        }