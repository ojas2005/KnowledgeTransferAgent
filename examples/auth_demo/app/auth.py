"""Credential checks and signed session creation."""

import hashlib
import hmac
import os

from .db import get_user


def verify_password(password: str, expected_hash: str) -> bool:
    supplied = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(supplied, expected_hash)


def authenticate(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user


def create_session(user_id: int) -> str:
    secret = os.environ["SESSION_SECRET"]
    message = str(user_id).encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return "{}.{}".format(user_id, signature)
