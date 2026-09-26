"""
Repository scanning logic to detect untested functions and produce overall code metrics.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Any


def scan_repo(path: str) -> List[Dict[str, Any]]:
    """
    Walks a given directory, parses Python files using the ast module,
    and returns a list of functions that have no matching test file.
    """
    res = scan_repo_full(path)
    return res["untested_functions"]


def scan_repo_full(path: str) -> Dict[str, Any]:
    """
    Walks directory, parses Python files using AST, and returns detailed dictionary
    containing all functions categorized by tested and untested status.
    A function is considered tested if a module-level test file (test_<module>.py)
    OR a function-level test file (test_<function_name>.py) exists in a /tests directory.
    """
    repo_path = Path(path).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        raise ValueError(f"Path does not exist or is not a directory: {path}")

    # Find all test file names present in any 'tests' directory under repo_path
    test_files = set()
    for p in repo_path.rglob("*.py"):
        if "tests" in p.parts:
            test_files.add(p.name)

    all_functions: List[Dict[str, Any]] = []
    untested_functions: List[Dict[str, Any]] = []
    tested_functions: List[Dict[str, Any]] = []

    ignored_dirs = {".git", ".venv", "venv", "env", "__pycache__", "build", "dist", ".pytest_cache", "site-packages"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignored_dirs and d != "tests"]

        root_path = Path(root)
        if "tests" in root_path.parts:
            continue

        for file in files:
            if not file.endswith(".py") or file.startswith("test_") or file.endswith("_test.py"):
                continue

            file_path = root_path / file
            relative_file_path = file_path.relative_to(repo_path)
            
            expected_module_test_filename = f"test_{file}"

            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(file_path))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [arg.arg for arg in node.args.args]
                    expected_func_test_filename = f"test_{node.name}.py"

                    # Check module-level test_module.py OR function-level test_func.py
                    has_matching_test = (
                        expected_module_test_filename in test_files or
                        expected_func_test_filename in test_files
                    )

                    matching_test_file = (
                        expected_func_test_filename if expected_func_test_filename in test_files
                        else expected_module_test_filename
                    )

                    func_item = {
                        "file": str(relative_file_path).replace("\\", "/"),
                        "function": node.name,
                        "line": node.lineno,
                        "args": args,
                        "matching_test_file": matching_test_file,
                        "is_tested": has_matching_test
                    }
                    all_functions.append(func_item)
                    if has_matching_test:
                        tested_functions.append(func_item)
                    else:
                        untested_functions.append(func_item)

    return {
        "total": len(all_functions),
        "tested_count": len(tested_functions),
        "untested_count": len(untested_functions),
        "all_functions": all_functions,
        "untested_functions": untested_functions,
        "tested_functions": tested_functions
    }
