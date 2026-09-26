import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.runner import run_tests

client = TestClient(app)


def test_run_tests_function():
    test_file = Path(__file__).resolve().parent.parent.parent / "demo_repo" / "tests" / "test_validate_email.py"
    res = run_tests(str(test_file))
    assert res["status"] == "passed"
    assert res["summary"]["passed"] == 3
    assert len(res["tests"]) == 3
    assert res["tests"][0]["status"] == "passed"


def test_run_tests_endpoint():
    test_file = Path(__file__).resolve().parent.parent.parent / "demo_repo" / "tests" / "test_validate_email.py"
    response = client.post("/run-tests", json={"test_file_path": str(test_file)})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "passed"
    assert data["summary"]["passed"] == 3
    assert data["summary"]["failed"] == 0
