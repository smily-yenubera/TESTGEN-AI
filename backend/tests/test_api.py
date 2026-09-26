from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_endpoint(tmp_path):
    repo_dir = tmp_path / "demo_repo"
    repo_dir.mkdir()
    (repo_dir / "app.py").write_text("def index(): pass\n", encoding="utf-8")
    (repo_dir / "utils.py").write_text("def format_response(): pass\ndef validate_email(): pass\n", encoding="utf-8")
    
    tests_dir = repo_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("def test_index(): pass\n", encoding="utf-8")
    (tests_dir / "test_validate_email.py").write_text("def test_validate_email(): pass\n", encoding="utf-8")

    response = client.post("/scan", json={"path": str(repo_dir)})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    untested = data["untested_functions"]
    untested_names = [item["function"] for item in untested]
    
    assert "format_response" in untested_names
    assert "validate_email" not in untested_names
    assert "index" not in untested_names
