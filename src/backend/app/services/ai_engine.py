"""Compatibility shim for legacy imports.

Prefer importing from `app.core.services.ai_engine`.
"""

from app.core.services.ai_engine import CivicIntelligenceAI, ai_engine

__all__ = ["CivicIntelligenceAI", "ai_engine"]

