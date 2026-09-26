import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.fixer import suggest_fix, apply_fix

client = TestClient(app)


def test_suggest_fix_function():
    code = "def validate_email(email):\n    return email.split('@')[10]"
    trace = "IndexError: list index out of range"
    res = suggest_fix(code, trace)
    assert "explanation" in res
    assert "diff" in res


def test_apply_fix_function():
    demo_repo_path = Path(__file__).resolve().parent.parent.parent / "demo_repo"
    res = apply_fix(
        repo_path=str(demo_repo_path),
        file_path="utils.py",
        function_name="validate_email"
    )
    assert res["status"] == "success"
    assert "utils.py" in res["file_path"]


def test_apply_fix_endpoint():
    demo_repo_path = Path(__file__).resolve().parent.parent.parent / "demo_repo"
    payload = {
        "repo_path": str(demo_repo_path),
        "file_path": "utils.py",
        "function_name": "validate_email"
    }
    response = client.post("/apply-fix", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
