"""
Generate a daily SCMIRN enterprise executive briefing.

Usage:
    python scripts/generate_executive_briefing.py
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "src" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app  # noqa: E402


def main() -> int:
    app = create_app("development")
    payload = {
        "city_id": "metro-demo",
        "recipients": ["ceo@scmirn.local", "ciso@scmirn.local"],
        "include_pdf": True,
        "include_recommendations": True,
    }

    with app.test_client() as client:
        response = client.post("/api/v1/enterprise/executive/briefings/generate", json=payload)
        data = response.get_json()
        print(json.dumps(data, indent=2))
        return 0 if response.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
