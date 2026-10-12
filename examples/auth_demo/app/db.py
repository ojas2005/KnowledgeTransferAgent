"""In-memory user records for the demo."""

USERS = {"ada": {"id": 1, "password_hash": "41bd876b085d6031cb0e04de35b88d77f83a4ba39f879fee40805ac19e356023"}}


def get_user(username: str):
    return USERS.get(username)
