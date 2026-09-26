import ast
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.scanner import scan_repo, scan_repo_full
from app.generator import generate_tests
from app.runner import run_tests
from app.fixer import suggest_fix, apply_fix
from app.state import dashboard_state

app = FastAPI(title="TestGen AI Backend")

# Allow the set of permitted CORS origins to be configured via an environment
# variable so that the deployed frontend URL can be injected at runtime without
# code changes.  Falls back to localhost for local development.
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    path: str


class GenerateTestsRequest(BaseModel):
    repo_path: str
    function_name: str
    file_path: Optional[str] = None


class RunTestsRequest(BaseModel):
    test_file_path: str


class SuggestFixRequest(BaseModel):
    function_code: str
    error_trace: str


class ApplyFixRequest(BaseModel):
    repo_path: str
    file_path: Optional[str] = "utils.py"
    function_name: str
    fixed_code: Optional[str] = None
    diff: Optional[str] = None


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/dashboard-data")
def dashboard_data_endpoint():
    return dashboard_state.get_dashboard_data()


@app.post("/scan")
def scan_endpoint(request: ScanRequest):
    try:
        full_res = scan_repo_full(request.path)
        untested_functions = full_res["untested_functions"]
        
        dashboard_state.update_scan(
            total=full_res["total"],
            tested=full_res["tested_count"],
            untested=full_res["untested_count"],
            all_functions=full_res["all_functions"],
            untested_funcs=untested_functions
        )

        return {
            "status": "success",
            "untested_functions": untested_functions,
            "count": len(untested_functions)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scanning failed: {str(e)}")


def _find_function_in_repo(repo_path: Path, function_name: str, file_path_hint: Optional[str] = None):
    for p in repo_path.rglob("*.py"):
        if "tests" in p.parts or "venv" in p.parts or ".venv" in p.parts:
            continue
        if file_path_hint and not str(p).replace("\\", "/").endswith(file_path_hint.replace("\\", "/")):
            continue
        try:
            content = p.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(p))
            lines = content.splitlines()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                    end_line = getattr(node, 'end_lineno', node.lineno + 10)
                    func_lines = lines[node.lineno - 1 : end_line]
                    func_code = "\n".join(func_lines)
                    module_name = p.stem
                    return p, module_name, func_code
        except Exception:
            continue
    return None, None, None


@app.post("/generate-tests")
def generate_tests_endpoint(request: GenerateTestsRequest):
    repo_path = Path(request.repo_path).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Repository path does not exist: {request.repo_path}")

    target_file, module_name, function_code = _find_function_in_repo(
        repo_path, request.function_name, request.file_path
    )

    if not function_code:
        raise HTTPException(
            status_code=404,
            detail=f"Function '{request.function_name}' not found in repository at {request.repo_path}"
        )

    generated_code = generate_tests(function_code, request.function_name, module_name=module_name)

    tests_dir = repo_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    test_file_path = tests_dir / f"test_{request.function_name}.py"
    test_file_path.write_text(generated_code, encoding="utf-8")

    dashboard_state.add_generated_test(
        function_name=request.function_name,
        module_name=module_name,
        test_file_path=str(test_file_path),
        generated_code=generated_code
    )

    return {
        "status": "success",
        "function_name": request.function_name,
        "module_name": module_name,
        "test_file_path": str(test_file_path),
        "generated_code": generated_code
    }


@app.post("/run-tests")
def run_tests_endpoint(request: RunTestsRequest):
    try:
        results = run_tests(request.test_file_path)
        dashboard_state.update_test_run(results)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")


@app.post("/suggest-fix")
def suggest_fix_endpoint(request: SuggestFixRequest):
    try:
        result = suggest_fix(request.function_code, request.error_trace)
        if "explanation" in result and "diff" in result:
            dashboard_state.add_fix_suggestion(
                function_code=request.function_code,
                explanation=result["explanation"],
                diff=result["diff"]
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fix suggestion failed: {str(e)}")


@app.post("/apply-fix")
def apply_fix_endpoint(request: ApplyFixRequest):
    try:
        res = apply_fix(
            repo_path=request.repo_path,
            file_path=request.file_path,
            function_name=request.function_name,
            fixed_code=request.fixed_code,
            diff=request.diff
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apply fix failed: {str(e)}")
