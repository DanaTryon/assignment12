import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.auth.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse
from app.models.user import User
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime

# Force coverage to register the module
import app.auth.dependencies

# Create a test app that uses the dependencies
test_app = FastAPI()

@test_app.get("/whoami")
def whoami(user: UserResponse = Depends(get_current_user)):
    return {"username": user.username}

@test_app.get("/active-check")
def active_check(user: UserResponse = Depends(get_current_active_user)):
    return {"status": "active"}

client = TestClient(test_app)

def test_get_current_user_invalid_token_route():
    with patch("app.auth.dependencies.User.verify_token", return_value=None):
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
        response = client.get("/active-check", headers={"Authorization": "Bearer validtoken"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Inactive user"
