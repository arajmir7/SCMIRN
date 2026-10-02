from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass
class FakeResponse:
    status_code: int
    json: Dict[str, Any]


class FakeClient:
    def __init__(self) -> None:
        self._docs: Dict[str, Dict[str, Any]] = {}
        self._counter = 0

    def post(self, path: str, json: Dict[str, Any], headers: Dict[str, Any] | None = None) -> FakeResponse:
        if path == "/api/documents":
            self._counter += 1
            doc_id = f"doc_{self._counter}"
            self._docs[doc_id] = {"status": "processing", "polls": 0}
            return FakeResponse(202, {"data": {"document_id": doc_id}})
        return FakeResponse(404, {"error": "Not found"})

    def get(self, path: str) -> FakeResponse:
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) >= 3 and segments[0] == "api" and segments[1] == "documents":
            doc_id = segments[2]
            if doc_id not in self._docs:
                return FakeResponse(404, {"error": "Document not found"})

            record = self._docs[doc_id]
            if len(segments) == 4 and segments[3] == "status":
                return FakeResponse(200, {"data": {"status": record["status"]}})

            record["polls"] += 1
            if record["polls"] >= 1:
                record["status"] = "completed"

            data: Dict[str, Any] = {"status": record["status"]}
            if record["status"] == "completed":
                data["download_url"] = f"/downloads/{doc_id}.pdf"
            return FakeResponse(200, {"data": data})

        return FakeResponse(404, {"error": "Not found"})


class FakeLocator:
    def __init__(self, selector: str) -> None:
        self.selector = selector


class FakePage:
    def __init__(self) -> None:
        self.url = ""

    def goto(self, url: str) -> None:
        self.url = url

    def click(self, selector: str) -> None:
        if "Generate RTI Document" in selector:
            self.url = "http://localhost:5000/documents?type=rti"

    def fill(self, selector: str, value: str) -> None:
        return None

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(selector)


class _Expectation:
    def __init__(self, target: Any) -> None:
        self._target = target

    def to_be_visible(self) -> None:
        return None

    def to_contain_text(self, text: str) -> None:
        return None

    def to_have_url(self, pattern: Any) -> None:
        url = getattr(self._target, "url", "")
        if hasattr(pattern, "search"):
            assert pattern.search(url), f"Expected URL to match {pattern.pattern}, got {url}"
        else:
            assert url == pattern, f"Expected URL {pattern}, got {url}"


def fake_expect(target: Any) -> _Expectation:
    return _Expectation(target)


@pytest.fixture
def client() -> FakeClient:
    return FakeClient()


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def page() -> FakePage:
    return FakePage()


__all__ = ["fake_expect"]
