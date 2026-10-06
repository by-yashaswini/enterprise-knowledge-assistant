import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_token


def test_password_hashing():
    hashed = hash_password("SecurePass123!")
    assert hashed != "SecurePass123!"
    assert verify_password("SecurePass123!", hashed)
    assert not verify_password("WrongPass", hashed)


def test_jwt_roundtrip():
    token = create_access_token(subject="user-123", extra_claims={"role": "ENGINEER"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "ENGINEER"
    assert payload["type"] == "access"