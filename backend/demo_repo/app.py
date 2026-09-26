"""
Flask-style demo app entrypoint
"""

def index():
    return {"message": "Welcome to demo app"}


def get_users():
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


def create_user(username, email):
    return {"id": 3, "username": username, "email": email}
