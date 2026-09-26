"""
Pytest test suite for function `format_response`
Generated covering happy path, edge cases, and error cases.
"""
import sys
from pathlib import Path
import pytest

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from utils import format_response


def test_format_response_happy_path():
    """Happy path test with standard payload."""
    res = format_response({"key": "value"})
    assert res["status"] == 200
    assert res["data"] == {"key": "value"}


def test_format_response_edge_cases():
    """Edge cases with custom code and None payload."""
    res = format_response(None, code=404)
    assert res["status"] == 404
    assert res["data"] is None


def test_format_response_error_cases():
    """Error cases with unexpected arguments."""
    with pytest.raises(TypeError):
        format_response()
