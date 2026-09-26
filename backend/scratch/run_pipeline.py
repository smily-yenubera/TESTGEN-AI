import urllib.request
import json
from pathlib import Path

repo_path = r"C:\Testgen-ai\demo_repo"
base_url = "http://127.0.0.1:8000"


def post(endpoint, data):
    req = urllib.request.Request(
        f"{base_url}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode("utf-8"))


print("=== STEP 1: SCAN REPO ===")
scan_res = post("/scan", {"path": repo_path})
print(json.dumps(scan_res, indent=2))

print("\n=== STEP 2: GENERATE TESTS ===")
gen_res = post("/generate-tests", {"repo_path": repo_path, "function_name": "validate_email"})
print(json.dumps(gen_res, indent=2))

print("\n=== STEP 3: RUN TESTS ===")
run_res = post("/run-tests", {"test_file_path": gen_res["test_file_path"]})
print(json.dumps(run_res, indent=2))

print("\n=== STEP 4: SUGGEST FIX ===")
failed_test = next((t for t in run_res.get("tests", []) if t["status"] == "failed"), None)
error_trace = failed_test["traceback"] if failed_test else "IndexError: list index out of range"
function_code = (Path(repo_path) / "utils.py").read_text()

fix_res = post("/suggest-fix", {
    "function_code": function_code,
    "error_trace": error_trace
})
print(json.dumps(fix_res, indent=2))
