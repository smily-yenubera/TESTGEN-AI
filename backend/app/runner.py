"""
Test execution runner module using subprocess and pytest JSON reporting.
"""

import sys
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List


def run_tests(test_file_path: str) -> Dict[str, Any]:
    """
    Executes the given pytest file in a subprocess, captures pass/fail results
    and full stack traces for failures, returning structured JSON.
    """
    test_path = Path(test_file_path).resolve()
    if not test_path.exists():
        raise ValueError(f"Test file does not exist: {test_file_path}")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        report_json_path = Path(tmp.name)

    try:
        # Determine working directory (parent repo folder)
        cwd = test_path.parent.parent if test_path.parent.name == "tests" else test_path.parent

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(test_path),
            "-v",
            "--json-report",
            f"--json-report-file={report_json_path}"
        ]

        result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)

        if report_json_path.exists() and report_json_path.stat().st_size > 0:
            with open(report_json_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            return _format_pytest_json_report(report_data, str(test_path))
        else:
            return {
                "status": "failed" if result.returncode != 0 else "passed",
                "test_file": str(test_path),
                "summary": {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "duration": 0.0
                },
                "tests": [],
                "stdout": result.stdout,
                "stderr": result.stderr
            }
    finally:
        if report_json_path.exists():
            try:
                report_json_path.unlink()
            except Exception:
                pass


def _format_pytest_json_report(report_data: Dict[str, Any], test_file_path: str) -> Dict[str, Any]:
    summary_raw = report_data.get("summary", {})
    summary = {
        "total": summary_raw.get("total", 0),
        "passed": summary_raw.get("passed", 0),
        "failed": summary_raw.get("failed", 0),
        "skipped": summary_raw.get("skipped", 0),
        "duration": round(report_data.get("duration", 0.0), 4)
    }

    tests_list: List[Dict[str, Any]] = []

    for item in report_data.get("tests", []):
        nodeid = item.get("nodeid", "")
        test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
        outcome = item.get("outcome", "unknown")
        
        call_info = item.get("call", {})
        error_message = None
        traceback_str = None

        if outcome == "failed":
            crash = call_info.get("crash", {})
            error_message = crash.get("message", None) or str(call_info.get("longrepr", ""))
            traceback_str = str(call_info.get("longrepr", "")) or crash.get("message", None)

        tests_list.append({
            "name": test_name,
            "nodeid": nodeid,
            "status": outcome,
            "duration": round(call_info.get("duration", 0.0), 4),
            "error_message": error_message,
            "traceback": traceback_str
        })

    overall_status = "passed" if summary["failed"] == 0 and summary["total"] > 0 else "failed"

    return {
        "status": overall_status,
        "test_file": test_file_path,
        "summary": summary,
        "tests": tests_list
    }
