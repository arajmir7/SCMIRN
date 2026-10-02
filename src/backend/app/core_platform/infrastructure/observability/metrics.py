from __future__ import annotations

from datetime import datetime
import importlib
import time
from typing import Any


class _Metric:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def labels(self, *args: Any, **kwargs: Any) -> "_Metric":
        return self

    def observe(self, *args: Any, **kwargs: Any) -> None:
        return None

    def inc(self, *args: Any, **kwargs: Any) -> None:
        return None

    def set(self, *args: Any, **kwargs: Any) -> None:
        return None


try:
    _prometheus_client = importlib.import_module("prometheus_client")
    Counter = _prometheus_client.Counter  # type: ignore
    Histogram = _prometheus_client.Histogram  # type: ignore
    Gauge = _prometheus_client.Gauge  # type: ignore
except Exception:
    Counter = Histogram = Gauge = _Metric  # type: ignore

try:
    _flask = importlib.import_module("flask")
    request = _flask.request
except Exception:
    request = None  # type: ignore

# Define metrics
DOCUMENT_GENERATION_COUNTER = Counter(
    'scmirn_documents_generated_total',
    'Total documents generated',
    ['doc_type', 'status']
)

AI_RESPONSE_TIME = Histogram(
    'scmirn_ai_response_seconds',
    'AI engine response time',
    ['intent_type']
)

ACTIVE_USERS = Gauge(
    'scmirn_active_users',
    'Currently active users'
)

# Middleware to track metrics
class MetricsMiddleware:
    def before_request(self):
        if request is None:
            return
        request.start_time = time.time()
    
    def after_request(self, response):
        if request is None:
            return response

        start_time = getattr(request, "start_time", None)
        if start_time is None:
            return response

        duration = time.time() - start_time

        if '/api/ai-assistant' in getattr(request, "path", ""):
            payload = request.get_json(silent=True) if hasattr(request, "get_json") else None
            intent_type = payload.get('detected_intent', 'unknown') if isinstance(payload, dict) else 'unknown'
            AI_RESPONSE_TIME.labels(intent_type=intent_type).observe(duration)

        return response

try:
    _structlog = importlib.import_module("structlog")
    _logger = _structlog.get_logger()
except Exception:
    import logging

    class _FallbackLogger:
        def __init__(self, base_logger: logging.Logger) -> None:
            self._base_logger = base_logger

        def info(self, event: str, **kwargs: Any) -> None:
            self._base_logger.info("%s %s", event, kwargs)

    _logger = _FallbackLogger(logging.getLogger(__name__))

logger = _logger


def get_current_trace_id() -> str | None:
    if request is None:
        return None
    try:
        return request.headers.get("X-Trace-Id")
    except Exception:
        return None


def log_document_generation(doc_id: str, user_id: int, doc_type: str):
    logger.info(
        "document_generated",
        document_id=doc_id,
        user_id=user_id,
        doc_type=doc_type,
        timestamp=datetime.utcnow().isoformat(),
        service="document_service",
        trace_id=get_current_trace_id()  # Distributed tracing
    )
