"""
In-memory shared state manager for TestGen AI Dashboard.
"""

from typing import Dict, Any, List
import threading


class DashboardState:
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self.total_functions_scanned: int = 0
            self.tested_count: int = 0
            self.untested_count: int = 0
            self.scanned_functions: List[Dict[str, Any]] = []
            self.untested_functions: List[Dict[str, Any]] = []
            self.generated_tests: List[Dict[str, Any]] = []
            self.last_test_run: Dict[str, Any] = {}
            self.fix_suggestions: List[Dict[str, Any]] = []

    def update_scan(self, total: int, tested: int, untested: int, all_functions: List[Dict[str, Any]], untested_funcs: List[Dict[str, Any]]):
        with self._lock:
            self.total_functions_scanned = total
            self.tested_count = tested
            self.untested_count = untested
            self.scanned_functions = all_functions
            self.untested_functions = untested_funcs

    def add_generated_test(self, function_name: str, module_name: str, test_file_path: str, generated_code: str):
        with self._lock:
            # Update existing or append new
            existing = next((t for t in self.generated_tests if t["function_name"] == function_name), None)
            record = {
                "function_name": function_name,
                "module_name": module_name,
                "test_file_path": test_file_path,
                "generated_code": generated_code,
                "status": "generated"
            }
            if existing:
                existing.update(record)
            else:
                self.generated_tests.append(record)

    def update_test_run(self, run_result: Dict[str, Any]):
        with self._lock:
            self.last_test_run = run_result
            # Match test outcomes to generated tests
            for test_item in run_result.get("tests", []):
                name = test_item.get("name", "")
                status = test_item.get("status", "")
                for gen_test in self.generated_tests:
                    func = gen_test.get("function_name", "")
                    if func and func in name:
                        gen_test["status"] = status
                        gen_test["last_error"] = test_item.get("error_message")

    def add_fix_suggestion(self, function_code: str, explanation: str, diff: str):
        with self._lock:
            suggestion = {
                "function_code": function_code,
                "explanation": explanation,
                "diff": diff,
                "status": "pending"
            }
            # Avoid duplicate pending suggestions for same code
            existing = next((f for f in self.fix_suggestions if f["function_code"] == function_code), None)
            if existing:
                existing.update(suggestion)
            else:
                self.fix_suggestions.append(suggestion)

    def get_dashboard_data(self) -> Dict[str, Any]:
        with self._lock:
            passed_tests_count = self.last_test_run.get("summary", {}).get("passed", 0)
            failed_tests_count = self.last_test_run.get("summary", {}).get("failed", 0)

            return {
                "status": "success",
                "summary": {
                    "total_functions_scanned": self.total_functions_scanned,
                    "tested_count": self.tested_count,
                    "untested_count": self.untested_count,
                    "generated_tests_count": len(self.generated_tests),
                    "passed_tests_count": passed_tests_count,
                    "failed_tests_count": failed_tests_count,
                    "pending_fixes_count": len(self.fix_suggestions)
                },
                "untested_functions": self.untested_functions,
                "generated_tests": self.generated_tests,
                "last_test_run": self.last_test_run,
                "fix_suggestions": self.fix_suggestions
            }


# Global shared state instance
dashboard_state = DashboardState()
