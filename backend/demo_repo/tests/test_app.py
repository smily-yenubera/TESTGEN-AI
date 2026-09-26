"""
Tests for app.py
"""
from app import index, get_users, create_user


def test_index():
    res = index()
    assert res["message"] == "Welcome to demo app"


def test_get_users():
    users = get_users()
    assert len(users) == 2


def test_create_user():
    user = create_user("charlie", "charlie@example.com")
    assert user["username"] == "charlie"
