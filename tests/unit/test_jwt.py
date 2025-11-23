import pytest
import asyncio
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.auth import jwt as jwt_utils
from app.schemas.token import TokenType
from app.core.config import get_settings

settings = get_settings()

# -------------------------------
# Password hashing
# -------------------------------

def test_password_hash_and_verify():
    raw = "SecurePass123!"
    hashed = jwt_utils.get_password_hash(raw)
    assert jwt_utils.verify_password(raw, hashed)

# -------------------------------
# create_token
# -------------------------------

def test_create_token_success():
    token = jwt_utils.create_token("user123", TokenType.ACCESS, timedelta(minutes=5))
    assert isinstance(token, str)

def test_create_token_failure(monkeypatch):
    monkeypatch.setattr(jwt_utils.jwt, "encode", lambda *a, **k: (_ for _ in ()).throw(Exception("boom")))
    with pytest.raises(HTTPException) as exc_info:
        jwt_utils.create_token("user123", TokenType.ACCESS)
    assert exc_info.value.status_code == 500
    assert "Could not create token" in exc_info.value.detail

# -------------------------------
# decode_token
# -------------------------------

@pytest.mark.asyncio
async def test_decode_token_valid(monkeypatch):
    token = jwt_utils.create_token("user123", TokenType.ACCESS, timedelta(minutes=5))
    monkeypatch.setattr(jwt_utils, "is_blacklisted", AsyncMock(return_value=False))
    payload = await jwt_utils.decode_token(token, TokenType.ACCESS)
    assert payload["sub"] == "user123"
    assert payload["type"] == "access"

@pytest.mark.asyncio
async def test_decode_token_expired(monkeypatch):
    token = jwt_utils.create_token("user123", TokenType.ACCESS, timedelta(seconds=-1))
    monkeypatch.setattr(jwt_utils, "is_blacklisted", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as exc_info:
        await jwt_utils.decode_token(token, TokenType.ACCESS)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has expired"

@pytest.mark.asyncio
async def test_decode_token_invalid_type(monkeypatch):
    token = "fake-token"
    monkeypatch.setattr(jwt_utils.jwt, "decode", lambda *a, **k: {"sub": "user123", "type": "refresh", "jti": "abc"})
    monkeypatch.setattr(jwt_utils, "is_blacklisted", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as exc_info:
        await jwt_utils.decode_token(token, TokenType.ACCESS)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token type"


@pytest.mark.asyncio
async def test_decode_token_revoked(monkeypatch):
    token = jwt_utils.create_token("user123", TokenType.ACCESS)
    monkeypatch.setattr(jwt_utils, "is_blacklisted", AsyncMock(return_value=True))
    with pytest.raises(HTTPException) as exc_info:
        await jwt_utils.decode_token(token, TokenType.ACCESS)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has been revoked"

@pytest.mark.asyncio
async def test_decode_token_invalid_signature(monkeypatch):
    # Tamper with secret so signature fails
    token = jwt_utils.create_token("user123", TokenType.ACCESS)
    monkeypatch.setattr(jwt_utils.settings, "JWT_SECRET_KEY", "wrongsecret")
    monkeypatch.setattr(jwt_utils, "is_blacklisted", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as exc_info:
        await jwt_utils.decode_token(token, TokenType.ACCESS)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

# -------------------------------
# get_current_user
# -------------------------------

@pytest.mark.asyncio
async def test_get_current_user_success(monkeypatch):
    token = jwt_utils.create_token("user123", TokenType.ACCESS)
    fake_user = MagicMock()
    fake_user.is_active = True
    fake_db = MagicMock()
    fake_db.query().filter().first.return_value = fake_user
    monkeypatch.setattr(jwt_utils, "decode_token", AsyncMock(return_value={"sub": "user123"}))
    result = await jwt_utils.get_current_user(token=token, db=fake_db)
    assert result is fake_user

@pytest.mark.asyncio
async def test_get_current_user_not_found(monkeypatch):
    token = jwt_utils.create_token("user123", TokenType.ACCESS)
    fake_db = MagicMock()
    fake_db.query().filter().first.return_value = None
    monkeypatch.setattr(jwt_utils, "decode_token", AsyncMock(return_value={"sub": "user123"}))
    with pytest.raises(HTTPException) as exc_info:
        await jwt_utils.get_current_user(token=token, db=fake_db)
    assert exc_info.value.status_code == 401
    assert "User not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_inactive(monkeypatch):
    token = jwt_utils.create_token("user123", TokenType.ACCESS)
    fake_user = MagicMock()
    fake_user.is_active = False
    fake_db = MagicMock()
    fake_db.query().filter().first.return_value = fake_user
    monkeypatch.setattr(jwt_utils, "decode_token", AsyncMock(return_value={"sub": "user123"}))
    with pytest.raises(HTTPException) as exc_info:
        await jwt_utils.get_current_user(token=token, db=fake_db)
    assert exc_info.value.status_code == 401
    assert "Inactive user" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_decode_exception(monkeypatch):
    token = "badtoken"
    fake_db = MagicMock()
    async def fake_decode(*a, **k):
        raise Exception("decode failed")
    monkeypatch.setattr(jwt_utils, "decode_token", fake_decode)
    with pytest.raises(HTTPException) as exc_info:
        await jwt_utils.get_current_user(token=token, db=fake_db)
    assert exc_info.value.status_code == 401
    assert "decode failed" in exc_info.value.detail

def test_create_token_with_uuid(monkeypatch):
    # Create a UUID
    user_uuid = uuid.uuid4()
    # Call create_token with a UUID
    token = jwt_utils.create_token(user_uuid, TokenType.ACCESS, expires_delta=None)
    assert isinstance(token, str)
    # Decode the token to confirm the UUID was converted to string
    payload = jwt_utils.jwt.decode(
        token,
        jwt_utils.settings.JWT_SECRET_KEY,
        algorithms=[jwt_utils.settings.ALGORITHM]
    )
    assert payload["sub"] == str(user_uuid)