from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4
from app.main import app  # ensure main is imported for side effects
import pytest
from unittest.mock import patch
from datetime import datetime
from types import SimpleNamespace

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_frontend_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Calculator" in response.text  # crude check for template rendering

def test_register_and_login():
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"test{uuid4().hex[:8]}@example.com",
        "username": f"user_{uuid4().hex[:8]}",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!"
    }
    reg = client.post("/auth/register", json=user_data)
    assert reg.status_code in (201, 400)  # 400 if user already exists

    if reg.status_code == 400:
        return None  # skip login if registration failed

    login = client.post("/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token
    return token


def test_create_list_get_update_delete_calculation():
    token = test_register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    calc = client.post("/calculations", json={
        "type": "addition",
        "inputs": [2.0, 3.0]
    }, headers=headers)
    assert calc.status_code == 201
    calc_id = calc.json()["id"]
    assert calc.json()["result"] == 5

    # List
    listing = client.get("/calculations", headers=headers)
    assert listing.status_code == 200
    assert any(c["id"] == calc_id for c in listing.json())

    # Get
    get = client.get(f"/calculations/{calc_id}", headers=headers)
    assert get.status_code == 200
    assert get.json()["result"] == 5

    # Update
    update = client.put(f"/calculations/{calc_id}", json={
        "inputs": [10, 5]
    }, headers=headers)
    assert update.status_code == 200
    assert update.json()["result"] == 15

    # Delete
    delete = client.delete(f"/calculations/{calc_id}", headers=headers)
    assert delete.status_code == 204

    # Confirm deletion
    confirm = client.get(f"/calculations/{calc_id}", headers=headers)
    assert confirm.status_code == 404

def get_token():
    username = f"user_{uuid4().hex[:8]}"
    password = "SecurePass123!"
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"{username}@example.com",
        "username": username,
        "password": password,
        "confirm_password": password
    }
    reg = client.post("/auth/register", json=user_data)
    assert reg.status_code == 201

    login = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    return token, username, password



@pytest.mark.parametrize("calc_type,inputs,expected", [
    ("addition", [2.0, 3.0], 5.0),
    ("subtraction", [10.0, 4.0], 6.0),
    ("multiplication", [3.0, 5.0], 15.0),
    ("division", [100.0, 2.0], 50.0),
])
def test_calculation_types(calc_type, inputs, expected):
    token, _, _ = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/calculations", json={
        "type": calc_type,
        "inputs": inputs
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["result"] == expected


def test_login_form():
    _, username, password = get_token()
    response = client.post("/auth/token", data={
        "username": username,
        "password": password
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_calculation_crud():
    token, _, _  = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    create = client.post("/calculations", json={
        "type": "addition",
        "inputs": [1.0, 2.0]
    }, headers=headers)
    assert create.status_code == 201
    calc_id = create.json()["id"]

    # Get
    get = client.get(f"/calculations/{calc_id}", headers=headers)
    assert get.status_code == 200
    assert get.json()["result"] == 3.0

    # Update
    update = client.put(f"/calculations/{calc_id}", json={
        "inputs": [10.0, 5.0]
    }, headers=headers)
    assert update.status_code == 200
    assert update.json()["result"] == 15.0

    # Delete
    delete = client.delete(f"/calculations/{calc_id}", headers=headers)
    assert delete.status_code == 204

    # Confirm deletion
    confirm = client.get(f"/calculations/{calc_id}", headers=headers)
    assert confirm.status_code == 404

def test_invalid_uuid():
    token, _, _  = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/calculations/not-a-uuid", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid calculation id format."

def test_division_by_zero():
    token, _, _ = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/calculations", json={
        "type": "division",
        "inputs": [100.0, 0.0]
    }, headers=headers)
    assert response.status_code == 422
    assert "Cannot divide by zero" in response.text

def test_lifespan_startup():
    with TestClient(app) as client:
        # Trigger any request to ensure app is running
        response = client.get("/health")
        assert response.status_code == 200

def test_register_duplicate_email():
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "SecurePass123!"

    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "username": username,
        "password": password,
        "confirm_password": password
    }

    # First registration should succeed
    response1 = client.post("/auth/register", json=user_data)
    assert response1.status_code == 201

    # Second registration with same email should fail
    user_data["username"] = f"{username}_new"  # change username, keep email
    response2 = client.post("/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "already" in response2.json()["detail"].lower()

def test_login_invalid_credentials():
    # First, register a valid user
    username = f"user_{uuid4().hex[:8]}"
    password = "SecurePass123!"
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"{username}@example.com",
        "username": username,
        "password": password,
        "confirm_password": password
    }
    reg = client.post("/auth/register", json=user_data)
    assert reg.status_code == 201

    # Now try logging in with the wrong password
    response = client.post("/auth/login", json={
        "username": username,
        "password": "WrongPassword!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_login_expires_at_naive_datetime():
    username = f"user_{uuid4().hex[:8]}"
    password = "SecurePass123!"
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"{username}@example.com",
        "username": username,
        "password": password,
        "confirm_password": password
    }
    reg = client.post("/auth/register", json=user_data)
    assert reg.status_code == 201

    # Create a mock user object with attributes
    mock_user = SimpleNamespace(
        id=uuid4(),
        username=username,
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        is_active=True,
        is_verified=True
    )

    naive_expires = datetime.utcnow().replace(tzinfo=None)

    with patch("app.main.User.authenticate") as mock_auth:
        mock_auth.return_value = {
            "user": mock_user,
            "access_token": "fake-access",
            "refresh_token": "fake-refresh",
            "expires_at": naive_expires
        }

        response = client.post("/auth/login", json={
            "username": username,
            "password": password
        })

        assert response.status_code == 200
        expires_at = response.json()["expires_at"]
        assert "T" in expires_at and expires_at.endswith("Z")

def test_login_form_invalid_credentials():
    username = f"user_{uuid4().hex[:8]}"
    password = "SecurePass123!"
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"{username}@example.com",
        "username": username,
        "password": password,
        "confirm_password": password
    }

    # Register the user
    reg = client.post("/auth/register", json=user_data)
    assert reg.status_code == 201

    # Attempt login with wrong password using form data
    response = client.post("/auth/token", data={
        "username": username,
        "password": "WrongPassword!"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_create_calculation_value_error():
    token, _, _ = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.main.Calculation.create") as mock_create:
        mock_create.side_effect = ValueError("Invalid calculation")

        response = client.post("/calculations", json={
            "type": "addition",
            "inputs": [1.0, 2.0]
        }, headers=headers)

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid calculation"

def test_update_calculation_invalid_uuid():
    token, _, _ = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put("/calculations/not-a-uuid", json={
        "inputs": [10.0, 5.0]
    }, headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid calculation id format."

def test_update_calculation_not_found():
    token, _, _ = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Generate a valid UUID that doesn't exist in the DB
    non_existent_id = str(uuid4())

    response = client.put(f"/calculations/{non_existent_id}", json={
        "inputs": [10.0, 5.0]
    }, headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."


def test_delete_calculation_invalid_uuid():
    token, _, _ = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/calculations/not-a-uuid", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid calculation id format."

def test_delete_calculation_not_found():
    token, _, _ = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    non_existent_id = str(uuid4())

    response = client.delete(f"/calculations/{non_existent_id}", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."

