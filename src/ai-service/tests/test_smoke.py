from pathlib import Path


def test_project_layout_has_core_modules() -> None:
    root = Path(__file__).resolve().parents[1]

    assert (root / "app" / "document_generator.py").exists()
    assert (root / "app" / "engine" / "response_generator.py").exists()

