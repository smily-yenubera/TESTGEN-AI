import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.generator import generate_tests

client = TestClient(app)


def test_generate_tests_function():
    code = "def add(a, b):\n    return a + b\n"
    res = generate_tests(code, "add", module_name="math_utils")
    assert "def test_add_" in res
    assert "pytest" in res


def test_generate_tests_endpoint():
    demo_repo_path = Path(__file__).resolve().parent.parent.parent / "demo_repo"
    payload = {
        "repo_path": str(demo_repo_path),
        "function_name": "validate_email"
    }
    response = client.post("/generate-tests", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["function_name"] == "validate_email"
    assert "test_validate_email.py" in data["test_file_path"]

    # Verify that file was saved in demo_repo/tests/test_validate_email.py
    saved_file = Path(data["test_file_path"])
    assert saved_file.exists()
    content = saved_file.read_text(encoding="utf-8")
    assert "def test_validate_email_" in content
