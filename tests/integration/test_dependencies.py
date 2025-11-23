import pytest
from unittest.mock import patch
from fastapi import HTTPException, status, Depends, FastAPI, testclient
from fastapi.testclient import TestClient
import app.auth.dependencies
from app.auth.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse
from app.models.user import User
from uuid import uuid4
from datetime import datetime, timezone
from types import SimpleNamespace


# Temporary app for dependency testing
test_app = FastAPI()

@test_app.get("/whoami")
def whoami(user: UserResponse = Depends(get_current_user)):
    return {"username": user.username}

@test_app.get("/active-check")
def active_check(user: UserResponse = Depends(get_current_active_user)):
    return {"status": "active"}

# Sample user data dictionaries for testing
sample_user_data = {
    "id": uuid4(),
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": True,
    "is_verified": True,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

inactive_user_data = {
    "id": uuid4(),
    "username": "inactiveuser",
    "email": "inactive@example.com",
    "first_name": "Inactive",
    "last_name": "User",
    "is_active": False,
    "is_verified": False,
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc)
}

# Fixture for mocking token verification
@pytest.fixture
def mock_verify_token():
    with patch.object(User, 'verify_token') as mock:
        yield mock

# Test get_current_user with valid token and complete payload
def test_get_current_user_valid_token_existing_user(mock_verify_token):
    mock_verify_token.return_value = sample_user_data

    user_response = get_current_user(token="validtoken")

    assert isinstance(user_response, UserResponse)
    assert user_response.id == sample_user_data["id"]
    assert user_response.username == sample_user_data["username"]
    assert user_response.email == sample_user_data["email"]
    assert user_response.first_name == sample_user_data["first_name"]
    assert user_response.last_name == sample_user_data["last_name"]
    assert user_response.is_active == sample_user_data["is_active"]
    assert user_response.is_verified == sample_user_data["is_verified"]
    assert user_response.created_at == sample_user_data["created_at"]
    assert user_response.updated_at == sample_user_data["updated_at"]

    mock_verify_token.assert_called_once_with("validtoken")

# Test get_current_user with invalid token (returns None)
def test_get_current_user_invalid_token(mock_verify_token):
    mock_verify_token.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalidtoken")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"

    mock_verify_token.assert_called_once_with("invalidtoken")

# Test get_current_user with valid token but incomplete payload (simulate missing fields)
def test_get_current_user_valid_token_incomplete_payload(mock_verify_token):
    # Return an empty dict simulating missing required fields
    mock_verify_token.return_value = {}

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="validtoken")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"

    mock_verify_token.assert_called_once_with("validtoken")

# Test get_current_active_user with an active user
def test_get_current_active_user_active(mock_verify_token):
    mock_verify_token.return_value = sample_user_data

    current_user = get_current_user(token="validtoken")
    active_user = get_current_active_user(current_user=current_user)

    assert isinstance(active_user, UserResponse)
    assert active_user.is_active is True

# Test get_current_active_user with an inactive user
def test_get_current_active_user_inactive(mock_verify_token):
    mock_verify_token.return_value = inactive_user_data

    current_user = get_current_user(token="validtoken")

    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(current_user=current_user)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Inactive user"

def test_get_current_user_invalid_token_route():
    with patch("app.auth.dependencies.User.verify_token", return_value=None):
        client = TestClient(test_app)
        response = client.get("/whoami", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

def test_get_current_active_user_inactive_route():
    inactive_user_dict = {
        "id": str(uuid4()),
        "username": "inactive_user",
        "email": "inactive@example.com",
        "first_name": "Inactive",
        "last_name": "User",
        "is_active": False,
        "is_verified": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    with patch("app.auth.dependencies.User.verify_token", return_value=inactive_user_dict):
        client = TestClient(test_app)
        response = client.get("/active-check", headers={"Authorization": "Bearer validtoken"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Inactive user"


