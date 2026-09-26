import urllib.request
import json

code = "def validate_email(email):\n    # Intentionally broken function: raises IndexError when called\n    return email.split('@')[10]"
trace = "IndexError: list index out of range"

req = urllib.request.Request(
    "http://127.0.0.1:8000/suggest-fix",
    data=json.dumps({"function_code": code, "error_trace": trace}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
print(json.dumps(res, indent=2))
