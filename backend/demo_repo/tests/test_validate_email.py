"""
Pytest test suite for function `validate_email`
Generated covering happy path, edge cases, and error cases.
"""
import sys
from pathlib import Path
import pytest

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from utils import validate_email


def test_validate_email_happy_path():
    """Happy path test with standard valid email."""
    assert validate_email("user@example.com") is True


def test_validate_email_edge_cases():
    """Edge cases with empty or invalid format emails."""
    assert validate_email("") is False
    assert validate_email("user@domain") is False
    assert validate_email("invalid-email") is False


def test_validate_email_error_cases():
    """Error cases with non-string inputs."""
    with pytest.raises(TypeError):
        validate_email(123)
