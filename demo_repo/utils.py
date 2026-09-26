"""
Helper utilities for demo app
"""

def format_response(data, code=200):
    return {"status": code, "data": data}


def validate_email(email):
    if not isinstance(email, str):
        raise TypeError("Email must be a string")
    return "@" in email and "." in email
