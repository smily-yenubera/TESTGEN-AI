import pytest
from pathlib import Path
from app.scanner import scan_repo, scan_repo_full


def test_scan_repo_function_level_coverage(tmp_path):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    (repo_dir / "utils.py").write_text("def fn_a():\n    pass\n\ndef fn_b():\n    pass\n", encoding="utf-8")
    
    tests_dir = repo_dir / "tests"
    tests_dir.mkdir()
    # Generated test file matching function fn_a
    (tests_dir / "test_fn_a.py").write_text("def test_fn_a(): pass\n", encoding="utf-8")

    full_res = scan_repo_full(str(repo_dir))
    
    assert full_res["total"] == 2
    assert full_res["tested_count"] == 1
    assert full_res["untested_count"] == 1
    
    untested_names = [item["function"] for item in full_res["untested_functions"]]
    assert "fn_b" in untested_names
    assert "fn_a" not in untested_names


def test_scan_repo_module_level_coverage(tmp_path):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    (repo_dir / "service.py").write_text("def get_data():\n    pass\n", encoding="utf-8")
    
    tests_dir = repo_dir / "tests"
    tests_dir.mkdir()
    # Module-level test file test_service.py
    (tests_dir / "test_service.py").write_text("def test_get_data(): pass\n", encoding="utf-8")

    full_res = scan_repo_full(str(repo_dir))
    
    assert full_res["total"] == 1
    assert full_res["tested_count"] == 1
    assert full_res["untested_count"] == 0
