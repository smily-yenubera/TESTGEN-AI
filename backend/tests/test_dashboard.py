import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.state import dashboard_state

client = TestClient(app)


def test_dashboard_data_workflow(tmp_path):
    dashboard_state.reset()
    
    res0 = client.get("/dashboard-data")
    assert res0.status_code == 200
    data0 = res0.json()
    assert data0["summary"]["total_functions_scanned"] == 0
    
    repo_dir = tmp_path / "demo_repo"
    repo_dir.mkdir()
    (repo_dir / "app.py").write_text("def index():\n    return {'message': 'ok'}\n", encoding="utf-8")
    (repo_dir / "utils.py").write_text("def format_response(data):\n    return {'data': data}\n", encoding="utf-8")
    
    tests_dir = repo_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("from app import index\ndef test_index(): assert index()['message'] == 'ok'\n", encoding="utf-8")

    scan_res = client.post("/scan", json={"path": str(repo_dir)})
    assert scan_res.status_code == 200
    
    res1 = client.get("/dashboard-data")
    data1 = res1.json()
    assert data1["summary"]["total_functions_scanned"] == 2
    assert data1["summary"]["tested_count"] == 1
    assert data1["summary"]["untested_count"] == 1
    assert len(data1["untested_functions"]) == 1

    gen_res = client.post("/generate-tests", json={
        "repo_path": str(repo_dir),
        "function_name": "format_response"
    })
    assert gen_res.status_code == 200
    test_file_path = gen_res.json()["test_file_path"]

    res2 = client.get("/dashboard-data")
    data2 = res2.json()
    assert data2["summary"]["generated_tests_count"] == 1

    run_res = client.post("/run-tests", json={"test_file_path": test_file_path})
    assert run_res.status_code == 200

    res3 = client.get("/dashboard-data")
    data3 = res3.json()
    assert data3["summary"]["passed_tests_count"] >= 1

    fix_res = client.post("/suggest-fix", json={
        "function_code": "def func(): return 1/0",
        "error_trace": "ZeroDivisionError"
    })
    assert fix_res.status_code == 200

    res4 = client.get("/dashboard-data")
    data4 = res4.json()
    assert data4["summary"]["pending_fixes_count"] == 1
